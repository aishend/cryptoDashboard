import pandas as pd
from binance.client import Client
import mplfinance as mpf
import os
from datetime import datetime
import time
import math # For checking NaN

# --- Configuration ---
# It's recommended to use environment variables or a .env file for API keys
# Install python-dotenv: pip install python-dotenv
from dotenv import load_dotenv
load_dotenv()

# Replace with your actual API Key and Secret (or leave empty if only fetching public data)
# Using environment variables is safer than hardcoding
api_key = os.getenv("BINANCE_API_KEY", "IiPTCvu1AAziLvdusHHkCus5NCpwU0mQ0vMcZnRLwZeFNCA3ODdEIgHYLrDsPYij")
api_secret = os.getenv("BINANCE_API_SECRET", "sUdrgJMQ15FceuPSLjc5NkKY951iWTUvBJmOGUgmhPln05f3jHHEBfnKPuRLnEbe")

client = Client(api_key, api_secret)

symbol = 'BTCUSDT' # Trading pair
interval = Client.KLINE_INTERVAL_1HOUR # Candlestick interval (e.g., 1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
lookback_days = 30 # How many days of data to fetch

# Pivot Lengths (matching the Pine Script defaults)
leftLenH = 10
rightLenH = 10
leftLenL = 10
rightLenL = 10

# --- Data Fetching ---
def get_binance_klines(symbol, interval, start_str):
    """Fetch historical klines from Binance."""
    klines = client.get_historical_klines(symbol, interval, start_str)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    # Convert OHLCV columns to numeric
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col])
    return df

# Fetch data starting from a date
start_date = (datetime.now() - pd.Timedelta(days=lookback_days)).strftime('%d %b, %Y')
df = get_binance_klines(symbol, interval, start_date)

if df.empty:
    print("Could not fetch data.")
    exit()

print(f"Fetched {len(df)} bars for {symbol} ({interval})")

# --- Pivot Calculation Logic ---

def calculate_pivots(df, left_len, right_len, price_col='high', pivot_type='high'):
    """
    Calculates pivot points based on left and right lengths.
    Mimics Pine Script's ta.pivothigh/pivotlow logic for detection.
    """
    pivot_points = [math.nan] * len(df) # Initialize with NaN

    # The pivot is confirmed at index i if the price at i - right_len
    # is the extreme (high or low) in the window [i - right_len - left_len, i - right_len + right_len]
    # which simplifies to the window [i - left_len - right_len, i]

    # Need enough data for the initial window
    start_idx_offset = left_len + right_len

    # Iterate through the data starting from the first possible confirmation bar
    for i in range(start_idx_offset, len(df)):
        # Index of the potential pivot bar
        pivot_idx = i - right_len

        # Ensure pivot_idx is valid
        if pivot_idx < 0:
            continue

        # Define the window for checking the extremum
        window_start = max(0, pivot_idx - left_len)
        window_end = min(len(df) - 1, pivot_idx + right_len) # End index is inclusive for clarity, though slice handles it

        # Get the price data for the window
        window_data = df[price_col].iloc[window_start : window_end + 1]

        # Get the price at the potential pivot bar
        pivot_price = df[price_col].iloc[pivot_idx]

        is_pivot = False
        if pivot_type == 'high':
            # Check if the potential pivot price is the max in the window
            if pivot_price == window_data.max():
                 # Also ensure it's not a plateau (multiple bars with the same max high) - optional but common in some definitions
                 # This simple check works for distinct pivots. For plateaus, more complex logic is needed.
                 # For this basic replication, just checking the max is sufficient.
                 is_pivot = True
        elif pivot_type == 'low':
            # Check if the potential pivot price is the min in the window
            if pivot_price == window_data.min():
                 # Similar check for plateaus on lows
                 is_pivot = True

        if is_pivot:
            # Store the pivot value at the index where the pivot occurred
            pivot_points[pivot_idx] = pivot_price

    return pivot_points

# Calculate Pivot Highs and Lows
df['pivot_high'] = calculate_pivots(df, leftLenH, rightLenH, price_col='high', pivot_type='high')
df['pivot_low'] = calculate_pivots(df, leftLenL, rightLenL, price_col='low', pivot_type='low')

# --- Visualization ---

# Create addplots for the pivots
# Instead of using dropna() which causes size mismatch, keep NaNs for scatter plot
apds = [
    mpf.make_addplot(df['pivot_high'], type='scatter', marker='v', markersize=100, color='red'),
    mpf.make_addplot(df['pivot_low'], type='scatter', marker='^', markersize=100, color='green'),
]

# Plot the data
mpf.plot(df,
         type='candle',
         style='yahoo', # Choose a style (e.g., 'yahoo', 'binance', 'tradingview')
         title=f"{symbol} - {interval} with Pivot Points (L{leftLenH}/R{rightLenH} H, L{leftLenL}/R{rightLenL} L)",
         ylabel='Price',
         addplot=apds,
         figscale=1.5, # Adjust figure size
         warn_too_much_data=len(df)+100 # Silence the warning about too much data
        )

print("Plot generated.")