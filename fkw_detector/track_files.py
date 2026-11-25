'''
File:   track_files.py

Spec:   This script manages a SQLite database of all files seen by ai_pi repository.
        This script should run after copy_to_pi.py has completed execution.
        The database created by this script is...

        Files on the WISPR are organized as follows:
        /260929/
            /WISPR_260929_123456.dat
            /WISPR_260929_223456.dat
        /260930/
            /WISPR_260930_123456.dat
            /WISPR_260930_223456.dat

   
        With a complete database of all the stored files, this script creates a 
        CSV 'menu' which serves as a do-this-now mission directive
        which is used by transform_and_inference to understand what files need
        to be analyzed next.

        # TODO: check for truth
        # Note: This script looks at the most recent date directory
        # and compares it to the most recent date directory stored in
        # analyst_logs/observed_dates.csv. This means that if new
        # dates appear that are BEFORE the most latest date, this
        # script will ignore them and assume all dates are processed. 
       

I/O:    This program looks at the from the WISPR data stored on the Raspberry Pi's
        massive m.2 memory chip and creates a mission directive (menu) for 
        transform and inference. 

ID:     tf 

Usage:  python3 fkw_detector/track_files.py
'''

import os
import sys
import yaml
import pandas as pd
import sqlite3
import re
from datetime import datetime, timezone

# Add project root to sys.path so audio_transform can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# ==============================================================================
# --- Configuration Defaults ---
LOGS_DIR = project_root + "/analyst_logs"           # Directory where daily CSVs will be saved
SAMPLING_RATE = 3                                   # Pick 1 in every N files (e.g., 3)
CONFIG_PATH = "config/config.yaml"
DATABASE_PATH = project_root + "/file_track.db"

# --- Regex Patterns for Database ---
FILE_RE = re.compile(r"^WISPR_(\d{6})_(\d{6})\.dat$")
FOLDER_RE = re.compile(r"^\d{6}$")

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

# ============= Helper Functions ==============
def list_date_dirs(audio_root):
    """Return sorted names of subdirectories that look like YYMMDD."""
    return sorted(
        d for d in os.listdir(audio_root)
        if FOLDER_RE.match(d) and os.path.isdir(os.path.join(audio_root, d))
    )


def list_audio_files(date_dir_path, date_dir=None):
    """Return sorted names of valid WISPR_YYMMDD_HHMMSS.dat files in a date folder.

    If date_dir is given, the date embedded in the filename must match it
    (so WISPR_260930_*.dat inside /260929/ is rejected).
    """
    files = []
    for name in os.listdir(date_dir_path):
        if not FILE_RE.match(name):
            continue
        if not os.path.isfile(os.path.join(date_dir_path, name)):
            continue
        if date_dir is not None and name.split("_")[1] != date_dir:
            continue
        files.append(name)
    return sorted(files)

# ============================ Database Functions ==============================

