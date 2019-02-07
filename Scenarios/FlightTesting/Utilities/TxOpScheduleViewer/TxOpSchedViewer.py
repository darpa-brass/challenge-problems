#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#---    TxOp Schedule Viewer for Link Manager Algorithm Evaluator           ---
#---                                                                        ---
#--- Last Updated: February 7, 2019                                         ---
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

import sys
import os
import argparse
from lxml import etree
import json
import time
import math
import curses
from curses import wrapper
import signal


ns = {"xsd": "http://www.w3.org/2001/XMLSchema",
      "mdl": "http://www.wsmr.army.mil/RCC/schemas/MDL",
      "tmatsP": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsPGroup",
      "tmatsD": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsDGroup"}


# shortcut dictionary for passing common arguments
n = {"namespaces": ns}

next_timer     = 0
epoch_ms       = 100                # epoch size in milliseconds
epoch_sec      = epoch_ms / 1000    # epoch size converted to seconds
epochs_per_sec = 1000 / epoch_ms    # number of epochs per second
epoch_num      = 0

debug                = 0            # Debug value: initially 0, e.g. no debug

radio_list = []                     # List of Radio objects


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------


class RanConfig:
    """Class to contain RAN Configuration info"""
    
    def __init__(self, name, freq=0, epoch_ms=0, guard=0):
        self.name = name
        self.freq = freq
        self.epoch_ms = epoch_ms
        self.guard    = guard
        

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------


class TxOp:
    """Class to contain TxOp info"""
    
    def __init__(self, freq=0, start_usec=0, stop_usec=0, timeout=0):
        self.freq = freq
        self.start_usec = start_usec
        self.stop_usec = stop_usec
        self.timeout = timeout


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------


class RadioLink:
    """Class to contain Radio Link info"""
    
    def __init__(self, name, src, dst):
        self.name = name
        self.src  = src
        self.dst  = dst
        self.tx_sched = []
        
    
    def add_txop(self, txop):
        self.tx_sched.append(txop)
        


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------


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


def parse_mdl(mdl_f):
    global debug
    
    parser = etree.XMLParser(remove_blank_text=True)
    mdl = etree.parse(mdl_f, parser)
    
    if debug >= 3:
        print("***** MDL FILE CONTENTS *****")
        print(etree.tostring(mdl))
        print("***** END MDL FILE *****")

#------------------------------------------------------------------------------


def print_banner():
    global stdscr
    global banner_pad
    
    height, width = stdscr.getmaxyx()
    
    header = '*' * 90
    banner_pad.addstr(0, 0, header, curses.color_pair(2) | curses.A_BOLD)
    banner_pad.addstr(1, 0, "*****           TxOp Schedule Viewer for Link Manager Algorithm Evaluator            *****", curses.color_pair(2) | curses.A_BOLD)
    banner_pad.addstr(2, 0, header, curses.color_pair(2) | curses.A_BOLD)
    banner_pad.addstr(3,0, ' '*89)
    banner_pad.noutrefresh(0,0, 0,0, 3,width-1)
    
    
#------------------------------------------------------------------------------


def print_file_info(f, name, config):
    global stdscr
    global file_info_pad
    
    height, width = stdscr.getmaxyx()
    
    #file_info_pad.addstr(0, 0, "MDL File: {0:76}".format(f), curses.A_BOLD)
    #file_info_pad.addstr(1, 0, "Name: {0:80}".format(name), curses.A_BOLD)
    #file_info_pad.addstr(2, 0, "Configuration Version: {0:63}".format(config), curses.A_BOLD | curses.A_UNDERLINE)
    msg1 = "MDL File: {}".format(f)
    msg2 = "Name: {}".format(name)
    msg3 = "Configuration Version: {}".format(config)
    file_info_pad.addstr(0, 0, "{0:^86}".format(msg1), curses.A_BOLD)
    file_info_pad.addstr(1, 0, "{0:^86}".format(msg2), curses.A_BOLD)
    file_info_pad.addstr(2, 0, "{0:^86}".format(msg3), curses.A_BOLD | curses.A_UNDERLINE)
    
    if (height-1) >= 8:
        file_info_pad.noutrefresh(0,0, 4,2, 6,(width-1))
    else:
        file_info_pad.noutrefresh(0,0, 4,2, (height-2),(width-1))


#------------------------------------------------------------------------------


def print_ran_stats(ran):
    global stdscr
    global ran_pad
    
    txt_CYAN_on_BLACK    = curses.color_pair(5)
    
    height, width = stdscr.getmaxyx()
    
    ran_pad.addstr(0, 0, "RAN Configuration Name:.....   {0:55}".format(ran.name), txt_CYAN_on_BLACK | curses.A_BOLD)
    ran_pad.addstr(1, 0, "Center Frequency:...........   {0} MHz{1:45}".format(int(ran.freq)/1000000, ' '), txt_CYAN_on_BLACK | curses.A_BOLD)
    ran_pad.addstr(2, 0, "Epoch Size:.................   {0} ms{1:49}".format(ran.epoch_ms, ' '), txt_CYAN_on_BLACK | curses.A_BOLD)
    ran_pad.addstr(3, 0, "Guard Time:.................   {0} secs{1:45}".format(ran.guard, ' '), txt_CYAN_on_BLACK | curses.A_BOLD)
    
    start_row_pos = 8
    last_row_pos  = 12
    
    if (height-1) >= last_row_pos:
        ran_pad.noutrefresh(0,0, start_row_pos,2, last_row_pos,(width-1))
    elif (height-1) >= start_row_pos:
        ran_pad.noutrefresh(0,0, start_row_pos,2, (height-1),(width-1))
        

#------------------------------------------------------------------------------


def print_links_info(links):
    global stdscr
    global link_info_pad
    
    height, width = stdscr.getmaxyx()
    
    rows_needed = 0
    for l in links:
        if len(l.tx_sched) == 0: rows_needed += 4 + 1
        else:                    rows_needed += 4 + len(l.tx_sched)
    
    link_info_pad = curses.newpad(rows_needed, 90)
    
    start_row = 0
    for link in links:
        print_link_info(link, start_row)
        if len(link.tx_sched) >0 : start_row += 4 + len(link.tx_sched)
        else:                   start_row += 4 + 1
    
    start_row_pos = 14
    last_row_pos = start_row_pos + rows_needed
    
    if (height-1) >= last_row_pos:
        link_info_pad.noutrefresh(0,0, start_row_pos,2, last_row_pos, (width-1))        # TODO: add check for height
    elif (height-1) >= start_row_pos:
        link_info_pad.noutrefresh(0,0, start_row_pos,2, (height-1), (width-1))
    
#------------------------------------------------------------------------------


def print_link_info(link, row):
    global link_info_pad
    
    # Color Pair Assignments
    txt_CYAN_on_BLACK    = curses.color_pair(5)
    txt_GREEN_on_BLACK   = curses.color_pair(6)
    txt_YELLOW_on_BLACK  = curses.color_pair(7)
    txt_RED_on_BLACK     = curses.color_pair(8)
    txt_MAGENTA_on_BLACK = curses.color_pair(9)
    txt_WHITE_on_BLACK   = curses.color_pair(10)
    
    link_info_pad.addstr(row,0, "Link: {}".format(link.name), curses.A_BOLD)
    link_info_pad.addstr(row+1,0, "Source Radio RF MAC Addr:      {}".format(link.src), curses.A_BOLD)
    link_info_pad.addstr(row+2,0, "Destination Group RF MAC Addr: {}".format(link.dst), curses.A_BOLD)

    if (len(link.tx_sched)) > 0:
        print_txops_info(link.tx_sched, row+3)
    else:
        link_info_pad.addstr(row+3,0, "  NO TXOPS DEFINED IN MDL FOR THIS LINK", txt_YELLOW_on_BLACK | curses.A_BOLD)
        #pass

#------------------------------------------------------------------------------


def print_txops_info(txops, row):
    global link_info_pad
    
    for idx, txop in enumerate(txops, start=0):
        print_txop_info(txop, idx, row+idx)


#------------------------------------------------------------------------------


def print_txop_info(txop, idx, row):
    global link_info_pad
    
    txt_GREEN_on_BLACK   = curses.color_pair(6)
    
    txop_str = "  TxOp {0}: {1:6d} - {2:6d} us (TTL: {3:3d}) @ {4} MHz\r".format(
              idx+1, int(txop.start_usec), int(txop.stop_usec), int(txop.timeout), 
              int(txop.freq)/1000000)
    
    link_info_pad.addstr(row,0, txop_str, txt_GREEN_on_BLACK |curses.A_BOLD)
    
    if debug >=1:
        print("  TxOp {0}: {1:6d} - {2:6d} us (TTL: {3:3d}) @ {4} MHz\r".format(
              idx+1, int(txop.start_usec), int(txop.stop_usec), int(txop.timeout), 
              int(txop.freq)/1000000))


#------------------------------------------------------------------------------


def main(stdscr):  
    #def main():
    global mdl_file
    rans_list  = []
    links_list = []
    
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
    
    height, width = stdscr.getmaxyx()

    stdscr.clear()
    stdscr.refresh()
    
    # Sanity check for window height requirements
    if height < 10:
        bangs = '!' * int((width-49)/2)
        msg1 = bangs + '  DID YOU WANT TO SEE SOMETHING IN THIS WINDOW?  ' + bangs
        msg2 = bangs + '    TRY MAKING THE WINDOW A LITTLE BIT DEEPER.   ' + bangs
        msg3 = bangs + '            RESIZE WINDOW TO CONTINUE            ' + bangs
        stdscr.addstr(0,0,"{0:^{1}}".format(msg1, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
        stdscr.addstr(1,0,"{0:^{1}}".format(msg2, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
        stdscr.addstr(2,0,"{0:^{1}}".format(msg3, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
        stdscr.refresh()
        return
    
    # Parse MDL file, and create the RAN Config (assuming only a single RAN Config)
    #parse_mdl(mdl_file)
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(mdl_file, parser)
    
    if debug >= 3:
        print("***** MDL FILE CONTENTS *****")
        print(etree.tostring(root))
        print("***** END MDL FILE *****")
    
    # Parse MDL file for Configuration Version
    root_name       = root.find("mdl:Name", namespaces=ns).text
    root_config_ver = root.find("mdl:ConfigurationVersion", namespaces=ns).text
    
    # Parse MDL file for RAN Config Parameters
    rans = root.xpath("//mdl:RANConfiguration", namespaces=ns)
    for ran in rans:
        rname  = ran.find("mdl:Name", namespaces=ns).text
        rfreq  = ran.find("mdl:CenterFrequencyHz", namespaces=ns).text
        repoch = ran.find("mdl:EpochSize", namespaces=ns).text
        rguard = ran.find("mdl:MaxGuardTimeSec", namespaces=ns).text
        if debug >=2: print("RAN Name: {}, Frequency: {}, Epoch Size: {}ms, Guardband: {} sec".format(rname, rfreq, repoch, rguard))
        new_ran = RanConfig(name=rname, freq=rfreq, epoch_ms=repoch, guard=rguard)
        rans_list.append(new_ran)
    
    
    # Parse MDL for Radio Links and their associated Transmission Schedules
    radio_links = root.xpath("//mdl:RadioLink", namespaces=ns)
    for radio_link in radio_links:
        rlname = radio_link.find("mdl:Name", namespaces=ns).text
        rlsrc_idref = radio_link.find("mdl:SourceRadioRef", namespaces=ns).attrib
        tmas = root.xpath("//mdl:TmNSApp[@ID='{}']".format(rlsrc_idref["IDREF"]), namespaces=ns)
        rlsrc = tmas[0].find("mdl:TmNSRadio/mdl:RFMACAddress", namespaces=ns).text
        rldst_idref = radio_link.find("mdl:DestinationRadioGroupRef", namespaces=ns).attrib
        rgs = root.xpath("//mdl:RadioGroup[@ID='{}']".format(rldst_idref["IDREF"]), namespaces=ns)
        rldst = rgs[0].find("mdl:GroupRFMACAddress", namespaces=ns).text
        
        new_link = RadioLink(rlname, rlsrc, rldst)
        
        tx_sched = radio_link.find("mdl:TransmissionSchedule", namespaces=ns)
        if tx_sched != None:
            # Loop through the TxOps if they are defined for this link
            for txop in tx_sched:
                txop_freq    = txop.find("mdl:CenterFrequencyHz", namespaces=ns).text
                txop_start   = txop.find("mdl:StartUSec", namespaces=ns).text
                txop_stop    = txop.find("mdl:StopUSec", namespaces=ns).text
                txop_timeout = txop.find("mdl:TxOpTimeout", namespaces=ns).text
                new_txop     = TxOp(txop_freq, txop_start, txop_stop, txop_timeout)
                new_link.add_txop(new_txop)
            
        links_list.append(new_link)
    
    #for i in links_list:
    #    print("{}: SRC Radio: {}  DST Group: {}\r".format(i.name, i.src, i.dst))
 
    while True:
        height, width = stdscr.getmaxyx()

        stdscr.clear()
        stdscr.refresh()
           
        # Sanity check for window height requirements
        if height < 10:
            bangs = '!' * int((width-49)/2)
            msg1 = bangs + '  DID YOU WANT TO SEE SOMETHING IN THIS WINDOW?  ' + bangs
            msg2 = bangs + '    TRY MAKING THE WINDOW A LITTLE BIT DEEPER.   ' + bangs
            msg3 = bangs + '            RESIZE WINDOW TO CONTINUE            ' + bangs
            stdscr.addstr(0,0,"{0:^{1}}".format(msg1, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
            stdscr.addstr(1,0,"{0:^{1}}".format(msg2, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
            stdscr.addstr(2,0,"{0:^{1}}".format(msg3, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
            stdscr.refresh()
        elif width < 40:
            bangs = '!' * int((width-34)/2)
            msg1 = bangs + '  NOT SURE WHAT YOU EXPECT TO  ' + bangs
            msg2 = bangs + '  SEE ON SUCH A SKINNY SCREEN  ' + bangs
            msg3 = bangs + '  TRY MAKING IT WIDER, OR RISK ' + bangs
            msg4 = bangs + '            SKYNET             ' + bangs
            stdscr.addstr(0,0, "{0:^{1}}".format(msg1, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
            stdscr.addstr(1,0, "{0:^{1}}".format(msg2, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
            stdscr.addstr(2,0, "{0:^{1}}".format(msg3, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
            stdscr.addstr(3,0, "{0:^{1}}".format(msg4, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
            stdscr.refresh()
        else:
            print_banner()
            print_file_info(mdl_file, root_name, root_config_ver)
            print_links_info(links_list)
         
            if len(rans_list) > 0:
                print_ran_stats(rans_list[0])        # TODO: only printing the first RAN Config found
    
                stdscr.addstr((height-1),0, "*** PRESS ANY KEY TO CONTINUE ***", curses.color_pair(8) | curses.A_BOLD | BLINK)
    
                stdscr.refresh()
    

        keypress = stdscr.getch()           # Wait for user to press a key before exiting
        if keypress != curses.KEY_RESIZE:   break
        

#------------------------------------------------------------------------------


if __name__ == "__main__":
    # Argument Parser Declarations
    parser = argparse.ArgumentParser()
    parser.add_argument('FILE', action='store', default=sys.stdin, help='MDL file to examine', type=str)
    parser.add_argument('-d', action='store', default=0, dest='debug', help='Set the Debug level', type=int)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.0.1')
    cli_args = parser.parse_args()

    # CLI argument assignments
    mdl_file = cli_args.FILE
    debug = cli_args.debug
    
    stdscr = curses.initscr()
    banner_pad = curses.newpad(4, 90)     # Initialize Banner Pad
    file_info_pad = curses.newpad(4, 90)  # Initialize File Info Pad
    ran_pad    = curses.newpad(5, 90)     # Initialize RAN Pad
    link_info_pad = curses.newpad(8, 90)  # Initialize Link Info Pad
    
    
    if os.name == 'nt':                         # If running on Windows, disable the "blinking" feature of curses
        BLINK = 0                               #   because it doesn't look very good.
    else: BLINK = curses.A_BLINK
    
    wrapper(main)
    #main()
    
    #while True:
    #    signal.pause()