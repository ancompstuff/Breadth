yahoo_market_details = {
        1: {'idx_code': '^BVSP', 'market': 'Bovespa', 'codes_csv': 'IBOV.csv'},
        2: {'idx_code': '^IXIC', 'market': 'NASDAQ', 'codes_csv': 'NASDAQ.csv'},
        3: {'idx_code': '^FTLC', 'market': 'FTSE350', 'codes_csv': 'FTSE350.csv'},
        4: {'idx_code': '^GSPC', 'market': 'SP500', 'codes_csv': 'SP500.csv'},
        5: {'idx_code': '^DJI', 'market': 'Dow30', 'codes_csv': 'DOW.csv'},
        6: {'idx_code': 'GC=F', 'market': 'Gold', 'codes_csv': 'none'},
        7: {'idx_code': 'BTC-USD', 'market': 'Bitcoin', 'codes_csv': 'none'},
        8: {'idx_code': 'BRL=X', 'market': 'USDollar', 'codes_csv': 'none'},
        9: {'idx_code': 'CL=F', 'market': 'Crude', 'codes_csv': 'none'},
        10: {'idx_code': 'ZN=F', 'market': '10yrT-note', 'codes_csv': 'none'},
        11: {'idx_code': 'ZT=F', 'market': '2yrT-note', 'codes_csv': 'none'},
        12: {'idx_code': '^VIX', 'market': 'VIX', 'codes_csv': 'none'},
        13: {'idx_code': '^BVSP', 'market': '3 ticker test', 'codes_csv': 'TEST.csv'},
        14: {'idx_code': '^IGCX', 'market': 'iGov', 'codes_csv': 'IGCX.csv'}
}
file_locations = {
        "downloaded_data_folder": "../Trading Data/Data_files_test",
        "pdf_folder": "../Trading Data/Data_files_test/PDF_test",
        "codes_to_download_folder": "../Trading Data/Modular_Codes_to_download",
        "yahoo_markets_dictionary": "yahoo_market_details.json"
}

ma_groups = {
        "short": {"periods": [5, 12, 25],
                  "color": "blue",
                  "port": "curtas"},
        "mid": {"periods": [40, 80],
                "color": "cyan",
                "port": "médias"},
        "long": {"periods": [50, 100, 200],
                 "color": "darkblue",
                 "port": "longas"}
        }

mas_list = sorted([ma for group_data in ma_groups.values() for ma in group_data["periods"]])
# # Resulting mas_list: [5, 12, 25, 40, 50, 80, 100, 200]

