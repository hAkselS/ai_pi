'''
File:   serial_command_handler.py

Spec:   This script listens for serial commands from the Seaglider and 
        dispatches functions and scripts accordingly. There are two
        primary commands: 'start' and 'download'. When start is received,
        this script will launch main.py. This script also has a method to 
        stop main.py if download is received while main.py is still running.
        When download is received, this script will call prep_download() which
        summarizes and packetizes the results from the most recent dive and 
        sends them to the Seaglider through serial (or ymodem TBD).

I/O:    This program listens on a serial port (default: /dev/ttyXXX) for commands from the Seaglider.
        This program outputs the results of the most recent dive to the Seaglider through serial (or ymodem TBD).
        Allowed commands are:
            1. start 
                - Receives: 'start,a,2026-08-19T20:59:20Z'
                            '\r'
                - (Yes, a new line then a \r (return))
                - Launches main.py and analyzes directive stored in param. 
                - Params must be a number between 0 and 15,999,999 (TODO: needs testing)
            2. download 
                - Prepares data for download and sends a packet to Seaglider. 

ID:     sch

Usage:  <python3 pi_logger/serial_command_handler.py>
'''

import subprocess
import time
import sys
import os
import serial
from datetime import datetime, timezone
import yaml
import glob

# ==============================================================================
# --- Configuration Defaults ---
CONFIG_PATH = 'config/config.yaml'
MAIN_SCRIPT_PATH = 'pi_logger/main.py'  # Path to main.py relative to this script
FKW_RESULTS_PATH = os.path.expanduser('~/FKW_detector/data_products/packets')
# ------------------------------------------------------------------------------

# --- YAML Configuration Defaults ---
try:
    with open(CONFIG_PATH, "r") as config_file:
        config = yaml.safe_load(config_file) or {}
except (FileNotFoundError, PermissionError):
    print("ERROR: sch: YAML failed to open for initial configs")
    config = {}  # File couldn't be opened, fall back to empty dict

# .get() keeps the system running even if theres trouble in yaml town
SERIAL_PORT = config.get("SERIAL_PORT", '/dev/ttys001')
BAUD_RATE = config.get("BAUD_RATE", 9600)
TERMINATOR = config.get("TERMINATOR", "\r")
DELIMITER = config.get("DELIMITER", ",")
PROMPT = config.get("PROMPT", "P>")

# ==============================================================================


# ==============================================================================
# GLOBAL STATE FLAGS & STATUS VARIABLES

# ==============================================================================


# ==============================================================================
# --- Handler Functions ---
# ==============================================================================
def set_pi_datetime(date_string):
    # Parse ISO format (replace 'Z' with explicit UTC offset for older Python versions)
    dt = datetime.fromisoformat(date_string.replace("Z", "+00:00"))

    # Format as 'YYYY-MM-DD HH:MM:SS' in UTC
    formatted_time = dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Save date into config.yaml (for now) 
    # TODO: think of a better place to store this
    with open(CONFIG_PATH, "r") as config_file:
        config = yaml.safe_load(config_file) or {}
    
        config["DATE_TIME"] = formatted_time
    
        with open(CONFIG_PATH, "w") as config_file:
            yaml.safe_dump(config, config_file, sort_keys=False)

    # Use a subprocess to set the datetime
    if os.getenv("BENCHTEST") != "1":
        # Run this if BENCHTEST is NOT set
        subprocess.run(["sudo", "date", "-u", "-s", formatted_time], check=True)
    else:
            print("WARNING: sch: RPi time set skipped due to BENCHTEST mode.")

    
    new_time = datetime.now(timezone.utc)
    print(f"\nsch: set_pi_datetime has been called with string -> [{date_string}]\n" \
    f"     new datetime -> [{new_time}]")


def set_dive_climb(dive_letter):
    print(f"sch: set_dive_climb has been called with letter -> [{dive_letter}]")
    # Check for valid dive letter
    if dive_letter not in ("a","b",):
        print("ERROR: sch: Dive letter must be 'a' or 'b'")
        return 

    # Open config then write dive letter
    with open(CONFIG_PATH, "r") as config_file:
        config = yaml.safe_load(config_file) or {}

    config["DIVE_CLIMB"] = dive_letter

    with open(CONFIG_PATH, "w") as config_file:
        yaml.safe_dump(config, config_file, sort_keys=False)

    print(f"sch: set_dive_climb: updated DIVE_CLIMB to [{dive_letter}]")


# TODO: create start mission function! 
def start_mission():
    print("sch: start mission has been called!")
    pass

# TODO: Make the send FKW_results function in another file
#        Also handle tracking what files have been sent here
#        This function should be called with no args! 
#        Old function is saved for reference!

def send_fkw_results(): 
    print("sch: send fkw results has been called!")
   

# ==============================================================================
# --- Process Control Helpers ---
# ==============================================================================

def shutdown_pi():
    '''shutdown the raspberry pi once all tasks are finished.'''
    print("sch: Warning: shutdown pi has been called (but is an empty funciton)")



# ==============================================================================
# --- Main Serial Listener Loop ---
# ==============================================================================
def run_serial_handler():

    print(f"sch: Starting serial listener on {SERIAL_PORT} @ {BAUD_RATE} baud...\n")

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    except Exception as e:
        print(f"[Error] Failed to open serial port {SERIAL_PORT}: {e}")
        sys.exit(1)

    buffer = ""

    while True:

        # 1. Read available incoming bytes and append to the buffer
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            buffer += data

        # 2. Check if a complete line/command has arrived (looking for \n or \r)
        if '\n' in buffer or '\r' in buffer:
            # Split the buffer into complete lines and remaining incomplete chunk
            # Handles both \r\n, \n, or \r delimiters cleanly
            lines = buffer.replace('\r', '\n').split('\n')
            
            # The last element is whatever incomplete fragment remains after the final delimiter
            buffer = lines.pop()

            # Process every fully received line
            for line in lines:
                cmd = line.strip()
                if not cmd:
                    continue  # Ignore empty lines

                print(f"sch: Processing complete command -> [{cmd}]")

                # ===========================================
                # -- Handle START ('start') scenario --
                # ===========================================
                if cmd.startswith('start'): 

                    parsed_start_cmd = [item.strip() for item in cmd.split(",")]
                    print(f"sch: start case: parsed_start_cmd -> {parsed_start_cmd}")

                    if (len(parsed_start_cmd) != 3
                        or not parsed_start_cmd[1].isalpha() 
                        or len(parsed_start_cmd[1]) != 1 
                        or not parsed_start_cmd[2].replace('Z', '').replace('-', '').replace(':', '').replace('T', '').isalnum()): 
                        
                        print("ERROR: sch: invalid start command format... Ignoring.\n")
                        continue

                    pi_start, pi_dive, pi_date = parsed_start_cmd

                    set_pi_datetime(pi_date)
                    set_dive_climb(pi_dive)

                    start_mission() 
                    shutdown_pi() # Once finished, the pi should shutdown

                # ===========================================
                # -- Handle DOWNLOAD ('download') scenario --
                # ===========================================
                elif 'download' in cmd:
                    print(f"sch: download case received -> [{cmd}]")
                    send_fkw_results() # Send the fkw results over serial

        # Small sleep to prevent aggressive CPU spinning when idle
        time.sleep(0.05)


if __name__ == '__main__':
    run_serial_handler()
