# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ---      Scenario File Generator for Data Rate Input Generator             ---
# ---                                                                        ---
# --- Last Updated: April 22, 2019                                           ---
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

import os
import argparse
import csv
import json
from shutil import copyfile
import shutil


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


if __name__ == "__main__":
    # Argument Parser Declarations
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', action='store', dest='csv_file', required=True, type=str,
                        help='CSV file of the data rates for the scenario.')
    parser.add_argument('-T', action='store', dest='test_dir', required=True, type=str,
                        help='The test directory to store the collection of JSON files that define the radio '
                             'data input rates for the test.  Files are named according to the time that they should '
                             'be applied to the simulation (e.g. 30.json, 45.json, 100.json, etc.)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.0.1')

    cli_args = parser.parse_args()

    # CLI argument assignments
    csv_file = cli_args.csv_file
    test_dir = cli_args.test_dir

    # Check to see if the Test Directory exists.  If so, prompt the user to see if they want to let it
    # be overwritten or not.  If not, the program exits.
    if os.path.isdir(test_dir):
        while True:
            choice = input("\n  Test Directory already exists.  Replace it and all of its contents? (Y|N)  ")
            if (choice == 'N') or (choice == 'n') or (choice == "No") or (choice == "no"):
                print("    Good idea.  Test Directory remains unmodified.  Exiting.")
                exit(0)
            elif (choice == 'Y') or (choice == 'y') or (choice == "Yes") or (choice == "yes"):
                print("    OK.  Preparing the bit laser...", end='')
                shutil.rmtree(test_dir)
                print("Done!")
                break
            else:
                print("    Sorry, that response didn't compute.  Please enter 'Y' or 'N'.")
        
    os.mkdir(test_dir)
    copyfile(csv_file, test_dir + '/' + csv_file)       # Put a copy of the CSV File into the target directory as an FYI
    
    # Check to see if the CSV file exists.  If it does not, flag user, and then exit.
    if os.path.isfile(csv_file) is False:
        print("  CSV file '{}' does not exist.  Exiting.".format(csv_file))
        exit(-1)
    
    # Open CSV file, and build the data rate scenario files from it.
    print("  Reading CSV data...")
    with open(csv_file) as f:
        csv_data = csv.reader(f, delimiter=',')
        for row in csv_data:
            time = row[0]
            name = row[1].lstrip()
            bitrate = row[2]
            burstiness = row[3]
            value_tx = row[4]
            
            rate_data = []
            
            # Check to see if JSON file exists.  If so, load the rate_data list.
            json_file = test_dir + '/' + str(time) + '.json'
            if os.path.isfile(json_file):
                with open(json_file, 'r') as jf:
                    rate_data = json.load(jf)
            
            # Add new data (e.g. row from CSV file) to the rate_data list
            rate_data.append({"RadioName": name,
                              "DataInRate-bps": int(bitrate),
                              "Burstiness": float(burstiness),
                              "ValuePerKbTx": float(value_tx)})
                                  
            # Write the rate_data list to the JSON file
            with open(json_file, 'w') as jf:
                json.dump(rate_data, jf, indent=4)
            
    print("    Done!.")
    print("  Data Rate files for the test scenario are found here: {}".format(test_dir))