ma_color_map = {
        # MA5 group
        'MA5': 'blue',
        'Nº>MA5': 'lightblue',
        'Nº<MA5': 'deepskyblue',
        '%>MA_5': 'deepskyblue',
        '%>MA5': 'deepskyblue',
        '%<MA5': 'dodgerblue',
        '%<MA_5': 'dodgerblue',
        '%±MA5': 'steelblue',

        'VWMA5': 'red',
        'Nº>VWMA5': 'lightcoral',
        'Nº<VWMA5': 'darkred',
        '%>VWMA_5': 'salmon',
        '%>VWMA5': 'salmon',
        '%<VWMA5': 'firebrick',
        '%<VWMA_5': 'firebrick',
        '%±VWMA5': 'crimson',

        # MA12 group
        'MA12': 'green',
        'Nº>MA12': 'palegreen',
        'Nº<MA12': 'darkgreen',
        '%>MA_5_12': 'limegreen',
        '%>MA12': 'limegreen',
        '%<MA12': 'forestgreen',
        '%<MA_5_12': 'forestgreen',
        '%±MA12': 'mediumseagreen',

        'VWMA12': 'orange',
        'Nº>VWMA12': 'lightsalmon',
        'Nº<VWMA12': 'darkorange',
        '%>VWMA_5_12': 'coral',
        '%>VWMA12': 'coral',
        '%<VWMA12': 'orangered',
        '%<VWMA_5_12': 'orangered',
        '%±VWMA12': 'tomato',

        # MA25 group
        'MA25': 'purple',
        'Nº>MA25': 'plum',
        'Nº<MA25': 'indigo',
        '%>MA_5_12_25': 'mediumorchid',
        '%>MA25': 'mediumorchid',
        '%<MA25': 'darkviolet',
        '%<MA_5_12_25': 'darkviolet',
        '%±MA25': 'violet',

        'VWMA25': 'brown',
        'Nº>VWMA25': 'sandybrown',
        'Nº<VWMA25': 'sienna',
        '%>VWMA_5_12_25': 'peru',
        '%>VWMA25': 'peru',
        '%<VWMA25': 'chocolate',
        '%<VWMA_5_12_25': 'chocolate',
        '%±VWMA25': 'rosybrown',

        # MA40 group
        'MA40': 'cyan',
        'Nº>MA40': 'paleturquoise',
        'Nº<MA40': 'teal',
        '%>MA_40': 'mediumturquoise',
        '%>MA40': 'mediumturquoise',
        '%<MA40': 'darkcyan',
        '%<MA_40': 'darkcyan',
        '%±MA40': 'turquoise',

        'VWMA40': 'magenta',
        'Nº>VWMA40': 'orchid',
        'Nº<VWMA40': 'darkmagenta',
        '%>VWMA_40': 'violet',
        '%>VWMA40': 'violet',
        '%<VWMA40': 'purple',
        '%<VWMA_40': 'purple',
        '%±VWMA40': 'plum',

        # MA50 group
        'MA50': 'gold',
        'Nº>MA50': 'khaki',
        'Nº<MA50': 'darkgoldenrod',
        '%>MA_50': 'yellow',
        '%>MA50': 'yellow',
        '%<MA50': 'goldenrod',
        '%<MA_50': 'goldenrod',
        '%±MA50': 'lightgoldenrodyellow',

        'VWMA50': 'darkblue',
        'Nº>VWMA50': 'cornflowerblue',
        'Nº<VWMA50': 'mediumblue',
        '%>VWMA_50': 'royalblue',
        '%>VWMA50': 'royalblue',
        '%<VWMA50': 'navy',
        '%<VWMA_50': 'navy',
        '%±VWMA50': 'slateblue',

        # MA80 group
        'MA80': 'lime',
        'Nº>MA80': 'lightgreen',
        'Nº<MA80': 'darkolivegreen',
        '%>MA_40_80': 'springgreen',
        '%>MA80': 'springgreen',
        '%<MA80': 'olivedrab',
        '%<MA_40_80': 'olivedrab',
        '%±MA80': 'forestgreen',

        'VWMA80': 'salmon',
        'Nº>VWMA80': 'lightcoral',
        'Nº<VWMA80': 'red',
        '%>VWMA_40_80': 'tomato',
        '%>VWMA80': 'tomato',
        '%<VWMA80': 'firebrick',
        '%<VWMA_40_80': 'firebrick',
        '%±VWMA80': 'crimson',

        # MA100 group
        'MA100': 'coral',
        'Nº>MA100': 'lightcoral',
        'Nº<MA100': 'indianred',
        '%>MA_50_100': 'salmon',
        '%>MA100': 'salmon',
        '%<MA100': 'brown',
        '%<MA_50_100': 'brown',
        '%±MA100': 'maroon',

        'VWMA100': 'darkcyan',
        'Nº>VWMA100': 'cadetblue',
        'Nº<VWMA100': 'teal',
        '%>VWMA_50_100': 'steelblue',
        '%>VWMA100': 'steelblue',
        '%<VWMA100': 'darkslategray',
        '%<VWMA_50_100': 'darkslategray',
        '%±VWMA100': 'slategray',

        # MA200 group - new unique colors
        'MA200': 'darkmagenta',
        'Nº>MA200': 'orchid',
        'Nº<MA200': 'mediumvioletred',
        '%>MA_50_100_200': 'deeppink',
        '%>MA200': 'deeppink',
        '%<MA200': 'palevioletred',
        '%<MA_50_100_200': 'palevioletred',
        '%±MA200': 'hotpink',

        'VWMA200': 'darkslateblue',
        'Nº>VWMA200': 'slateblue',
        'Nº<VWMA200': 'mediumslateblue',
        '%>VWMA_50_100_200': 'blueviolet',
        '%>VWMA200': 'blueviolet',
        '%<VWMA200': 'rebeccapurple',
        '%<VWMA_50_100_200': 'rebeccapurple',
        '%±VWMA200': 'indigo'
    }

