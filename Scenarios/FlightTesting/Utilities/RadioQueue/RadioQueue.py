#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#---    Radio Queue Status Display for Link Manager Algorithm Evaluator     ---
#---                                                                        ---
#--- Last Updated: January 30, 2019                                         ---
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

import sys
import argparse
import json
from collections import deque
import threading
import time
import math
import curses
from curses import wrapper
import signal


next_timer     = 0
epoch_ms       = 100                # epoch size in milliseconds
epoch_sec      = epoch_ms / 1000    # epoch size converted to seconds
epochs_per_sec = 1000 / epoch_ms    # number of epochs per second
epoch_num      = 0

MAX_BW         = 10000000           # max bandwidth of RF channel in bits per second
MAX_BW_MBPS    = MAX_BW / 1000000   # max bandwidth of RF channel in Megabits per second

MAX_QUEUE_SIZE_BYTES = 4194240      # TmNS Radio queues not expected to be larger than 4.2 MB (per DSCP Queue?).
enforce_max_q_size   = False        # Should the simulation enforce the MAX_QUEUE_SIZE_BYTES as a hard limit?
debug                = 0            # Debug value: initially 0, e.g. no debug

radio_list = []                     # List of Radio objects


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

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
        if self.online == False: return
        self.q_delta_bps = self.din_bps - self.dout_bps
        if self.q_delta_bps > 0:
            q_delta_per_epoch = int(math.ceil(self.q_delta_bps / self.epochs_per_sec / 8))
            q_bytes_remaining = MAX_QUEUE_SIZE_BYTES - self.q_len
            if (enforce_max_q_size and (q_delta_per_epoch > q_bytes_remaining)):
                for x in range (q_bytes_remaining):
                    self.q.append(x)
            else:
                for x in range(q_delta_per_epoch):
                    self.q.append(x)
        elif self.q_delta_bps < 0:
            q_delta_per_epoch = int(math.floor(self.q_delta_bps / self.epochs_per_sec / 8))
            if self.q_len <= (abs(q_delta_per_epoch)):
                self.q.clear()
            else:
                for x in range (abs(q_delta_per_epoch)):
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
        

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------


def run_epoch():
    global epoch_num
    global radio_list
    global stdscr
    global next_timer
    
    #threading.Timer(epoch_sec, run_epoch).start()   # Set callback timer for next epoch update
    next_timer = threading.Timer(epoch_sec, run_epoch)
    next_timer.start()
    
    # Reload JSON file for Radio Data Input Rates, parse contents, and update Radio objects
    with open("data_input_rates.json") as f:        # TODO: make filename a command line argument
        ldict_radios = json.load(f)

    # Parse the list of Radio dictionaries from JSON file
    for d in ldict_radios:
        unknown_radio = True
        for r in radio_list:
            if r.name == d['RadioName']:
                if debug == 3: print ("found radio in list already")
                unknown_radio = False
                r.online = True
                if "DataInRate-bps" in d: r.din_bps = d["DataInRate-bps"]
                if "MissionValue" in d: r.mission_val = d["MissionValue"]
                break
        if unknown_radio:
            add_radio_to_list(d)
    
    # If a Radio is removed from a test mission (e.g., the Data Input JSON file), then mark as "offline"
    if (len(ldict_radios) < len(radio_list)):
        for r in radio_list:
            offline_radio = True
            for d in ldict_radios:
                if d['RadioName'] == r.name:
                    offline_radio = False
                    break
            if offline_radio:
                if r.online: 
                    r.go_offline()         # If the offline radio was previously online, call go_offline()
                    if debug >= 1: print ("'{}' has gone offline.".format(r.name))
    
    
    # Reload JSON file for LM Bandwidth Allocations for Radio Data Output Rates (a.k.a. the "RF Drain Rate")
    with open("bw_allocs.json", 'r') as f:          # TODO: make filename a command line argument
        d_bw_allocs = json.load(f)
    
    # Parse the Bandwidth Allocations dictionaries from JSON file
    for d in d_bw_allocs:
        unknown_radio = True
        for r in radio_list:
            if r.name == d['RadioName']:
                if debug == 3: print ("found radio in list already")
                unknown_radio = False
                if "AllocatedBw-bps" in d: r.dout_bps = d["AllocatedBw-bps"]
                else:                      r.dout_bps = 0
                break
        if unknown_radio:
            add_radio_to_list(d)
    
    # If a Radio is removed from the LM's bandwidth allocations, zeroize the corresponding radio_list value for din_bps
    if (len(d_bw_allocs) < len(radio_list)):
        for r in radio_list:
            unsched_radio = True
            for d in d_bw_allocs:
                if d['RadioName'] == r.name:
                    unsched_radio = False
                    break
            if unsched_radio:
                r.dout_bps = 0               # This radio is no longer being scheduled by the LM, so drop its allocations to 0
    
    
    # Update all Radio info
    for r in radio_list:
        r.update_q()
    
    write_qlens_to_json(radio_list)
    
    # Print windows and graphics panels if not in Debug mode
    if debug == 0:
        now = time.time()
        header_str = "EPOCH #{0:<6d} | TIME: {1:17f}".format(epoch_num, now)
        stdscr.addstr(4, 2, "Epoch size: {0:4d}ms".format(epoch_ms), curses.A_BOLD)
        stdscr.addstr(5, 2, header_str, curses.A_BOLD | curses.A_UNDERLINE)
        stdscr.addstr(6, 2, " ")
    
        # Print to screen
        print_border(len(radio_list))
        print_lm_stats(radio_list)
        print_epoch_stats(radio_list)
        print_queues(radio_list)
    
        stdscr.refresh()
    
    else: print_stats(radio_list)       # Debug mode: use print() to console rather than curses.
    
    epoch_num = epoch_num + 1


