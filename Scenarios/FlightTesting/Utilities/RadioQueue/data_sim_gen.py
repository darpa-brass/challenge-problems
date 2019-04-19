# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ---      Data Rate Input Generator for Radio Queue Visualizer Utility      ---
# ---                                                                        ---
# --- Last Updated: April 18, 2019                                        ---
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
import random

next_timer = 0
epoch_ms = 100                      # epoch size in milliseconds
epoch_sec = epoch_ms / 1000         # epoch size converted to seconds
epochs_per_sec = 1000 / epoch_ms    # number of epochs per second
epoch_num = 0
debug = 0                           # Debug value: initially 0, e.g. no debug

radio_list = []                     # List of Radio objects

msg_list = []

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


class RadioDataInput:
    """Class to contain the characteristics associated with the data input to a Radio."""

    def __init__(self, name, rate_bps=0, burstiness=0.0, val_per_kb_tx=0.0):
        self.name = name
        self.input_rate_bps = rate_bps
        self.burstiness = burstiness
        self.value_per_kb_tx = val_per_kb_tx



# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


def init_epoch_vals(ms):
    global epoch_ms
    global epoch_sec
    global epochs_per_sec
    
    epoch_ms = ms                       # epoch size in milliseconds
    epoch_sec = epoch_ms / 1000         # epoch size converted to seconds
    epochs_per_sec = 1000 / epoch_ms    # number of epochs per second


# ------------------------------------------------------------------------------


def change_input_rate(rname, value):
    global radio_list

    for r in radio_list:
        if r.name == rname:
            r.input_rate_bps = value


# ------------------------------------------------------------------------------


def change_burstiness(rname, value):
    global radio_list

    for r in radio_list:
        if r.name == rname:
            r.burstiness = value


# ------------------------------------------------------------------------------


def change_value_per_tx(rname, value):
    global radio_list

    for r in radio_list:
        if r.name == rname:
            r.value_per_kb_tx = value


# ------------------------------------------------------------------------------


def init_radio_list(input_file):
    global radio_list

    with open(input_file, 'r') as f:
        ldict_radios = json.load(f)

    for d in ldict_radios:
        name = d['RadioName']
        newRDI = RadioDataInput(name)
        radio_list.append(newRDI)


# ------------------------------------------------------------------------------


def update_input_rates_file(file, radios):
    rlist = []

    for r in radios:
        radio_d = {}
        radio_d['RadioName'] = r.name
        radio_d['DataInRate-bps'] = r.input_rate_bps
        radio_d['Burstiness'] = r.burstiness
        radio_d['ValuePerKbTx'] = r.value_per_kb_tx
        rlist.append(radio_d)

    with open(file, 'w') as f:
        json.dump(rlist, f, indent=4)


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    # Argument Parser Declarations
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', action='store', default=100, dest='epoch_size_ms',
                        help='Set the Epoch size (milliseconds) [default: 100]', type=int)
    parser.add_argument('-i', action='store', dest='data_input_rates', required=True, type=str,
                        help='Json with the data input rates for a set of Radios')
    parser.add_argument('-w', action='store', default=10, dest='wait',
                        help='Seconds to wait before switching to the next test condition', type=int)
    parser.add_argument('-d', action='count', default=0, dest='debug', help='Set the Debug/Verbosity level')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.0.1')

    cli_args = parser.parse_args()

    # CLI argument assignments
    data_input_rates_file = cli_args.data_input_rates
    wait_sec = cli_args.wait

    init_epoch_vals(cli_args.epoch_size_ms)     # Pass CLI Epoch size (ms) to the init_epoch_vals() function

    debug = cli_args.debug

    # Initialize the radio_list with all radios from the initial data_input_rate
    init_radio_list(data_input_rates_file)

    # Test Condition 1
    change_input_rate("TA1", 5000)
    change_burstiness("TA2", 0.2)
    change_value_per_tx("TA1", 0.5)
    update_input_rates_file(data_input_rates_file, radio_list)
    print("  Test Condition 1")
    time.sleep(wait_sec)

    # Test Condition 2
    print("  Test Condition 2")

    # Test Condition 3