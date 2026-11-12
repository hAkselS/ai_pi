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

        Note: This script looks at the most recent date directory
        and compares it to the most recent date directory stored in
        analyst_logs/observed_dates.csv. This means that if new
        dates appear that are BEFORE the most latest date, this
        script will ignore them and assume all dates are processed. 
       

I/O:    This program looks at the data stored on the WISPR
        and outputs a list of files per calendar (UTC) date).
        The transform and inference script uses these file outputs to 
        determine what to do next! 

ID:     tf 

Usage:  python3 fkw_detector/track_files.py
'''

import os
import sys
import csv
import yaml
import numpy as np
# from collections import defaultdict
# from pathlib import Path

# Add project root to sys.path so audio_transform can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# ==============================================================================
# --- Configuration Defaults ---
# local_audio_path = project_root + '/2024_descent'   # TODO: Get this path from another script
LOGS_DIR = project_root +"/analyst_logs"       # Directory where daily CSVs will be saved
SAMPLING_RATE = 3                 # Pick 1 in every N files (e.g., 3)
DATE_TRACK_CSV= LOGS_DIR + "/observed_dates.csv" # This is one file created and maintained by this script
CONFIG_PATH = "config/config.yaml"

# --- CSV Configurations ---
date_tracker_header = ['directory', 'indexed', 'completed']
file_tracker_header = ['file_name_and_path', 'select_for_sampling', 'attemped_sampling', 'sample_success']

# --- YAML Configuration Defaults ---
try:
    with open(CONFIG_PATH, "r") as config_file:
        config = yaml.safe_load(config_file) or {}
except (FileNotFoundError, PermissionError):
    print("ERROR: sch: YAML failed to open for initial configs")
    config = {}  # File couldn't be opened, fall back to empty dict

# # .get() keeps the system running even if theres trouble in yaml town
LOCAL_AUDIO_PATH = config.get("SSD_DIR", '2024_descent') # TODO: make this pi relevant
SAMPLE_EVERY_X_FILES = config.get("SAMPLE_EVERY_X_FILES", 4) # Sample every Xth file
NUMBER_OF_SAMPLES = config.get("FKW_SAMPLES", 30) # Sample X total files
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

# ==============================================================================

def find_all_date_folders(local_audio_path=LOCAL_AUDIO_PATH):
    '''
    This function uses os.listdir to create a sorted current !!!ARRAY!!! of directories.
    This function compares the directories in the current ARRAY to the potentially obsolete 
    !!!CSV!!! of existing date folders. Any new date folders that are more recent, and therefor
    greater in value, are added to the CSV of existing date folders.

    '''
    if os.path.exists(local_audio_path):
        
        # --- Create a sorted array of int(directories) ---
        valid_dirs = [
            item
            for item in os.listdir(local_audio_path)
            if item.isdigit()
            and len(item) ==6
            and os.path.isdir(os.path.join(local_audio_path,item))
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
        print(f"tf: ERROR: wispr memory path ({local_audio_path}) does not exist!")
        return False

def find_all_files(local_audio_path=LOCAL_AUDIO_PATH):
    '''
    Iterate through the directories and store all file names with required fields set to false. 
    Apply selected for sampling to appropriate files.
    '''

    # --- Create an collection of files via observed dates list --- 
    with open(DATE_TRACK_CSV, mode='r', encoding='utf-8', newline='') as observed_dates_csv:
        reader = csv.DictReader(observed_dates_csv)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not rows:
        print(f"tf: WARNING: no rows in {DATE_TRACK_CSV}")
        return 

    # Note the most recent directory, remember that the directories are ~already sorted~
    most_recent_directory = rows[-1]["directory"]

    sampling_index_i = 1 
    for row in rows:
        # Skip if already indexed
        if row["indexed"] != "False":
            continue 

        # --- Index the date the directory into a new CSV file ---
        curr_date_directory = row["directory"]
        print(f"tf: Indexing new directory into {curr_date_directory}.csv") # Known conflict, prints even when no new directories are found b/c always re-index most recent directory
        curr_date_directory_path = os.path.join(local_audio_path, curr_date_directory)
        audio_files_per_day_csv_path = os.path.join(LOGS_DIR, curr_date_directory) + '.csv'

        audio_files = [
            item
            for item in os.listdir(curr_date_directory_path)
            if item.startswith("WISPR")
            and item.endswith(".dat")
            and len(item) == 23
            and os.path.isfile(os.path.join(curr_date_directory_path, item))
        ]

        # Writer the per day CSV
        # Note: Overwrites each time the file is opened here
        with open(audio_files_per_day_csv_path, mode='w', encoding='utf-8', newline='') as date_dot_csv:
            writer = csv.writer(date_dot_csv)

            # --- Write the header and the rows & select files for sampling ---
            writer.writerow(file_tracker_header)
            for file_name in audio_files:
                # Select a file for sampling if modulo is zero
                if (sampling_index_i % SAMPLE_EVERY_X_FILES) == 0:
                    writer.writerow([file_name, True, False, False])
                else:
                    writer.writerow([file_name, False, False, False])
                sampling_index_i = sampling_index_i + 1 

        # Mark "indexed" in program memory
        if curr_date_directory != most_recent_directory:
            row["indexed"] = "True"

    # Note a job well done       
    print(f"tf: Populated date.csv(s) and selected files for sampling")

    # --- Mark "indexed" = "True" in observed_dates.csv
    with open(DATE_TRACK_CSV, mode='w', encoding='utf-8', newline='') as observed_dates_csv:
        writer = csv.DictWriter(observed_dates_csv, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

      
# TODO: create make menu 
# Make menu should look at the most recent completed=False file and
# Add all the files selected for sampling (along with their fully qualified paths)
# to the menu
# The menu function should look for a max number of files to add to the menu.
# The menu function should start at the most recent file and work backwards through days
# until it has added enough files to the menu
def create_menu(LOGS_DIR=LOGS_DIR, NUMBER_OF_SAMPLES=NUMBER_OF_SAMPLES):
    '''
    Creat a file menu for the transform and inference script to ingest. 
    '''
    with open(DATE_TRACK_CSV, mode='r', encoding='utf-8', newline='') as observed_dates_csv:
        reader = csv.DictReader(observed_dates_csv)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not rows:
        print(f"tf: WARNING: no rows in {DATE_TRACK_CSV}")
        return 

    ### TODO: Add number of samples worth of files into a date_time_menu.csv
    # Make sure that the files include fully qualified paths, check the paths before putting in. 
    # No need to mark anything here
    # Name the menu "dive_start_time_menu"
    # Ensure to include the date range into the menu somewhere
    

    

def main():
    create_or_check_dateCSV()
    find_all_date_folders()
    find_all_files()

if __name__ == "__main__":
    main()