#------------------------------------------------------------------------------    


def add_radio_to_list(radio_d):
    if debug == 3: print ("New Radio found.  Adding to the Radio List")
    new_radio = Radio(radio_d['RadioName'])
    if "DataInRate-bps" in radio_d: new_radio.din_bps = radio_d['DataInRate-bps']
    if "MissionValue" in radio_d: new_radio.mission_val = radio_d['MissionValue']
    if "AllocatedBw-bps" in radio_d: new_radio.dout_bps = radio_d['AllocatedBw-bps']
    new_radio.epochs_per_sec = epochs_per_sec
    radio_list.append(new_radio)
    if debug == 1: print ("'{}' has been added to the Radio List".format(radio_list[-1].name))


#------------------------------------------------------------------------------    


def write_qlens_to_json(radios):
    queues = []
    
    for r in radios:
        radio_d = {}
        radio_d['RadioName'] = r.name
        radio_d['QLen'] = int(math.ceil(r.q_len / 8))
        queues.append(radio_d)
    
    with open("radio_queues.json", "w") as f:
        json.dump(queues,f)


#------------------------------------------------------------------------------


def print_stats(rlist):
    if debug == 2:
        print("EPOCH  | TIME              | Radio    | Allocated BW  | Data Input Rate | Queue Depth | Queue Status")
        now = time.time()
        for r in radio_list:
            if   r.online == False: q_status                      = " X   (OFFLINE)  "
            elif r.q_delta_bps > 0: q_status                      = " ^   (growing)  "
            elif (r.q_delta_bps < 0) and (r.q_len > 0):  q_status = " v   (shrinking)"
            elif (r.q_delta_bps < 0) and (r.q_len == 0): q_status = " _   (empty)    "
            elif r.q_delta_bps == 0: q_status                     = " -   (balanced) "
            else: q_status = " meh"
        
            print("{0:6d} | {1:17f} | {2:8} | {3:8.3f} kbps | {4:8.3f} kbps   | {5:8.3f} KB |   {6:16} ".format(
                epoch_num, 
                now, 
                r.name, 
                (r.dout_bps / 1000), 
                (r.din_bps / 1000),
                (r.q_len / 1000),
                q_status))


#------------------------------------------------------------------------------


