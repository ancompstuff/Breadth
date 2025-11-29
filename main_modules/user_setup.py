"""
Usage
-----
Run interactively:
    python -m main_modules.user_setup
or
    python Structured_Breadth/main_modules/user_setup.py

Notes
-----
- Expects the following to exist and be importable:
    from core.my_data_types import Config, FileLocations, load_file_locations
    from core.constants import yahoo_market_details

- Expects utils:
    utils/attach_num_tickers.py      -> provides count_tickers(obj)
    utils/ddmmyyyy_format.py   -> provides parse_ddmmyyyy(prompt, default=None)
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Tuple

from core.my_data_types import Config, FileLocations, load_file_locations
from core.constants import yahoo_market_details

# utils
from utils.attach_num_tickers import attach_number_tickers
from utils.ddmmyyyy_format import parse_ddmmyyyy


# ---------------------------------------------------------------------------
# Small internal helpers (thin wrappers / glue + validation)
# ---------------------------------------------------------------------------

def _today_or_yesterday_if_before_hour(reference_hour: int) -> str:
    """Return YYYY-MM-DD representing the most-recent usable market date
    considering a 'reference_hour' (market close hour)."""
    now = datetime.now()
    if now.weekday() in {5, 6}:  # weekend -> use previous Friday
        friday = now - timedelta(days=(now.weekday() - 4))
        return friday.strftime("%Y-%m-%d")
    if now.hour < reference_hour:
        # market not closed today: use yesterday
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")
    return now.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# User interaction helpers
# ---------------------------------------------------------------------------

def get_objective_from_user() -> int:
    """Print the menu and ask user to choose an objective. Returns int 1-5."""
    objective_options = {
        1: "Plot BVSP, update BVSP, lookback 252 (Enter for 252)",
        2: "Plot BVSP, update all, choose lookback (Enter for 252)",
        3: "Choose: i) market to plot, ii) update all or only 'market to plot', iii) choose lookback or study period(?)",
        4: "Create new databases. Choose: i) start date ii) mkt 2 study', iii) update all/mkt2study', iv) lookback",
        5: "TEST (creates new database ONLY for TEST)"
    }

    print("What do you want to do?\n" + "*" * 23)
    for k, v in objective_options.items():
        print(f"{k}: {v}")

    while True:
        raw = input("Enter your choice. <Return> for Default (1): ").strip() or "5"  # "1" put back after testing
        try:
            choice = int(raw)
            if choice in objective_options:
                return choice
            print("Invalid choice. Enter 1-5.")
        except ValueError:
            print("Invalid choice. Enter a number (1-5).")


def which_market_to_study(fileloc: FileLocations) -> Dict[int, dict]:
    """
    Receive a pre-built `markets` dict (already enriched with number_tickers)
    List available markets (those with codes_csv != 'none'), ask user to choose one,
    returns p. ex: {1: {"market": "Brazil", "idx_code": "^BVSP", "codes_csv": "IBOV.csv", "number_tickers": 82}}
    """
    # Prepare available markets, remove those without codes.csv folder
    markets = {k: v for k, v in yahoo_market_details.items()
               if v.get("codes_csv", "none") != "none"}

    print("\nAvailable Markets:")
    print("-" * 75)
    for key, value in markets.items():
        csv_path = os.path.join(fileloc.codes_to_download_folder, value["codes_csv"])
        exists = os.path.exists(csv_path)
        marker = "" if exists else " (CSV missing)"
        # Print available markets
        print(f"{key}: {value['market']} ({value['idx_code']}){marker} — tickers: {value.get('number_tickers', 0)}")
    print("-" * 75)

    while True:
        raw_choice = input("\nSelect market to study (enter number, default=1): ").strip() or "1"
        try:
            choice = int(raw_choice)
            if choice in markets:
                market_info = markets[choice]
                print(f"Selected: {market_info['market']}, {market_info['idx_code']}, tickers: {market_info['number_tickers']}")
                return {choice: market_info}
            print(f"Invalid choice: {choice}. Choose from available numbers.")
        except Exception as e:
            print(f"Error parsing choice: {e}")


def which_markets_to_download(selected: Dict[int, dict], mode: str= 'update') -> Dict[int, dict]:
    """
    Ask user whether to update all markets or only the selected one(s).
    Returns a dictionary of markets to update. Ensures number_tickers attached.
    """
    markets = {k: v for k, v in yahoo_market_details.items() if v.get("codes_csv", "none") != "none"}

    if mode == 'update':
        raw = input("Update all markets (1, default) or selected (2)? ").strip()
        if not raw or raw == "1":
            print("Will update all markets.")
            return markets
        if raw == "2":
            print("Will update selected market.")
            return selected
        print("Invalid input; defaulting to all markets.")
        return markets

    elif mode == "download":
        raw = input("Create new files for: 1) ALL markets/default or 2) STUDY market? ").strip()

        if not raw or raw == "1":
            print("Will download and build all markets.")
            return markets

        if raw == "2":
            print("Will download and build ONLY the study market.")
            return selected

        print("Invalid input; defaulting to ALL markets.")
        return markets

    else:
        raise ValueError(f"Invalid mode '{mode}' supplied to which_markets_to_download")


def how_far_to_lookback(default: int = 252) -> int:
    """Ask user how many days lookback to use. Default 252."""
    while True:
        try:
            raw = input(f"Period for lookback? <Enter> for default ({default} days): ").strip()
            if not raw:
                print(f"Will use: {default} days")
                return default
            val = int(raw)
            print(f"Will use: {val} days")
            return val
        except ValueError:
            print("Invalid input. Please enter an integer number of days.")


def get_update_date(reference_time: int) -> str:
    """Ask user for an explicit last date in DDMMYYYY or use computed default."""
    raw = input("Enter date you want to update to (DDMMYYYY) or press <Enter> to use today: ").strip()
    if not raw:
        return _today_or_yesterday_if_before_hour(reference_time)
    try:
        parsed = parse_ddmmyyyy(raw)  # parse_ddmmyyyy expects user-style input; we call with raw
        # parse_ddmmyyyy returns YYYY-MM-DD
        print(f"Will download up to: {datetime.strptime(parsed, '%Y-%m-%d').strftime('%d-%m-%Y')}")
        return parsed
    except Exception:
        print("Invalid date format. Use DDMMYYYY or press <Enter> for today.")
        return get_update_date(reference_time)


# ---------------------------------------------------------------------------
# Option builders (each returns a params dict used by assemble_config_object)
# ---------------------------------------------------------------------------

def build_option_1_defaults(reference_time: int) -> dict:
    """Default: Plot BVSP, update BVSP, 252 days lookback."""
    markets = {k: v for k, v in yahoo_market_details.items() if v.get("codes_csv", "none") != "none"}
    market_to_study = {1: markets[1]}
    end_date = _today_or_yesterday_if_before_hour(reference_time)

    return {
        "objective": 1,
        "market_to_study": market_to_study,
        "to_update": market_to_study,
        "graph_lookback": 252,
        "yf_start_date": "2020-01-01",  # not relevant as updating
        "download_end_date": end_date,
        #"yf_end_date": end_date,  # set when config built
        "study_end_date": None  # not relevant
    }


def build_option_2_update_all(reference_time: int) -> dict:
    """Plot BVSP, update all, 1008 days lookback."""
    markets = {k: v for k, v in yahoo_market_details.items() if v.get("codes_csv", "none") != "none"}
    market_to_study = {1: markets[1]}
    end_date = _today_or_yesterday_if_before_hour(reference_time)
    chosen_lookback = how_far_to_lookback()

    return {
        "objective": 2,
        "market_to_study": market_to_study,
        "to_update": markets,
        "graph_lookback": chosen_lookback,
        "yf_start_date": "2020-01-01",  # not relevant as updating
        "download_end_date": end_date,
        #"yf_end_date": end_date,  # set when config built
        "study_end_date": None  # not relevant
    }


def build_option_3_custom(fileloc: FileLocations, reference_time: int) -> dict:
    """
    Choose: i) market to plot, ii) update all or only 'market to plot', iii) choose lookback or study period(?),
    Returns params dictionary.
    """
    markets = {k: v for k, v in yahoo_market_details.items() if v.get("codes_csv", "none") != "none"}
    market_to_study = which_market_to_study(fileloc)
    to_update = which_markets_to_download(market_to_study, mode="update")
    study_end_date = None

    while True:
        print("\nChoose either: 1 = Lookback (from today) or 2 = Lookback (from other date: DDMMYYYY)")
        raw_choice = input("Choose 1 or 2 (<Enter> for 1): ").strip() or "1"
        choice=int(raw_choice)

        if choice == 1 or choice==2:
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")

    if choice == 2:
        # Loop for date until we get a valid one using parse_ddmmyyyy
        while study_end_date is None:
            raw_study_end = input("Enter study end date (DDMMYYYY): ").strip()
            # Handle empty input immediately if you want
            if not raw_study_end:
                print("Date cannot be empty.")
                continue
            try:
                study_end_date = parse_ddmmyyyy(raw_study_end)
            except Exception:
                print("❌ Invalid end date format. Expected DDMMYYYY. Please try again.")
                study_end_date = None

        # Set new (or same) lookback
    chosen_lookback = how_far_to_lookback()
    end_date = _today_or_yesterday_if_before_hour(reference_time)

    return {
        "objective": 3,
        "market_to_study": market_to_study,
        "to_update": to_update,
        "graph_lookback": chosen_lookback,
        "yf_start_date": "2020-01-01",
        "download_end_date": end_date,
        #"yf_end_date": end_date,  # set when config built
        "study_end_date": study_end_date
    }


def build_option_4_build_databases(fileloc: FileLocations,  reference_time: int) -> dict:
    """
    Create new databases: ask for start date, choose market, update selection, choose lookback.
    
    Args:
        reference_time: The reference time for date calculations
        fileloc: FileLocations object containing paths to data files
    """
    # Get validated start date (DDMMYYYY -> YYYY-MM-DD) via parse_ddmmyyyy helper
    while True:
        raw_start = input("Default start download date is 01/01/2020. Else enter start download date (DDMMYYYY): ").strip() or "01012020"
        try:
            start_download_on = parse_ddmmyyyy(raw_start)
            break
        except Exception:
            print("❌ Invalid start date format. Expected DDMMYYYY. Please try again.")

    markets = {k: v for k, v in yahoo_market_details.items() if v.get("codes_csv", "none") != "none"}
    market_to_study = which_market_to_study(fileloc)
    to_update = which_markets_to_download(market_to_study, mode="download")
    chosen_lookback = how_far_to_lookback()
    end_date = get_update_date(reference_time)

    return {
        "objective": 4,
        "market_to_study": market_to_study,
        "to_update": to_update,
        "graph_lookback": chosen_lookback,
        "yf_start_date": start_download_on,
        "download_end_date": end_date,
        #"yf_end_date": end_date,
        "study_end_date": None
    }


def build_option_5_test(reference_time: int) -> dict:
    """Test case: small test market (13), create DB only for TEST."""

    """# pick market 13 if present
    if 13 not in yahoo_market_details:
        print("Test market 13 not defined in yahoo_market_details.")
        market_to_study = {next(iter(yahoo_market_details)): next(iter(yahoo_market_details.values()))}
    else:
        market_to_study = {13: yahoo_market_details[13]}

    # Get validated start date
    while True:
        raw_start = input("Default start download date is 01/01/2020. Else enter start download date (DDMMYYYY): ").strip() or "01012020"
        try:
            start_download_on = parse_ddmmyyyy(raw_start)                             
            break
        except Exception:
            print("❌ Invalid start date format. Expected DDMMYYYY. Please try again.")

    end_date = get_update_date(reference_time)

    # Lookback from today or choose other period
    print("\nChoose either: 1 = Lookback (from today) or 2 = Lookback (from other date: DDMMYYYY)")
    choice = input("Choose 1 or 2 (<Enter> for 1): ").strip() or "1"
    if choice == "1":
        chosen_lookback = how_far_to_lookback()  # default is 252
        study_end_date = None
    elif choice == "2":
        study_end_date = None
        # Loop for date until we get a valid one using parse_ddmmyyyy
        while study_end_date is None:
            raw_study_end = input("Enter study end date (DDMMYYYY): ").strip()
            # Handle empty input immediately if you want
            if not raw_study_end:
                print("Date cannot be empty.")
                continue
            try:
                study_end_date = parse_ddmmyyyy(raw_study_end)
            except Exception:
                print("❌ Invalid end date format. Expected DDMMYYYY. Please try again.")
                study_end_date = None
        chosen_lookback = how_far_to_lookback()"""

    """return {
        "objective": 5,
        "market_to_study": market_to_study,
        "to_update": market_to_study,
        "graph_lookback": chosen_lookback,
        "yf_start_date": start_download_on,
        "download_end_date": end_date,
        #"yf_end_date": end_date,
        "study_end_date": study_end_date
    }"""
    return {
            "objective": 5,
            "market_to_study": {13: yahoo_market_details[13]},
            "to_update": {13: yahoo_market_details[13]},
            "graph_lookback": 252,
            "yf_start_date": "2020-01-01",
            "download_end_date": _today_or_yesterday_if_before_hour(reference_time),
            #"yf_end_date": end_date,
            "study_end_date": _today_or_yesterday_if_before_hour(reference_time)
        }



# ---------------------------------------------------------------------------
# Config assembler
# ---------------------------------------------------------------------------

def assemble_config_object(params: dict) -> Config:
    """
    Convert params dict to Config using project field names.
    """
    last = params.get("download_end_date")
    yahoo_end_date = None
    if last:
        end_date_obj = datetime.strptime(last, "%Y-%m-%d")
        yahoo_end_date = (end_date_obj + timedelta(days=1)).strftime("%Y-%m-%d")

    cfg = Config(
        to_do=params["objective"],
        market_to_study=params["market_to_study"],
        to_update=params.get("to_update"),
        graph_lookback=params.get("graph_lookback"),
        yf_start_date=params.get("yf_start_date"),
        download_end_date=last,
        yf_end_date=yahoo_end_date or params.get("yahoo_end_date"),
        study_end_date=params.get("study_end_date")
    )
    return cfg


def what_do_you_want_to_do(fileloc) -> Config:
    """
    Main interactive entry point. Builds and returns a Config object.
    """
    #fileloc = load_file_locations()
    hoje = datetime.now()
    reference_time = 18  # local market close hour used to decide 'today' vs 'yesterday'

    # compute markets filter once and attach number_tickers
    markets_with_csv = {k: v for k, v in yahoo_market_details.items() if v.get("codes_csv", "none") != "none"}
    markets = attach_number_tickers(fileloc.codes_to_download_folder, markets_with_csv)

    objective = get_objective_from_user()

    if objective == 1:
        params = build_option_1_defaults(reference_time)
    elif objective == 2:
        params = build_option_2_update_all(reference_time)
    elif objective == 3:
        params = build_option_3_custom(fileloc, reference_time)
    elif objective == 4:
        params = build_option_4_build_databases(fileloc,reference_time)
    elif objective == 5:
        params = build_option_5_test(reference_time)
    else:
        # fallback safe defaults
        params = build_option_1_defaults(reference_time)

    config = assemble_config_object(params)
    return config


# ---------------------------------------------------------------------------
# CLI behaviour: when run as script, produce the Config and print summary
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    fileloc = load_file_locations()
    cfg = what_do_you_want_to_do(fileloc)
    print("The Config object looks like this:")
    print(cfg)
    try:
        # to_dict() method assumed present on Config (kept from original)
        print(f"Config object printed as dictionary:\n{json.dumps(cfg.to_dict(), indent=4)}")
    except Exception:
        # fallback: print __dict__ if no to_dict
        try:
            print(json.dumps(cfg.__dict__, indent=4))
        except Exception:
            print("Could not serialize Config object for pretty printing.")
