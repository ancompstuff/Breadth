# IMPORT FUNCTIONS
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path
# Load file locations + dataclasses
from core.my_data_types import load_file_locations
# Interactive config builder
from main_modules.user_setup import what_do_you_want_to_do
# Your run-task dispatcher (you will implement this soon)
from main_modules.update_or_create import update_or_create_databases

#############################################
# main.py — Central dispatcher for Structured_Breadth
#############################################
"""
Responsibilities:
-----------------
1. Load file location settings from core/file_locations.json
2. Run interactive user setup and return a Config object
3. Dispatch to the correct action: update or create databases
4. (Later) plot charts, generate PDFs, etc.
"""

def main():

    # 1) Load the file_locations.json in the core/ folder
    config_path = Path("core") / "file_locations.json"
    fileloc = load_file_locations(config_path)

    # 2) Run the full interactive setup
    config = what_do_you_want_to_do(fileloc)

    # 3) Execute the requested action (update DB or rebuild DBs)
    index_df, components_df = update_or_create_databases(config, fileloc)

    print(f"index_df last line:\n{index_df.tail(1)}")
    print(f"components_df last line:\n{components_df.tail(1)}")


###################################
# Main
###################################

if __name__ == "__main__":
    main()
