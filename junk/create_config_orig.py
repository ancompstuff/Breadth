import json
import os
import pandas as pd
from datetime import datetime, timedelta
from core.my_data_types import Config, FileLocations, load_file_locations_dict
from core.constants import yahoo_market_details, file_locations


# ====================== HELPER FUNCTION TO COUNT THE TICKERS IN THE CSV =============================#
def count_tickers(csv_path: str) -> int:
#######################################################################################################
    """Return number of tickers in CSV (uses pandas; header 'Codes' is treated as column name)."""
    print(f"csv path is: {csv_path}")
    if not csv_path or csv_path.lower() == "none":
        return 0
    if not os.path.exists(csv_path):
        # choose behaviour: return 0 or raise — we return 0 and print warning
        print(f"Warning: ticker file not found: {csv_path}")
        return 0
    try:
        df_codes = pd.read_csv(csv_path)
        return len(df_codes)
    except Exception as e:
        print(f"Warning: error reading {csv_path}: {e}")
        return 0


#######################################################################################################
def what_do_you_want_to_do():
#######################################################################################################


    fileloc = load_file_locations_dict(file_locations)

    hoje = datetime.now()
    reference_time = 18
    default_start_date = "2020-01-01"  # used for initial testing

    markets = {k: v for k, v in yahoo_market_details.items() if v["codes_csv"] != "none"}

    # Set default values to avoid "Local variable 'xxx' might be referenced before assignment"
    ###########################################################################################
    markt_to_study = {1:markets[1]}

    # print(f"default chosen market: ", markt_to_study)
    ################################
    update = markt_to_study
    # print(f"default update market: ", update)
    ################################
    chosen_lookback = 252  # 1 yr
    end_date = download_until(hoje, reference_time)  # end_download_on
    start_download_on = default_start_date
    end_download_on = download_until(hoje, reference_time) # end_date
    # When doing historic study
    study_start_date = None
    study_end_date = None
    ###########################################################################################
    # --- Compute num_tickers for default markt_to_study immediately ---
    # markt_to_study is a dict like {"1": {...}}
    default_key = next(iter(markt_to_study))  # default is 1
    default_info = markt_to_study[default_key]
    csv_filename = default_info.get("codes_csv", "none")
    # build full path using your folder variable
    csv_path = os.path.join(fileloc.codes_to_download_folder, csv_filename)

    num_tickers = count_tickers(csv_path)

    print('What do you want to do?')
    print('***********************')
    # Define the options as a dictionary
    objective_options = {
        1: "Plot BVSP, update BVSP, 252 days lookback (Default)",
        2: "Plot BVSP, update all, 1008 days lookback",
        3: "Choose: 'market to plot', update all or only 'market to plot', choose lookback or study period",
        4: "Create new databases. Choose: a) 'market to plot', b) update all or 'market to plot', and c) lookback",
        5: "TEST (creates new database ONLY for TEST)"
        }
    # Loop through the dictionary to print the options
    for key, value in objective_options.items():
        print(f'{key}: {value}')

    while True:  # Will execute until finds a <break>
            try:
                objective = int(input('Enter your choice. <Return> for Default (1): ') or 1)
                if objective in objective_options:
                    break  # Exit the loop if the input is valid
                else:
                    print('Invalid choice. Enter choice or <Return> for 1')
            except ValueError:
                print('Invalid choice. Enter choice or <Return> for 1')

    if objective == 1:  # Plot BVSP, update BVSP, 252 days lookback (Default)
        # print('\n*******************************************************')
        # print('** Plot BVSP, update BVSP, 252 days lookback (Default) **')
        # print('*********************************************************')
        # Use default for markt_to_study
        # Use default for update
        chosen_lookback = 252  # 1 yr
        end_date = end_download_on
        study_end_date = None
        # markt_to_study already default; num_tickers already set above

    elif objective == 2:  # Plot BVSP, update all, 1008 days lookback
        # print('\n*********************************************')
        # print('** Plot BVSP, update all, 1008 days lookback **')
        # print('***********************************************')
        # Use default for markt_to_study
        update = markets
        chosen_lookback = 1008  # 4yrs
        end_date = end_download_on
        study_end_date = None
        # markt_to_study already default; num_tickers already set above

    elif objective == 3:  # Choose: market to plot, update all/market to plot, lookback or study period
        markt_to_study, num_tickers = which_market_to_study(fileloc.codes_to_download_folder)
        print("\nChoose either: 1 = 'Lookback' (e.g., 252 days) or 2 = Explicit end date (YYYYMMDD) + lookback")
        choice = input("Choose 1 or 2 (<Enter> for 1): ").strip() or "1"
        if choice == "1":
            chosen_lookback = how_far_to_lookback()
            update = which_markets_to_download(markets, markt_to_study)
        elif choice == "2":
            study_end_date_str = None  # input("Enter end date (YYYYMMDD): ").strip()
            update = None
            # LOOP for Study End Date
            while study_end_date_str is None:
                raw_end = input("Enter study end date (DDMMYYYY): ").strip()
                try:
                    # Validate format: DDMMYYYY -> datetime object
                    end_date_obj = datetime.strptime(raw_end, "%d%m%Y")

                    # Store validated date in YYYY-MM-DD format
                    study_end_date_str = end_date_obj.strftime("%Y-%m-%d")

                except ValueError:
                    print("❌ Invalid end date format. Expected DDMMYYYY (e.g., 31102025). Please try again.")
                    study_end_date = None

            else:
                # Success: Assign final variables
                study_end_date = study_end_date_str

            chosen_lookback = how_far_to_lookback()

        else:
            print("Invalid input. Using default lookback (252 days).")
            chosen_lookback = 252

        #chosen_lookback = how_far_to_lookback()
        end_date = end_download_on

    elif objective == 4:  # Create new databases. Choose: market to plot, update all/market to plot, lookback
        # print('\n***************************************************************************************')
        # print('*** Create new databases. Choose: market to plot, update all/market to plot, lookback ***')
        # print('*****************************************************************************************')
        # Initialize the variable to store the validated start date
        start_download_on = None
        while start_download_on is None:
            # 1. Get the raw input
            raw_start = input(
                "Default start download date is 01/01/2020. Else enter start download date (DDMMYYYY): ").strip() or "01012020"
            try:
                # Validate format: DDMMYYYY -> datetime object
                start_date_obj = datetime.strptime(raw_start, "%d%m%Y")

                # Store validated date in YYYY-MM-DD format
                start_download_on = start_date_obj.strftime("%Y-%m-%d")

            except ValueError:
                print("❌ Invalid start date format. Expected DDMMYYYY (e.g., 31102025). Please try again.")
                start_download_on = None

        #start = input("Default start download date is 01/01/2020. Else enter start download date (DDMMYYYY): ") or "01012020"
        # Convert DDMMYYYY to YYYY-MM-DD
        #start_download_on = datetime.strptime(start, "%d%m%Y").strftime("%Y-%m-%d")

        markt_to_study, num_tickers = which_market_to_study(fileloc.codes_to_download_folder)
        update = which_markets_to_download(markets, markt_to_study)
        chosen_lookback = how_far_to_lookback()
        end_date = get_update_date(hoje, reference_time)
        study_start_date = None
        study_end_date = None

    elif objective == 5:  # Testing (Test DF)
        # print('\n***************************')
        # print('** Testing (DOW/50d **')
        # print('***************************')
        markt_to_study = {13:markets[13]}
        # update = markt_to_study
        update = which_markets_to_download({13: markets[13]}, {13: markets[13]})
        chosen_lookback = 50
        end_date = end_download_on
        study_end_date = None
        # 1. Get the filename ('TEST')
        csv_filename = markets[13].get("codes_csv", "none")
        # 2. Construct the full path
        csv_path = os.path.join(fileloc.codes_to_download_folder, csv_filename)
        # 3. Call count_tickers with the path
        num_tickers = count_tickers(csv_path)

