# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ---    Radio Queue Status Display for Link Manager Algorithm Evaluator     ---
# ---                                                                        ---
# --- Last Updated: February 20, 2019                                         ---
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


next_timer = 0
epoch_ms = 100                      # epoch size in milliseconds
epoch_sec = epoch_ms / 1000         # epoch size converted to seconds
epochs_per_sec = 1000 / epoch_ms    # number of epochs per second
epoch_num = 0

MAX_BW = 10000000                   # max bandwidth of RF channel in bits per second
MAX_BW_MBPS = MAX_BW / 1000000      # max bandwidth of RF channel in Megabits per second

MAX_QUEUE_SIZE_BYTES = 4194240      # TmNS Radio queues not expected to be larger than 4.2 MB (per DSCP Queue?).
enforce_max_q_size = False         # Should the simulation enforce the MAX_QUEUE_SIZE_BYTES as a hard limit?
debug = 0                           # Debug value: initially 0, e.g. no debug

radio_list = []                     # List of Radio objects


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class Radio:
    """Class to contain radio status and statistics."""
    
    def __init__(self, name):
        self.name = name
        self.q = deque()
        self.din_bps = 0            # bits per second
        self.dout_bps = 0           # bits per second
        self.mission_val = 0
        self.q_delta_bps = 0        # bits per second
        self.q_len = 0              # bytes
        self.epochs_per_sec = 1
        self.online = True          # status: True: online, False: offline
        
    def update_q(self):
        if self.online is False:
            return
        self.q_delta_bps = self.din_bps - self.dout_bps
        if self.q_delta_bps > 0:
            q_delta_per_epoch = int(math.ceil(self.q_delta_bps / self.epochs_per_sec / 8))
            q_bytes_remaining = MAX_QUEUE_SIZE_BYTES - self.q_len
            if enforce_max_q_size and (q_delta_per_epoch > q_bytes_remaining):
                for x in range(q_bytes_remaining):
                    self.q.append(x)
            else:
                for x in range(q_delta_per_epoch):
                    self.q.append(x)
        elif self.q_delta_bps < 0:
            q_delta_per_epoch = int(math.floor(self.q_delta_bps / self.epochs_per_sec / 8))
            if self.q_len <= (abs(q_delta_per_epoch)):
                self.q.clear()
            else:
                for x in range(abs(q_delta_per_epoch)):
                    self.q.popleft()
        self.q_len = len(self.q)
        
    def go_offline(self):
        self.online = False
        self.din_bps = 0
        self.dout_bps = 0
        self.q_delta_bps = 0
        self.mission_val = 0
        self.q.clear()
        self.q_len = len(self.q)
        

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


def run_epoch():
    global epoch_num
    global radio_list
    global stdscr
    global next_timer
    global time_pad
    global text_d
    
    # Set callback timer for next epoch update
    next_timer = threading.Timer(epoch_sec, run_epoch)
    next_timer.start()

    height, width = stdscr.getmaxyx()
    
    # Reload JSON file for Radio Data Input Rates, parse contents, and update Radio objects
    with open("data_input_rates.json") as f:        # TODO: make filename a command line argument
        ldict_radios = json.load(f)

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
                if "MissionValue" in d:
                    r.mission_val = d["MissionValue"]
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

    # Reload JSON file for LM Bandwidth Allocations for Radio Data Output Rates (a.k.a. the "RF Drain Rate")
    with open("bw_allocs.json", 'r') as f:          # TODO: make filename a command line argument
        d_bw_allocs = json.load(f)
    
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
    
    write_qlens_to_json(radio_list)
    
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
        print_border(len(radio_list))
        print_time()
        print_lm_stats(radio_list)
        print_radio_stats(radio_list)
        print_queues(radio_list)
    
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
    if "MissionValue" in radio_d:
        new_radio.mission_val = radio_d['MissionValue']
    if "AllocatedBw-bps" in radio_d:
        new_radio.dout_bps = radio_d['AllocatedBw-bps']
    new_radio.epochs_per_sec = epochs_per_sec
    radio_list.append(new_radio)
    if debug == 1:
        print("'{}' has been added to the Radio List".format(radio_list[-1].name))


