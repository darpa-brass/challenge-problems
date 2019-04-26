# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ---    Radio Queue Status Display for Link Manager Algorithm Evaluator     ---
# ---                                                                        ---
# --- Last Updated: February 28, 2019                                        ---
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

import sys
import os
import argparse
import json
from collections import deque
import threading
import time
import math
import curses
from curses import wrapper
import signal
import random
import logging

next_timer = 0
epoch_ms = 100                      # epoch size in milliseconds
epoch_sec = epoch_ms / 1000         # epoch size converted to seconds
epochs_per_sec = 1000 / epoch_ms    # number of epochs per second
epoch_num = 0

lm_eff_eff_vals_q = deque()

MAX_BW = 10000000                   # max bandwidth of RF channel in bits per second
MAX_BW_MBPS = MAX_BW / 1000000      # max bandwidth of RF channel in Megabits per second

MAX_QUEUE_SIZE_BYTES = 4194240      # TmNS Radio queues not expected to be larger than 4.2 MB (per DSCP Queue?).
enforce_max_q_size = False         # Should the simulation enforce the MAX_QUEUE_SIZE_BYTES as a hard limit?
debug = 0                           # Debug value: initially 0, e.g. no debug

radio_list = []                     # List of Radio objects
system_vals_array = []              # Array for holding last 'N' system values for sliding average
AVG_WINDOW_SIZE = 100

msg_list = []

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


class Radio:
    """Class to contain radio status and statistics."""
    
    def __init__(self, name):
        self.name = name
        self.q = deque()
        self.din_bps = 0                # bits per second
        self.dout_bps = 0               # bits per second
        self.inburst_factor = 0.0       # deviation from input value
        self.burst_din_bps = 0.0        # actual data input rate in bits per second
        self.value_per_kb_tx = 0.0      # points earned for each KB transmitted
        self.current_epoch_value = 0.0  # value of transmitted kbits from last epoch
        self.q_delta_bps = 0            # bits per second
        self.q_len = 0                  # bytes
        self.epochs_per_sec = 1         # number of epochs per second
        self.online = True              # status: True: online, False: offline
        
    def update_q(self):
        if self.online is False:
            return
        self.burst_din_bps = self.din_bps * (1+(random.uniform((-1*self.inburst_factor), self.inburst_factor)))
        self.q_delta_bps = self.burst_din_bps - self.dout_bps

        # if q_delta_bps is positive (+), then queue grows
        if self.q_delta_bps > 0:
            q_delta_per_epoch = int(math.ceil(self.q_delta_bps / self.epochs_per_sec / 8))
            q_bytes_remaining = MAX_QUEUE_SIZE_BYTES - self.q_len
            if enforce_max_q_size and (q_delta_per_epoch > q_bytes_remaining):
                for x in range(q_bytes_remaining):
                    self.q.append(x)
            else:
                for x in range(q_delta_per_epoch):
                    self.q.append(x)
            self.current_epoch_value = ((self.dout_bps / self.epochs_per_sec) / 1000) * self.value_per_kb_tx
        # if q_delta_bps is negative (-), then queue shrinks
        elif self.q_delta_bps < 0:
            q_delta_per_epoch = int(math.floor(self.q_delta_bps / self.epochs_per_sec / 8))
            if self.q_len <= (abs(q_delta_per_epoch)):
                self.current_epoch_value = (((self.din_bps / self.epochs_per_sec) / 1000) + ((self.q_len * 8) / 1000))\
                                           * self.value_per_kb_tx
                self.q.clear()
            else:
                for x in range(abs(q_delta_per_epoch)):
                    self.q.popleft()
                self.current_epoch_value = ((self.dout_bps / self.epochs_per_sec) / 1000) * self.value_per_kb_tx
        # if q_delta_bps is 0, then queue remains the same
        elif self.q_delta_bps == 0:
            self.current_epoch_value = ((self.dout_bps / self.epochs_per_sec) / 1000) * self.value_per_kb_tx
        self.q_len = len(self.q)
        
    def go_offline(self):
        self.online = False
        self.din_bps = 0
        self.dout_bps = 0
        self.inburst_factor = 0.0
        self.burst_din_bps = 0.0
        self.q_delta_bps = 0
        self.value_per_kb_tx = 0.0
        self.current_epoch_value = 0.0
        self.q.clear()
        self.q_len = len(self.q)
        

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


class Message:
    """Class to contain status messages (infos/warnings/errors)."""

    def __init__(self, name='Unknown', level='UNKNOWN', msg=" "):
        self.name = name
        self.level = level
        self.msg = msg


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

def setup_logger():
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    log = logging.getLogger()

    fileHandler = logging.FileHandler(__name__)
    fileHandler.setFormatter(logFormatter)
    log.addHandler(fileHandler)

    # consoleHandler = logging.StreamHandler()
    # consoleHandler.setFormatter(logFormatter)
    # log.addHandler(consoleHandler)

    log.setLevel('INFO')
    return log


