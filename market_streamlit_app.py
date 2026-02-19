import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Index Open vs High", layout="wide")

st.title("Live Index Open (Yahoo Finance)")
st.write("Simple dashboard comparing today's **open**, **high**, and **low** for major indices.")

# Define indices
indices = {
    "^NSEI": "Nifty 50 (India)",
    "^NSEBANK": "BankNift (India)",
    "^BSESN": "Sensex (India)",
}

@st.cache_data(ttl=60)
def get_data(symbols):
    rows = []
    for sym, name in symbols.items():
        ticker = yf.Ticker(sym)
        info = ticker.info  # has regularMarketOpen/High/Low for live session[web:36][web:40]
        open_price = info.get("regularMarketOpen")
        high_price = info.get("regularMarketDayHigh")
        low_price = info.get("regularMarketDayLow")
        if open_price is not None and high_price is not None and low_price is not None:
            gain = high_price - open_price
            pct_gain = (gain / open_price) * 100 if open_price != 0 else None
            rows.append({
                "Index": f"{name} ({sym})",
                "Open": open_price,
                "High": high_price,
                "Low": low_price,
                "Gain (High - Open)": gain,
                "% Gain": pct_gain,
            })
        else:
            rows.append({
                "Index": f"{name} ({sym})",
                "Open": None,
                "High": None,
                "Low": None,
                "Gain (High - Open)": None,
                "% Gain": None,
            })
    return pd.DataFrame(rows)

refresh = st.button("Refresh now")

df = get_data(indices)

if refresh:
    get_data.clear()
    df = get_data(indices)

st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def color_gain(val):
    if pd.isna(val):
        return ""
    color = "green" if val > 0 else "red"
    return f"color: {color}; font-weight: bold;"  # style rule for positive/negative[web:43][web:45]

styled = (
    df.style
    .format({
        "Open": "{:.2f}",
        "High": "{:.2f}",
        "Low": "{:.2f}",
        "Gain (High - Open)": "{:.2f}",
        "% Gain": "{:.2f}",
    })
    .applymap(color_gain, subset=["Gain (High - Open)", "% Gain"])
)

st.dataframe(styled, use_container_width=True)

# Simple stats
valid = df.dropna(subset=["Gain (High - Open)"])
if not valid.empty:
    avg_gain = valid["Gain (High - Open)"].mean()
    st.write(f"Average gain across indices: {avg_gain:.2f}")
else:
    st.write("No valid data available right now.")