# ------------------------------------------------------------------------------


def write_qlens_to_json(radios):
    queues = []
    
    for r in radios:
        radio_d = {}
        radio_d['RadioName'] = r.name
        radio_d['QLen'] = int(math.ceil(r.q_len / 8))
        queues.append(radio_d)
    
    with open("radio_queues.json", "w") as f:
        json.dump(queues, f)


# ------------------------------------------------------------------------------


def print_stats(rlist):
    if debug == 2:
        print("EPOCH  | TIME              | Radio    | Allocated BW  | Data Input Rate | Queue Depth | Queue Status")
        now = time.time()
        for r in radio_list:
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


def print_lm_stats(rlist):
    global lm_pad
    global text_d
    
    height, width = stdscr.getmaxyx()
    
    # Color Pair Assignments
    txt_CYAN_on_BLACK = curses.color_pair(5)
    txt_GREEN_on_BLACK = curses.color_pair(6)
    txt_YELLOW_on_BLACK = curses.color_pair(7)
    txt_RED_on_BLACK = curses.color_pair(8)
    txt_MAGENTA_on_BLACK = curses.color_pair(9)
    # txt_WHITE_on_BLACK = curses.color_pair(10)
    
    total_bw_allocated = 0
    
    for r in rlist:
        total_bw_allocated += r.dout_bps
    
    total_bw_allocated_Mbps = total_bw_allocated / 1000000
    utilization = (total_bw_allocated_Mbps / MAX_BW_MBPS) * 100
    
    header = "+------------------------------------------------------------------------------------+"
    bw_str = "|   LM Total Bandwidth Allocated:  {0:7.3f} Mbps of {1:5.3f} Mbps  |  {2:6.2f}% utilized  |".format(
        total_bw_allocated_Mbps,
        MAX_BW_MBPS,
        utilization)
    
    lm_pad.addstr(0, 0, header, txt_CYAN_on_BLACK | curses.A_BOLD)
    if utilization < 50:
        lm_pad.addstr(1, 0, bw_str, txt_YELLOW_on_BLACK | curses.A_BOLD | curses.A_STANDOUT | BLINK)
    elif utilization < 80:
        lm_pad.addstr(1, 0, bw_str, txt_CYAN_on_BLACK | curses.A_BOLD | curses.A_STANDOUT)
    elif utilization < 95:
        lm_pad.addstr(1, 0, bw_str, txt_GREEN_on_BLACK | curses.A_BOLD | curses.A_STANDOUT)
    elif utilization <= 100:
        lm_pad.addstr(1, 0, bw_str, txt_MAGENTA_on_BLACK | curses.A_BOLD | curses.A_STANDOUT | BLINK)
    else:
        lm_pad.addstr(1, 0, bw_str, text_d['ERROR_BLACK'] | curses.A_BOLD | curses.A_STANDOUT | BLINK)
    lm_pad.addstr(2, 0, header, txt_CYAN_on_BLACK | curses.A_BOLD)
    
    start_line_pos = 7
    last_line_pos = 9
    
    if (height-1) >= last_line_pos:
        lm_pad.noutrefresh(0, 0, start_line_pos, 2, last_line_pos, (width-1))
    elif (height-1) >= start_line_pos:
        lm_pad.noutrefresh(0, 0, start_line_pos, 2, (height-1), (width-1))
    

# ------------------------------------------------------------------------------


