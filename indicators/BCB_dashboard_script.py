import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, date
from io import StringIO
import os

# -----------------------------
# Configuration
# -----------------------------
BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"

SERIES = {
    1: "BRL/USD Exchange Rate – End of period (commercial rate)",
    3546: "International Reserves Total (US$ million, monthly )",
    22701: "Current Account - monthly - net (US$ million)",
    23079: "Current account accumulated in 12 months in relation to GDP - monthly (%)",
    29581:	"Percentage of the highest risk balance of the credit portfolio – Non-financial corporations – Total",
    27815: "Broad money supply - M4 (end-of-period balance)",
    433: "IPCA",
    1178: "SELIC Policy Interest Rate (annualized, 252-day basis)",
    11: "Selic Diária",
    256: "Taxa Juros Longo Prazo",
    24363: "CB Economic Activity Index",
    27574: "Índice de Commodities - (IC-Br)",
    27575: "IC-Br - Agropecuária",
    27577: "IC-Br - Energia",
    27576: "IC-Br - Metal",
    4390: "Selic Acumulada no mes",
    4468: "Net public debt - Balances in reais (million) - Total - Federal Government and Banco Central",
    13762: "Gross General Government Debt (% of GDP)"
}

# Overall desired range for the dashboard
START_DATE = date(2010, 1, 1)
END_DATE = date.today()

# Default max years per request
DEFAULT_MAX_YEARS_PER_REQUEST = 10

# For some heavy/long series we can lower the chunk size
SERIES_MAX_YEARS = {
    1: 5,      # FX – shorter chunks to avoid 504
    # others can use default
}

# Output directory
OUT_DIR = r"F:\Documents\PyCharmProjects\GitHub\TradingData\Data_files\bacen_data"
os.makedirs(OUT_DIR, exist_ok=True)


# -----------------------------
# Date helpers
# -----------------------------
def date_to_str(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def generate_date_chunks(start: date, end: date, max_years: int):
    """
    Yield (chunk_start, chunk_end) pairs where each chunk spans at most max_years.
    """
    current_start = start
    while current_start <= end:
        year_limit = current_start.year + max_years - 1
        chunk_end = date(year_limit, 12, 31)
        if chunk_end > end:
            chunk_end = end
        yield current_start, chunk_end
        current_start = date(chunk_end.year + 1, 1, 1)


# -----------------------------
# Fetch one series with CSV + chunking
# -----------------------------
def fetch_sgs_series(code: int,
                     start: date = START_DATE,
                     end: date = END_DATE) -> pd.Series:
    """
    Fetch a single SGS series as a pandas Series with datetime index
    using the CSV endpoint and chunked requests, robust to missing/invalid data.
    """
    max_years = SERIES_MAX_YEARS.get(code, DEFAULT_MAX_YEARS_PER_REQUEST)
    all_chunks = []

    for chunk_start, chunk_end in generate_date_chunks(start, end, max_years):
        params = {
            "formato": "csv",
            "dataInicial": date_to_str(chunk_start),
            "dataFinal": date_to_str(chunk_end),
        }
        url = BASE_URL.format(code=code)

        headers = {
            "User-Agent": "python-requests-bcb-dashboard/1.0",
            "Accept": "text/csv, */*;q=0.8",
        }

        print(
            f"  -> chunk {date_to_str(chunk_start)} to {date_to_str(chunk_end)}"
        )
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            resp.raise_for_status()
        except requests.HTTPError as e:
            print(
                f"    HTTP error for code {code} on {params['dataInicial']}–{params['dataFinal']}: {e}"
            )
            continue
        except requests.RequestException as e:
            print(
                f"    Request error for code {code} on {params['dataInicial']}–{params['dataFinal']}: {e}"
            )
            continue

        text = resp.text
        if not text.strip():
            print(f"    Empty response for code {code} on this chunk; skipping.")
            continue

        # Quick check: if it looks like HTML (error page), skip
        first_100 = text[:100].lower()
        if "<html" in first_100 or "<!doctype html" in first_100:
            print(f"    Non-CSV (HTML) response for code {code}; skipping this chunk.")
            continue

        try:
            df = pd.read_csv(
                StringIO(text),
                sep=";",
                decimal=",",
                parse_dates=["data"],
                dayfirst=True,
            )
        except ValueError as e:
            print(
                f"    CSV parse error for code {code} on {params['dataInicial']}–{params['dataFinal']}: {e}"
            )
            try:
                df_raw = pd.read_csv(StringIO(text), sep=";", decimal=",")
                print(f"    Raw columns for code {code}: {df_raw.columns.tolist()}")
            except Exception as e2:
                print(f"    Failed to inspect raw CSV for code {code}: {e2}")
            continue
        except Exception as e:
            print(
                f"    Unexpected CSV error for code {code} on {params['dataInicial']}–{params['dataFinal']}: {e}"
            )
            continue

        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]

        if "data" not in df.columns or "valor" not in df.columns:
            print(
                f"    Unexpected CSV columns for code {code}: {df.columns.tolist()} – skipping chunk."
            )
            continue

        all_chunks.append(df[["data", "valor"]])

    if not all_chunks:
        print(f"  !! No valid data fetched for code {code}.")
        return pd.Series(dtype="float64")

    full_df = pd.concat(all_chunks, ignore_index=True)

    # Drop duplicates by date, keep last
    full_df = full_df.drop_duplicates(subset=["data"]).sort_values("data")

    s = full_df.set_index("data")["valor"].astype("float64")
    s.name = SERIES.get(code, str(code))
    return s


