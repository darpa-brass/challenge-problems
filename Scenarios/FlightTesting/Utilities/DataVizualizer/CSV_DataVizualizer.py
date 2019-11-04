import os
import sys
import time
import argparse
import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def normalize_time(time_list):
    start_time = time_list[0]
    time = [(x - start_time)/10**9 for x in time_list]
    return time


def main(cli_args):
    time_label = ('Time(s)')
    value_label = ('Acceleration(m/s^2)')
    bad_data_path = cli_args.base_bad
    corrected_data_path = cli_args.base_corrected
    nominal_data_path = cli_args.base_nominal
    original_data_dict = {}
    corrected_data_dict = {}
    dataset = pd.DataFrame()
    sns.set(style="darkgrid")




    with open(corrected_data_path, 'r') as f1:
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

    for file in sorted(os.listdir(nominal_data_path)):
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
                        
                time_array = np.mean(np.asarray(normalize_time(times)).reshape(-1, 61), axis=1)
                nominal_data = np.mean(np.asarray(value).reshape(-1, 61), axis=1)

                nominal_dataset = pd.DataFrame({value_label: nominal_data,
                                                time_label: time_array}).assign(source='Ground Truth',
                                                                                data_channel=file_name)

            dataset = pd.concat([dataset, nominal_dataset],
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
                    print()
                    time_array = np.mean(np.asarray(normalize_time(times)).reshape(-1, 61), axis=1)
                    original_data = np.mean(np.asarray(value).reshape(-1, 61), axis=1)
                    modified_correction = np.mean(np.asarray(corrected_data[index]).reshape(-1, 61), axis=1)


                    original_dataset = pd.DataFrame({value_label: original_data,
                                                     time_label: time_array}).assign(source='Original',
                                                                                 data_channel=file_name)

                    corrected_dataset = pd.DataFrame({value_label: modified_correction,
                                                      time_label: time_array}).assign(source='Adapted',
                                                                                      data_channel=file_name)

                # dataset = pd.concat([dataset, original_dataset, corrected_dataset],
                #                     axis=0,
                #                     ignore_index=False,
                #                     sort=False)

                if index == 0:

                    dataset = pd.concat([dataset, original_dataset, corrected_dataset],
                                        axis=0,
                                        ignore_index=False,
                                        sort=False)

                    length = len(original_dataset[value_label])
                    print("Average percentage error:")
                    print((sum(original_dataset[value_label]-corrected_dataset[value_label])/length) / (sum(original_dataset[value_label])/length))
                else:
                    dataset = pd.concat([dataset, original_dataset],
                                        axis=0,
                                        ignore_index=False,
                                        sort=False)

                index += 1

    sns.relplot(x=time_label, y=value_label, hue="source",  col="data_channel", data=dataset)
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
