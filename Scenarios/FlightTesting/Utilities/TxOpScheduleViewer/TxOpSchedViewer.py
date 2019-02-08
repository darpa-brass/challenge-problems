#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#---    TxOp Schedule Viewer for Link Manager Algorithm Evaluator           ---
#---                                                                        ---
#--- Last Updated: February 8, 2019                                         ---
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

epoch_ms       = 100                # epoch size in milliseconds

debug          = 0                  # Debug value: initially 0, e.g. no debug

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------


class RanConfig:
    """Class to contain RAN Configuration info"""
    
    def __init__(self, name, id_attr, freq=0, epoch_ms=0, guard_ms=0):
        self.name = name
        self.id   = id_attr
        self.freq = freq
        self.epoch_ms = epoch_ms
        self.guard_ms = guard_ms
        self.links = []
        
        
    def add_link(self, link):
        self.links.append(link)
        

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


def print_banner():
    global stdscr
    global banner_pad
    
    txt_WHITE_on_BLUE = curses.color_pair(8)
    
    height, width = stdscr.getmaxyx()
    
    header = '*' * 106
    banner_pad.addstr(0, 0, header, txt_WHITE_on_BLUE | curses.A_BOLD)
    banner_pad.addstr(1, 0, "**********              TxOp Schedule Viewer for Link Manager Algorithm Evaluator               **********", txt_WHITE_on_BLUE | curses.A_BOLD)
    banner_pad.addstr(2, 0, header, txt_WHITE_on_BLUE | curses.A_BOLD)
    banner_pad.addstr(3,0, ' '*105)
    banner_pad.noutrefresh(0,0, 0,0, 3,(width-1))
    
    
#------------------------------------------------------------------------------


def print_file_info(f, name, config):
    global stdscr
    global file_info_pad
    
    height, width = stdscr.getmaxyx()
    
    msg1 = "MDL File: {}".format(f)
    msg2 = "Name: {}".format(name)
    msg3 = "Configuration Version: {}".format(config)
    file_info_pad.addstr(0, 0, "{0:^102}".format(msg1), curses.A_BOLD)
    file_info_pad.addstr(1, 0, "{0:^102}".format(msg2), curses.A_BOLD)
    file_info_pad.addstr(2, 0, "{0:^102}".format(msg3), curses.A_BOLD | curses.A_UNDERLINE)
    
    if (height-1) >= 8:
        file_info_pad.noutrefresh(0,0, 4,2, 6,(width-1))
    else:
        file_info_pad.noutrefresh(0,0, 4,2, (height-2),(width-1))


#------------------------------------------------------------------------------


def print_ran_stats(ran):
    global stdscr
    global ran_pad
    
    txt_WHITE_on_BLACK    = curses.color_pair(7)
    
    height, width = stdscr.getmaxyx()
    
    ran_pad.addstr(0, 0, "RAN Configuration Name:.....   {0:71}".format(ran.name), txt_WHITE_on_BLACK | curses.A_REVERSE | curses.A_BOLD)
    ran_pad.addstr(1, 0, "Center Frequency:...........   {0} MHz{1:61}".format(int(ran.freq)/1000000, ' '), txt_WHITE_on_BLACK | curses.A_REVERSE | curses.A_BOLD)
    ran_pad.addstr(2, 0, "Epoch Size:.................   {0} ms{1:65}".format(ran.epoch_ms, ' '), txt_WHITE_on_BLACK | curses.A_REVERSE | curses.A_BOLD)
    ran_pad.addstr(3, 0, "Guard Time:.................   {0} ms{1:65}".format(ran.guard_ms, ' '), txt_WHITE_on_BLACK | curses.A_REVERSE | curses.A_BOLD)
    
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
    for idx, link in enumerate (links, start=0):
        print_link_info(link, start_row, idx)
        if len(link.tx_sched) >0 : start_row += 4 + len(link.tx_sched)
        else:                      start_row += 4 + 1
    
    start_row_num = 19
    last_row_num = start_row_num + rows_needed
    
    if (height-1) >= last_row_num:
        link_info_pad.noutrefresh(0,0, start_row_num,2, last_row_num, (width-1))        # TODO: add check for height
    elif (height-1) >= start_row_num:
        link_info_pad.noutrefresh(0,0, start_row_num,2, (height-1), (width-1))
    