def run_epoch():
    global epoch_num
    global epochs_per_sec
    global epoch_ms
    global radio_list
    global msg_list
    global stdscr
    global next_timer
    global time_pad
    global text_d
    global realtime_mode
    global q_viz_mode
    global history_plot_mode
    global data_input_rates
    global bw_allocs
    global database

    
    # Set callback timer for next epoch update
    next_timer = threading.Timer(epoch_sec, run_epoch)
    next_timer.start()

    height, width = stdscr.getmaxyx()

    stdscr.nodelay(True)

    # Set Command Line Mode
    keypress = stdscr.getch()
    if keypress != -1:
        if keypress == ord('r'):    # If selected, use 'Realtime Mode'
            realtime_mode = True
        elif keypress == ord('s'):  # If selected, use 'Slow Refresh mode'
            realtime_mode = False
        elif keypress == ord('q'):  # If selected, toggle Queue Visualization
            q_viz_mode = not q_viz_mode
        elif keypress == ord('h'):  # If selected, toggle history plot
            history_plot_mode = not history_plot_mode
        elif keypress == ord('x'):  # If selected, exit application
            next_timer.cancel()
            restore_screen()
            sys.exit()

    # Reload JSON file for Radio Data Input Rates, parse contents, and update Radio objects
    # Reload JSON file for LM Bandwidth Allocations for Radio Data Output Rates (a.k.a. the "RF Drain Rate")

    if database:
        radio_usage_node_list = database.get_nodes_by_type('Radio_Input')
        radio_control_node_list = database.get_nodes_by_type('Radio_Control')
        radio_usage_node = radio_usage_node_list[0]
        radio_control_node = radio_control_node_list[0]
        ldict_radios = radio_usage_node.Input_Rate
        d_bw_allocs = radio_control_node.BW_Allocs
    else:
        with open(data_input_rates, 'r') as f:
            ldict_radios = json.load(f)

        with open(bw_allocs, 'r') as f:
            d_bw_allocs = json.load(f)

    # Parse the list of Radio dictionaries from JSON file
    for d in ldict_radios:
        unknown_radio = True
        for r in radio_list:
            if r.name == d['RadioName']:
                if debug == 3:
                    print("found radio in list already")
                unknown_radio = False
                r.online = True
                if "DataInRate-bps" in d:
                    r.din_bps = d["DataInRate-bps"]
                if "Burstiness" in d:
                    r.inburst_factor = d["Burstiness"]
                else:
                    r.inburst_factor = 0.0
                if "ValuePerKbTx" in d:
                    r.value_per_kb_tx = d["ValuePerKbTx"]
                break
        if unknown_radio:
            add_radio_to_list(d)

    # If a Radio is removed from a test mission (e.g., the Data Input JSON file), then mark as "offline"
    if len(ldict_radios) < len(radio_list):
        for r in radio_list:
            offline_radio = True
            for d in ldict_radios:
                if d['RadioName'] == r.name:
                    offline_radio = False
                    break
            if offline_radio:
                if r.online:
                    r.go_offline()         # If the offline radio was previously online, call go_offline()
                    if debug >= 1:
                        print("'{}' has gone offline.".format(r.name))



    # Parse the Bandwidth Allocations dictionaries from JSON file
    for d in d_bw_allocs:
        unknown_radio = True
        for r in radio_list:
            if r.name == d['RadioName']:
                if debug == 3:
                    print("found radio in list already")
                unknown_radio = False
                if "AllocatedBw-bps" in d:
                    r.dout_bps = d["AllocatedBw-bps"]
                else:
                    r.dout_bps = 0
                break
        if unknown_radio:
            add_radio_to_list(d)

    # If a Radio is removed from the LM's bandwidth allocations, zeroize the corresponding radio_list value for din_bps
    if len(d_bw_allocs) < len(radio_list):
        for r in radio_list:
            unsched_radio = True
            for d in d_bw_allocs:
                if d['RadioName'] == r.name:
                    unsched_radio = False
                    break
            if unsched_radio:
                r.dout_bps = 0      # This radio is no longer being scheduled by the LM, so drop its allocations to 0

    # Update all Radio info
    for r in radio_list:
        r.update_q()

    queues = write_qlens_to_json(radio_list)

    if database:
        try:
            radio_queues_node_list = database.get_nodes_by_type("Radio_Queues")
            radio_queues_node = radio_queues_node_list[0]

            database.update_node(radio_queues_node._rid,
                                 {'Radio_Queues': queues},
                                 version=radio_usage_node._version,
                                 transaction=True)
        except:
            pass

    total_bw_allocated = 0
    total_bw_utilized = 0

    for r in radio_list:
        total_bw_allocated += r.dout_bps
        if r.current_epoch_value == 0:
            total_bw_utilized += 0
        else:
            total_bw_utilized += ((r.current_epoch_value / r.value_per_kb_tx) * r.epochs_per_sec) / 1000  # in Mbps

    total_bw_allocated_Mbps = total_bw_allocated / 1000000
    utilization_of_max = (total_bw_allocated_Mbps / MAX_BW_MBPS) * 100
    if total_bw_allocated_Mbps == 0:
        utilization_of_allocation = 0.0
    else:
        utilization_of_allocation = float((total_bw_utilized / total_bw_allocated_Mbps) * 100)
    effective_efficiency = (total_bw_utilized / MAX_BW_MBPS) * 100
    avg_effective_efficiency = calculate_avg_lm_effective_efficiency(effective_efficiency)

    if realtime_mode or ((epoch_num % epochs_per_sec) == 0):
        # Print windows and graphics panels if not in Debug mode
        if debug == 0:
            stdscr.clear()
            stdscr.noutrefresh()

            # Sanity check for window height requirements
            if height < 10:
                bangs = '!' * int((width-49)/2)
                msg1 = bangs + '  DID YOU WANT TO SEE SOMETHING IN THIS WINDOW?  ' + bangs
                msg2 = bangs + '    TRY MAKING THE WINDOW A LITTLE BIT DEEPER.   ' + bangs
                msg3 = bangs + '            RESIZE WINDOW TO CONTINUE            ' + bangs
                stdscr.addstr(0, 0, "{0:^{1}}".format(msg1, width), text_d['ERROR_BLACK'] | curses.A_BOLD | BLINK)
                stdscr.addstr(1, 0, "{0:^{1}}".format(msg2, width), text_d['ERROR_BLACK'] | curses.A_BOLD | BLINK)
                stdscr.addstr(2, 0, "{0:^{1}}".format(msg3, width), text_d['ERROR_BLACK'] | curses.A_BOLD | BLINK)
                stdscr.refresh()
                return

            if width < 50:
                bangs = '!' * int((width-40)/2)
                msg1 = bangs + '    NOT SURE WHAT YOU EXPECT TO SEE    ' + bangs
                msg2 = bangs + '        ON SUCH A SKINNY SCREEN        ' + bangs
                msg3 = bangs + '  TRY MAKING IT WIDER, OR RISK SKYNET  ' + bangs
                stdscr.addstr(0, 0, "{0:^{1}}".format(msg1, width), text_d['ERROR_BLACK'] | curses.A_BOLD | BLINK)
                stdscr.addstr(1, 0, "{0:^{1}}".format(msg2, width), text_d['ERROR_BLACK'] | curses.A_BOLD | BLINK)
                stdscr.addstr(2, 0, "{0:^{1}}".format(msg3, width), text_d['ERROR_BLACK'] | curses.A_BOLD | BLINK)
                stdscr.refresh()
                return

            # Print to screen
            print_banner()
            print_lm_stats(total_bw_allocated_Mbps, utilization_of_max, total_bw_utilized,
                           utilization_of_allocation, effective_efficiency)
            print_system_values(radio_list)
            print_radio_stats(radio_list)
            if q_viz_mode is True:
                print_queues(radio_list)
            if history_plot_mode is True:
                print_history(lm_eff_eff_vals_q, len(radio_list), avg_effective_efficiency, q_viz_mode)
            refresh_msg_list(utilization_of_max, effective_efficiency, radio_list)
            print_messages(msg_list)
            print_time()
            print_toolbar()

            stdscr.refresh()

        else:
            print_stats(radio_list)       # Debug mode: use print() to console rather than curses.

    epoch_num = epoch_num + 1


# ------------------------------------------------------------------------------


def add_radio_to_list(radio_d):
    if debug == 3:
        print("New Radio found.  Adding to the Radio List")
    new_radio = Radio(radio_d['RadioName'])
    if "DataInRate-bps" in radio_d:
        new_radio.din_bps = radio_d['DataInRate-bps']
    if "ValuePerKbTx" in radio_d:
        new_radio.value_per_kb_tx = radio_d['ValuePerKbTx']
    if "AllocatedBw-bps" in radio_d:
        new_radio.dout_bps = radio_d['AllocatedBw-bps']
    new_radio.epochs_per_sec = epochs_per_sec
    radio_list.append(new_radio)
    if debug == 1:
        print("'{}' has been added to the Radio List".format(radio_list[-1].name))


# ------------------------------------------------------------------------------


def write_qlens_to_json(radios):
    # return queues to be used optionally write_qlens_to_database and log_updates

    global database
    queues = []
    
    for r in radios:
        radio_d = {}
        radio_d['RadioName'] = r.name
        radio_d['QLen'] = int(math.ceil(r.q_len / 8))
        radio_d['CurrentEpochValue'] = r.current_epoch_value
        if r.online is True:
            radio_d['IsOnline'] = 1
        else:
            radio_d['IsOnline'] = 0
        queues.append(radio_d)
    if database is None:
        with open("radio_queues.json", "w") as f:
            json.dump(queues, f)

    return queues

# ------------------------------------------------------------------------------


def print_stats(rlist):
    if debug == 2:
        print("EPOCH  | TIME              | Radio    | Allocated BW  | Data Input Rate | Queue Depth | Queue Status")
        now = time.time()
        for r in rlist:
            if r.online is False:
                q_status = " X   (OFFLINE)  "
            elif r.q_delta_bps > 0:
                q_status = " ^   (growing)  "
            elif (r.q_delta_bps < 0) and (r.q_len > 0):
                q_status = " v   (shrinking)"
            elif (r.q_delta_bps < 0) and (r.q_len == 0):
                q_status = " _   (empty)    "
            elif r.q_delta_bps == 0:
                q_status = " -   (balanced) "
            else:
                q_status = " meh"
        
            print("{0:6d} | {1:17f} | {2:8} | {3:8.3f} kbps | {4:8.3f} kbps   | {5:8.3f} KB |   {6:16} ".format(
                epoch_num, 
                now, 
                r.name, 
                (r.dout_bps / 1000), 
                (r.din_bps / 1000),
                (r.q_len / 1000),
                q_status))


# ------------------------------------------------------------------------------