def print_radio_stats(rlist):
    global radio_pad
    global text_d

    rwin_width = 86
    radio_pad = curses.newpad((len(rlist)+1), rwin_width)
    radio_pad.bkgd(text_d['BG'])
    
    # Color Pair Assignments
    txt_WHITE_on_RED = curses.color_pair(1)
    txt_WHITE_on_BLUE = curses.color_pair(2)
    txt_WHITE_on_GREEN = curses.color_pair(3)
    txt_BLACK_on_WHITE = curses.color_pair(4)
    txt_YELLOW_on_BLACK = curses.color_pair(7)
    
    height, width = stdscr.getmaxyx()
    
    header = "{0:^10}|{1:^15}|{2:^17}|{3:^17}|{4:^19}".format(
        'Radio',
        'Allocated BW',
        'Data Input Rate',
        'Queue Depth',
        'Queue Status')
    radio_pad.addstr(0, 0, header, curses.A_BOLD | curses.A_UNDERLINE)
    
    txt_mode = curses.A_DIM
    
    for idx, r in enumerate(radio_list, start=1):
        if r.online is False:
            q_status = " X   (OFFLINE)  "
            txt_mode = (text_d['OFFLINE'] | curses.A_BOLD | curses.A_REVERSE | BLINK)
        elif r.q_delta_bps > 0: 
            q_status = " ^   (growing)  "
            txt_mode = (text_d['Q_GROW'] | curses.A_REVERSE | curses.A_BOLD)
        elif (r.q_delta_bps < 0) and (r.q_len > 0): 
            q_status = " v   (shrinking)"
            txt_mode = (text_d['Q_SHRINK'] | curses.A_REVERSE | curses.A_BOLD)
        elif (r.q_delta_bps < 0) and (r.q_len == 0): 
            q_status = " _   (empty)    "
            txt_mode = (text_d['Q_EMPTY'] | curses.A_REVERSE | curses.A_BOLD)
        elif r.q_delta_bps == 0: 
            q_status = " -   (balanced) "
            txt_mode = (text_d['Q_STEADY'] | curses.A_REVERSE | curses.A_BOLD)
        else: 
            q_status = " meh"
        
        radio_str = "{0:^10}| {1:8.3f} kbps |  {2:8.3f} kbps  | {3:8.3f} KBytes |  {4} ".format(
            r.name, 
            (r.dout_bps / 1000), 
            (r.din_bps / 1000),
            (r.q_len / 1000),
            q_status)
        
        radio_pad.addstr(idx, 0, radio_str, txt_mode)     # idx corresponds to row number for printing
        
    start_line_pos = 11
    last_line_pos = len(rlist) + 11

    if (width-1) > 82:
        pad_width = 82
    else:
        pad_width = width-1

    if (height-1) >= last_line_pos:
        radio_pad.noutrefresh(0, 0, start_line_pos, 2, last_line_pos, pad_width)  # Refresh the Radio Pad
    elif (height-1) >= start_line_pos:
        radio_pad.noutrefresh(0, 0, start_line_pos, 2, (height-1), pad_width)  # Refresh the Radio Pad


# ------------------------------------------------------------------------------