#------------------------------------------------------------------------------


def print_link_info(link, row, cp):
    global link_info_pad
    
    link_info_pad.addstr(row,0, "Link: {}".format(link.name), curses.color_pair((cp%7)+1) | curses.A_BOLD)
    link_info_pad.addstr(row+1,0, "Source Radio RF MAC Addr:      {0:5d} [0x{0:04x}] ".format(int(link.src)), curses.color_pair((cp%7)+1) | curses.A_BOLD)
    link_info_pad.addstr(row+2,0, "Destination Group RF MAC Addr: {0:5d} [0x{0:04x}] ".format(int(link.dst)), curses.color_pair((cp%7)+1) | curses.A_BOLD)

    if (len(link.tx_sched)) > 0:
        print_txops_info(link.tx_sched, row+3, cp)
    else:
        link_info_pad.addstr(row+3,2, "  NO TXOPS DEFINED IN MDL FOR THIS LINK  ", curses.color_pair((cp%7)+1) | curses.A_REVERSE | curses.A_BOLD)

#------------------------------------------------------------------------------


def print_txops_info(txops, row, cp):
    global link_info_pad
    
    for idx, txop in enumerate(txops, start=0):
        print_txop_info(txop, idx, row+idx, cp)


#------------------------------------------------------------------------------


def print_txop_info(txop, idx, row, cp):
    global link_info_pad
    
    txop_str = "  TxOp {0}: {1:6d} - {2:6d} us (TTL: {3:3d}) @ {4} MHz  \r".format(
              idx+1, int(txop.start_usec), int(txop.stop_usec), int(txop.timeout), 
              int(txop.freq)/1000000)
    
    link_info_pad.addstr(row,0, txop_str, curses.color_pair((cp%7)+1) | curses.A_REVERSE)
    
    if debug >=1:
        print("  TxOp {0}: {1:6d} - {2:6d} us (TTL: {3:3d}) @ {4} MHz\r".format(
              idx+1, int(txop.start_usec), int(txop.stop_usec), int(txop.timeout), 
              int(txop.freq)/1000000))


#------------------------------------------------------------------------------


def print_txops_in_epoch(epoch_ms, links):
    global stdscr
    global epoch_pad
    global txop_display_pad

    # Color Pair Assignments
    txt_BLUE_on_BLACK    = curses.color_pair(1)
    txt_GREEN_on_BLACK   = curses.color_pair(2)
    txt_RED_on_BLACK     = curses.color_pair(3)
    txt_CYAN_on_BLACK    = curses.color_pair(4)
    txt_YELLOW_on_BLACK  = curses.color_pair(5)
    txt_MAGENTA_on_BLACK = curses.color_pair(6)
    txt_WHITE_on_BLACK   = curses.color_pair(7)

    height, width = stdscr.getmaxyx()

    start_row_num = 13
    last_row_num  = 17
    bar = (int(epoch_ms))/100
    scale_str = "one bar = {} ms".format(bar)
    epoch_bar = "+----------------------------------------------------------------------------------------------------+"
    
    epoch_pad.addstr(0, 0, "{0:>102}".format(scale_str))
    epoch_pad.addstr(1, 0, epoch_bar)
    epoch_pad.addstr(2, 0, '|{0:100}|'.format(" "))
    epoch_pad.addstr(3, 0, epoch_bar)
    
    for idx, link in enumerate(links, start=0):
        for txop in link.tx_sched:
            need_half_block_right = False
            need_half_block_left = False
            start_pos = (int(txop.start_usec) / 1000) / bar
            stop_pos  = (int(txop.stop_usec) / 1000) / bar
            frac_start = 0
            frac_stop  = 0
            
            if (math.floor(start_pos) > 0): frac_start = start_pos%math.floor(start_pos)
            start_pos = math.floor(start_pos)
            if   (frac_start >= 0.75): start_pos += 1
            elif (frac_start >= 0.25): need_half_block_right = True
            
            if (math.floor(stop_pos) > 0):frac_stop = stop_pos%math.floor(stop_pos)
            stop_pos = math.floor(stop_pos)
            if   (frac_stop >= 0.75): stop_pos += 1
            elif (frac_stop >= 0.25): need_half_block_left = True
            
            num_bars = stop_pos - start_pos
            if need_half_block_right and need_half_block_left:
                graphic = u'\u2590' + u'\u2588' * int(num_bars-1) + u'\u258c'
            elif need_half_block_right:
                graphic = u'\u2590' + u'\u2588' * int(num_bars-1)
            elif need_half_block_left:
                graphic = u'\u2588' * int(num_bars) + u'\u258c'
            else:
                graphic = u'\u2588' * int(num_bars)

            epoch_pad.addstr(2, int(start_pos)+1, graphic, curses.color_pair((idx%7)+1))
            

    if (height-1) >= last_row_num:
        epoch_pad.noutrefresh(0,0, start_row_num,2, last_row_num,(width-1))
    elif (height-1) >= start_row_num:
        epoch_pad.noutrefresh(0,0, start_row_num,2, (height-1),(width-1))
        