def print_lm_stats(total_bw_allocated_Mbps, utilization_of_max, total_bw_utilized,
                   utilization_of_allocation, effective_efficiency):
    global lm_pad
    global text_d
    
    height, width = stdscr.getmaxyx()
    pad_height, pad_width = lm_pad.getmaxyx()

    lm_pad.clear()

    horizon = border_d['TS'] * 84
    lm_pad.addstr(0, 0, "{0}{1}{2}".format(border_d['TL'], horizon, border_d['TR']), text_d['BORDER'])
    lm_pad.addstr(0, 30, "{0}".format(" LM Efficiency Statistics "))
    for i in range(pad_height-2):
        lm_pad.addstr(i+1, 0, "{0}".format(border_d['LS']), text_d['BORDER'])
        lm_pad.addstr(i+1, 85, "{0}".format(border_d['RS']), text_d['BORDER'])
    lm_pad.addstr(pad_height-1, 0, "{0}{1}{2}".format(border_d['BL'], horizon, border_d['BR']), text_d['BORDER'])

    bw_str1 = "  LM Total Bandwidth Allocated:  {0:6.2f} Mbps of {1:5.2f} Mbps  |                     ".format(
        total_bw_allocated_Mbps,
        MAX_BW_MBPS,
        utilization_of_max)
    bw_str2 = "  Radios' Bandwidth Utilized:    {0:6.2f} Mbps of the {1:5.2f} Mbps Allocated           ".format(
        total_bw_utilized,
        total_bw_allocated_Mbps)
    bw_str3 = "  Effective LM Allocation Efficiency:   {0:6.2f}% {1} ".format(effective_efficiency, ' '*35)

    lm_pad.addstr(1, 1, bw_str1, curses.A_BOLD)
    lm_pad.addstr(2, 1, bw_str2, curses.A_BOLD)
    lm_pad.addstr(3, 1, bw_str3, curses.A_BOLD)

    if utilization_of_max == 0:
        lm_pad.addstr(1, 66, "{0:6.2f}% utilized".format(utilization_of_max), text_d['LM_0'] | curses.A_BOLD)
    elif utilization_of_max < 50:
        lm_pad.addstr(1, 66, "{0:6.2f}% utilized".format(utilization_of_max), text_d['LM_50'] | curses.A_BOLD)
    elif utilization_of_max < 80:
        lm_pad.addstr(1, 66, "{0:6.2f}% utilized".format(utilization_of_max), text_d['LM_80'] | curses.A_BOLD)
    elif utilization_of_max < 95:
        lm_pad.addstr(1, 66, "{0:6.2f}% utilized".format(utilization_of_max), text_d['LM_95'] | curses.A_BOLD)
    elif utilization_of_max <= 100:
        lm_pad.addstr(1, 66, "{0:6.2f}% utilized".format(utilization_of_max), text_d['LM_100'] | curses.A_BOLD)
    else:
        lm_pad.addstr(1, 66, "{0:6.2f}% utilized".format(utilization_of_max), text_d['LM_101'] | curses.A_BOLD)

    if int(utilization_of_allocation) > 100:
        lm_pad.addstr(2, 76, "({0:5.2f}%)".format(utilization_of_allocation), text_d['ERROR_BLACK'] | curses.A_BOLD)
    elif int(utilization_of_allocation) == 100:
        lm_pad.addstr(2, 76, "({0:5.2f}%)".format(utilization_of_allocation), text_d['EFF_100'] | curses.A_BOLD)
    elif int(utilization_of_allocation) >= 90:
        lm_pad.addstr(2, 76, "({0:5.2f}%)".format(utilization_of_allocation), text_d['EFF_90'] | curses.A_BOLD)
    elif int(utilization_of_allocation) >= 80:
        lm_pad.addstr(2, 76, "({0:5.2f}%)".format(utilization_of_allocation), text_d['EFF_80'] | curses.A_BOLD)
    elif int(utilization_of_allocation) >= 70:
        lm_pad.addstr(2, 76, "({0:5.2f}%)".format(utilization_of_allocation), text_d['EFF_70'] | curses.A_BOLD)
    elif int(utilization_of_allocation) >= 60:
        lm_pad.addstr(2, 76, "({0:5.2f}%)".format(utilization_of_allocation), text_d['EFF_60'] | curses.A_BOLD)
    elif int(utilization_of_allocation) >= 50:
        lm_pad.addstr(2, 76, "({0:5.2f}%)".format(utilization_of_allocation), text_d['EFF_50'] | curses.A_BOLD)
    elif int(utilization_of_allocation) >= 40:
        lm_pad.addstr(2, 76, "({0:5.2f}%)".format(utilization_of_allocation), text_d['EFF_40'] | curses.A_BOLD)
    elif int(utilization_of_allocation) >= 30:
        lm_pad.addstr(2, 76, "({0:5.2f}%)".format(utilization_of_allocation), text_d['EFF_30'] | curses.A_BOLD)
    elif int(utilization_of_allocation) >= 20:
        lm_pad.addstr(2, 76, "({0:5.2f}%)".format(utilization_of_allocation), text_d['EFF_20'] | curses.A_BOLD)
    elif int(utilization_of_allocation) >= 10:
        lm_pad.addstr(2, 76, "({0:5.2f}%)".format(utilization_of_allocation), text_d['EFF_10'] | curses.A_BOLD)
    elif int(utilization_of_allocation) > 0:
        lm_pad.addstr(2, 76, "({0:5.2f}%)".format(utilization_of_allocation), text_d['EFF_0'] | curses.A_BOLD)
    else:
        lm_pad.addstr(2, 76, "({0:5.2f}%)".format(utilization_of_allocation), text_d['ERROR_BLACK'] | curses.A_BOLD)

    if effective_efficiency > 100:
        lm_pad.addstr(3, 41, "{0:6.2f}% {1} ".format(effective_efficiency, ' ' * 35), text_d['ERROR_BLACK'] |
                      curses.A_BOLD)
    elif effective_efficiency == 100:
        lm_pad.addstr(3, 41, "{0:6.2f}% {1} ".format(effective_efficiency, ' ' * 35), text_d['EFF_100'] | curses.A_BOLD)
    elif effective_efficiency >= 90:
        lm_pad.addstr(3, 41, "{0:6.2f}% {1} ".format(effective_efficiency, ' ' * 35), text_d['EFF_90'] | curses.A_BOLD)
    elif effective_efficiency >= 80:
        lm_pad.addstr(3, 41, "{0:6.2f}% {1} ".format(effective_efficiency, ' ' * 35), text_d['EFF_80'] | curses.A_BOLD)
    elif effective_efficiency >= 70:
        lm_pad.addstr(3, 41, "{0:6.2f}% {1} ".format(effective_efficiency, ' ' * 35), text_d['EFF_70'] | curses.A_BOLD)
    elif effective_efficiency >= 60:
        lm_pad.addstr(3, 41, "{0:6.2f}% {1} ".format(effective_efficiency, ' ' * 35), text_d['EFF_60'] | curses.A_BOLD)
    elif effective_efficiency >= 50:
        lm_pad.addstr(3, 41, "{0:6.2f}% {1} ".format(effective_efficiency, ' ' * 35), text_d['EFF_50'] | curses.A_BOLD)
    elif effective_efficiency >= 40:
        lm_pad.addstr(3, 41, "{0:6.2f}% {1} ".format(effective_efficiency, ' ' * 35), text_d['EFF_40'] | curses.A_BOLD)
    elif effective_efficiency >= 30:
        lm_pad.addstr(3, 41, "{0:6.2f}% {1} ".format(effective_efficiency, ' ' * 35), text_d['EFF_30'] | curses.A_BOLD)
    elif effective_efficiency >= 20:
        lm_pad.addstr(3, 41, "{0:6.2f}% {1} ".format(effective_efficiency, ' ' * 35), text_d['EFF_20'] | curses.A_BOLD)
    elif effective_efficiency >= 10:
        lm_pad.addstr(3, 41, "{0:6.2f}% {1} ".format(effective_efficiency, ' ' * 35), text_d['EFF_10'] | curses.A_BOLD)
    elif effective_efficiency > 0:
        lm_pad.addstr(3, 41, "{0:6.2f}% {1} ".format(effective_efficiency, ' ' * 35), text_d['EFF_0'] | curses.A_BOLD)
    else:
        lm_pad.addstr(3, 41, "{0:6.2f}% {1} ".format(effective_efficiency, ' ' * 35), text_d['ERROR_BLACK'] |
                      curses.A_BOLD)
    
    start_line_pos = 8
    last_line_pos = 12
    
    if (height-1) >= last_line_pos:
        lm_pad.noutrefresh(0, 0, start_line_pos, 2, last_line_pos, (width-1))
    elif (height-1) >= start_line_pos:
        lm_pad.noutrefresh(0, 0, start_line_pos, 2, (height-1), (width-1))
    

