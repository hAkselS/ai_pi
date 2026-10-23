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

I/O:    This program looks at the data stored on the WISPR
        and outputs a list of files.

ID:     tf 

Usage:  python3 fkw_detector/track_files.py
'''

import os
import sys
import re
import csv
from collections import defaultdict
from pathlib import Path

# Add project root to sys.path so audio_transform can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# ==============================================================================
# --- Configuration Defaults ---
local_memory_path = project_root + '2024_descent'   # TODO: Get this path from another script
# ==============================================================================



# --- Configuration ---
LOGS_DIR = "./analyst_logs"       # Directory where daily CSVs will be saved
SAMPLING_RATE = 3                 # Pick 1 in every N files (e.g., 3)

# Regex pattern to extract YYMMDD date from filenames like WISPR_240930_000003.dat
FILENAME_PATTERN = re.compile(r"WISPR_(\d{2})(\d{2})(\d{2})_.*\.dat$", re.IGNORECASE)


def parse_date_from_filename(filename):
    """
    Extracts the YYMMDD string and converts it to YYYY-MM-DD.
    Example: WISPR_240930_000003.dat -> 2024-09-30
    """
    match = FILENAME_PATTERN.search(filename)
    if match:
        year, month, day = match.groups()
        return f"20{year}-{month}-{day}"
    return None


def generate_daily_inventory(local_memory_path, logs_dir, sample_rate):
    """
    Scans the source directory, groups files by date extracted from their names,
    applies sampling, and writes daily CSV log files.
    """
    os.makedirs(logs_dir, exist_ok=True)

    print(f"Scanning directory: {local_memory_path}...")
    
    # 1. Gather all matching files using os.scandir for high performance
    file_records = []
    with os.scandir(local_memory_path) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.endswith(".dat"):
                date_str = parse_date_from_filename(entry.name)
                if date_str:
                    file_records.append((entry.name, date_str))

    # 2. Sort files alphabetically so sampling and entries are strictly ordered
    file_records.sort(key=lambda x: x[0])
    print(f"Found {len(file_records):,} matching .dat files.")

    # 3. Group files by date while applying the sampling rule
    daily_files = defaultdict(list)
    
    for index, (filename, date_str) in enumerate(file_records, start=1):
        # Sample every Nth file
        is_selected = (index % sample_rate == 0)
        
        daily_files[date_str].append({
            "filename": filename,
            "selected": is_selected,
            "analyzed": False,
            "success": False
        })

    # 4. Write out to individual daily CSV files
    fieldnames = ["filename", "selected", "analyzed", "success"]

    for date_str, records in daily_files.items():
        csv_path = Path(logs_dir) / f"{date_str}.csv"
        
        # Check if the file already exists to avoid overwriting headers if running incrementally
        file_exists = csv_path.exists()
        
        with open(csv_path, mode="a", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
                
            writer.writerows(records)

    print(f"Successfully generated/updated daily CSV logs in '{logs_dir}' across {len(daily_files)} day(s).")


if __name__ == "__main__":
    generate_daily_inventory(
        local_memory_path=local_memory_path,
        logs_dir=LOGS_DIR,
        sample_rate=SAMPLING_RATE
    )