#------------------------------------------------------------------------------


def print_too_short(height, width):
    global stdscr
    
    bangs = '!' * int((width-49)/2)
    msg1 = bangs + '  DID YOU WANT TO SEE SOMETHING IN THIS WINDOW?  ' + bangs
    msg2 = bangs + '    TRY MAKING THE WINDOW A LITTLE BIT DEEPER.   ' + bangs
    msg3 = bangs + '            RESIZE WINDOW TO CONTINUE            ' + bangs
    stdscr.addstr(0,0,"{0:^{1}}".format(msg1, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
    stdscr.addstr(1,0,"{0:^{1}}".format(msg2, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
    stdscr.addstr(2,0,"{0:^{1}}".format(msg3, width), curses.color_pair(1) | curses.A_BOLD | BLINK)


#------------------------------------------------------------------------------


def print_too_skinny(height, width):
    global stdscr
    
    bangs = '!' * int((width-34)/2)
    msg1 = bangs + '  NOT SURE WHAT YOU EXPECT TO  ' + bangs
    msg2 = bangs + '  SEE ON SUCH A SKINNY SCREEN  ' + bangs
    msg3 = bangs + '  TRY MAKING IT WIDER, OR RISK ' + bangs
    msg4 = bangs + '            SKYNET             ' + bangs
    stdscr.addstr(0,0, "{0:^{1}}".format(msg1, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
    stdscr.addstr(1,0, "{0:^{1}}".format(msg2, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
    stdscr.addstr(2,0, "{0:^{1}}".format(msg3, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
    stdscr.addstr(3,0, "{0:^{1}}".format(msg4, width), curses.color_pair(1) | curses.A_BOLD | BLINK)
    

#------------------------------------------------------------------------------


def main(stdscr):  
    global mdl_file
    rans_list  = []
    links_list = []
    
    # Color Pair Setup
    #curses.init_pair(1, curses.COLOR_WHITE,   curses.COLOR_RED)     # Pair 1: 
    #curses.init_pair(2, curses.COLOR_WHITE,   curses.COLOR_BLUE)    # Pair 2: 
    #curses.init_pair(3, curses.COLOR_WHITE,   curses.COLOR_GREEN)   # Pair 3: 
    #curses.init_pair(4, curses.COLOR_BLACK,   curses.COLOR_WHITE)   # Pair 4: 
    curses.init_pair(1, curses.COLOR_CYAN,    curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN,   curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED,     curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW,  curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_BLUE,    curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_WHITE,   curses.COLOR_BLACK)
    curses.init_pair(8, curses.COLOR_WHITE,   curses.COLOR_BLUE)
    
    height, width = stdscr.getmaxyx()

    stdscr.clear()
    stdscr.refresh()

    
    # Parse MDL file, and create the RAN Config (assuming only a single RAN Config)
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
        rid    = ran.attrib['ID']
        rfreq  = ran.find("mdl:CenterFrequencyHz", namespaces=ns).text
        repoch = ran.find("mdl:EpochSize", namespaces=ns).text
        rguard = float(ran.find("mdl:MaxGuardTimeSec", namespaces=ns).text)*1000
        if debug >=2: print("RAN Name: {}, Frequency: {}, Epoch Size: {}ms, Guardband: {}ms".format(rname, rfreq, repoch, rguard))
        new_ran = RanConfig(name=rname, id_attr=rid, freq=rfreq, epoch_ms=repoch, guard_ms=rguard)
        rans_list.append(new_ran)

    
    # Parse MDL for Radio Links and their associated Transmission Schedules
    radio_links = root.xpath("//mdl:RadioLink", namespaces=ns)
    for radio_link in radio_links:
        rlname = radio_link.find("mdl:Name", namespaces=ns).text
        rlsrc_idref = radio_link.find("mdl:SourceRadioRef", namespaces=ns).attrib
        tmas = root.xpath("//mdl:TmNSApp[@ID='{}']".format(rlsrc_idref["IDREF"]), namespaces=ns)
        rlsrc = tmas[0].find("mdl:TmNSRadio/mdl:RFMACAddress", namespaces=ns).text
        ran_idref = (tmas[0].find("mdl:TmNSRadio/mdl:RANConfigurationRef", namespaces=ns).attrib)['IDREF']
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
        
        # Iterate through the list of RANs, and add the Link to the appropriate RAN
        for r in rans_list:
            if r.id == ran_idref:
                r.add_link(new_link)
 
    ran_idx = 1
    while True:
        height, width = stdscr.getmaxyx()

        stdscr.clear()
        stdscr.refresh()
           
        # Sanity check for window height requirements
        if height < 10:
            print_too_short(height, width)
        elif width < 50:
            print_too_skinny(height, width)
        else:
            print_banner()
            print_file_info(mdl_file, root_name, root_config_ver)
            if len(rans_list) > 0:
                print_ran_stats(rans_list[ran_idx-1])
                if len(rans_list[ran_idx-1].links) > 0:
                    print_links_info(rans_list[ran_idx-1].links)
                print_txops_in_epoch(rans_list[ran_idx-1].epoch_ms, rans_list[ran_idx-1].links)
            
            stdscr.addstr((height-1),0, "*** PRESS ANY KEY TO CONTINUE ***", curses.color_pair(3) | curses.A_BOLD | BLINK)
        stdscr.refresh()
    
        keypress = stdscr.getkey()          # Wait for user to press a key
        if keypress.isdigit(): ran_idx = int(keypress)
        elif keypress == 'q': break
        
        if ran_idx == 0: ran_idx += 1
        if ran_idx > len(rans_list): ran_idx = len(rans_list)


#------------------------------------------------------------------------------


if __name__ == "__main__":
    # Argument Parser Declarations
    parser = argparse.ArgumentParser()
    parser.add_argument('FILE', action='store', default=sys.stdin, help='MDL file to examine', type=str)
    parser.add_argument('-d', action='store', default=0, dest='debug', help='Set the Debug level', type=int)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1.0')
    cli_args = parser.parse_args()

    # CLI argument assignments
    mdl_file = cli_args.FILE
    debug = cli_args.debug
    
    stdscr           = curses.initscr()
    banner_pad       = curses.newpad(4, 106)    # Initialize Banner Pad
    file_info_pad    = curses.newpad(4, 102)    # Initialize File Info Pad
    ran_pad          = curses.newpad(5, 102)    # Initialize RAN Pad
    link_info_pad    = curses.newpad(8, 102)    # Initialize Link Info Pad
    epoch_pad        = curses.newpad(10, 102)   # Initialize Epoch Pad
    txop_display_pad = curses.newpad(1, 100)    # Initialize TxOp Display Pad
    
    if os.name == 'nt':                         # If running on Windows, disable the "blinking" feature of curses
        BLINK = 0                               #   because it doesn't look very good.
    else: BLINK = curses.A_BLINK
    
    wrapper(main)
    #main()
    
    #while True:
    #    signal.pause()