# ------------------------------------------------------------------------------


def print_radio_stats(rlist):
    global radio_pad
    global text_d
    global border_d

    rwin_width = 87

    height, width = stdscr.getmaxyx()
    pad_height, pad_width = radio_pad.getmaxyx()

    if pad_height != (len(rlist)+2):
        radio_pad = curses.newpad((len(rlist)+2), rwin_width)
        radio_pad.bkgd(text_d['BG'])

    horizon = border_d['TS'] * (rwin_width - 3)
    radio_pad.addstr(0, 0, "{0}{1}{2}".format(border_d['TL'], horizon, border_d['TR']), text_d['BORDER'])
    radio_pad.addstr(len(rlist) + 1, 0, "{0}{1}{2}".format(border_d['BL'], horizon, border_d['BR']), text_d['BORDER'])

    radio_pad.addstr(0, 2, " Radio ")
    radio_pad.addstr(0, 13, " Allocated BW ")
    radio_pad.addstr(0, 30, " Avg Data Input ")
    radio_pad.addstr(0, 50, " Queue Depth ")
    radio_pad.addstr(0, 67, " Trend ")
    radio_pad.addstr(0, 76, " Value ")
    
    txt_mode = curses.A_DIM
    
    for idx, r in enumerate(radio_list, start=1):
        if r.online is False:
            q_status = 'OFF'
            txt_mode = (curses.color_pair(((idx-1) % 2) + 1) | curses.A_BOLD)
        elif r.q_delta_bps > 0:
            q_status = ' ^ '
            txt_mode = (curses.color_pair(((idx-1) % 2) + 1) | curses.A_BOLD)
        elif (r.q_delta_bps < 0) and (r.q_len > 0):
            q_status = ' v '
            txt_mode = (curses.color_pair(((idx-1) % 2) + 1) | curses.A_BOLD)
        elif (r.q_delta_bps < 0) and (r.q_len == 0):
            q_status = ' _ '
            txt_mode = (curses.color_pair(((idx-1) % 2) + 1) | curses.A_BOLD)
        elif r.q_delta_bps == 0:
            q_status = ' - '
            txt_mode = (curses.color_pair(((idx-1) % 2) + 1) | curses.A_BOLD)
        else: 
            q_status = " meh"
        
        radio_str = "{0:^10}| {1:8.0f} kbps  | {2:10.0f} kbps  | {3:8.1f} KBytes  |  {4}  | {5:6.1f}  ".format(
            r.name, 
            (r.dout_bps / 1000), 
            (r.din_bps / 1000),
            (r.q_len / 1000),
            q_status,
            r.current_epoch_value)
        
        radio_pad.addstr(idx, 1, radio_str, txt_mode)     # idx corresponds to row number for printing
        radio_pad.addstr(idx, 0, border_d['LS'], text_d['BORDER'])
        radio_pad.addstr(idx, rwin_width-2, border_d['RS'], text_d['BORDER'])

        if os.name == 'nt':
            star = '*'
        else:
            star = u'\u2605'
        if r.current_epoch_value < (((r.dout_bps / r.epochs_per_sec) / 1000) * r.value_per_kb_tx):
            radio_pad.addstr(idx, 84, star, text_d['WARNING_BLACK'])
        else:
            radio_pad.addstr(idx, 84, ' ')
        
    start_line_pos = 14
    last_line_pos = len(rlist) + 15

    if (width-1) > rwin_width:
        last_width_pos = rwin_width
    else:
        last_width_pos = width-1

    if (height-1) >= last_line_pos:
        radio_pad.noutrefresh(0, 0, start_line_pos, 2, last_line_pos, last_width_pos)  # Refresh the Radio Pad
    elif (height-1) >= start_line_pos:
        radio_pad.noutrefresh(0, 0, start_line_pos, 2, (height-1), last_width_pos)  # Refresh the Radio Pad


# ------------------------------------------------------------------------------


def print_queues(rlist):
    global q_pad
    qwin_width = 86

    height, width = stdscr.getmaxyx()
    pad_height, pad_width = q_pad.getmaxyx()

    if pad_height != (len(rlist) + 3):
        q_pad = curses.newpad(((len(rlist))+3), qwin_width)
        q_pad.bkgd(text_d['BG'])

    horizon = border_d['TS'] * (qwin_width - 2)
    q_pad.addstr(0, 0, "{0}{1}{2}".format(border_d['TL'], horizon, border_d['TR']), text_d['BORDER'])
    q_pad.addstr(0, 2, " Radio ")
    q_pad.addstr(0, 34, " Queue ")
    q_pad.addstr(0, 68, " Queue Status ")
    q_pad.addstr(len(rlist) + 1, 0, "{0}{1}{2}".format(border_d['BL'], horizon, border_d['BR']), text_d['BORDER'])

    for idx, r in enumerate(rlist, start=0):
        q_pad.addstr(idx+1, 0, border_d['LS'], text_d['BORDER'])                # Left Border Character
        q_pad.addstr(idx+1, qwin_width-1, border_d['RS'], text_d['BORDER'])     # Right Border Character
        print_queue(r, int(idx))                                # Update the Queue graphic for the iterated Radio
             
    start_line_pos = len(rlist) + 17
    last_line_pos = (len(rlist) * 2) + 20
    
    if (height-1) >= last_line_pos:
        q_pad.noutrefresh(0, 0, start_line_pos, 2, last_line_pos, (width-1))
    elif (height-1) >= start_line_pos:
        q_pad.noutrefresh(0, 0, start_line_pos, 2, (height-1), (width-1))


# ------------------------------------------------------------------------------


def print_queue(r, idx):
    global q_pad
    global text_d
    
    q_full_pct = int((r.q_len * 100) / MAX_QUEUE_SIZE_BYTES)    # Percent full of the queue
    q_chars = int(q_full_pct / 2)
    if q_chars > 50:
        q_chars = 50                                            # 50 is the number of chars for the queue graphic
    q_graphic = u'\u2588' * q_chars                             # u'\u2588' is the extended Ascii FULL BLOCK character
    if (q_chars < 50) and (q_full_pct % 2 == 1):
        q_graphic = q_graphic + u'\u258c'

    txt_mode = curses.color_pair((idx % 2) + 1)

    q_str = "|{0:50}|".format(q_graphic)
    q_pct = "{0:3d}%".format(q_full_pct)
    q_pad.addstr(idx+1,  1, "{0:^11}".format(r.name), txt_mode | curses.A_BOLD)
    q_pad.addstr(idx+1, 12, q_str,  txt_mode | curses.A_BOLD)
    q_pad.addstr(idx+1, 65, q_pct, txt_mode | curses.A_BOLD)
 
    
# ------------------------------------------------------------------------------

