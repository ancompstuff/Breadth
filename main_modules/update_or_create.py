from main_modules.create_databases import create_databases
from main_modules.update_databases import update_databases

"""# Imports for testing. Delete after
from core.my_data_types import load_file_locations, Config, FileLocations
from datetime import datetime"""

def update_or_create_databases(config, fileloc):
    """
    Dispatcher:
    - If config.to_do in {1,2,3} → update existing DBs
    - If config.to_do in {4,5}   → create/rebuild DBs
    """

    """# Delete this config - only used for testing
    config = Config(
        to_do=5,
        market_to_study={
            13: {'idx_code': '^BVSP', 'market': '3 ticker test', 'codes_csv': 'TEST.csv', "number_tickers": 3}},
        to_update={13: {'idx_code': '^BVSP', 'market': '3 ticker test', 'codes_csv': 'TEST.csv', "number_tickers": 3}},
        graph_lookback=252,
        yf_start_date="2020-01-01",
        download_end_date=datetime.now().strftime("%Y-%m-%d"),
        yf_end_date=datetime.now().strftime("%Y-%m-%d"),
        study_end_date=datetime.now().strftime("%Y-%m-%d")
    )
"""
    if config.to_do in (1, 2, 3):
        print("\n⚙ Updating existing databases...")
        return update_databases(config, fileloc)

    elif config.to_do in (4, 5):
        print("\n🛠 Creating (rebuilding) databases...")
        return create_databases(config, fileloc)

    else:
        raise ValueError(f"Invalid to_do value: {config.to_do}")