def print_queues(rlist):
    global q_pad
    qwin_width = 86
    
    q_pad = curses.newpad(((len(rlist)*3)+3), qwin_width)
    q_pad.bkgd(text_d['BANNER'])
    
    height, width = stdscr.getmaxyx()
    
    header = " {0:^11}|{1:^50}|{2:^22}".format('Radio', 'Queue', 'Queue Status')
    blank = " " * (qwin_width-1)
    q_pad.addstr(0, 0, header, curses.A_REVERSE | curses.A_BOLD)                              # Header Row / Top Border
    q_pad.addstr((len(rlist)*3)+1, 0, "{0}".format(blank), curses.A_REVERSE | curses.A_BOLD)  # Bottom Border
    q_pad.addstr((len(rlist)*3)+1, qwin_width-1, " ", curses.A_REVERSE | curses.A_BOLD)  # Bottom Right Border Character
    
    for idx, r in enumerate(rlist, start=0):
        q_pad.addstr((3*idx)+1, 0, " ", curses.A_REVERSE | curses.A_BOLD)                # Left Border Character
        q_pad.addstr((3*idx)+2, 0, " ", curses.A_REVERSE | curses.A_BOLD)                # Left Border Character
        q_pad.addstr((3*idx)+3, 0, " ", curses.A_REVERSE | curses.A_BOLD)                # Left Border Character
        q_pad.addstr((3*idx)+1, qwin_width-1, " ", curses.A_REVERSE | curses.A_BOLD)     # Right Border Character
        q_pad.addstr((3*idx)+2, qwin_width-1, " ", curses.A_REVERSE | curses.A_BOLD)     # Right Border Character
        q_pad.addstr((3*idx)+3, qwin_width-1, " ", curses.A_REVERSE | curses.A_BOLD)     # Right Border Character
        print_queue(r, int(idx))                                # Update the Queue graphic for the iterated Radio
             
    start_line_pos = len(rlist) + 14
    last_line_pos = (len(rlist) * 4) + 17
    
    if (height-1) >= last_line_pos:
        q_pad.noutrefresh(0, 0, start_line_pos, 2, last_line_pos, (width-1))
    elif (height-1) >= start_line_pos:
        q_pad.noutrefresh(0, 0, start_line_pos, 2, (height-1), (width-1))


# ------------------------------------------------------------------------------


def print_queue(r, idx):
    global q_pad
    global text_d
    
    header = "+--------------------------------------------------+"
    
    q_full_pct = int((r.q_len * 100) / MAX_QUEUE_SIZE_BYTES)    # Percent full of the queue
    q_chars = int(q_full_pct / 2)
    if q_chars > 50:
        q_chars = 50                               # 50 is the number of chars for the queue graphic
    q_graphic = u'\u2588' * q_chars                             # u'\u2588' is the extended Ascii FULL BLOCK character
    if (q_chars < 50) and (q_full_pct % 2 == 1):
        q_graphic = q_graphic + u'\u258c'
    
    if q_full_pct == 0:
        q_state = "EMPTY"
    elif q_full_pct >= 100:
        q_state = "FULL"
    else:
        q_state = "Utilized"
    
    if q_chars < 10:
        txt_mode = text_d['BAR_EMPTY']
    elif q_chars < 20:
        txt_mode = text_d['BAR_20']
    elif q_chars < 30:
        txt_mode = text_d['BAR_40']
    elif q_chars < 40:
        txt_mode = text_d['BAR_60']
    elif q_chars < 50:
        txt_mode = text_d['BAR_80']
    else:
        txt_mode = text_d['ERROR_BLACK'] | BLINK
    
    q_str = "|{0:50}|  {1:2d}% Queue {2}".format(q_graphic, q_full_pct, q_state)
    q_pad.addstr((3*idx)+1, 12, header, txt_mode | curses.A_BOLD)
    q_pad.addstr((3*idx)+2,  1, "{0:^11}".format(r.name), curses.A_BOLD)
    q_pad.addstr((3*idx)+2, 12, q_str,  txt_mode | curses.A_BOLD)
    q_pad.addstr((3*idx)+3, 12, header, txt_mode | curses.A_BOLD)
 
    
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

    block = u'\u2588'
    for i in range(4):
        for j in range(8):
            for k in range(8):
                curses.init_pair((i*4)+(j*8)+k+1,(i*4)+(j*8)+k, 235)
                stdscr.addstr((i*8)+(j) + 60, k+5, "{0}".format(block), curses.color_pair((i*4)+(j*8)+k+1))
            stdscr.addstr((i*8)+j+60, 0, "{0}".format((i*64)+(j*8)))
            stdscr.refresh()

    keypress = stdscr.getkey()

    restore_screen()
    sys.exit()


# ------------------------------------------------------------------------------


