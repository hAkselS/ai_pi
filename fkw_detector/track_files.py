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
from collections import defaultdict
from pathlib import Path

# Add project root to sys.path so audio_transform can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# ==============================================================================
# --- Configuration Defaults ---
WISPR_MEMORY_PATH = project_root + '/2024_descent'   # TODO: Get this path from another script
LOGS_DIR = "./analyst_logs"       # Directory where daily CSVs will be saved
SAMPLING_RATE = 3                 # Pick 1 in every N files (e.g., 3)

# ==============================================================================




