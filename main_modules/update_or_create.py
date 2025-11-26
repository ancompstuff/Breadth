from main_modules.create_databases import create_databases
from main_modules.update_databases import update_databases

def update_or_create_databases(config, fileloc):
    """
    Dispatcher:
    - If config.to_do in {1,2,3} → update existing DBs
    - If config.to_do in {4,5}   → create/rebuild DBs
    """

    if config.to_do in (1, 2, 3):
        print("\n⚙ Updating existing databases...")
        return update_databases(config, fileloc)

    elif config.to_do in (4, 5):
        print("\n🛠 Creating (rebuilding) databases...")
        return create_databases(config, fileloc)

    else:
        raise ValueError(f"Invalid to_do value: {config.to_do}")