def print_banner():
    global stdscr
    global banner_pad
    global text_d
    
    height, width = stdscr.getmaxyx()
    
    header = '*' * 90
    banner_pad.addstr(0, 0, header, text_d['BANNER'] | curses.A_BOLD)
    banner_pad.addstr(1, 0, "*****        Radio Queue Status Display for Link Manager Algorithm Evaluator"
                            "         *****", text_d['BANNER'] | curses.A_BOLD)
    banner_pad.addstr(2, 0, header, text_d['BANNER'] | curses.A_BOLD)
    banner_pad.addstr(3, 0, ' '*89)
    banner_pad.noutrefresh(0, 0, 0, 0, 3, width-1)
    
    
# ------------------------------------------------------------------------------


def print_time():
    global stdscr
    global time_pad
    
    height, width = stdscr.getmaxyx()
    
    now = time.time()
    header_str = "EPOCH #{0:<6d} | TIME: {1:17f}".format(epoch_num, now)
    time_pad.addstr(0, 0, "Epoch size: {0:4d}ms".format(epoch_ms), curses.A_BOLD)
    time_pad.addstr(1, 0, header_str, curses.A_BOLD | curses.A_UNDERLINE)
    time_pad.addstr(2, 0, " ")
    
    if (width-1) >= 90:
        time_pad.noutrefresh(0, 0, 4, 2, 6, 90)
    else:
        time_pad.noutrefresh(0, 0, 4, 2, 6, width-1)
    

# ------------------------------------------------------------------------------


def print_border(num_radios):
    global stdscr
    global border_pad
    global text_d

    height, width = stdscr.getmaxyx()
    
    pad_lines = (num_radios * 4) + 15
    border_pad = curses.newpad(pad_lines, 91)
    border_pad.bkgd(text_d['BG'])

    # Print bar on left and right borders
    bar = u'\u2588'
    for i in range(pad_lines-1):
        border_pad.addstr(i, 0, " ", text_d['BANNER'] | curses.A_REVERSE)
        border_pad.addstr(i, 89, " ", text_d['BANNER'] | curses.A_REVERSE)
    
    last_line_pos = pad_lines+3
    
    border_pad.addstr(pad_lines-1, 0, "{}".format(' ' * 90), text_d['BANNER'] | curses.A_REVERSE)
    
    if (height-1) >= last_line_pos:
        border_pad.noutrefresh(0, 0, 3, 0, last_line_pos, (width-1))
    else:
        border_pad.noutrefresh(0, 0, 3, 0, (height-1), (width-1))


# ------------------------------------------------------------------------------