def print_history(q, num_radios, avg_eff_eff, q_viz_enabled):
    global stdscr
    global history_pad

    height, width = stdscr.getmaxyx()
    pad_height, pad_width = history_pad.getmaxyx()

    history_pad.clear()

    title = " LM Effective Efficiency (last 100 epochs) "
    horizon = border_d['TS'] * (pad_width-2)
    history_pad.addstr(0, 0, "{0}{1}{2}".format(border_d['TL'], horizon, border_d['TR']), text_d['BORDER'])
    history_pad.addstr(0, 23, title)
    for i in range(pad_height-2):
        history_pad.addstr(i+1, 0, "{0}".format(border_d['LS']), text_d['BORDER'])
        history_pad.addstr(i+1, 85, "{0}".format(border_d['RS']), text_d['BORDER'])
    history_pad.addstr(pad_height-2, 0, "{0}{1}{2}".format(border_d['BL'], horizon, border_d['BR']), text_d['BORDER'])

    crosshair = u'\u253C'
    x_axis = border_d['BS'] * 51
    y_axis = border_d['LS']
    for i in range(pad_height-5):
        history_pad.addstr(i+1, 6, y_axis)
    history_pad.addstr(pad_height-4, 6, "{0}{1}".format(crosshair, x_axis))
    history_pad.addstr(1, 2, "100")
    history_pad.addstr(13, 2, " 50")
    history_pad.addstr(26, 2, "  0")

    for i in range(25):
        for idx in range(0, len(q), 2):
            red_block = False
            if ((len(q) % 2) == 1) and (idx == (len(q)-1)):
                block = get_graph_char(0, q[0], i)
                if q[0] > 100.0:
                    red_block = True
            else:
                neg_index = idx*(-1)
                block = get_graph_char(q[neg_index-2], q[neg_index-1], i)
                if (q[neg_index-2] > 100.0) | (q[neg_index-1] > 100.0):
                    red_block = True
            if red_block is False:
                history_pad.addstr((25-(int(i))), 6+(50-(int(idx/2))), block, text_d['BAR_60'])
            else:
                history_pad.addstr((25 - (int(i))), 6 + (50 - (int(idx / 2))), block, text_d['TREND_DOWN'])

    # Print Text Values and Trend
    history_pad.addstr(5, 61, "Current Value: {0:5.2f}".format(q[-1]))
    history_pad.addstr(6, 61, "Average Value: {0:5.2f}".format(avg_eff_eff))

    if int(q[-1]) > int(avg_eff_eff):
        trend = u'\u2191' + ' UP'
        txt_mode = text_d['TREND_UP']
    elif (q[-1]) < int(avg_eff_eff):
        trend = u'\u2193' + ' DOWN'
        txt_mode = text_d['TREND_DOWN']
    else:
        trend = u'\u2248' + ' STEADY'
        txt_mode = text_d['TREND_STEADY']
    history_pad.addstr(8, 61, "Trending: {0}".format(trend), txt_mode | curses.A_BOLD)

    if q_viz_enabled:
        start_line_pos = (int(num_radios) * 2) + 20
    else:
        start_line_pos = int(num_radios) + 17

    if start_line_pos < (height-6):
        history_pad.noutrefresh(0, 0, start_line_pos, 2, height-6, width-1)


# ------------------------------------------------------------------------------


def get_graph_char(a, b, thd):
    global graph_d
    # a is a number between 0-100
    # b is a number between 0-100
    # thd is the full_block threshold (4 dots per block)

    a_full = int(a / 4)
    a_part = int(a % 4)
    b_full = int(b / 4)
    b_part = int(b % 4)

    if a_full > thd:
        # a is 4
        if b_full > thd:
            # b is 4
            return graph_d['4_4']
        elif b_full == thd:
            if b_part == 0:
                return graph_d['4_0']
            elif b_part == 1:
                return graph_d['4_1']
            elif b_part == 2:
                return graph_d['4_2']
            elif b_part == 3:
                return graph_d['4_3']
        else:
            return graph_d['4_0']
    elif a_full == thd:
        if a_part == 0:
            if b_full > thd:
                # b is 4
                return graph_d['0_4']
            elif b_full == thd:
                if b_part == 0:
                    return graph_d['0_0']
                elif b_part == 1:
                    return graph_d['0_1']
                elif b_part == 2:
                    return graph_d['0_2']
                elif b_part == 3:
                    return graph_d['0_3']
            else:
                return graph_d['0_0']
        elif a_part == 1:
            if b_full > thd:
                # b is 4
                return graph_d['1_4']
            elif b_full == thd:
                if b_part == 0:
                    return graph_d['1_0']
                elif b_part == 1:
                    return graph_d['1_1']
                elif b_part == 2:
                    return graph_d['1_2']
                elif b_part == 3:
                    return graph_d['1_3']
            else:
                return graph_d['1_0']
        elif a_part == 2:
            if b_full > thd:
                # b is 4
                return graph_d['2_4']
            elif b_full == thd:
                if b_part == 0:
                    return graph_d['2_0']
                elif b_part == 1:
                    return graph_d['2_1']
                elif b_part == 2:
                    return graph_d['2_2']
                elif b_part == 3:
                    return graph_d['2_3']
            else:
                return graph_d['2_0']
        elif a_part == 3:
            if b_full > thd:
                # b is 4
                return graph_d['3_4']
            elif b_full == thd:
                if b_part == 0:
                    return graph_d['3_0']
                elif b_part == 1:
                    return graph_d['3_1']
                elif b_part == 2:
                    return graph_d['3_2']
                elif b_part == 3:
                    return graph_d['3_3']
            else:
                return graph_d['3_0']
    else:
        # a is 0
        if b_full > thd:
            # b is 4
            return graph_d['0_4']
        elif b_full == thd:
            if b_part == 0:
                return graph_d['0_0']
            elif b_part == 1:
                return graph_d['0_1']
            elif b_part == 2:
                return graph_d['0_2']
            elif b_part == 3:
                return graph_d['0_3']
        return graph_d['0_0']


# ------------------------------------------------------------------------------


def print_system_values(rlist):
    global system_value_pad
    global AVG_WINDOW_SIZE
    global lm_eff_eff_vals_q

    height, width = stdscr.getmaxyx()

    sum_current_epoch_values = 0
    for r in rlist:
        sum_current_epoch_values += r.current_epoch_value

    avg_sys_val = calculate_avg_system_value(sum_current_epoch_values)
    avg_lm_eff_eff_val = (sum(lm_eff_eff_vals_q)) / (max(len(lm_eff_eff_vals_q), 1))

    system_value_pad.addstr(0, 0, "  Current System Value:", curses.A_BOLD)
    system_value_pad.addstr(0, 25, "    {0:^10.3f}".format(sum_current_epoch_values))
    system_value_pad.addstr(1, 0, "  Average System Value:", curses.A_BOLD)
    system_value_pad.addstr(1, 25, "    {0:^10.3f}".format(avg_sys_val))

    system_value_pad.addstr(0, 45, "  LM Effective Efficiency:")
    system_value_pad.addstr(0, 80, "{0:^8.2f}".format(lm_eff_eff_vals_q[-1]))
    system_value_pad.addstr(1, 45, "  Average LM Effective Efficiency:")
    system_value_pad.addstr(1, 80, "{0:^8.2f}".format(avg_lm_eff_eff_val))

    start_line_pos = 4
    start_width_pos = 0
    last_line_pos = start_line_pos + 3

    if (width-1) >= start_width_pos:
        system_value_pad.noutrefresh(0, 0, start_line_pos, start_width_pos, last_line_pos, (width-1))


# ------------------------------------------------------------------------------


def calculate_avg_system_value(current_value):
    global system_vals_array
    global AVG_WINDOW_SIZE
    global epoch_num

    if len(system_vals_array) < AVG_WINDOW_SIZE:
        system_vals_array.append(float(current_value))
    else:
        pos = epoch_num % AVG_WINDOW_SIZE
        system_vals_array[pos] = float(current_value)

    return float(sum(system_vals_array)) / (max(len(system_vals_array), 1))


# ------------------------------------------------------------------------------


def calculate_avg_lm_effective_efficiency(current_value):
    global lm_eff_eff_vals_q
    global AVG_WINDOW_SIZE
    global epoch_num

    if len(lm_eff_eff_vals_q) < AVG_WINDOW_SIZE:
        lm_eff_eff_vals_q.append(float(current_value))
    else:
        lm_eff_eff_vals_q.popleft()
        lm_eff_eff_vals_q.append(float(current_value))

    return float(sum(lm_eff_eff_vals_q)) / (max(len(lm_eff_eff_vals_q), 1))


# ------------------------------------------------------------------------------


