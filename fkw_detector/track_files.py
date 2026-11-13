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
import yaml
import pandas as pd
import sqlite3 as sql

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
DATABASE_NAME = "file_track.db"


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

# Sqlite hello world 




# ==============================================================================


      
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
    pass 


if __name__ == "__main__":
    main()

### --- claude generated code --- 
# Not yet tested 

#     import os
# import re
# import sqlite3
# from datetime import datetime, timezone

# # --- Config ---
# AUDIO_ROOT = "/path/to/2024_descent"       # root containing 241001/, 241002/, ...
# DB_PATH = "/path/to/file_tracker.db"
# SAMPLE_EVERY_N = 10                        # every Nth newly indexed file is selected

# FILE_RE = re.compile(r"^WISPR_(\d{6})_(\d{6})\.dat$")
# FOLDER_RE = re.compile(r"^\d{6}$")


# def init_db(conn):
#     conn.execute("PRAGMA journal_mode=WAL")
#     conn.execute("PRAGMA synchronous=FULL")
#     conn.executescript("""
#         CREATE TABLE IF NOT EXISTS files (
#             file_name_and_path  TEXT PRIMARY KEY,   -- relative to AUDIO_ROOT, e.g. 241001/WISPR_241001_000047.dat
#             file_datetime_utc   TEXT NOT NULL,      -- YYYY-MM-DD HH:MM:SS, parsed from the file name
#             indexed_at_utc      TEXT NOT NULL,      -- when this script added the row
#             select_for_sampling INTEGER NOT NULL DEFAULT 0,
#             attempted_sampling  INTEGER NOT NULL DEFAULT 0,
#             sample_success      INTEGER NOT NULL DEFAULT 0
#         );
#         CREATE INDEX IF NOT EXISTS idx_pending
#             ON files (select_for_sampling, attempted_sampling, file_name_and_path);

#         CREATE TABLE IF NOT EXISTS meta (
#             key   TEXT PRIMARY KEY,
#             value INTEGER NOT NULL
#         );
#         INSERT OR IGNORE INTO meta (key, value) VALUES ('sample_counter', 0);
#     """)
#     conn.commit()


# def find_all_files(audio_root=AUDIO_ROOT, db_path=DB_PATH, sample_every_n=SAMPLE_EVERY_N):
#     """Scan every date folder, insert files not yet in the DB, flag every Nth for sampling."""
#     conn = sqlite3.connect(db_path)
#     try:
#         init_db(conn)

#         existing = {row[0] for row in conn.execute("SELECT file_name_and_path FROM files")}
#         max_existing = max(existing) if existing else None

#         new_files = []       # (rel_path, file_datetime_utc)
#         out_of_order = []    # rel_paths that sort before already-indexed files
#         skipped = 0

#         date_dirs = sorted(
#             d for d in os.listdir(audio_root)
#             if FOLDER_RE.match(d) and os.path.isdir(os.path.join(audio_root, d))
#         )
#         for date_dir in date_dirs:
#             date_dir_path = os.path.join(audio_root, date_dir)
#             for file_name in list_audio_files(date_dir_path):
#                 rel_path = f"{date_dir}/{file_name}"
#                 if rel_path in existing:
#                     continue

#                 m = FILE_RE.match(file_name)
#                 if not m or m.group(1) != date_dir:
#                     skipped += 1
#                     continue
#                 try:
#                     # Validates the date AND the time (e.g. rejects hour 25)
#                     dt = datetime.strptime(m.group(1) + m.group(2), "%y%m%d%H%M%S")
#                 except ValueError:
#                     skipped += 1
#                     continue

#                 if max_existing is not None and rel_path < max_existing:
#                     out_of_order.append(rel_path)

#                 new_files.append((rel_path, dt.strftime("%Y-%m-%d %H:%M:%S")))

#         # --- Summary warnings (one line each) ---
#         if out_of_order:
#             print(f"WARNING: {len(out_of_order)} new file(s) sort before already-indexed files "
#                   f"(out-of-order arrival, e.g. {min(out_of_order)}); "
#                   f"sampling selection may be uneven.")
#         if skipped:
#             print(f"WARNING: skipped {skipped} file(s) with malformed names, invalid timestamps, "
#                   f"or a date that doesn't match their folder.")

#         if not new_files:
#             print("No new files to index.")
#             return

#         now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
#         with conn:
#             counter = conn.execute("SELECT value FROM meta WHERE key='sample_counter'").fetchone()[0]

#             rows = []
#             for rel_path, file_dt in new_files:
#                 counter += 1
#                 selected = 1 if counter % sample_every_n == 0 else 0
#                 rows.append((rel_path, file_dt, now_utc, selected))

#             conn.executemany(
#                 """INSERT OR IGNORE INTO files
#                    (file_name_and_path, file_datetime_utc, indexed_at_utc, select_for_sampling)
#                    VALUES (?, ?, ?, ?)""",
#                 rows,
#             )
#             conn.execute("UPDATE meta SET value=? WHERE key='sample_counter'", (counter,))

#         n_selected = sum(r[3] for r in rows)
#         print(f"Indexed {len(rows)} new files ({n_selected} selected for sampling).")
#     finally:
#         conn.close()

########### --- Analyzer side --- 
# def get_next_file(conn):
#     row = conn.execute("""
#         SELECT file_name_and_path FROM files
#         WHERE select_for_sampling = 1 AND attempted_sampling = 0
#         ORDER BY file_name_and_path DESC
#         LIMIT 1
#     """).fetchone()
#     return row[0] if row else None

# def mark_result(conn, rel_path, success):
#     with conn:
#         conn.execute(
#             "UPDATE files SET attempted_sampling = 1, sample_success = ? WHERE file_name_and_path = ?",
#             (1 if success else 0, rel_path),
#         )

######## --- Description --- 
Decisions and assumptions

# No indexed flag. Every run re-lists all folders and inserts only files missing from the DB, so a partially filled newest folder just picks up its extra files next boot.
# Path sorting equals chronological sorting. YYMMDD/WISPR_YYMMDD_NNNNNN.dat sorts correctly as plain text (as long as it stays within the same century), so ORDER BY ... DESC gives newest first.
# Counter persists in the meta table, which cost only a few lines. Old selections never change, and a new SAMPLE_EVERY_N only applies to newly indexed files.
# Out-of-order arrivals (#2) get a warning only, since that was the cheap option. The files are still indexed, just continuing the count.
# “Date and UTC time” is stored as file_date (from the filename) and indexed_at_utc (when the script added the row). The 000047 part looks like a sequence number rather than a time, so I stored it as file_number. If it actually encodes a time of day, tell me how and I’ll parse it.
# Column name fix: I spelled it attempted_sampling rather than attemped_sampling. Change it if you want the original spelling, but it needs to match in the analyzer.
# Power-loss settings: WAL mode with synchronous=FULL, and each scan is one transaction, so a power cut leaves either the whole batch or none of it. Re-running just re-adds whatever was missing.
# Mismatched files are skipped. Files whose name doesn’t match the regex, or whose date doesn’t match their folder, are skipped with a warning rather than indexed.

# If you ever need to pause or inspect the DB from the shell, sqlite3 file_tracker.db "SELECT COUNT(*), SUM(select_for_sampling), SUM(attempted_sampling) FROM files;" gives a quick status summary.