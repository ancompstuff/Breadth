import yfinance as yf

df = yf.download("^BVSP", start="2020-01-01")
print(df.head())
print(df.empty)