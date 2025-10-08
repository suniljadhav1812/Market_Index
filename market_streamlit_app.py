import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import timedelta

# -------------------------------
# Helper functions
# -------------------------------
def fetch_data(symbol, days):
    data = yf.download(symbol, period=f"{days}d", interval="1d")
    return data['Close'].dropna()

def fit_trend_line(dates, values, forecast_days):
    # Convert dates to numeric values (days since start)
    x = np.arange(len(dates))
    # Fit a linear trend line
    coeffs = np.polyfit(x, values, 1)  # Linear fit (degree 1)
    trend_line = np.polyval(coeffs, x)
    # Extend for forecast
    x_future = np.arange(len(dates) + forecast_days)
    trend_future = np.polyval(coeffs, x_future)
    return x, trend_line, x_future, trend_future

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("📈 NIFTY / BANKNIFTY Tracker")

# Sidebar controls
index_choice = st.sidebar.radio(
    "Select Index",
    ["NIFTY", "BANKNIFTY"],
    index=0
)
days = st.sidebar.selectbox("Select period (days)", [30, 90, 180, 365], index=3)
forecast_days = st.sidebar.number_input("Forecast days into future", min_value=1, max_value=30, value=5, step=1)

# -------------------------------
# Fetch & prepare data
# -------------------------------
symbol = "^NSEI" if index_choice == "NIFTY" else "^NSEBANK"
data = fetch_data(symbol, days)

if data.empty:
    st.warning(f"⚠️ No data available for {index_choice}.")
    st.stop()

# Reverse data (latest to oldest)
data = data.iloc[::-1]

# Convert index to datetime if not already
dates = pd.to_datetime(data.index)

# -------------------------------
# Plot
# -------------------------------
fig, ax = plt.subplots(figsize=(12, 6))

# Plot actual data
ax.plot(dates, data, label=index_choice, marker="o", color="blue")

# Highlight current (latest) value
latest_date = dates[0]
latest_val = float(data.iloc[0])
ax.scatter(latest_date, latest_val, color='red', s=100, zorder=5)
ax.annotate(f"{latest_val:.2f}", (latest_date, latest_val),
            textcoords="offset points", xytext=(0, 10),
            ha='center', color='red', fontweight='bold')

# Fit and plot trend line with forecast
x, trend_line, x_future, trend_future = fit_trend_line(dates, data, forecast_days)

# Extend dates for forecast
future_dates = [dates[0] + timedelta(days=i) for i in range(len(dates), len(dates) + forecast_days)]
all_dates = list(dates) + future_dates

# Plot trend line (past data)
ax.plot(dates, trend_line, label="Trend Line", color="green", linestyle="--")

# Plot forecasted trend
ax.plot(all_dates, trend_future, label=f"{forecast_days}-Day Forecast", color="orange", linestyle="--")

ax.set_title(f"{index_choice} - Last {days} Days with {forecast_days}-Day Forecast")
ax.set_xlabel("Date")
ax.set_ylabel("Closing Price")
ax.legend()
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig)

# -------------------------------
# Data Preview
# -------------------------------
st.subheader("📊 Data Preview")

# Prepare DataFrame
df = pd.DataFrame({index_choice: data})

# Highlight latest row
def highlight_latest(row):
    if row.name == df.index[0]:
        return ['background-color: yellow'] * len(row)
    return [''] * len(row)

st.dataframe(df.style.apply(highlight_latest, axis=1))

# Add forecasted values to DataFrame
forecast_df = pd.DataFrame({
    index_choice: trend_future[-forecast_days:],
    "Type": ["Forecast"] * forecast_days
}, index=future_dates)
df["Type"] = "Actual"
combined_df = pd.concat([df, forecast_df])

st.subheader(f"📅 Forecasted Values (Next {forecast_days} Days)")
st.dataframe(forecast_df[[index_choice]])

# Download button
csv = combined_df.to_csv().encode("utf-8")
st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name=f"{index_choice.lower()}_{days}d_with_forecast.csv",
    mime="text/csv",
)