def align_bcb_with_yahoo(bcb_monthly: pd.DataFrame,
                         yahoo_df: pd.DataFrame,
                         price_col: str = "Adj Close") -> pd.DataFrame:
    """
    Align BCB monthly data with Yahoo daily data.

    - bcb_monthly: DataFrame with monthly BCB series (index = period end dates)
    - yahoo_df: DataFrame with daily Yahoo prices (index = daily dates)
    - price_col: name of the price column to bring in (e.g. 'Adj Close')

    Returns a daily DataFrame on Yahoo's calendar with:
      - all BCB columns forward-filled
      - one extra column for the Yahoo price
    """
    bcb_monthly = bcb_monthly.copy()
    yahoo_df = yahoo_df.copy()

    # Ensure datetime indices
    bcb_monthly.index = pd.to_datetime(bcb_monthly.index)
    yahoo_df.index = pd.to_datetime(yahoo_df.index)

    # Reindex BCB to Yahoo's index (daily / business days), then forward-fill
    bcb_daily = bcb_monthly.reindex(yahoo_df.index)
    bcb_daily = bcb_daily.ffill()

    if price_col not in yahoo_df.columns:
        raise KeyError(f"Column '{price_col}' not found in yahoo_df")

    combined = bcb_daily.copy()
    combined[price_col] = yahoo_df[price_col]

    return combined

# -----------------------------
# Download all series
# -----------------------------
all_series = {}
for code, label in SERIES.items():
    print(f"Downloading {code} - {label} ...")
    s = fetch_sgs_series(code, START_DATE, END_DATE)
    all_series[label] = s

# Align into one DataFrame
df = pd.concat(all_series.values(), axis=1, join="outer")
df.columns = list(all_series.keys())

# Ensure index is DatetimeIndex
df.index = pd.to_datetime(df.index)

# Drop series with no data at all
df = df.dropna(axis=1, how="all")

print("\nDataFrame index type:", type(df.index))
print("Columns:", df.columns.tolist())
print("Head:\n", df.head())

# -----------------------------
# Save data to disk
# -----------------------------
raw_csv_path = os.path.join(OUT_DIR, "bcb_dashboard_raw.csv")
monthly_csv_path = os.path.join(OUT_DIR, "bcb_dashboard_monthly.csv")

# Save raw (daily/irregular) data
df.to_csv(raw_csv_path, index_label="date")
print(f"Saved raw data to: {raw_csv_path}")

# Monthly data (end of month)
df_m = df.resample("ME").last()
df_m.to_csv(monthly_csv_path, index_label="date")
print(f"Saved monthly data to: {monthly_csv_path}")