def print_lm_stats(rlist):
    global lmwin
    
    # Color Pair Assignments
    txt_CYAN_on_BLACK    = curses.color_pair(5)
    txt_GREEN_on_BLACK   = curses.color_pair(6)
    txt_YELLOW_on_BLACK  = curses.color_pair(7)
    txt_RED_on_BLACK     = curses.color_pair(8)
    txt_MAGENTA_on_BLACK = curses.color_pair(9)
    txt_WHITE_on_BLACK   = curses.color_pair(10)
    
    total_bw_allocated = 0
    
    for r in rlist:
        total_bw_allocated += r.dout_bps
    
    total_bw_allocated_Mbps = total_bw_allocated / 1000000
    utilization = (total_bw_allocated_Mbps / MAX_BW_MBPS) * 100
    
    
    header = "+------------------------------------------------------------------------------------+"
    bw_str = "|   LM Total Bandwidth Allocated:  {0:7.3f} Mbps of {1:5.3f} Mbps  |  {2:6.2f}% utilized  |".format(
        (total_bw_allocated_Mbps), MAX_BW_MBPS, utilization)

    
    lmwin.addstr(0, 0, header, txt_CYAN_on_BLACK | curses.A_BOLD)
    if   utilization <   50: lmwin.addstr(1, 0, bw_str, txt_YELLOW_on_BLACK  | curses.A_BOLD | curses.A_STANDOUT | curses.A_BLINK )
    elif utilization <   80: lmwin.addstr(1, 0, bw_str, txt_CYAN_on_BLACK    | curses.A_BOLD | curses.A_STANDOUT)
    elif utilization <   95: lmwin.addstr(1, 0, bw_str, txt_GREEN_on_BLACK   | curses.A_BOLD | curses.A_STANDOUT)
    elif utilization <= 100: lmwin.addstr(1, 0, bw_str, txt_MAGENTA_on_BLACK | curses.A_BOLD | curses.A_STANDOUT | curses.A_BLINK )
    else:                    lmwin.addstr(1, 0, bw_str, txt_RED_on_BLACK     | curses.A_BOLD | curses.A_STANDOUT | curses.A_BLINK )
    lmwin.addstr(2, 0, header, txt_CYAN_on_BLACK | curses.A_BOLD)
        
    lmwin.noutrefresh()     # Refresh the LM Window
    

#------------------------------------------------------------------------------


def print_epoch_stats(rlist):
    global rwin
    rwin_width = 86
    rwin = curses.newwin(((len(rlist))+1), rwin_width, 11, 2)
    
    # Color Pair Assignments
    txt_WHITE_on_RED   = curses.color_pair(1)
    txt_WHITE_on_BLUE  = curses.color_pair(2)
    txt_WHITE_on_GREEN = curses.color_pair(3)
    txt_BLACK_on_WHITE = curses.color_pair(4)
    txt_YELLOW_on_BLACK = curses.color_pair(7)
    
    
    header = "{0:^10}|{1:^15}|{2:^17}|{3:^17}|{4:^19}".format('Radio', 'Allocated BW', 'Data Input Rate', 'Queue Depth', 'Queue Status')
    rwin.addstr(0, 0, header, curses.A_BOLD | curses.A_UNDERLINE)
    
    txt_mode = curses.A_DIM
    
    for idx, r in enumerate(radio_list, start=1):
        if r.online == False:
            q_status = " X   (OFFLINE)  "
            txt_mode = (txt_YELLOW_on_BLACK | curses.A_BLINK)
        elif r.q_delta_bps > 0: 
            q_status = " ^   (growing)  "
            txt_mode = txt_WHITE_on_RED
        elif (r.q_delta_bps < 0) and (r.q_len > 0): 
            q_status = " v   (shrinking)"
            txt_mode = txt_WHITE_on_GREEN
        elif (r.q_delta_bps < 0) and (r.q_len == 0): 
            q_status = " _   (empty)    "
            txt_mode = txt_BLACK_on_WHITE
        elif r.q_delta_bps == 0: 
            q_status = " -   (balanced) "
            txt_mode = txt_WHITE_on_BLUE
        else: 
            q_status = " meh"
        
        rstr = "{0:^10}| {1:8.3f} kbps |  {2:8.3f} kbps  | {3:8.3f} KBytes |  {4} ".format(
            r.name, 
            (r.dout_bps / 1000), 
            (r.din_bps / 1000),
            (r.q_len / 1000),
            q_status)
        
        rwin.addstr(idx, 0, rstr, txt_mode)     # idx corresponds to row number for printing
        
    rwin.noutrefresh()      # Refresh the Radio Window


