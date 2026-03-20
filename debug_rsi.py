#!/usr/bin/env python
import yfinance as yf
import pandas as pd
import numpy as np

ticker = 'MSFT'
period = 14

print(f"Testing RSI calculation for {ticker}...")
data = yf.download(ticker, period="3mo", progress=False)
print(f"Data shape: {data.shape}")
print(f"Data columns: {data.columns.tolist()}")

if len(data) < period:
    print(f"Insufficient data: {len(data)} < {period}")
else:
    print(f"Data length OK: {len(data)} >= {period}")
    
    # Calculate RSI
    delta = data["Close"].diff()
    print(f"\nDelta shape: {delta.shape}")
    print(f"Delta type: {type(delta)}")
    
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    print(f"Gain shape: {gain.shape}")
    print(f"Loss shape: {loss.shape}")
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    print(f"\nRSI shape: {rsi.shape}")
    print(f"RSI values (last 5):\n{rsi.tail()}")
    
    # Try to extract last value
    last_rsi = rsi.iloc[-1]
    print(f"\nLast RSI value type: {type(last_rsi)}")
    print(f"Last RSI value: {last_rsi}")
    print(f"Is NaN?: {pd.isna(last_rsi)}")
    
    # Try dropna approach
    rsi_dropna = rsi.dropna()
    print(f"\nAfter dropna - length: {len(rsi_dropna)}")
    if len(rsi_dropna) > 0:
        last_valid = rsi_dropna.iloc[-1]
        print(f"Last valid RSI: {last_valid}")
        print(f"Type: {type(last_valid)}")
        print(f"Float conversion: {float(last_valid)}")
