import os

# Folder → files mapping
structure = {
    "core": [
        "__init__.py",
        "constants.py",
        "my_data_types.py",
        "utils.py",
    ],
    "data": [
        "__init__.py",
        "loader.py",
        "databases.py",
        "aligner.py",
    ],
    "indicators": [
        "__init__.py",
        "moving_averages.py",
        "breadth.py",
        "compression.py",
        "highs_lows.py",
        "volume.py",
        "run_length.py",
        "rsi.py",
        "breakout.py",
        "breakout_readiness.py",
        "breakout_score.py",
        "williams.py",
    ],
    "plotting": [
        "__init__.py",
        "common_plot_setup.py",
        "index_vs_ma.py",
        "volume_plots.py",
        "highs_lows_plots.py",
        "breadth_plots.py",
        "compression_plots.py",
        "runlength_plots.py",
        "rsi_plots.py",
        "breakout_plots.py",
        "williams_plots.py",
        "breakout_readiness_plots.py",
        "breakout_score_plots.py",
    ],
    "legacy": [
        "__init__.py",
    ],
}

def create_structure():
    for folder, files in structure.items():
        os.makedirs(folder, exist_ok=True)
        for filename in files:
            filepath = os.path.join(folder, filename)
            if not os.path.exists(filepath):
                open(filepath, "w").close()

    print("Project structure created successfully.")

if __name__ == "__main__":
    create_structure()