#------------------------------------------------------------------------------


def print_queues(rlist):
    global qwin
    qwin_width = 86
    
    qwin = curses.newwin(((len(rlist)*3)+3), qwin_width, len(rlist) + 14, 2)
    header = " {0:^11}|{1:^50}|{2:^22}".format('Radio', 'Queue', 'Queue Status')
    blank = " " * (qwin_width-1)
    qwin.addstr(0, 0, header, curses.A_BOLD | curses.A_REVERSE)                 # Header Row / Top Border
    qwin.addstr((len(rlist)*3)+1, 0, "{0}".format(blank), curses.A_REVERSE)     # Bottom Border
    qwin.addstr((len(rlist)*3)+1, qwin_width-1, " ", curses.A_REVERSE)          # Bottom Right Border Character
    
    for idx, r in enumerate(rlist, start=0):
        qwin.addstr((3*idx)+1, 0, " ", curses.A_REVERSE)                # Left Border Character
        qwin.addstr((3*idx)+2, 0, " ", curses.A_REVERSE)                # Left Border Character
        qwin.addstr((3*idx)+3, 0, " ", curses.A_REVERSE)                # Left Border Character
        qwin.addstr((3*idx)+1, qwin_width-1, " ", curses.A_REVERSE)     # Right Border Character
        qwin.addstr((3*idx)+2, qwin_width-1, " ", curses.A_REVERSE)     # Right Border Character
        qwin.addstr((3*idx)+3, qwin_width-1, " ", curses.A_REVERSE)     # Right Border Character
        print_queue(r, int(idx))                                        # Update the Queue graphic for the iterated Radio
             
    qwin.noutrefresh()  # Refresh the Queue Graphics Window


#------------------------------------------------------------------------------


def print_queue(r, idx):
    global qwin
    
    # Color Pair Assignments
    txt_CYAN_on_BLACK    = curses.color_pair(5)
    txt_GREEN_on_BLACK   = curses.color_pair(6)
    txt_YELLOW_on_BLACK  = curses.color_pair(7)
    txt_RED_on_BLACK     = curses.color_pair(8)
    txt_MAGENTA_on_BLACK = curses.color_pair(9)
    txt_WHITE_on_BLACK   = curses.color_pair(10)
    
    header = "+--------------------------------------------------+"
    
    q_full_pct = int((r.q_len * 100) / MAX_QUEUE_SIZE_BYTES)                        # Percent full of the queue
    q_chars = int(q_full_pct / 2)
    if q_chars > 50: q_chars = 50                                                   # 50 is the number of chars for the queue graphic
    q_graphic = u'\u2588' * q_chars                                                 # u'\u2588' is the extended Ascii FULL BLOCK character
    if ((q_chars < 50) and (q_full_pct%2 == 1)): q_graphic = q_graphic + u'\u258c'
    
    if   q_chars ==  0: q_state = "EMPTY"
    elif q_chars == 50: q_state = "FULL"
    else:               q_state = "Utilized"
    
    if   q_chars < 10: txt_mode = txt_WHITE_on_BLACK
    elif q_chars < 20: txt_mode = txt_CYAN_on_BLACK
    elif q_chars < 30: txt_mode = txt_YELLOW_on_BLACK
    elif q_chars < 40: txt_mode = txt_MAGENTA_on_BLACK
    elif q_chars < 50: txt_mode = txt_RED_on_BLACK
    else:              txt_mode = txt_RED_on_BLACK | curses.A_BLINK
    
    #q_str = "{0:9} |{1:50}|  {2:2d}% Queue {3}".format(r.name, q_graphic, q_full_pct, q_state)
    q_str = "|{0:50}|  {1:2d}% Queue {2}".format(q_graphic, q_full_pct, q_state)
    qwin.addstr((3*idx)+1, 12, header, txt_mode | curses.A_BOLD)
    qwin.addstr((3*idx)+2,  1, "{0:^11}".format(r.name), curses.A_BOLD)
    qwin.addstr((3*idx)+2, 12, q_str,  txt_mode | curses.A_BOLD)
    qwin.addstr((3*idx)+3, 12, header, txt_mode | curses.A_BOLD)
 
    