# df_m: monthly DataFrame with all series, columns are SERIES labels
# We need at least "Selic Diária" and "IPCA" for get_idx1_idx2/bcb_align
bcb_subset_cols = [col for col in df_m.columns if col in ["Selic Diária", "IPCA"]]
bcb_subset = df_m[bcb_subset_cols].copy()

# Save in the folder get_idx1_idx2 expects:
# fileloc.bacen_downloaded_data_folder / "BCB_IPCA_SELIC.csv"
from core.constants import file_locations
from core.my_data_types import load_file_locations_dict

fileloc = load_file_locations_dict(file_locations)
bcb_folder = fileloc.bacen_downloaded_data_folder

os.makedirs(bcb_folder, exist_ok=True)
bcb_ipca_selic_path = os.path.join(bcb_folder, "BCB_IPCA_SELIC.csv")
bcb_subset.to_csv(bcb_ipca_selic_path, index_label="date")
print(f"Saved BCB_IPCA_SELIC.csv to: {bcb_ipca_selic_path}")

# -----------------------------
# Plotting dashboard (multi-panel)
# -----------------------------
plt.style.use("seaborn-v0_8-darkgrid")

n_series = len(df_m.columns)
n_rows = (n_series + 1) // 2  # 2 columns per row

fig, axes = plt.subplots(n_rows, 2, figsize=(18, 2.0 * n_rows), sharex=False)
axes = axes.flatten() if n_series > 1 else [axes]

for ax, col in zip(axes, df_m.columns):
    ax.plot(df_m.index, df_m[col], label=col)
    ax.set_title(col, fontsize=10)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, alpha=0.3)

# Hide unused axes if any
for j in range(n_series, len(axes)):
    fig.delaxes(axes[j])

fig.suptitle(
    "Brazil – Selected Macroeconomic and Financial Indicators (BCB/SGS, CSV endpoint)",
    fontsize=14,
)

fig.tight_layout(rect=[0, 0.03, 1, 0.96])

# Save figure
plot_path = os.path.join(OUT_DIR, "bcb_dashboard.png")
fig.savefig(plot_path, dpi=150)
print(f"Saved dashboard plot to: {plot_path}")

# -----------------------------
# Bring in Yahoo price_data and align
# -----------------------------
from plotting.common_plot_setup import PlotSetup  # adjust import to your actual module/package

combined_daily = align_bcb_with_yahoo(df_m, price_data, price_col="Adj Close")

# -----------------------------
# Second plot: normalized series on one chart (BCB + Adj Close)
# -----------------------------
df_norm = combined_daily.copy()

for col in df_norm.columns:
    series = df_norm[col].dropna()
    if series.empty:
        df_norm[col] = pd.NA
        continue

    base = series.iloc[0]
    if base == 0 or pd.isna(base):
        df_norm[col] = pd.NA
    else:
        df_norm[col] = (df_norm[col] / base) * 100.0

# Optionally drop columns that could not be normalized
df_norm = df_norm.dropna(axis=1, how="all")

plt.style.use("seaborn-v0_8-darkgrid")  # keep same style

fig2, ax2 = plt.subplots(figsize=(18, 8))

for col in df_norm.columns:
    ax2.plot(df_norm.index, df_norm[col], label=col)

ax2.set_title("Normalized indicators + Adj Close (index = 100 at series start)",
              fontsize=14)
ax2.set_ylabel("Index (start = 100)")
ax2.tick_params(axis="x", rotation=30)

# Turn on both horizontal and vertical grid lines
ax2.grid(True, which="both", axis="both", alpha=0.4)

# If there are many series, make the legend outside the plot
ax2.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=8)

fig2.tight_layout(rect=[0, 0.03, 0.80, 0.96])

# Save normalized plot
norm_plot_path = os.path.join(OUT_DIR, "bcb_dashboard_normalized_with_yahoo.png")
fig2.savefig(norm_plot_path, dpi=150)
print(f"Saved normalized dashboard plot (with Yahoo) to: {norm_plot_path}")

plt.show()