def main(stdscr):
    global text_d
    # Color Pair Setup
    curses.init_pair(1, curses.COLOR_WHITE,   curses.COLOR_RED)     # Pair 1: Queue Growing
    curses.init_pair(2, curses.COLOR_WHITE,   curses.COLOR_BLUE)    # Pair 2: Queue Balanced
    curses.init_pair(3, curses.COLOR_WHITE,   curses.COLOR_GREEN)   # Pair 3: Queue Shrinking
    curses.init_pair(4, curses.COLOR_BLACK,   curses.COLOR_WHITE)   # Pair 4: Queue Empty
    curses.init_pair(5, curses.COLOR_CYAN,    curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_GREEN,   curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_YELLOW,  curses.COLOR_BLACK)
    curses.init_pair(8, curses.COLOR_RED,     curses.COLOR_BLACK)
    curses.init_pair(9, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(10, curses.COLOR_WHITE,  curses.COLOR_BLACK)

    # Color Pair Setup
    #curses.init_pair(1, 114, 235)  # greenish 1
    #curses.init_pair(2, 152, 235)  # bluish 1
    #curses.init_pair(3, 182, 235)  # purplish 1
    #curses.init_pair(4, 210, 235)  # redish 1
    #curses.init_pair(5, 229, 235)  # yellowish 1
    #curses.init_pair(6, 42, 235)  # greenish 2
    #curses.init_pair(7, 37, 235)  # bluish 2
    #curses.init_pair(8, 135, 235)  # purplish 2
    #curses.init_pair(9, 175, 235)  # redish 2
    #curses.init_pair(10, 222, 235)  # yellowish 2
    curses.init_pair(11, 114, 15)  # greenish 1 on white
    curses.init_pair(12, 152, 15)  # bluish 1 on white
    curses.init_pair(13, 182, 15)  # purplish 1 on white
    curses.init_pair(14, 210, 15)  # redish 1 on white
    curses.init_pair(15, 229, 15)  # yellowish 1 on white
    curses.init_pair(16, 42, 15)  # greenish 2 on white
    curses.init_pair(17, 37, 15)  # bluish 2 on white
    curses.init_pair(18, 135, 15)  # purplish 2 on white
    curses.init_pair(19, 175, 15)  # redish 2 on white
    curses.init_pair(20, 222, 15)  # yellowish 2 on white
    curses.init_pair(50, 1, 235)  # LM Allocation Efficiency: == 0%
    curses.init_pair(51, 1, 235)  # LM Allocation Efficiency: < 50%
    curses.init_pair(52, 1, 235)  # LM Allocation Efficiency: < 80%
    curses.init_pair(53, 1, 235)  # LM Allocation Efficiency: < 95%
    curses.init_pair(54, 1, 235)  # LM Allocation Efficiency: == 100%
    curses.init_pair(55, 1, 235)  # LM Allocation Efficiency: > 100%
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
    text_d['BANNER'] = curses.color_pair(249)
    text_d['FOR_SCORE'] = curses.color_pair(250)
    text_d['PASS_WHITE'] = curses.color_pair(251)
    text_d['PASS_BLACK'] = curses.color_pair(252)
    text_d['ERROR_WHITE'] = curses.color_pair(253)
    text_d['ERROR_BLACK'] = curses.color_pair(254)
    text_d['BG'] = curses.color_pair(255)

    if debug == 0:
        stdscr.bkgd(text_d['BG'])
        banner_pad.bkgd(text_d['BG'])
        time_pad.bkgd(text_d['BG'])
        lm_pad.bkgd(text_d['BG'])
        q_pad.bkgd(text_d['BG'])
        border_pad.bkgd(text_d['BG'])
        stdscr.clear()
        
    run_epoch()


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    # Argument Parser Declarations
    parser = argparse.ArgumentParser()
    parser.add_argument('-L', action='store_true', default=False, dest='enforce_max_q_size',
                        help='Limit Queue by the MAX_QUEUE_SIZE')
    parser.add_argument('-M', action='store', default=-1, dest='max_queue_size',
                        help='Set MAX queue size in Bytes [default: 4194240]', type=int)
    parser.add_argument('-E', action='store', default=100, dest='epoch_size_ms',
                        help='Set the Epoch size (milliseconds) [default: 100]', type=int)
    parser.add_argument('-d', action='store', default=0, dest='debug', help='Set the Debug level', type=int)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.1.1')
    cli_args = parser.parse_args()

    # CLI argument assignments
    init_epoch_vals(cli_args.epoch_size_ms)     # Pass CLI Epoch size (ms) to the init_epoch_vals() function

    enforce_max_q_size = cli_args.enforce_max_q_size
    if cli_args.max_queue_size >= 0:
        MAX_QUEUE_SIZE_BYTES = cli_args.max_queue_size    # Set MAX Queue Size in Byte if CLI argument provided
    debug = cli_args.debug
    text_d = {}
    
    stdscr = curses.initscr()               # Initial main screen for curses
    banner_pad = curses.newpad(4, 90)       # Initialize Banner Pad
    time_pad = curses.newpad(3, 87)         # Initialize Time Pad
    lm_pad = curses.newpad(3, 87)           # Initialize LM Pad
    radio_pad = curses.newpad(10, 88)       # Initialize Radio Pad
    q_pad = curses.newpad(10, 88)           # Initialize Queue Pad
    border_pad = curses.newpad(17, 90)      # Initialize Border Pad
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
