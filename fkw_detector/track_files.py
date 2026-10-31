'''
File:   track_files.py

Spec:   This script manages a list of all files seen by ai_pi repository.
        Once copy to pi is finished, this script looks through the WISPRs
        memory and appends all the new files a csv file.
        There is a CSV file for every day (UTC) of operation.
        Each entry has:
            - File name and local path
            - Selected for sampling 
            - Sampled
            - Sample status

        This script also manages a CSV containing all the dates (sorted)
        that have already been analyzed, thus eliminating the need
        to look through all files each time this script runs. 

        Note: Files on the WISPR are organized as follows
        /260929/
            /WISPR_260929_123456.dat
            /WISPR_260929_223456.dat
        /260930/
            /WISPR_260930_123456.dat
            /WISPR_260930_223456.dat

I/O:    This program looks at the data stored on the WISPR
        and outputs a list of files per calendar (UTC) date).

ID:     tf 

Usage:  python3 fkw_detector/track_files.py
'''

import os
import sys
import re
import csv
import numpy as np
from collections import defaultdict
from pathlib import Path

# Add project root to sys.path so audio_transform can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# ==============================================================================
# --- Configuration Defaults ---
wispr_memory_path = project_root + '/2024_descent'   # TODO: Get this path from another script
LOGS_DIR = project_root +"/analyst_logs"       # Directory where daily CSVs will be saved
SAMPLING_RATE = 3                 # Pick 1 in every N files (e.g., 3)
DATE_TRACK_CSV= LOGS_DIR + "/observed_dates.csv"
# ==============================================================================

# ==============================================================================
# --- CSV Configurations ---
date_tracker_header = ['directory', 'completed']

# ==============================================================================

def read_updated_memory_path():
    '''Get the most updated wispr memory path 
    from a yaml file or other script'''
    pass

def create_or_check_date_CSV(LOGS_DIR=LOGS_DIR):
    # Check if the directory exists
    if not os.path.isdir(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    
    # Check if the CSV file exists
    if not os.path.isfile(DATE_TRACK_CSV):
        # Create the file and add the header
        with open(DATE_TRACK_CSV, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(date_tracker_header)       


def find_all_date_folders(wispr_memory_path=wispr_memory_path, LOGS_DIR=LOGS_DIR):
    if os.path.exists(wispr_memory_path):
        
        # directories_list = np.array(os.listdir(wispr_memory_path))
        valid_dirs = [
            item
            for item in os.listdir(wispr_memory_path)
            if item.isdigit()
            and len(item) ==6
            and os.path.isdir(os.path.join(wispr_memory_path,item))
        ]

        array_of_directories = np.sort(valid_dirs)
        print ("Directories List:")
        print(array_of_directories)
        print(array_of_directories[1])


        # Add directoies into the master list in order
        date_csv = os.path.exists(DATE_TRACK_CSV)


        # Add all values that are greater than the current last entry
        if date_csv:
            with open(DATE_TRACK_CSV, mode='r+', encoding='utf-8') as date_csv_file:
                num_rows = sum(1 for row in date_csv_file)
                writer = csv.writer(date_csv_file)
                index = 1
                for d in array_of_directories:
                    if index >= num_rows:
                        writer.writerow([d, False])
                    index = index + 1 


    else:
        print(f"tf: ERROR: wispr memory path ({wispr_memory_path}) does not exist!")


def main():
    create_or_check_date_CSV()
    find_all_date_folders()

if __name__ == "__main__":
    main()