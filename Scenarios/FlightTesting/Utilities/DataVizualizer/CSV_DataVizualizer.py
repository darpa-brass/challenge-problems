import os
import sys
import time
import argparse
import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def main(cli_args):
    bad_data_path = cli_args.base_bad
    corrected_data_path = cli_args.base_corrected
    nominal_data_path = cli_args.base_nominal
    original_data_dict = {}
    corrected_data_dict = {}
    dataset = pd.DataFrame()
    sns.set(style="darkgrid")



    for file in os.listdir(corrected_data_path):
        bad_file_path = os.path.join(corrected_data_path, file)
        if os.path.isfile(bad_file_path):
            ext = os.path.splitext(file)[-1].lower()
            if ext == ".csv":
                with open(bad_file_path, 'r') as f1:
                    csv_file = csv.reader(f1)
                    corrected_data = []
                    channel_1 = []
                    channel_2 = []
                    channel_3 = []
                    for row in csv_file:
                        try:
                            channel_1.append(float(row[0]))
                            channel_2.append(float(row[1]))
                            channel_3.append(float(row[2]))
                        except ValueError:
                            continue
        corrected_data = [channel_1, channel_2, channel_3]

    for file in os.listdir(nominal_data_path):
        nominal_file_path = os.path.join(nominal_data_path, file)

        file_name = os.path.splitext(file)[0].lower()
        ext = os.path.splitext(file)[-1].lower()
        if ext == ".csv" and os.path.isfile(nominal_file_path):
            with open(nominal_file_path, 'r') as f1:
                csv_file = csv.reader(f1)
                value = []
                times = []
                for row in csv_file:
                    try:
                        value.append(int(row[0]))
                        times.append(float(row[1]))
                    except ValueError:
                        continue
                time_array = np.asarray(times)
                nominal_dataset = pd.DataFrame({'value': np.asarray(value),
                                                 'time': time_array})

            dataset = pd.concat([dataset, nominal_dataset.assign(source='nominal', data_channel=file_name)],
                                axis=0,
                                ignore_index=False,
                                sort=False)

    index = 0
    for file in os.listdir(bad_data_path):
        bad_file_path = os.path.join(bad_data_path, file)
        if os.path.isfile(bad_file_path):
            file_name = os.path.splitext(file)[0].lower()
            ext = os.path.splitext(file)[-1].lower()
            if ext == ".csv":

                with open(bad_file_path, 'r') as f1:
                    csv_file = csv.reader(f1)
                    value = []
                    times = []
                    for row in csv_file:
                        try:
                            value.append(int(row[0]))
                            times.append(float(row[1]))
                        except ValueError:
                            continue
                    time_array = np.asarray(times)
                    original_dataset = pd.DataFrame({'value': np.asarray(value),
                                                     'time': time_array})

                    corrected_dataset = pd.DataFrame({'value': np.asarray(corrected_data[index]),
                                                      'time': time_array})


                    # original_data_dict[file_name] = {'value': np.asarray(value), 'time': np.asarray(times)}
                    # corrected_data_dict[file_name] = {'time': np.asarray(times), 'value': np.asarray(corrected_data[index])}

                dataset = pd.concat([dataset,
                                      original_dataset.assign(source='original', data_channel=file_name),
                                      corrected_dataset.assign(source='corrected', data_channel=file_name)],
                                     axis=0,
                                     ignore_index=False,
                                     sort=False)
                index = +1

    g = sns.FacetGrid(dataset, col="source", row="data_channel", margin_titles=True)
    g.map(plt.scatter, "time", "value")
    plt.show()


if __name__ == "__main__":
    now = time.strftime("%Y%m%d_%H%M%S")
    # Argument Parser Declarations
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', action='store', default=None, dest='base_bad', help='Path to incorrect Base Acceleration Data in CSV format', type=str)
    parser.add_argument('-bc', action='store', default=None, dest='base_corrected', help='Path to synthesized Base Acceleration Data in CSV format', type=str)
    parser.add_argument('-bn', action='store', default=None, dest='base_nominal', help='Path to ground truth Base Acceleration Data in CSV format', type=str)
    cli_args = parser.parse_args()
    main(cli_args)
