# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ---       Data Rate Input Updater  for Radio Queue Visualizer Utility      ---
# ---                                                                        ---
# --- Last Updated: April 19, 2019                                           ---
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

import os
import argparse
import json
from shutil import copyfile
import time
debug = 0                           # Debug value: initially 0, e.g. no debug


# ------------------------------------------------------------------------------
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