def init_db(conn):
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS files (
            file_name_and_path  TEXT PRIMARY KEY,   -- relative to AUDIO_ROOT, e.g. 241001/WISPR_241001_000047.dat
            file_datetime_utc   TEXT NOT NULL,      -- YYYY-MM-DD HH:MM:SS, parsed from the file name
            indexed_at_utc      TEXT NOT NULL,      -- when this script added the row
            select_for_sampling INTEGER NOT NULL DEFAULT 0,
            attempted_sampling  INTEGER NOT NULL DEFAULT 0,
            sample_success      INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_pending
        ON files (select_for_sampling, attempted_sampling, file_name_and_path);

        CREATE TABLE IF NOT EXISTS meta (
            key   TEXT PRIMARY KEY,
            value INTEGER NOT NULL
        );
        INSERT OR IGNORE INTO meta (key, value) VALUES ('sample_counter', 0);
    """)
    conn.commit()

def find_all_files(audio_root=LOCAL_AUDIO_PATH, db_path=DATABASE_PATH, sample_every_n=SAMPLE_EVERY_X_FILES):
    """Scan every date folder, insert files not yet in the DB, flag every Nth for sampling."""
    conn = sqlite3.connect(db_path)
    try:
        init_db(conn)

        existing = {row[0] for row in conn.execute("SELECT file_name_and_path FROM files")}
        max_existing = max(existing) if existing else None

        new_files = []       # (rel_path, file_datetime_utc)
        out_of_order = []    # rel_paths that sort before already-indexed files
        skipped = 0

        date_dirs = sorted(
            d for d in os.listdir(audio_root)
            if FOLDER_RE.match(d) and os.path.isdir(os.path.join(audio_root, d))
        )
        for date_dir in date_dirs:
            date_dir_path = os.path.join(audio_root, date_dir)
            for file_name in list_audio_files(date_dir_path):
                rel_path = f"{date_dir}/{file_name}"
                if rel_path in existing:
                    continue

                m = FILE_RE.match(file_name)
                if not m or m.group(1) != date_dir:
                    skipped += 1
                    continue
                try:
                    # Validates the date AND the time (e.g. rejects hour 25)
                    dt = datetime.strptime(m.group(1) + m.group(2), "%y%m%d%H%M%S")
                except ValueError:
                    skipped += 1
                    continue

                if max_existing is not None and rel_path < max_existing:
                    out_of_order.append(rel_path)

                new_files.append((rel_path, dt.strftime("%Y-%m-%d %H:%M:%S")))

        # --- Summary warnings (one line each) ---
        if out_of_order:
            print(f"WARNING: {len(out_of_order)} new file(s) sort before already-indexed files "
                  f"(out-of-order arrival, e.g. {min(out_of_order)}); "
                  f"sampling selection may be uneven.")
        if skipped:
            print(f"WARNING: skipped {skipped} file(s) with malformed names, invalid timestamps, "
                  f"or a date that doesn't match their folder.")

        if not new_files:
            print("No new files to index.")
            return

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        with conn:
            counter = conn.execute("SELECT value FROM meta WHERE key='sample_counter'").fetchone()[0]

            rows = []
            for rel_path, file_dt in new_files:
                counter += 1
                selected = 1 if counter % sample_every_n == 0 else 0
                rows.append((rel_path, file_dt, now_utc, selected))

            conn.executemany(
                """INSERT OR IGNORE INTO files
                   (file_name_and_path, file_datetime_utc, indexed_at_utc, select_for_sampling)
                   VALUES (?, ?, ?, ?)""",
                rows,
            )
            conn.execute("UPDATE meta SET value=? WHERE key='sample_counter'", (counter,))

        n_selected = sum(r[3] for r in rows)
        print(f"Indexed {len(rows)} new files ({n_selected} selected for sampling).")
    finally:
        conn.close()

   
# ------------------------------ Debugging / Testing ------------------------------
def show_db(db_path=DATABASE_PATH, start=0, end=None, only_selected=False, only_pending=False):
    """DEBUG ONLY: print a summary of the DB and a slice of the files table.

    start / end   Slice-style row indices over the (filtered) rows, sorted by path.
                  end is exclusive. Negative start counts from the end,
                  e.g. start=-20 shows the last 20 rows.
    only_selected Only rows flagged select_for_sampling=1.
    only_pending  Only rows selected for sampling but not yet attempted.

    Call with: 
        python3 -c "from fkw_detector.track_files import show_db; show_db(start=-20)"
    """
    conn = sqlite3.connect(db_path)
    try:
        try:
            total, selected, attempted, succeeded = conn.execute(
                """SELECT COUNT(*),
                          COALESCE(SUM(select_for_sampling), 0),
                          COALESCE(SUM(attempted_sampling), 0),
                          COALESCE(SUM(sample_success), 0)
                   FROM files"""
            ).fetchone()
            counter = conn.execute(
                "SELECT value FROM meta WHERE key='sample_counter'"
            ).fetchone()
        except sqlite3.OperationalError as e:
            print(f"DEBUG: could not read database ({e}). Has init_db run?")
            return

        print(f"=== {db_path} ===")
        print(f"total files: {total} | selected: {selected} | "
              f"attempted: {attempted} | succeeded: {succeeded} | "
              f"sample_counter: {counter[0] if counter else 'n/a'}")

        where = []
        if only_selected:
            where.append("select_for_sampling = 1")
        if only_pending:
            where.append("select_for_sampling = 1 AND attempted_sampling = 0")
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        n_rows = conn.execute(f"SELECT COUNT(*) FROM files {where_sql}").fetchone()[0]

        # Resolve slice bounds (negative start counts from the end)
        if start < 0:
            start = max(n_rows + start, 0)
        stop = n_rows if end is None else min(end, n_rows)
        limit = max(stop - start, 0)

        if limit == 0:
            print(f"(no rows in range; {n_rows} row(s) match the filter)")
            return

        df = pd.read_sql_query(
            f"""SELECT file_name_and_path, file_datetime_utc, indexed_at_utc,
                       select_for_sampling, attempted_sampling, sample_success
                FROM files {where_sql}
                ORDER BY file_name_and_path
                LIMIT ? OFFSET ?""",
            conn,
            params=(limit, start),
        )
        df.index = range(start, start + len(df))  # show real row numbers

        print(f"showing rows {start}..{start + len(df) - 1} of {n_rows}")
        with pd.option_context("display.max_rows", None,
                               "display.max_columns", None,
                               "display.width", 200):
            print(df.to_string())
    finally:
        conn.close()


def main():
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        init_db(conn)
    finally:
        conn.close()
    find_all_files(audio_root=LOCAL_AUDIO_PATH, db_path=DATABASE_PATH, sample_every_n=SAMPLE_EVERY_X_FILES)


if __name__ == "__main__":
    main()


# # ============== Menu Stuff ++++++++++++++++
      
# # TODO: create make menu 
# # Make menu should look at the most recent completed=False file and
# # Add all the files selected for sampling (along with their fully qualified paths)
# # to the menu
# # The menu function should look for a max number of files to add to the menu.
# # The menu function should start at the most recent file and work backwards through days
# # until it has added enough files to the menu
# def create_menu(LOGS_DIR=LOGS_DIR, NUMBER_OF_SAMPLES=NUMBER_OF_SAMPLES):
#     '''
#     Creat a file menu for the transform and inference script to ingest. 
#     '''
#     with open(DATE_TRACK_CSV, mode='r', encoding='utf-8', newline='') as observed_dates_csv:
#         reader = csv.DictReader(observed_dates_csv)
#         fieldnames = reader.fieldnames
#         rows = list(reader)

#     if not rows:
#         print(f"tf: WARNING: no rows in {DATE_TRACK_CSV}")
#         return 

#     ### TODO: Add number of samples worth of files into a date_time_menu.csv
#     # Make sure that the files include fully qualified paths, check the paths before putting in. 
#     # No need to mark anything here
#     # Name the menu "dive_start_time_menu"
#     # Ensure to include the date range into the menu somewhere