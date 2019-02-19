# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ---    TxOp Schedule Viewer for Link Manager Algorithm Evaluator           ---
# ---                                                                        ---
# --- Last Updated: February 18, 2019                                        ---
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

import sys
import os
import io
import types
from importlib import import_module
import argparse
from lxml import etree
import math
import operator
import curses
from curses import wrapper
from IPython import get_ipython
from nbformat import read
from IPython.core.interactiveshell import InteractiveShell


ns = {"xsd": "http://www.w3.org/2001/XMLSchema",
      "mdl": "http://www.wsmr.army.mil/RCC/schemas/MDL",
      "tmatsP": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsPGroup",
      "tmatsD": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsDGroup"}


# shortcut dictionary for passing common arguments
n = {"namespaces": ns}

MAX_BW_MBPS = 10.0      # Max data rate (Mbps)
debug = 0               # Debug value: initially 0, e.g. no debug

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


class RanConfig:
    """Class to contain RAN Configuration info"""
    
    def __init__(self, name, id_attr, freq=0, epoch_ms=0, guard_ms=0.0):
        self.name = name
        self.id = id_attr
        self.freq = freq
        self.epoch_ms = epoch_ms
        self.guard_ms = guard_ms
        self.links = []
        self.efficiency_pct = 0
        self.gb_violated = False

    def add_link(self, link):
        self.links.append(link)
    
    def check_guardbands(self):
        txop_list = []
        for l in self.links:
            for t in l.tx_sched:
                start_stop = {'start': int(t.start_usec), 'stop': int(t.stop_usec)}
                txop_list.append(start_stop)
        txop_list.sort(key=operator.itemgetter('start'))
        for i in range(len(txop_list) - 1):
            if int(txop_list[i+1]['start']) < (int(txop_list[i]['stop']) + 1 + (self.guard_ms * 1000)):
                self.gb_violated = True
                if debug >= 2:
                    print("GUARDBAND VIOLATION DETECTED!!! {} {}\r".format(txop_list[i], txop_list[i+1]))


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


class QoSPolicy:
    """Class to contain QoSPolicy info"""
    
    def __init__(self, name, id_attr, lmmc=0, ac=0, lmax=1000000):
        self.name = name
        self.id = id_attr
        self.lmmc = lmmc
        self.ac = ac
        self.max_latency_usec = lmax


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


class TxOp:
    """Class to contain TxOp info"""
    
    def __init__(self, freq=0, start_usec=0, stop_usec=0, timeout=0):
        self.freq = freq
        self.start_usec = start_usec
        self.stop_usec = stop_usec
        self.timeout = timeout
        self.duration_usec = int(stop_usec) - int(start_usec) + 1


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


class RadioLink:
    """Class to contain Radio Link info"""
    
    def __init__(self, name, id_attr, src, dst, qp=None, lat=0):
        self.name = name
        self.id = id_attr
        self.src = src
        self.dst = dst
        self.tx_sched = []
        self.qos_policy = qp
        self.max_latency_usec = lat             # Maximum Possible Latency achievable
        self.tx_dur_per_epoch_usec = 0

    def add_txop(self, txop):
        self.tx_sched.append(txop)
        self.tx_dur_per_epoch_usec += txop.duration_usec

    def calc_max_latency(self, epoch_usec):
        # initialize max_latency_usec with wrap-around TxOps
        if len(self.tx_sched) > 0:
            self.max_latency_usec = (int(epoch_usec) - (int(self.tx_sched[-1].stop_usec) + 1)) + \
                                    int(self.tx_sched[0].start_usec)
        else:
            self.max_latency_usec = 0
        
        # iterate through the Link's TxOp Schedule, and compare latencies between TxOps with the previous max latency
        for i in range(len(self.tx_sched) - 1):
            temp_latency = int(self.tx_sched[i+1].start_usec) - (int(self.tx_sched[i].stop_usec) + 1)
            if temp_latency > self.max_latency_usec:
                self.max_latency_usec = temp_latency


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


class NotebookLoader(object):
    """Module Loader for Jupyter Notebooks"""

    def __init__(self, path=None):
        self.shell = InteractiveShell.instance()
        self.path = path

    def load_module(self, fullname):
        """import a notebook as a module"""
        path = find_notebook(fullname, self.path)

        print("importing Jupyter notebook from %s" % path)

        # load the notebook object
        with io.open(path, 'r', encoding='utf-8') as f:
            nb = read(f, 4)

        # create the module and add it to sys.modules
        # if name in sys.modules:
        #    return sys.modules[name]
        mod = types.ModuleType(fullname)
        mod.__file__ = path
        mod.__loader__ = self
        mod.__dict__['get_ipython'] = get_ipython
        sys.modules[fullname] = mod

        # extra work to ensure that magics that would affect the user_ns
        # actually affect the notebook module's ns
        save_user_ns = self.shell.user_ns
        self.shell.user_ns = mod.__dict__

        try:
            for cell in nb.cells:
                if cell.cell_type == 'code':
                    # transform the input to executable Python
                    code = self.shell.input_transformer_manager.transform_cell(cell.source)
                    # run the code in the module
                    exec(code, mod.__dict__)
        finally:
            self.shell.user_ns = save_user_ns
        return mod


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


class NotebookFinder(object):
    """Module finder that locates Jupyter Notebooks"""

    def __init__(self):
        self.loaders = {}

    def find_module(self, fullname, path=None):
        nb_path = find_notebook(fullname, path)
        if not nb_path:
            return

        key = path
        if path:
            # lists aren't hashable
            key = os.path.sep.join(path)

        if key not in self.loaders:
            self.loaders[key] = NotebookLoader(path)
        return self.loaders[key]


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


def find_notebook(fullname, path=None):
    """find a notebook, given its fully qualified name and an optional path

    This turns "foo.bar" into "foo/bar.ipynb"
    and tries turning "Foo_Bar" into "Foo Bar" if Foo_Bar
    does not exist.
    """
    name = fullname.rsplit('.', 1)[-1]
    if not path:
        path = ['']
    for d in path:
        nb_path = os.path.join(d, name + ".ipynb")
        if os.path.isfile(nb_path):
            return nb_path
        # let import Notebook_Name find "Notebook Name.ipynb"
        nb_path = nb_path.replace("_", " ")
        if os.path.isfile(nb_path):
            return nb_path


# ------------------------------------------------------------------------------


def print_banner():
    global stdscr
    global banner_pad
    global text_d
    
    height, width = stdscr.getmaxyx()
    
    header = '*' * 106
    banner_txt = "**********              TxOp Schedule Viewer for Link Manager Algorithm Evaluator" \
                 "               **********"
    banner_pad.addstr(0, 0, header, text_d['BANNER'] | curses.A_BOLD)
    banner_pad.addstr(1, 0, banner_txt, text_d['BANNER'] | curses.A_BOLD)
    banner_pad.addstr(2, 0, header, text_d['BANNER'] | curses.A_BOLD)
    banner_pad.addstr(3, 0, ' '*105)
    banner_pad.noutrefresh(0, 0, 0, 0, 2, (width-1))
    
    
# ------------------------------------------------------------------------------


def print_file_info(f, name, config, s_file):
    global stdscr
    global file_info_pad
    global text_d

    height, width = stdscr.getmaxyx()
    
    msg1 = "MDL File: {}".format(f)
    msg2 = "Name: {}".format(name)
    msg3 = "Configuration Version: {}".format(config)
    msg4 = "Score Criteria: {}".format(s_file)
    file_info_pad.addstr(0, 0, "{0:^102}".format(msg1), text_d['BG'] | curses.A_BOLD)
    file_info_pad.addstr(1, 0, "{0:^102}".format(msg2), text_d['BG'] | curses.A_BOLD)
    file_info_pad.addstr(2, 0, "{0:^102}".format(msg3), text_d['BG'] | curses.A_BOLD)
    if s_file is None:
        file_info_pad.addstr(3, 0, "{0:>102}".format('Not for score'),
                             text_d['ERROR_BLACK'] | curses.A_BOLD | curses.A_UNDERLINE)
    else:
        file_info_pad.addstr(3, 0, "{0:>102}".format(msg4), text_d['FOR_SCORE'] | curses.A_BOLD | curses.A_UNDERLINE)
    
    if (height-1) >= 9:
        file_info_pad.noutrefresh(0, 0, 4, 2, 7, (width-1))
    else:
        file_info_pad.noutrefresh(0, 0, 4, 2, (height-2), (width-1))


# ------------------------------------------------------------------------------


def print_ran_stats(ran):
    global stdscr
    global ran_pad
    global text_d
    
    height, width = stdscr.getmaxyx()
    
    ran_pad.addstr(0, 0, "RAN Configuration Name:.....   {0:71}".format(ran.name),
                   text_d['BG'] | curses.A_REVERSE | curses.A_BOLD)
    ran_pad.addstr(1, 0, "Center Frequency:...........   {0} MHz{1:61}".format(int(ran.freq)/1000000, ' '),
                   text_d['BG'] | curses.A_REVERSE | curses.A_BOLD)
    ran_pad.addstr(2, 0, "Epoch Size:.................   {0} ms{1:65}".format(ran.epoch_ms, ' '),
                   text_d['BG'] | curses.A_REVERSE | curses.A_BOLD)
    ran_pad.addstr(3, 0, "Guard Time:.................   {0:0.3f} ms{1:63}".format(ran.guard_ms, ' '),
                   text_d['BG'] | curses.A_REVERSE | curses.A_BOLD)
    
    start_row_pos = 9
    last_row_pos = 12
    
    if (height-1) >= last_row_pos:
        ran_pad.noutrefresh(0, 0, start_row_pos, 2, last_row_pos, (width-1))
    elif (height-1) >= start_row_pos:
        ran_pad.noutrefresh(0, 0, start_row_pos, 2, (height-1), (width-1))
        

# ------------------------------------------------------------------------------


def print_links_info(links, num_rans, epoch_ms):
    global stdscr
    global link_info_pad
    global text_d
    
    height, width = stdscr.getmaxyx()
    
    rows_needed = 1
    for l in links:
        if len(l.tx_sched) == 0:
            rows_needed += 4 + 1
        else:
            rows_needed += 4 + len(l.tx_sched)
    
    link_info_pad = curses.newpad(rows_needed, 102)
    link_info_pad.bkgd(text_d['BG'])
    
    link_info_pad.addstr(0, 0, "{0:^102}".format("RAN DETAILS"), text_d['BG'] | curses.A_UNDERLINE)
    link_info_pad.addstr(0, 96, "SCORE", text_d['BG'] | curses.A_UNDERLINE)
    
    start_row = 1
    for idx, link in enumerate(links, start=0):
        print_link_info(link, epoch_ms, start_row, idx)
        if len(link.tx_sched) > 0:
            start_row += 4 + len(link.tx_sched)
        else:
            start_row += 4 + 1
    
    start_row_num = 16 + (5 * num_rans)
    last_row_num = start_row_num + rows_needed
    
    if (height-1) >= last_row_num:
        link_info_pad.noutrefresh(0, 0, start_row_num, 2, last_row_num, (width-1))
    elif (height-1) >= start_row_num:
        link_info_pad.noutrefresh(0, 0, start_row_num, 2, (height-1), (width-1))


# ------------------------------------------------------------------------------


def print_link_info(link, epoch_ms, row, cp):
    global link_info_pad
    global mod_name

    txt_color = curses.color_pair((cp % 10) + 1)

    link_info_pad.addstr(row, 0, "Link: {}".format(link.name), txt_color | curses.A_BOLD)
    link_info_pad.addstr(row+1, 0, "Source Radio RF MAC Addr:      {0:5d} [0x{0:04x}] ".format(int(link.src)),
                         txt_color | curses.A_BOLD)
    link_info_pad.addstr(row+2, 0, "Destination Group RF MAC Addr: {0:5d} [0x{0:04x}] ".format(int(link.dst)),
                         txt_color | curses.A_BOLD)
    link_info_pad.addstr(row+1, 56, "Max Latency Requirement:    ", txt_color)
    link_info_pad.addstr(row+2, 56, "Max Latency Achievable:     ", txt_color | curses.A_UNDERLINE)
    link_info_pad.addstr(row+3, 56, "Minimum Capacity Required:  ", txt_color)
    link_info_pad.addstr(row+4, 56, "Allocated Bandwidth:        ", txt_color)

    if link.qos_policy is None:
        link_info_pad.addstr(row+1, 84, "No QoS Policy!",
                             txt_color | curses.A_BOLD | curses.A_REVERSE | BLINK)
        if link.max_latency_usec == 0:
            link_info_pad.addstr(row+2, 84, "{0:^9}".format('N/A'), txt_color | curses.A_UNDERLINE)
        else:
            link_info_pad.addstr(row+2, 84, "{0:.3f} ms".format(int(link.max_latency_usec) / 1000),
                                 txt_color | curses.A_UNDERLINE)
            
    else:
        if int(link.qos_policy.max_latency_usec) == 1000000.0:
            link_info_pad.addstr(row+1, 84, "N/A", txt_color)
        else:
            link_info_pad.addstr(row+1, 84, "{0:.3f} ms".format(int(link.qos_policy.max_latency_usec) / 1000),
                                 txt_color)
    
        if link.max_latency_usec == 0:
            if link.qos_policy.max_latency_usec < 1000000.0:
                link_info_pad.addstr(row+2, 84, "{0:^9}".format('N/A'),
                                     txt_color | curses.A_UNDERLINE | curses.A_REVERSE | BLINK)
            else:
                link_info_pad.addstr(row+2, 84, "{0:^9}".format('N/A'),
                                     txt_color | curses.A_UNDERLINE)
        elif link.max_latency_usec < link.qos_policy.max_latency_usec:
            link_info_pad.addstr(row+2, 84, "{0:.3f} ms".format(int(link.max_latency_usec) / 1000),
                                 txt_color | curses.A_UNDERLINE)
        else: 
            link_info_pad.addstr(row+2, 84, "{0:.3f} ms".format(int(link.max_latency_usec) / 1000),
                                 txt_color | curses.A_UNDERLINE | curses.A_REVERSE | BLINK)

    alloc_bw_mbps = ((int(link.tx_dur_per_epoch_usec) * (1000 / int(epoch_ms))) / 1000000) * MAX_BW_MBPS
    
    if link.qos_policy is None:
        link_info_pad.addstr(row+3, 84, "No QoS Policy!", txt_color |
                             curses.A_BOLD | curses.A_REVERSE | BLINK)
        link_info_pad.addstr(row+4, 84, "{0:0.3f} Mbps".format(alloc_bw_mbps), txt_color)
    else:
        qp_ac_mbps = int(link.qos_policy.ac) / 1000000    # get QoS Policy rate in Mbps
        link_info_pad.addstr(row+3, 84, "{0:0.3f} Mbps".format(qp_ac_mbps), txt_color)
        
        if qp_ac_mbps <= alloc_bw_mbps:
            link_info_pad.addstr(row+4, 84, "{0:0.3f} Mbps".format(alloc_bw_mbps), txt_color)
        else:
            link_info_pad.addstr(row+4, 84, "{0:0.3f} Mbps".format(alloc_bw_mbps), txt_color | curses.A_REVERSE | BLINK)

    if mod_name in sys.modules:
        if 'fun_l' in dir(sys.modules[mod_name]):
            l_score = sys.modules[mod_name].fun_l(link.max_latency_usec / 1000)
        else:
            if debug >= 1:
                print("Function 'fun_l' not found in the SCORE_FILE\n")
            l_score = 0.0
        if 'fun_tp' in dir(sys.modules[mod_name]):
            tp_score = sys.modules[mod_name].fun_tp(alloc_bw_mbps * 1000)
        else:
            if debug >= 1:
                print("Function 'fun_tp' not found in the SCORE_FILE\n")
            tp_score = 0.0
    else:
        l_score = 0.0
        tp_score = 0.0

    link_info_pad.addstr(row+2, 96, "{0:0.1f}".format(l_score), txt_color | curses.A_UNDERLINE | curses.A_BOLD)
    link_info_pad.addstr(row+4, 96, "{0:0.1f}".format(tp_score), txt_color | curses.A_UNDERLINE | curses.A_BOLD)

    if (len(link.tx_sched)) > 0:
        print_txops_info(link.tx_sched, row+3, cp)
    else:
        link_info_pad.addstr(row+3, 2, "  NO TXOPS DEFINED IN MDL FOR THIS LINK  ",
                             txt_color | curses.A_REVERSE | curses.A_BOLD)


# ------------------------------------------------------------------------------


def print_txops_info(txops, row, cp):
    global link_info_pad
    
    for idx, txop in enumerate(txops, start=0):
        print_txop_info(txop, idx, row+idx, cp)


# ------------------------------------------------------------------------------


def print_txop_info(txop, idx, row, cp):
    global link_info_pad

    txt_color = curses.color_pair((cp % 10) + 1)
    txop_str = "  TxOp {0}: {1:6d} - {2:6d} us (TTL: {3:3d}) @ {4} MHz  \r".format(
              idx+1, int(txop.start_usec), int(txop.stop_usec), int(txop.timeout), 
              int(txop.freq)/1000000)
    
    link_info_pad.addstr(row, 0, txop_str, txt_color | curses.A_REVERSE)
    
    if debug >= 2:
        print("  TxOp {0}: {1:6d} - {2:6d} us (TTL: {3:3d}) @ {4} MHz\r".format(
              idx+1, int(txop.start_usec), int(txop.stop_usec), int(txop.timeout), 
              int(txop.freq)/1000000))


# ------------------------------------------------------------------------------


def print_txops_in_all_rans(rans, sel):
    global stdscr
    global epoch_pad
    global txop_display_pad
    global text_d
    
    height, width = stdscr.getmaxyx()
    
    rows_needed = (len(rans) * 5)
    epoch_pad = curses.newpad(rows_needed, 102)
    epoch_pad.bkgd(text_d['BG'])

    start_row_num = 15
    last_row_num = start_row_num + rows_needed
    
    for idx, ran in enumerate(rans, start=0):
        print_txops_in_epoch(ran, idx, sel)

    if (height-1) >= last_row_num:
        epoch_pad.noutrefresh(0, 0, start_row_num, 2, last_row_num, (width-1))
    elif (height-1) >= start_row_num:
        epoch_pad.noutrefresh(0, 0, start_row_num, 2, (height-1), (width-1))


# ------------------------------------------------------------------------------


def print_txops_in_epoch(ran, ran_num, sel):
    global stdscr
    global epoch_pad
    global txop_display_pad
    global text_d
    
    epoch_ms = ran.epoch_ms
    links = ran.links

    start_row_num = (ran_num * 5)
    bar = (int(epoch_ms))/100
    scale_str = "one bar = {} ms".format(bar)
    epoch_bar = "+----------------------------------------------------------------------------------------------------+"
    
    if ran_num == sel:
        epoch_pad.addstr(start_row_num, 0, "{0:>102}".format(scale_str), text_d['BG'] | curses.A_REVERSE)
        epoch_pad.addstr(start_row_num, 0, "{0}.)  {1}\t|\tBW Efficiency: {2:5.2f}%".
                         format((ran_num+1), ran.name, ran.efficiency_pct), text_d['BG'] | curses.A_REVERSE |
                         curses.A_BOLD)
        epoch_pad.addstr(start_row_num, 51, '|'.format(" "), text_d['BG'] | curses.A_REVERSE | curses.A_BOLD)
        epoch_pad.addstr(start_row_num, 54, 'Guardbands:', text_d['BG'] | curses.A_REVERSE | curses.A_BOLD)

        if ran.gb_violated is False:
            epoch_pad.addstr(start_row_num, 66, '{}'.format("OK"), text_d['PASS_WHITE'] | curses.A_BOLD)
        else:
            epoch_pad.addstr(start_row_num, 66, '{}'.format("VIOLATION"), text_d['ERROR_WHITE'] | curses.A_BOLD | BLINK)

        epoch_pad.addstr(start_row_num+1, 0, epoch_bar, text_d['BG'] | curses.A_REVERSE)
        epoch_pad.addstr(start_row_num+2, 0, '|{0:100}|'.format(" "), text_d['BG'] | curses.A_REVERSE)
        epoch_pad.addstr(start_row_num+3, 0, epoch_bar, text_d['BG'] | curses.A_REVERSE)
    else:
        epoch_pad.addstr(start_row_num, 0, "{0:>102}".format(scale_str), text_d['BG'])
        epoch_pad.addstr(start_row_num, 0, "{0}.)  {1}\t|\tBW Efficiency: {2:5.2f}%".
                         format((ran_num+1), ran.name, ran.efficiency_pct), text_d['BG'] | curses.A_BOLD)
        epoch_pad.addstr(start_row_num, 51, '|'.format(" "), text_d['BG'] | curses.A_BOLD)
        epoch_pad.addstr(start_row_num, 54, '{}'.format("Guardbands:"), text_d['BG'] | curses.A_BOLD)
        if ran.gb_violated is False:
            epoch_pad.addstr(start_row_num, 66, '{}'.format("OK"), text_d['PASS_BLACK'] | curses.A_BOLD)
        else:
            epoch_pad.addstr(start_row_num, 66, '{}'.format("VIOLATION"), text_d['ERROR_BLACK'] | curses.A_BOLD | BLINK)
        epoch_pad.addstr(start_row_num+1, 0, epoch_bar, text_d['BG'])
        epoch_pad.addstr(start_row_num+2, 0, '|{0:100}|'.format(" "), text_d['BG'])
        epoch_pad.addstr(start_row_num+3, 0, epoch_bar, text_d['BG'])
    
    for idx, link in enumerate(links, start=0):
        for txop in link.tx_sched:
            need_half_block_right = False
            need_half_block_left = False
            start_pos = (int(txop.start_usec) / 1000) / bar
            stop_pos = (int(txop.stop_usec) / 1000) / bar
            frac_start = 0
            frac_stop = 0
            
            if math.floor(start_pos) > 0:
                frac_start = start_pos % math.floor(start_pos)
            start_pos = math.floor(start_pos)
            if frac_start >= 0.75:
                start_pos += 1
            elif frac_start >= 0.25:
                need_half_block_right = True
            
            if math.floor(stop_pos) > 0:
                frac_stop = stop_pos % math.floor(stop_pos)
            stop_pos = math.floor(stop_pos)
            if frac_stop >= 0.75:
                stop_pos += 1
            elif frac_stop >= 0.25:
                need_half_block_left = True
            
            num_bars = stop_pos - start_pos
            if need_half_block_right and need_half_block_left:
                graphic = u'\u2590' + u'\u2588' * int(num_bars-1) + u'\u258c'
            elif need_half_block_right:
                graphic = u'\u2590' + u'\u2588' * int(num_bars-1)
            elif need_half_block_left:
                graphic = u'\u2588' * int(num_bars) + u'\u258c'
            else:
                graphic = u'\u2588' * int(num_bars)

            if ran_num == sel:
                epoch_pad.addstr(start_row_num+2, int(start_pos)+1, graphic, curses.color_pair((idx % 10) + 11))
            else:
                epoch_pad.addstr(start_row_num+2, int(start_pos)+1, graphic, curses.color_pair((idx % 10) + 1))
            

# ------------------------------------------------------------------------------


def print_too_short(width):
    global stdscr
    global text_d
    
    bangs = '!' * int((width-49)/2)
    msg1 = bangs + '  DID YOU WANT TO SEE SOMETHING IN THIS WINDOW?  ' + bangs
    msg2 = bangs + '    TRY MAKING THE WINDOW A LITTLE BIT DEEPER.   ' + bangs
    msg3 = bangs + '            RESIZE WINDOW TO CONTINUE            ' + bangs
    stdscr.addstr(0, 0, "{0:^{1}}".format(msg1, width), text_d['ERROR_BLACK'] | curses.A_BOLD | BLINK)
    stdscr.addstr(1, 0, "{0:^{1}}".format(msg2, width), text_d['ERROR_BLACK'] | curses.A_BOLD | BLINK)
    stdscr.addstr(2, 0, "{0:^{1}}".format(msg3, width), text_d['ERROR_BLACK'] | curses.A_BOLD | BLINK)


# ------------------------------------------------------------------------------


def print_too_skinny(width):
    global stdscr
    global text_d
    
    bangs = '!' * int((width-34)/2)
    msg1 = bangs + '  NOT SURE WHAT YOU EXPECT TO  ' + bangs
    msg2 = bangs + '  SEE ON SUCH A SKINNY SCREEN  ' + bangs
    msg3 = bangs + '  TRY MAKING IT WIDER, OR RISK ' + bangs
    msg4 = bangs + '            SKYNET             ' + bangs
    stdscr.addstr(0, 0, "{0:^{1}}".format(msg1, width), text_d['ERROR_BLACK'] | curses.A_BOLD | BLINK)
    stdscr.addstr(1, 0, "{0:^{1}}".format(msg2, width), text_d['ERROR_BLACK'] | curses.A_BOLD | BLINK)
    stdscr.addstr(2, 0, "{0:^{1}}".format(msg3, width), text_d['ERROR_BLACK'] | curses.A_BOLD | BLINK)
    stdscr.addstr(3, 0, "{0:^{1}}".format(msg4, width), text_d['ERROR_BLACK'] | curses.A_BOLD | BLINK)
    

# ------------------------------------------------------------------------------


def main(stdscr):  
    global mdl_file
    global score_file
    global text_d
    rans_list = []
    qos_policies_list = []
    
    # Color Pair Setup
    curses.init_pair(1, 114, 235)       # greenish 1
    curses.init_pair(2, 152, 235)       # bluish 1
    curses.init_pair(3, 182, 235)       # purplish 1
    curses.init_pair(4, 210, 235)       # redish 1
    curses.init_pair(5, 229, 235)       # yellowish 1
    curses.init_pair(6, 42,  235)       # greenish 2
    curses.init_pair(7, 37,  235)       # bluish 2
    curses.init_pair(8, 135, 235)       # purplish 2
    curses.init_pair(9, 175, 235)       # redish 2
    curses.init_pair(10, 222, 235)      # yellowish 2
    curses.init_pair(11, 114, 15)       # greenish 1 on white
    curses.init_pair(12, 152, 15)       # bluish 1 on white
    curses.init_pair(13, 182, 15)       # purplish 1 on white
    curses.init_pair(14, 210, 15)       # redish 1 on white
    curses.init_pair(15, 229, 15)       # yellowish 1 on white
    curses.init_pair(16, 42, 15)        # greenish 2 on white
    curses.init_pair(17, 37, 15)        # bluish 2 on white
    curses.init_pair(18, 135, 15)       # purplish 2 on white
    curses.init_pair(19, 175, 15)       # redish 2 on white
    curses.init_pair(20, 222, 15)       # yellowish 2 on white
    curses.init_pair(249, 27, 235)
    curses.init_pair(250, 10, 235)
    curses.init_pair(251, 10, 15)
    curses.init_pair(252, 10, 235)
    curses.init_pair(253, 9, 15)
    curses.init_pair(254, 9, 235)
    curses.init_pair(255, 15, 235)

    text_d['BANNER'] = curses.color_pair(249)
    text_d['FOR_SCORE'] = curses.color_pair(250)
    text_d['PASS_WHITE'] = curses.color_pair(251)
    text_d['PASS_BLACK'] = curses.color_pair(252)
    text_d['ERROR_WHITE'] = curses.color_pair(253)
    text_d['ERROR_BLACK'] = curses.color_pair(254)
    text_d['BG'] = curses.color_pair(255)

    stdscr.bkgd(text_d['BG'])
    stdscr.clear()
    stdscr.refresh()

    # Parse MDL file, and create the RAN Config (assuming only a single RAN Config)
    mdl_parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(mdl_file, mdl_parser)
    
    if debug >= 3:
        print("***** MDL FILE CONTENTS *****")
        print(etree.tostring(root))
        print("***** END MDL FILE *****")
    
    # Parse MDL file for Configuration Version
    root_name = root.find("mdl:Name", namespaces=ns).text
    root_config_ver = root.find("mdl:ConfigurationVersion", namespaces=ns).text
    
    # Parse MDL file for RAN Config Parameters
    rans = root.xpath("//mdl:RANConfiguration", namespaces=ns)
    for ran in rans:
        rname = ran.find("mdl:Name", namespaces=ns).text
        rid = ran.attrib['ID']
        rfreq = ran.find("mdl:CenterFrequencyHz", namespaces=ns).text
        repoch = ran.find("mdl:EpochSize", namespaces=ns).text
        rguard = float(ran.find("mdl:MaxGuardTimeSec", namespaces=ns).text) * 1000
        if debug >= 2:
            print("RAN Name: {}, Frequency: {}, Epoch Size: {}ms, Guardband: {}ms".format(rname, rfreq, repoch, rguard))
        new_ran = RanConfig(name=rname, id_attr=rid, freq=rfreq, epoch_ms=repoch, guard_ms=rguard)
        rans_list.append(new_ran)

    # Parse MDL file for Radio Links and their associated Transmission Schedules
    radio_links = root.xpath("//mdl:RadioLink", namespaces=ns)
    for radio_link in radio_links:
        rlname = radio_link.find("mdl:Name", namespaces=ns).text
        rlid = radio_link.attrib['ID']
        rlsrc_idref = radio_link.find("mdl:SourceRadioRef", namespaces=ns).attrib
        tmas = root.xpath("//mdl:TmNSApp[@ID='{}']".format(rlsrc_idref["IDREF"]), namespaces=ns)
        rlsrc = tmas[0].find("mdl:TmNSRadio/mdl:RFMACAddress", namespaces=ns).text
        ran_idref = tmas[0].find("mdl:TmNSRadio/mdl:RANConfigurationRef", namespaces=ns).attrib['IDREF']
        rldst_idref = radio_link.find("mdl:DestinationRadioGroupRef", namespaces=ns).attrib
        rgs = root.xpath("//mdl:RadioGroup[@ID='{}']".format(rldst_idref["IDREF"]), namespaces=ns)
        rldst = rgs[0].find("mdl:GroupRFMACAddress", namespaces=ns).text
        
        new_link = RadioLink(rlname, rlid, rlsrc, rldst)
        
        tx_sched = radio_link.find("mdl:TransmissionSchedule", namespaces=ns)
        if tx_sched is not None:
            # Loop through the TxOps if they are defined for this link
            for txop in tx_sched:
                txop_freq = txop.find("mdl:CenterFrequencyHz", namespaces=ns).text
                txop_start = txop.find("mdl:StartUSec", namespaces=ns).text
                txop_stop = txop.find("mdl:StopUSec", namespaces=ns).text
                txop_timeout = txop.find("mdl:TxOpTimeout", namespaces=ns).text
                new_txop = TxOp(txop_freq, txop_start, txop_stop, txop_timeout)
                new_link.add_txop(new_txop)
        
        # Iterate through the list of RANs, and add the Link to the appropriate RAN
        for r in rans_list:
            if r.id == ran_idref:
                r.add_link(new_link)
    
    # Parse MDL file for QoS Policy Info (specifically, the max latency requirement)
    qos_policies = root.xpath("//mdl:QoSPolicy", namespaces=ns)
    for qos_policy in qos_policies:
        # Find the max latency requirement for the policy
        latencies = qos_policy.findall(".//mdl:AveragePacketDelay", namespaces=ns)
        value_usec = 1000000.0
        for latency in latencies:
            temp_value_usec = float(latency.find("mdl:Value", namespaces=ns).text)
            units = latency.find("mdl:BaseUnit", namespaces=ns).text
            if units == "Second":
                temp_value_usec = temp_value_usec * 1000000
            if temp_value_usec < value_usec:
                value_usec = temp_value_usec
                        
        qpname = qos_policy.find("mdl:Name", namespaces=ns).text
        qpid = qos_policy.attrib['ID']
        qplmmc = qos_policy.find("mdl:LinkManagementMinCapacity/mdl:Value", namespaces=ns).text
        qpac = qos_policy.find("mdl:AssuredCapacity/mdl:Value", namespaces=ns).text
        qplmax = int(value_usec)
        new_qp = QoSPolicy(qpname, qpid, qplmmc, qpac, qplmax)
        qos_policies_list.append(new_qp)
        
        rlrefs = qos_policy.findall(".//mdl:RadioLinkRef", namespaces=ns)
        for rlref in rlrefs:
            for r in rans_list:
                for l in r.links:
                    if l.id == rlref.attrib["IDREF"]:
                        l.qos_policy = qos_policies_list[-1]

    # Calculate Schedule Efficiency per RAN
    for r in rans_list:
        total_time_usec = 0
        for l in r.links:
            for t in l.tx_sched:
                total_time_usec += t.duration_usec
        
        r.efficiency_pct = total_time_usec / (int(r.epoch_ms) * 1000) * 100
            
    # Calculate Minimum Latency Requirement Achievable
    for r in rans_list:
        epoch_usec = int(r.epoch_ms) * 1000
        for l in r.links:
            l.calc_max_latency(epoch_usec)

    # Check for any guardband violations
    for r in rans_list:
        r.check_guardbands()

    # Print to screen
    num_rans = len(rans_list)
    ran_idx = 1
    while True:
        height, width = stdscr.getmaxyx()

        stdscr.clear()
        stdscr.refresh()
           
        # Sanity check for window height requirements
        if height < 10:
            print_too_short(width)
        elif width < 50:
            print_too_skinny(width)
        else:
            print_banner()
            print_file_info(mdl_file, root_name, root_config_ver, score_file)
            if num_rans > 0:
                print_ran_stats(rans_list[ran_idx-1])
                if len(rans_list[ran_idx-1].links) > 0:
                    print_links_info(rans_list[ran_idx-1].links, num_rans, rans_list[ran_idx-1].epoch_ms)
                print_txops_in_all_rans(rans_list, (ran_idx-1))

            post_banner_pad.bkgd(text_d['BG'])
            post_banner_pad.addstr(0, 0, "***  ENTER RAN # FOR DETAILS   |   PRESS 'q' TO QUIT  ***",
                                   text_d['ERROR_BLACK'] | curses.A_BOLD | BLINK)
            post_banner_pad.noutrefresh(0, 0, (height-1), 0, (height-1), (width-1))
        stdscr.refresh()
    
        keypress = stdscr.getkey()          # Wait for user to press a key
        if keypress.isdigit():
            ran_idx = int(keypress)
        elif keypress == 'q':
            break
        
        if ran_idx == 0:
            ran_idx += 1
        if ran_idx > len(rans_list):
            ran_idx = len(rans_list)

# ------------------------------------------------------------------------------


def no_gui():
    return 0


if __name__ == "__main__":
    # Argument Parser Declarations
    parser = argparse.ArgumentParser()
    parser.add_argument('FILE', action='store', default=sys.stdin, help='MDL file to examine', type=str)
    parser.add_argument('-s', action='store', default=None, dest='SCORE',
                        help='JSON file to score MDL file performance', type=str)
    parser.add_argument('-d', action='store', default=0, dest='debug', help='Set the Debug level', type=int)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.2.3')
    cli_args = parser.parse_args()

    # CLI argument assignments
    mdl_file = cli_args.FILE
    score_file = cli_args.SCORE
    mod_name = None
    debug = cli_args.debug
    text_d = {}

    if score_file is not None:
        mod_name, ext = os.path.splitext(os.path.split(score_file)[-1])
        if ext == '.ipynb':
            sys.meta_path.append(NotebookFinder())      # Register the NotebookFinder with sys.meta_path
            InteractiveShell.enable_gui = no_gui()
            try:
                import_module(mod_name)
            except:
                score_file = None
        else:
            if debug >= 1:
                print("{} is not a valid SCORE_FILE.  Please specify an *.ipynb file.".format(score_file))
            score_file = None

    stdscr = curses.initscr()
    banner_pad = curses.newpad(4, 106)          # Initialize Banner Pad
    post_banner_pad = curses.newpad(1, 106)     # Initialize Post Banner Pad
    file_info_pad = curses.newpad(6, 102)       # Initialize File Info Pad
    ran_pad = curses.newpad(5, 102)             # Initialize RAN Pad
    link_info_pad = curses.newpad(8, 102)       # Initialize Link Info Pad
    epoch_pad = curses.newpad(10, 102)          # Initialize Epoch Pad
    txop_display_pad = curses.newpad(1, 100)    # Initialize TxOp Display Pad
    
    if os.name == 'nt':                         # If running on Windows, disable the "blinking" feature of curses
        BLINK = 0                               # because it doesn't look very good.
    else:
        BLINK = curses.A_BLINK
    
    wrapper(main)