def refresh_msg_list(utilization_of_max, effective_efficiency, radios):
    global msg_list

    msg_list.clear()

    if utilization_of_max > 100.0:
        new_msg = Message('LM', 'ERROR', "Allocated bandwidth is greater than channel bandwidth.")
        msg_list.append(new_msg)

    if effective_efficiency > 100.0:
        new_msg = Message('LM', 'ERROR', "Effective Efficiency reported > 100%.  Check bandwidth allocated.")
        msg_list.append(new_msg)

    for r in radios:
        if r.q_len / MAX_QUEUE_SIZE_BYTES >= 1.0:
            new_msg = Message(r.name, 'WARNING', "Queue is Full.")
            msg_list.append(new_msg)
        if r.current_epoch_value < (((r.dout_bps / r.epochs_per_sec) / 1000) * r.value_per_kb_tx):
            new_msg = Message(r.name, 'WARNING', "Allocated bandwidth is greater than this link's available output.")
            msg_list.append(new_msg)
        if r.online is False:
            if r.dout_bps > 0:
                new_msg = Message(r.name, 'ERROR', "LM is allocating bandwidth, but Radio is OFFLINE.")
            else:
                new_msg = Message(r.name, 'INFO', "Radio is OFFLINE.")
            msg_list.append(new_msg)


# ------------------------------------------------------------------------------


def print_messages(msgs):
    global message_pad
    global text_d

    height, width = stdscr.getmaxyx()
    pad_height, pad_width = message_pad.getmaxyx()

    if pad_height != (len(msgs) + 3):
        message_pad = curses.newpad(((len(msgs))+3), pad_width)
        message_pad.bkgd(text_d['BG'])

    message_pad.clear()

    horizon = border_d['TS'] * (pad_width-2)
    message_pad.addstr(0, 0, "{0}{1}{2}".format(border_d['TL'], horizon, border_d['TR']), text_d['BORDER'])
    message_pad.addstr(0, 30, " INFO / WARNINGS / ERRORS ")
    message_pad.addstr(len(msgs) + 1, 0, "{0}{1}{2}".format(border_d['BL'], horizon, border_d['BR']), text_d['BORDER'])

    for idx, m in enumerate(msgs):
        if m.level == 'ERROR':
            txt_mode = text_d['MSG_ERROR']
        elif m.level == 'WARNING':
            txt_mode = text_d['MSG_WARNING']
        elif m.level == 'INFO':
            txt_mode = text_d['MSG_INFO']
        else:
            txt_mode = text_d['MSG_UNKNOWN']

        message_pad.addstr(idx + 1, 0, border_d['LS'], text_d['BORDER'])  # Left Border Character
        message_pad.addstr(idx + 1, 2, "{0:<6}| {1:<7} | {2}".format(m.name, m.level, m.msg), txt_mode)
        message_pad.addstr(idx + 1, pad_width - 1, border_d['RS'], text_d['BORDER'])  # Right Border Character

    start_line_pos = height - (8 + len(msgs))
    last_line_pos = start_line_pos + pad_height

    message_pad.noutrefresh(0, 0, start_line_pos, 2, last_line_pos, (width-1))


# ------------------------------------------------------------------------------


def init_epoch_vals(ms):
    global epoch_ms
    global epoch_sec
    global epochs_per_sec
    
    epoch_ms = ms                       # epoch size in milliseconds
    epoch_sec = epoch_ms / 1000         # epoch size converted to seconds
    epochs_per_sec = 1000 / epoch_ms    # number of epochs per second


# ------------------------------------------------------------------------------


def restore_screen():
    curses.nocbreak()
    curses.echo()
    curses.endwin()


# ------------------------------------------------------------------------------


def sig_handler(sig, frame):
    global next_timer
    next_timer.cancel()

    restore_screen()
    sys.exit()


# ------------------------------------------------------------------------------


def print_banner():
    global stdscr
    global banner_pad
    global text_d
    global border_d
    
    height, width = stdscr.getmaxyx()
    pad_height, pad_width = banner_pad.getmaxyx()

    horizon = border_d['TS'] * (pad_width - 2)
    banner_pad.addstr(0, 0, "{0}{1}{2}".format(border_d['TL'], horizon, border_d['TR']), text_d['BORDER'])
    banner_pad.addstr(1, 0, "{0}{1}{2}".format(border_d['LS'],
                                               "            Radio Queue Status Display for "
                                               "Link Manager Algorithm Evaluator             ",
                                               border_d['RS']), text_d['BORDER'])
    banner_pad.addstr(2, 0, "{0}{1}{2}".format(border_d['BL'], horizon, border_d['BR']), text_d['BORDER'])
    banner_pad.noutrefresh(0, 0, 0, 0, 3, width-1)
    
    
# ------------------------------------------------------------------------------


def print_toolbar():
    global stdscr
    global toolbar_pad
    global text_d

    height, width = stdscr.getmaxyx()
    tp_height, tp_width = toolbar_pad.getmaxyx()

    q_msg = "q to toggle Queue Vizualization"
    realtime_msg = "(r)ealtime or (s)low refresh rate"
    history_msg = "(h)istory"
    quit_msg = "x to exit"

    toolbar_pad.addstr(0, 0, "{0}".format(border_d['TS']*(tp_width-1)))
    toolbar_pad.addstr(1, 0, " {0} | {1} | {2} | {3}".format(q_msg, realtime_msg, history_msg, quit_msg),
                       text_d['BORDER'])
    toolbar_pad.addstr(1, 1, "q", text_d['BORDER'] | curses.A_BOLD | curses.A_REVERSE)
    toolbar_pad.addstr(1, 36, "r", text_d['BORDER'] | curses.A_BOLD | curses.A_REVERSE)
    toolbar_pad.addstr(1, 50, "s", text_d['BORDER'] | curses.A_BOLD | curses.A_REVERSE)
    toolbar_pad.addstr(1, 72, "h", text_d['BORDER'] | curses.A_BOLD | curses.A_REVERSE)
    toolbar_pad.addstr(1, 83, "x", text_d['BORDER'] | curses.A_BOLD | curses.A_REVERSE)
    toolbar_pad.noutrefresh(0, 0, height-3, 0, height-2, width-1)


# ------------------------------------------------------------------------------


def print_time():
    global stdscr
    global time_pad
    
    height, width = stdscr.getmaxyx()
    
    now = time.time()
    header_str = "EPOCH #{0:<6d} | TIME: {1:17f}".format(epoch_num, now)
    time_pad.addstr(0, 0, "Epoch size: {0:4d}ms".format(epoch_ms), curses.A_BOLD)
    time_pad.addstr(1, 0, header_str, curses.A_BOLD)
    time_pad.addstr(2, 0, " ")
    
    if (width-1) >= 90:
        time_pad.noutrefresh(0, 0, height-5, 2, height-4, 90)
    else:
        time_pad.noutrefresh(0, 0, height-5, 2, height-4, width-1)
    

# ------------------------------------------------------------------------------


