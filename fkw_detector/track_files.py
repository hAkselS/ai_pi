'''
File:   track_files.py

Spec:   This script manages a list of all files seen by ai_pi repository.
        This script should run after copy_to_pi has completed.
        This script starts by creating or updating a CSV of all the WISPR
        date directories (sorted). 

        Files on the WISPR are organized as follows:
        /260929/
            /WISPR_260929_123456.dat
            /WISPR_260929_223456.dat
        /260930/
            /WISPR_260930_123456.dat
            /WISPR_260930_223456.dat

        Observed_dates.csv looks like this:
        directory,indexed,completed
        240930,False,False
        241001,False,False
        
        Where directory is the name of the directory, indexed indicates if all 
        the file names in the directory have been added to another file, and 
        completed indicates if the analyzes has finished said batch of files
        
        With a complete list of directories, this script checks this 'indexed'
        column in the observed_dates.csv. If False, the script adds all
        file names in said directory to a csv called **date**_files.csv.
        **date**_files.csv contains:
            - File name and local path
            - Selected for sampling 
            - Sampled
            - Sample status

        Which is used by transform_and_inference to understand what files need
        to be analyzed next.
       

I/O:    This program looks at the data stored on the WISPR
        and outputs a list of files per calendar (UTC) date).
        The transform and inference script uses these file outputs to 
        determine what to do next! 

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
DATE_TRACK_CSV= LOGS_DIR + "/observed_dates.csv" # This is one file created and maintained by this script

# --- CSV Configurations ---
date_tracker_header = ['directory', 'indexed', 'completed']
# ==============================================================================


# --- Helper Functions ---
def has_only_header(file_path):
    ''' Returns true if and only if there is exactly one non-empty line'''
    with open(file_path, mode="r", newline="", encoding="utf-8") as file:
        non_empty_rows = (row for row in csv.reader(file) if row)

        header = next(non_empty_rows, None)

        # Return false if the file is totally empty
        if header is None:
            return False

        first_data_row = next(non_empty_rows, None)
        if first_data_row == None:
            return True

        else: 
            return False


def read_updated_memory_path():
    '''Get the most updated wispr memory path 
    from a yaml file or other script'''
    pass

# ==============================================================================

def create_or_check_dateCSV(LOGS_DIR=LOGS_DIR):
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
    '''
    This function uses os.listdir to create a sorted current !!!ARRAY!!! of directories.
    This function compares the directories in the current ARRAY to the potentially obsolete 
    !!!CSV!!! of existing date folders. Any new date folders that are more recent, and therefor
    greater in value, are added to the CSV of existing date folders.

    '''
    if os.path.exists(wispr_memory_path):
        
        # --- Create a sorted array of int(directories) ---
        valid_dirs = [
            item
            for item in os.listdir(wispr_memory_path)
            if item.isdigit()
            and len(item) ==6
            and os.path.isdir(os.path.join(wispr_memory_path,item))
        ]

        # Sort and convert to integers
        array_of_directories = np.sort(valid_dirs)
        array_of_directories = array_of_directories.astype(int)

        # DEBUG
        #print ("Directories List:")
        #print(array_of_directories)
        #print(array_of_directories[1])

        # --- If the CSV is empty, populated it! ---
        if has_only_header(DATE_TRACK_CSV):
            # DEBUG
            print(f'tf: ((Empty CSV with only header,')
            print(f'tf:   populating [{len(array_of_directories)}] items from:')
            print(f'tf:   [{DATE_TRACK_CSV}] \ntf:   into observed_dates.csv))')
            with open(DATE_TRACK_CSV, mode="a", encoding="utf-8") as date_csv_file:
                writer = csv.writer(date_csv_file)
                for d in array_of_directories:
                    writer.writerow([d,False,False])
            # Exit the function with great success 
            return True               


        # --- If new directories, determine which ones are new! --- 
        date_csv = os.path.exists(DATE_TRACK_CSV)
        if date_csv:
            # Get the latest & therefor largest value from the CSV file
            with open(DATE_TRACK_CSV, mode='r+', encoding='utf-8') as date_csv_file:
               
               reader = csv.reader(date_csv_file)
               last_row = None
               for row in reader:
                    if row:
                        last_row = row  
            
            latest_csv_stored_directory = int(last_row[0])

            # Get the latest & therefor largest value from the array of new and old directories
            latest_array_stored_directory = array_of_directories[-1]

            # --- Add new directories to CSV ---

            # Case 1: new directories have been added
            if latest_array_stored_directory > latest_csv_stored_directory:
                print(f'tf: latest_array_stored_directory = [{latest_array_stored_directory}]')
                print(f'tf: latest_csv_stored_directory = [{latest_csv_stored_directory}]')
                with open(DATE_TRACK_CSV, mode='a', encoding='utf-8') as date_csv_file:
                    writer = csv.writer(date_csv_file)
                    for d in array_of_directories:
                        if d > latest_csv_stored_directory:
                            writer.writerow([d,False,False])
                return True

            # Case 2: no new files found
            elif latest_array_stored_directory == latest_csv_stored_directory:
                print('tf: No new files found')
                return True

            # Case 3: files have been deleted
            elif latest_array_stored_directory < latest_csv_stored_directory:
                print('tf: WARNING: latest array stored directory smaller than lastest CSV stored directory, was something deleted?')
                return False # Check this return value 

    else:
        print(f"tf: ERROR: wispr memory path ({wispr_memory_path}) does not exist!")
        return False


def main():
    create_or_check_dateCSV()
    find_all_date_folders()

if __name__ == "__main__":
    main()