trend_combinations = {
        # --- ABOVE MA ---
        ">MA_5": ["AboveBelowMA5"],
        ">MA_5_12": ["AboveBelowMA5", "AboveBelowMA12"],
        ">MA_5_12_25": ["AboveBelowMA5", "AboveBelowMA12", "AboveBelowMA25"],
        ">MA_40": ["AboveBelowMA40"],
        ">MA_40_80": ["AboveBelowMA40", "AboveBelowMA80"],
        ">MA_50": ["AboveBelowMA50"],
        ">MA_50_100": ["AboveBelowMA50", "AboveBelowMA100"],
        ">MA_50_100_200": ["AboveBelowMA50", "AboveBelowMA100", "AboveBelowMA200"],
        # --- ABOVE VWMA ---
        ">VWMA_5": ["AboveBelowVWMA5"],
        ">VWMA_5_12": ["AboveBelowVWMA5", "AboveBelowVWMA12"],
        ">VWMA_5_12_25": ["AboveBelowVWMA5", "AboveBelowVWMA12", "AboveBelowVWMA25"],
        ">VWMA_40": ["AboveBelowVWMA40"],
        ">VWMA_40_80": ["AboveBelowVWMA40", "AboveBelowVWMA80"],
        ">VWMA_50": ["AboveBelowVWMA50"],
        ">VWMA_50_100": ["AboveBelowVWMA50", "AboveBelowVWMA100"],
        ">VWMA_50_100_200": ["AboveBelowVWMA50", "AboveBelowVWMA100", "AboveBelowVWMA200"],
        # --- BELOW MA ---
        "<MA_5": ["AboveBelowMA5"],
        "<MA_5_12": ["AboveBelowMA5", "AboveBelowMA12"],
        "<MA_5_12_25": ["AboveBelowMA5", "AboveBelowMA12", "AboveBelowMA25"],
        "<MA_40": ["AboveBelowMA40"],
        "<MA_40_80": ["AboveBelowMA40", "AboveBelowMA80"],
        "<MA_50": ["AboveBelowMA50"],
        "<MA_50_100": ["AboveBelowMA50", "AboveBelowMA100"],
        "<MA_50_100_200": ["AboveBelowMA50", "AboveBelowMA100", "AboveBelowMA200"],
        # --- BELOW VWMA ---
        "<VWMA_5": ["AboveBelowVWMA5"],
        "<VWMA_5_12": ["AboveBelowVWMA5", "AboveBelowVWMA12"],
        "<VWMA_5_12_25": ["AboveBelowVWMA5", "AboveBelowVWMA12", "AboveBelowVWMA25"],
        "<VWMA_40": ["AboveBelowVWMA40"],
        "<VWMA_40_80": ["AboveBelowVWMA40", "AboveBelowVWMA80"],
        "<VWMA_50": ["AboveBelowVWMA50"],
        "<VWMA_50_100": ["AboveBelowVWMA50", "AboveBelowVWMA100"],
        "<VWMA_50_100_200": ["AboveBelowVWMA50", "AboveBelowVWMA100", "AboveBelowVWMA200"]
    }
