# utils/debug.py

import pandas as pd

DEBUG = False   # Global toggle: change to True when you want debug output

def set_debug(flag: bool):
    """
    Place this at the start of:
        1. if __name__ = __ "main"__ to debug function
        2. start of main program to debug all
    """

    global DEBUG
    DEBUG = flag

def debug(msg, df=None):
    """
    You place debug("message", dataframe) in strategic points inside functions.
    When DEBUG = True, print debug messages.
    When DEBUG = False, your whole system stays silent.
    """
    if not DEBUG:
        return

    print(f"[DEBUG] {msg}")

    if df is not None:
        if isinstance(df.columns, pd.MultiIndex):
            print("--- MultiIndex DataFrame Columns ---")
            print(df.columns.get_level_values(0).unique().tolist())
        else:
            print("--- DataFrame Columns ---")
            print(df.columns)

        print("--- Head() ---")
        print(df.head())
        print("------------------------------------")