def main(stdscr):
    global text_d

    # Color Pair Setup
    curses.init_pair(1, 182, 235)  # purplish 1
    curses.init_pair(2, 114, 235)  # greenish 1
    curses.init_pair(3, 152, 235)  # bluish 1
    curses.init_pair(4, 210, 235)  # redish 1
    curses.init_pair(5, 229, 235)  # yellowish 1
    curses.init_pair(6, 42, 235)   # greenish 2
    curses.init_pair(7, 37, 235)   # bluish 2
    curses.init_pair(8, 135, 235)  # purplish 2
    curses.init_pair(9, 175, 235)  # redish 2
    curses.init_pair(10, 222, 235)  # yellowish 2

    curses.init_pair(11, 12, 235)     # Windows: LM Allocation Efficiency: == 0%
    curses.init_pair(12, 221, 235)    # Windows: LM Allocation Efficiency: < 50%
    curses.init_pair(13, 37, 235)     # Windows: LM Allocation Efficiency: < 80%
    curses.init_pair(14, 42, 235)     # Windows: LM Allocation Efficiency: < 95%
    curses.init_pair(15, 160, 235)    # Windows: LM Allocation Efficiency: <= 100%
    curses.init_pair(16, 12, 235)     # Windows: LM Allocation Efficiency: > 100%
    curses.init_pair(20, 200, 235)    # Windows: Efficiency : 0
    curses.init_pair(21, 196, 235)    # Windows: Efficiency : 10
    curses.init_pair(22, 168, 235)    # Windows: Efficiency : 20
    curses.init_pair(23, 216, 235)    # Windows: Efficiency : 30
    curses.init_pair(24, 220, 235)    # Windows: Efficiency : 40
    curses.init_pair(25, 222, 235)    # Windows: Efficiency : 50
    curses.init_pair(26, 186, 235)    # Windows: Efficiency : 60
    curses.init_pair(27, 31, 235)     # Windows: Efficiency : 70
    curses.init_pair(28, 73, 235)     # Windows: Efficiency : 80
    curses.init_pair(29, 79, 235)     # Windows: Efficiency : 90
    curses.init_pair(30, 47, 235)     # Windows: Efficiency : 100
    curses.init_pair(31, 12, 235)     # Windows: MSG ERROR - redish
    curses.init_pair(32, 14, 235)     # Windows: MSG WARNING - yellowish
    curses.init_pair(33, 8, 235)      # Windows: MSG INFO - grayish
    curses.init_pair(34, 24, 235)     # Windows: MSG UNKNOWN - bluish
    curses.init_pair(35, 47, 235)     # Windows: Trend Up - greenish
    curses.init_pair(36, 24, 235)     # Windows: Trend Steady - bluish
    curses.init_pair(37, 160, 235)    # Windows: Trend Down - redish
    curses.init_pair(38, 14, 235)     # Windows: Warning - Black
    curses.init_pair(39, 12, 15)      # Windows: Error - White
    curses.init_pair(40, 12, 235)     # Windows: Error - Black

    curses.init_pair(50, 12, 235)   # LM Allocation Efficiency: == 0%
    curses.init_pair(51, 221, 235)  # LM Allocation Efficiency: < 50%
    curses.init_pair(52, 37, 235)   # LM Allocation Efficiency: < 80%
    curses.init_pair(53, 42, 235)   # LM Allocation Efficiency: < 95%
    curses.init_pair(54, 160, 235)  # LM Allocation Efficiency: <= 100%
    curses.init_pair(55, 12, 235)   # LM Allocation Efficiency: > 100%
    curses.init_pair(60, 196, 235)  # Efficiency: 0
    curses.init_pair(61, 200, 235)  # Efficiency: 10
    curses.init_pair(62, 208, 235)  # Efficiency: 20
    curses.init_pair(63, 216, 235)  # Efficiency: 30
    curses.init_pair(64, 226, 235)  # Efficiency: 40
    curses.init_pair(65, 228, 235)  # Efficiency: 50
    curses.init_pair(66, 192, 235)  # Efficiency: 60
    curses.init_pair(67, 63, 235)   # Efficiency: 70
    curses.init_pair(68, 81, 235)   # Efficiency: 80
    curses.init_pair(69, 79, 235)   # Efficiency: 90
    curses.init_pair(70, 76, 235)   # Efficiency: 100
    curses.init_pair(100, 182, 235)  # purplish = Queue Status: Offline
    curses.init_pair(101, 152, 235)  # bluish = Queue Status: Empty State
    curses.init_pair(102, 229, 235)  # yellowish = Queue Status: Steady State
    curses.init_pair(103, 114, 235)  # greenish = Queue Status: Shrinking State
    curses.init_pair(104, 210, 235)  # redish = Queue Status: Growing State
    curses.init_pair(200, 15, 235)   # white = Queue Depth: Empty - < 20%
    curses.init_pair(201, 37, 235)   # bluish = Queue Depth: 20% - 40%
    curses.init_pair(202, 222, 235)  # yellowish = Queue Depth: 40% - 60%
    curses.init_pair(203, 135, 235)  # purplish = Queue Depth: 60% - 80%
    curses.init_pair(204, 175, 235)  # redish = Queue Depth: 80% < 100%
    curses.init_pair(221, 114, 235)  # trend up - greenish
    curses.init_pair(222, 32, 235)   # trend steady - bluish
    curses.init_pair(223, 210, 235)  # trend down - redish
    curses.init_pair(231, 9, 235)    # MSG ERROR - redish
    curses.init_pair(232, 11, 235)   # MSG WARNING - yellowish
    curses.init_pair(233, 8, 235)    # MSG INFO - whitish
    curses.init_pair(234, 32, 235)   # MSG UNKNOWN - bluish
    curses.init_pair(247, 63, 235)   # border
    curses.init_pair(248, 11, 235)
    curses.init_pair(249, 27, 235)
    curses.init_pair(250, 10, 235)
    curses.init_pair(251, 10, 15)
    curses.init_pair(252, 10, 235)
    curses.init_pair(253, 9, 15)
    curses.init_pair(254, 9, 235)
    curses.init_pair(255, 15, 235)

    text_d['LM_0'] = curses.color_pair(50)
    text_d['LM_50'] = curses.color_pair(51)
    text_d['LM_80'] = curses.color_pair(52)
    text_d['LM_95'] = curses.color_pair(53)
    text_d['LM_100'] = curses.color_pair(54)
    text_d['LM_101'] = curses.color_pair(55)
    text_d['EFF_0'] = curses.color_pair(60)
    text_d['EFF_10'] = curses.color_pair(61)
    text_d['EFF_20'] = curses.color_pair(62)
    text_d['EFF_30'] = curses.color_pair(63)
    text_d['EFF_40'] = curses.color_pair(64)
    text_d['EFF_50'] = curses.color_pair(65)
    text_d['EFF_60'] = curses.color_pair(66)
    text_d['EFF_70'] = curses.color_pair(67)
    text_d['EFF_80'] = curses.color_pair(68)
    text_d['EFF_90'] = curses.color_pair(69)
    text_d['EFF_100'] = curses.color_pair(70)
    text_d['OFFLINE'] = curses.color_pair(100)
    text_d['Q_EMPTY'] = curses.color_pair(101)
    text_d['Q_STEADY'] = curses.color_pair(102)
    text_d['Q_SHRINK'] = curses.color_pair(103)
    text_d['Q_GROW'] = curses.color_pair(104)
    text_d['BAR_EMPTY'] = curses.color_pair(200)
    text_d['BAR_20'] = curses.color_pair(201)
    text_d['BAR_40'] = curses.color_pair(202)
    text_d['BAR_60'] = curses.color_pair(203)
    text_d['BAR_80'] = curses.color_pair(204)
    text_d['TREND_UP'] = curses.color_pair(221)
    text_d['TREND_STEADY'] = curses.color_pair(222)
    text_d['TREND_DOWN'] = curses.color_pair(223)
    text_d['MSG_ERROR'] = curses.color_pair(231)
    text_d['MSG_WARNING'] = curses.color_pair(232)
    text_d['MSG_INFO'] = curses.color_pair(233)
    text_d['MSG_UNKNOWN'] = curses.color_pair(234)
    text_d['BORDER'] = curses.color_pair(247)
    text_d['WARNING_BLACK'] = curses.color_pair(248)
    text_d['BANNER'] = curses.color_pair(249)
    text_d['FOR_SCORE'] = curses.color_pair(250)
    text_d['PASS_WHITE'] = curses.color_pair(251)
    text_d['PASS_BLACK'] = curses.color_pair(252)
    text_d['ERROR_WHITE'] = curses.color_pair(253)
    text_d['ERROR_BLACK'] = curses.color_pair(254)
    text_d['BG'] = curses.color_pair(255)

    # If running on Windows, use the following terminal colors
    if os.name == 'nt':
        curses.init_pair(1, 219, 235)  # purplish 1
        curses.init_pair(2, 114, 235)  # greenish 1

        text_d['LM_0'] = curses.color_pair(11)
        text_d['LM_50'] = curses.color_pair(12)
        text_d['LM_80'] = curses.color_pair(13)
        text_d['LM_95'] = curses.color_pair(14)
        text_d['LM_100'] = curses.color_pair(15)
        text_d['LM_101'] = curses.color_pair(16)
        text_d['EFF_0'] = curses.color_pair(20)
        text_d['EFF_10'] = curses.color_pair(21)
        text_d['EFF_20'] = curses.color_pair(22)
        text_d['EFF_30'] = curses.color_pair(23)
        text_d['EFF_40'] = curses.color_pair(24)
        text_d['EFF_50'] = curses.color_pair(25)
        text_d['EFF_60'] = curses.color_pair(26)
        text_d['EFF_70'] = curses.color_pair(27)
        text_d['EFF_80'] = curses.color_pair(28)
        text_d['EFF_90'] = curses.color_pair(29)
        text_d['EFF_100'] = curses.color_pair(30)
        text_d['TREND_UP'] = curses.color_pair(35)
        text_d['TREND_STEADY'] = curses.color_pair(36)
        text_d['TREND_DOWN'] = curses.color_pair(37)
        text_d['MSG_ERROR'] = curses.color_pair(31)
        text_d['MSG_WARNING'] = curses.color_pair(32)
        text_d['MSG_INFO'] = curses.color_pair(33)
        text_d['MSG_UNKNOWN'] = curses.color_pair(34)
        text_d['BORDER'] = curses.color_pair(247)
        text_d['WARNING_BLACK'] = curses.color_pair(38)
        text_d['BANNER'] = curses.color_pair(249)
        text_d['FOR_SCORE'] = curses.color_pair(250)
        text_d['PASS_WHITE'] = curses.color_pair(251)
        text_d['PASS_BLACK'] = curses.color_pair(252)
        text_d['ERROR_WHITE'] = curses.color_pair(39)
        text_d['ERROR_BLACK'] = curses.color_pair(40)
        text_d['BG'] = curses.color_pair(255)

    border_d['LS'] = u'\u2502'
    border_d['RS'] = u'\u2502'
    border_d['TS'] = u'\u2500'
    border_d['BS'] = u'\u2500'
    border_d['TL'] = u'\u250c'
    border_d['TR'] = u'\u2510'
    border_d['BL'] = u'\u2514'
    border_d['BR'] = u'\u2518'

    # graph_d['0_0'] = u'\u2800'
    graph_d['0_0'] = ' '
    graph_d['1_0'] = u'\u2840'
    graph_d['2_0'] = u'\u2844'
    graph_d['3_0'] = u'\u2846'
    graph_d['4_0'] = u'\u2847'
    graph_d['0_1'] = u'\u2880'
    graph_d['1_1'] = u'\u28C0'
    graph_d['2_1'] = u'\u28C4'
    graph_d['3_1'] = u'\u28C6'
    graph_d['4_1'] = u'\u28C7'
    graph_d['0_2'] = u'\u28A0'
    graph_d['1_2'] = u'\u28E0'
    graph_d['2_2'] = u'\u28E4'
    graph_d['3_2'] = u'\u28E6'
    graph_d['4_2'] = u'\u28E7'
    graph_d['0_3'] = u'\u28B0'
    graph_d['1_3'] = u'\u28F0'
    graph_d['2_3'] = u'\u28F4'
    graph_d['3_3'] = u'\u28F6'
    graph_d['4_3'] = u'\u28F7'
    graph_d['0_4'] = u'\u28B8'
    graph_d['1_4'] = u'\u28F8'
    graph_d['2_4'] = u'\u28FC'
    graph_d['3_4'] = u'\u28FE'
    graph_d['4_4'] = u'\u28FF'

    if debug == 0:
        stdscr.bkgd(text_d['BG'])
        banner_pad.bkgd(text_d['BG'])
        system_value_pad.bkgd(text_d['BG'])
        time_pad.bkgd(text_d['BG'])
        lm_pad.bkgd(text_d['BG'])
        q_pad.bkgd(text_d['BG'])
        history_pad.bkgd(text_d['BG'])
        message_pad.bkgd(text_d['BG'])
        toolbar_pad.bkgd(text_d['BG'])
        stdscr.clear()
        
    run_epoch()


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    log=setup_logger()
    log.info("Intializing Run")

    # Argument Parser Declarations
    parser = argparse.ArgumentParser()
    parser.add_argument('-I', action='store_false', default=True, dest='enforce_max_q_size',
                        help='Infinite Queue Size (not limited by the MAX_QUEUE_SIZE). \r'
                             'WARNING: This can utilize a lot of system resources.  \r'
                             'Use at your own risk!')
    parser.add_argument('-M', action='store', default=-1, dest='max_queue_size',
                        help='Set MAX queue size in Bytes [default: 4194240]', type=int)
    parser.add_argument('-E', action='store', default=100, dest='epoch_size_ms',
                        help='Set the Epoch size (milliseconds) [default: 100]', type=int)
    parser.add_argument('-r', action='store_true', default=False, dest='realtime_mode',
                        help='Realtime mode (screen updates 1x per epoch.  Default: Slow Refresh rate (1x per sec)')
    parser.add_argument('-d', action='store', default=0, dest='debug', help='Set the Debug level', type=int)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.3.2')
    parser.add_argument('-i', action='store', dest='data_input_rates', help='Json with the data  input rates for a set of Radios', type=str)
    parser.add_argument('-b', action='store', dest='bw_allocs', help='Json with the avaliable bandwidth for a set of Radios', type=str)
    parser.add_argument('--config', action='store', default=None, dest='config', help='Set config file for OrientDB ', type=str)
    parser.add_argument('--database', action='store', default=None, dest='database', help='Sets the name of the OrientDB database', type=str)
    cli_args = parser.parse_args()

    cli_dict = vars(cli_args)
    log.info('Command Line Inputs')
    for key in cli_dict:
        log.info('{} : {}'.format(key, cli_dict[key]))

    # CLI argument assignments
    data_input_rates = cli_args.data_input_rates
    bw_allocs = cli_args.bw_allocs
    init_epoch_vals(cli_args.epoch_size_ms)   # Pass CLI Epoch size (ms) to the init_epoch_vals() function
    database = None
    if cli_args.database is not None and cli_args.config is not None:
        from brass_api.orientdb.orientdb_helper import BrassOrientDBHelper
        database = BrassOrientDBHelper(cli_args.database, cli_args.config)
        database.open_database()

    enforce_max_q_size = cli_args.enforce_max_q_size
    if cli_args.max_queue_size >= 0:
        MAX_QUEUE_SIZE_BYTES = cli_args.max_queue_size    # Set MAX Queue Size in Byte if CLI argument provided

    realtime_mode = cli_args.realtime_mode
    q_viz_mode = True
    history_plot_mode = True
    debug = cli_args.debug
    text_d = {}
    border_d = {}
    graph_d = {}
    
    stdscr = curses.initscr()                # Initial main screen for curses
    banner_pad = curses.newpad(4, 90)        # Initialize Banner Pad
    system_value_pad = curses.newpad(4, 90)  # Initialize System Value Pad
    time_pad = curses.newpad(3, 87)          # Initialize Time Pad
    lm_pad = curses.newpad(5, 87)            # Initialize LM Pad
    radio_pad = curses.newpad(10, 88)        # Initialize Radio Pad
    q_pad = curses.newpad(10, 88)            # Initialize Queue Pad
    history_pad = curses.newpad(30, 86)      # Initialize History Pad
    message_pad = curses.newpad(5, 86)       # Initialize Message Pad
    toolbar_pad = curses.newpad(2, 100)      # Initialize Toolbar Pad
    curses.curs_set(0)
    
    signal.signal(signal.SIGINT, sig_handler)   # Register signal handler for graceful exiting (e.g. CTRL-C)
    
    if os.name == 'nt':                         # If running on Windows, disable the "blinking" feature of curses
        BLINK = 0                               # because it doesn't look very good.
    else:
        BLINK = curses.A_BLINK

    wrapper(main)
    
    if os.name == 'posix':
        while True:
            signal.pause()      # Need this for graceful exiting
