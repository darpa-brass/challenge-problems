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
from shutil import copyfile
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
    parser.add_argument('-r', action='store', dest='rate_file', required=True, type=str,
                        help='Name and location to store the current data input rate file.')
    parser.add_argument('-T', action='store', dest='test_dir', type=str, required=True,
                        help='The test directory that contains the collection of JSON files that define the radio '
                             'data input rates for the test.  Files are named according to the time that they should '
                             'be applied to the simulation (e.g. 30.json, 45.json, 100.json, etc.)')
    parser.add_argument('-l', action='store_true', default=False, dest='loop_mode',
                        help='Loop mode.  Repeat all test cases until user quits.')
    parser.add_argument('-d', action='count', default=0, dest='debug', help='Set the Debug/Verbosity level')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.0.1')

    cli_args = parser.parse_args()

    # CLI argument assignments
    rate_file = cli_args.rate_file
    test_dir = cli_args.test_dir
    loop = cli_args.loop_mode
    debug = cli_args.debug

    runtime = 0

    # Read test_dir for all JSON files.  Sort them by filename (number).
    test_file_times = []
    file_listing = os.listdir(test_dir)
    for f in file_listing:
        filename, ext = os.path.splitext(f)
        if ext == '.json':
            try:
                num = int(filename)
                test_file_times.append(num)
            except ValueError:
                pass

    # 0.json is the initializing file.  If it is not present, add a blank JSON file for this
    if 0 not in test_file_times:
        print("Initialization file not found.  Creating empty initialization at '{0}/0.json'.".format(test_dir))
        empty = []
        with open(test_dir + '/0.json', 'w') as f:
            json.dump(empty, f)
        test_file_times.append(0)

    test_file_times.sort()
    print(test_file_times)

    if len(test_file_times) == 0:
        print("  No test conditions found.  Check the {} directory.".format(test_dir))
        exit(-1)
    elif len(test_file_times) == 1:
        copyfile(test_dir + '/' + str(test_file_times[0]) + '.json', rate_file)
        print("Only one test condition found.  It has been loaded.  Script exiting.")
        exit(0)

    while True:
        for idx, t in enumerate(test_file_times, start=0):
            copyfile(test_dir + '/' + str(t) + '.json', rate_file)
            if idx+1 < len(test_file_times):
                wait_time = test_file_times[idx+1] - t
                print("  Test Condition {0} in progress...duration: {1} seconds".format(idx+1, wait_time))
            else:
                # Last test profile.  Use the previous test duration for this test profile
                wait_time = t - test_file_times[idx-1]
                print("  Test Condition {0} in progress...duration: {1} seconds".format(idx+1, wait_time))
            time.sleep(wait_time)
        if loop:
            print(" Repeating test profiles...")
        else:
            print(" All test profiles completed.")
            break
