import requests
import pandas as pd
import json
import matplotlib.pyplot as plt


# The original function is renamed and modified to handle multiple series and merging
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


# --- Example Usage ---

# 1. Define your parameters for multiple series
# IPCA (433) is monthly inflation, SELIC (4390) is the monthly accumulated rate.
SERIES_MAP = {
    433: 'IPCA (Monthly Inflation, %)',
    4390: 'SELIC (Monthly Accumulated Rate, %)'
}
START_DATE = '01/01/2023'  # January 1st, 2023
END_DATE = '31/12/2024'  # December 31st, 2024

# 2. Call the new function to fetch and merge the data
merged_data = fetch_and_merge_series(
    series_map=SERIES_MAP,
    start_date=START_DATE,
    end_date=END_DATE
)

# 3. Display the results and plot
if merged_data is not None:
    print("Successfully retrieved and merged data:")
    print(merged_data.head())
    print("\nData Shape (rows, columns):", merged_data.shape)
    print("\nData Types:")
    print(merged_data.dtypes)

    # 4. Plot the time series data using a secondary Y-axis
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # --- Plot IPCA on the primary axis (ax1) ---
    color1 = 'tab:red'
    ax1.set_xlabel('Date')
    ax1.set_ylabel(SERIES_MAP[433], color=color1)

    # Plot the first series (IPCA)
    merged_data['IPCA (Monthly Inflation, %)'].plot(
        ax=ax1,
        color=color1,
        marker='o',
        markersize=3,
        legend=False
    )
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, linestyle='--', alpha=0.5, which='major', axis='x')

    # --- Plot SELIC on the secondary axis (ax2) ---
    ax2 = ax1.twinx()  # Create a second axes that shares the same x-axis
    color2 = 'tab:blue'
    ax2.set_ylabel(SERIES_MAP[4390], color=color2)

    # Plot the second series (SELIC)
    merged_data['SELIC (Monthly Accumulated Rate, %)'].plot(
        ax=ax2,
        color=color2,
        marker='s',
        markersize=3,
        legend=False
    )
    ax2.tick_params(axis='y', labelcolor=color2)

    # --- Final Plot Customization ---
    plt.title('Comparison of IPCA and SELIC Monthly Accumulated Rate', fontsize=16)
    fig.tight_layout()  # Adjust layout

    # Manually create legends from the axes lines for a cleaner look
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()

    # Set the legend in a single box
    ax1.legend(
        lines1 + lines2,
        ['IPCA (Monthly Inflation, %)', 'SELIC (Monthly Accumulated Rate, %)'],
        loc='upper left'
    )

    plt.show()
    print("\nPlot generated successfully with two y-axes.")