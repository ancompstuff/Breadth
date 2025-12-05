import requests
import pandas as pd
import json, os
import matplotlib.pyplot as plt


def get_bcb_series(series_code, start_date, end_date):
    """
    Fetches a single time series from the BACEN SGS API and returns it as a pandas DataFrame.

    Args:
        series_code (int or str): The SGS code for the desired time series.
        start_date (str): The initial date for the query in 'dd/MM/aaaa' format.
        end_date (str): The final date for the query in 'dd/MM/aaaa' format.

    Returns:
        pandas.DataFrame: A DataFrame containing the indexed 'data' and the series 'valor',
                          or None if the request failed.
    """
    BASE_URL = (
        "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_code}/dados?"
        "formato=json&dataInicial={start_date}&dataFinal={end_date}"
    )

    final_url = BASE_URL.format(
        series_code=series_code,
        start_date=start_date,
        end_date=end_date
    )

    print(f"Fetching data for series {series_code} from URL: {final_url}")

    try:
        response = requests.get(final_url)
        response.raise_for_status()

        data = response.json()

        if not data:
            print(f"Warning: No data returned for series code {series_code}.")
            return None

        df = pd.DataFrame(data)

        # Clean up the DataFrame for time series analysis
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
        df = df.set_index('data')
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')

        # Rename the column clearly using the code
        df = df.rename(columns={'valor': f'{series_code}'})

        return df[[f'{series_code}']]  # Return only the value column

    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error for series {series_code}: {err}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request Error for series {series_code}: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON response for series {series_code}.")
        return None

def fetch_and_merge_bcb(series_map, start_date, end_date):
    """
    Fetches multiple series and merges them into a single DataFrame on the date index.

    Args:
        series_map (dict): A dictionary mapping series codes to display names (e.g., {433: 'IPCA', 4390: 'SELIC'}).
        start_date (str): The initial date for the query in 'dd/MM/aaaa' format.
        end_date (str): The final date for the query in 'dd/MM/aaaa' format.

    Returns:
        pandas.DataFrame: A merged DataFrame with all series, or None.
    """
    all_data = None

    print("-" * 50)
    for code, name in series_map.items():
        df_series = get_bcb_series(code, start_date, end_date)

        if df_series is not None:
            # Rename the column to the descriptive name
            df_series = df_series.rename(columns={str(code): name})

            if all_data is None:
                all_data = df_series
            else:
                # Merge the new series with the existing data on the index (Date)
                all_data = all_data.merge(df_series, left_index=True, right_index=True, how='outer')

    print("-" * 50)
    return all_data


def download_bcb_bcb(start_date, end_date, fileloc, config):
    series_map = {
        config.ipca_code: "IPCA",
        config.selic_code: "SELIC"
    }
    df = fetch_and_merge_bcb(series_map, start_date, end_date)
    if df is None:
        print("BCB returned no data.")
        return
    path = os.path.join(fileloc.bcb_data_folder, "BCB_IPCA_SELIC.csv")
    df.to_csv(path)
    print(f"BCB data saved: {path}")