#####################################################################################
    # Ensure "yahoo_end_date" is one day after "end_date". YFinance end_date is EXCLUSIVE
    #####################################################################################
    if end_date:
        # Convert end_date from string to datetime
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        # Add one day
        yahoo_end_date = (end_date_obj + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        yahoo_end_date = None

    #####################################################################################
    """
    Create configuration object  
        idx_code = next(iter(config.market_to_study.values()))['idx_code']
        market   = next(iter(config.market_to_study.values()))['market']
        codes    = next(iter(config.market_to_study.values()))['codes_csv']
    """
    #####################################################################################

    config = Config(
        to_do=objective,
        market_to_study=markt_to_study,
        number_tickers=num_tickers,
        to_update=update,
        graph_lookback=chosen_lookback,
        yahoo_start_date=start_download_on,
        last_date_to_download=end_date,
        yahoo_end_date=yahoo_end_date,
        study_end_date=study_end_date
    )

    return config


#######################################################################################################
def which_market_to_study(codes_to_download_folder):
    """
        Parameters:
            dictionary: yahoo_market_details
            codes_to_download_folder: Path to the folder containing the CSV files with ticker codes
        Returns:
            market_choice (dictionary of one entry), num_tickers (int)
    """
#######################################################################################################

    # Keep only markets that have an associated CSV of tickers
    markets = {k: v for k, v in yahoo_market_details.items() if v["codes_csv"] != "none"}

    """print(f"dictionary keys: {list(dictionary.keys())}")
    print(f"filtered markets: {list(markets.keys())}")
    print('\n' + '-'*75)
    print('Available Markets:')
    print('-'*75)"""

    for key, value in markets.items():
        # ✅ build full path to CSV file
        csv_path = os.path.join(codes_to_download_folder, value["codes_csv"])
        #print(f"→ Checking: {csv_path}")  # 🟡 shows the full path
        #print(f"  Exists? {os.path.exists(csv_path)}")  # 🟡 confirms file presence

        if os.path.exists(csv_path):
            df_codes = pd.read_csv(csv_path)
            #print(f"  Rows read: {len(df_codes)}")  # 🟡 shows rows actually read
            #print(f"  Columns: {df_codes.columns.tolist()}")
            #num_tickers = len(df_codes)
        else:
            print(f"⚠️ CSV not found: {csv_path}")
            #num_tickers = 0

        # store ticker count in dictionary for later use
        # value["num_tickers"] = num_tickers
        print(f'{key}: {value["market"]} ({value["idx_code"]})')
    print('-'*75)

    while True:  # Loop until valid input is given
        raw_choice = input("\nSelect market to study (1-13): ").strip()

        if not raw_choice:  # If user just hits enter
            print("Please enter a valid market number.")
            continue
            
        try:
            # FIX: Convert the user input to an integer here
            choice = int(raw_choice)
            if choice in markets:  # Check if choice is a valid key in markets
                market_info = markets[choice]
                print(f'\nSelected market: {market_info["market"]} ({market_info["idx_code"]})')
                # compute number of tickers here instead of reading from dict
                csv_path = os.path.join(codes_to_download_folder, market_info["codes_csv"])
                num_tickers = count_tickers(csv_path)
                return {choice: market_info}, num_tickers
            else:
                print(f"Invalid choice: {choice}. Please select a number between 1 and 13.")
                
        except Exception as e:
            print(f"Error: {e}. Please enter a valid number.")


#######################################################################################################
def which_markets_to_download(dictionary, selected):
    # Parameter: dictionary is yahoo_market_details
    # Returns:
        # market_choice (dictionary of one or more entries)
#######################################################################################################

    # Select true markets (not indexes)
    markets = {k: v for k, v in dictionary.items() if v["codes_csv"] != "none"}

    while True:
        user_input = input("Update all markets (1, default) or selected (2)? ").strip()
        choice = int(user_input) if user_input.isdigit() else 1

        if choice == 1:
            print("Will use all markets")
            return markets
        elif int(choice) ==2:
            print("Will use selected market")
            return selected
        else:
            print("Invalid input.")


#######################################################################################################
def how_far_to_lookback():
    # Returns:
        # lookback_period: Lookback period in days, integer
#######################################################################################################
    while True:
        try:
            # Prompt the user for input with a default of 252 days
            lookback_period = int(input("Period for lookback?\n"
                                        "<Enter> for default (252days/1yr): ") or 252)
            print(f'Will use: {lookback_period} days')
            return lookback_period  # Return value if input is valid
        except ValueError:
            print("Invalid input. Enter an integer: ")


#######################################################################################################
def download_until(hoje: datetime, reference_time: int) -> str:
    #  inputs:
        #  hj: datetime
        #  ref_time: integer
    # Returns:
        # dl_until: date in YYYY-MM-DD format
#######################################################################################################

    # 0: Mon, 1: Tue, 2: Wed, 3: Thur, 4: Fri, 5: Sat, 6: Sun
    # Check if it's a weekend; if so, download up to Friday
    if hoje.weekday() in {5, 6}:
        dl_until = hoje - timedelta(days=(hoje.weekday() % 5 + 1))  # Adjust to Friday
    # If weekday and before market closes, use yesterday (data unavailable)
    elif datetime.now().hour < reference_time:
        dl_until = (datetime.today() - timedelta(days=1)).date()  # Convert to date
    # If weekday and market closed, use today
    else:
        dl_until = datetime.today().date()  # Convert to today's date

    # Print the date in DD-MM-YYYY format
    print(f'Will download up to: {dl_until.strftime("%d-%m-%Y")}')
    # Return the date as a string in YYYY-MM-DD format
    return dl_until.strftime("%Y-%m-%d")


#######################################################################################################
def get_update_date(hoje: datetime, reference_time: int) -> str:
    #  returns user input end date, or default (download_until) as YYYY-MM-DD format
#######################################################################################################
    """
    Prompt the user for an update date or default to the calculated value.
    Inputs:
        - hj: datetime
        - ref_time: integer (market close hour, e.g., 16 for 4 PM)
    Returns:
        - update_date: datetime.date
    """
    while True:
        user_input_end_date = input(
            "Enter last date you want (DDMMYYYY) or press <Enter> to use today: "
        )

        if not user_input_end_date:  # Default behavior
            return download_until(hoje, reference_time)

        try:
            # Parse user input from DDMMYYYY to YYYY-MM-DD ready for YFinance
            parsed_date = datetime.strptime(user_input_end_date, "%d%m%Y").strftime("%Y-%m-%d")

            # Print the same date in DD-MM-YYYY format
            print(f'Will download up to: {datetime.strptime(parsed_date, "%Y-%m-%d").strftime("%d-%m-%Y")}')
            return parsed_date

        except ValueError:
            print("Invalid date format. Use DDMMYYYY format or press <Enter> for today.")


#######################################################################################################
#------------------------------------------------------------------------------------------------------
#                                        MAIN PROGRAM                                                 #
#------------------------------------------------------------------------------------------------------
#######################################################################################################
#-------------------------------------------
# FOLDER LOCATIONS
#-------------------------------------------
if __name__ == "__main__":

    hoje = datetime.now()
    reference_time = 18
    default_start_date = "2020-01-01"  # used for initial testing

    # Creates a Config object
    setup_dict = what_do_you_want_to_do()
    # RETURNS:
        # "to_do": "objective"
        # "market_to_study": "chosen_market"
        # "graph_lookback": "chosen_lookback"
        # "last_date_to_download": "end_date"
        # "first_date_to_download": "start_date"
    # Print the dictionary in a readable format
    print(f"The Config object looks like this:\n{setup_dict}")
    print(f"Printed as dictionary: \n {json.dumps(setup_dict.to_dict(), indent=4)}")