#------------------------------------------------------------------------------


def print_border(num_radios):
    global stdscr
    
    txt_WHITE_on_BLUE = curses.color_pair(2)
    
    # Print bar on left and right borders
    for i in range (3, ((num_radios * 4)+17)):
        stdscr.addstr(i, 0, " ", txt_WHITE_on_BLUE)
        stdscr.addstr(i, 89, " ", txt_WHITE_on_BLUE)
        
    stdscr.addstr((num_radios * 4)+17, 0, "{0:90}".format(" "), txt_WHITE_on_BLUE)
    stdscr.noutrefresh()

#------------------------------------------------------------------------------


def init_epoch_vals(ms):
    global epoch_ms
    global epoch_sec
    global epochs_per_sec
    
    epoch_ms        = ms                # epoch size in milliseconds
    epoch_sec       = epoch_ms / 1000   # epoch size converted to seconds
    epochs_per_sec  = 1000 / epoch_ms   # number of epochs per second

#------------------------------------------------------------------------------
       

def main(stdscr):
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
    
    if debug == 0:
        stdscr.clear()
    
        header = '*' * 90
        stdscr.addstr(0, 0, header, curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(1, 0, "*****        Radio Queue Status Display for Link Manager Algorithm Evaluator         *****", curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(2, 0, header, curses.color_pair(2) | curses.A_BOLD)
    
    run_epoch()


#------------------------------------------------------------------------------


def restore_screen():
    curses.nocbreak()
    curses.echo()
    curses.endwin()


#------------------------------------------------------------------------------


def sig_handler(sig, frame):
    global next_timer
    next_timer.cancel()
    restore_screen()
    sys.exit()


#------------------------------------------------------------------------------


if __name__ == "__main__":
    # Argument Parser Declarations
    parser = argparse.ArgumentParser()
    parser.add_argument('-L', action='store_true', default=False, dest='enforce_max_q_size', help='Limit Queue by the MAX_QUEUE_SIZE')
    parser.add_argument('-M', action='store', default=-1, dest='max_queue_size', help='Set MAX queue size in Bytes [default: 4194240]', type=int)
    parser.add_argument('-E', action='store', default=100, dest='epoch_size_ms', help='Set the Epoch size (milliseconds) [default: 100]', type=int)
    parser.add_argument('-d', action='store', default=0, dest='debug', help='Set the Debug level', type=int)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0.0')
    cli_args = parser.parse_args()

    # CLI argument assignments
    init_epoch_vals(cli_args.epoch_size_ms)     # Pass CLI Epoch size (ms) to the init_epoch_vals() function

    enforce_max_q_size = cli_args.enforce_max_q_size
    if (cli_args.max_queue_size >=0): MAX_QUEUE_SIZE_BYTES=cli_args.max_queue_size  # Set MAX Queue Size in Byte if CLI argument provided
    debug = cli_args.debug
    
    stdscr = curses.initscr()             # Initial main screen for curses
    lmwin  = curses.newwin(3,88,7,2)      # Initialize LM Window for curses
    rwin   = curses.newwin(10,88,0,2)     # Initialize Radio Window for curses
    qwin   = curses.newwin(10,88,0,2)     # Initialize Queue Graphics Window for curses
    curses.curs_set(0)
    
    signal.signal(signal.SIGINT, sig_handler)   # Register signal handler for graceful exiting (e.g. CTRL-C)

    wrapper(main)
    
    while True:
        signal.pause()      # Need this for graceful exiting
    