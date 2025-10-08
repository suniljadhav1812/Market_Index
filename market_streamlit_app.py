import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import timedelta
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# -------------------------------
# Helper functions
# -------------------------------
def fetch_data(symbol, days):
    """Fetch historical closing prices for the given symbol and period."""
    try:
        logger.debug(f"Fetching data for {symbol} over {days} days")
        data = yf.download(symbol, period=f"{days}d", interval="1d")
        if data.empty:
            logger.error(f"No data returned for {symbol}")
            return pd.Series()
        close_data = data['Close'].dropna()
        logger.debug(f"Fetched {len(close_data)} data points for {symbol}")
        return close_data
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return pd.Series()

def fit_trend_line(dates, values, forecast_days):
    """Fit a linear trend line and extend for forecasting."""
    try:
        x = np.arange(len(dates))
        coeffs = np.polyfit(x, values, 1)  # Linear fit
        trend_line = np.polyval(coeffs, x)
        x_future = np.arange(len(dates) + forecast_days)
        trend_future = np.polyval(coeffs, x_future)
        return x, trend_line, x_future, trend_future
    except Exception as e:
        logger.error(f"Error fitting trend line: {str(e)}")
        return None, None, None, None

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

# Debug mode toggle
debug_mode = st.sidebar.checkbox("Enable Debug Mode", value=False)

# -------------------------------
# Fetch & prepare data
# -------------------------------
symbol = "^NSEI" if index_choice == "NIFTY" else "^NSEBANK"
data = fetch_data(symbol, days)

if data.empty:
    st.error(f"⚠️ No data available for {index_choice}. Please try a different index or period.")
    if debug_mode:
        st.write("Debug: Data fetching failed. Check logs for details.")
    st.stop()

# Ensure data is a Pandas Series with a datetime index
try:
    data = pd.Series(data.values, index=pd.to_datetime(data.index))
    data = data.iloc[::-1]  # Reverse (latest to oldest)
    dates = data.index
except Exception as e:
    logger.error(f"Error processing data: {str(e)}")
    st.error(f"⚠️ Error processing data for {index_choice}: {str(e)}")
    if debug_mode:
        st.write(f"Debug: Data processing failed. Error: {str(e)}")
    st.stop()

# -------------------------------
# Plot
# -------------------------------
try:
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
    if trend_line is None:
        st.warning("⚠️ Could not generate trend line. Displaying data without forecast.")
    else:
        # Extend dates for forecast
        future_dates = [dates[0] + timedelta(days=i) for i in range(1, forecast_days + 1)]
        all_dates = list(dates) + future_dates

        # Plot trend line (past) and forecast
        ax.plot(dates, trend_line, label="Trend Line", color="green", linestyle="--")
        ax.plot(all_dates, trend_future, label=f"{forecast_days}-Day Forecast", color="orange", linestyle="--")

    ax.set_title(f"{index_choice} - Last {days} Days with {forecast_days}-Day Forecast")
    ax.set_xlabel("Date")
    ax.set_ylabel("Closing Price")
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
except Exception as e:
    logger.error(f"Error plotting data: {str(e)}")
    st.error(f"⚠️ Error generating plot: {str(e)}")
    if debug_mode:
        st.write(f"Debug: Plotting failed. Error: {str(e)}")
    st.stop()

# -------------------------------
# Data Preview
# -------------------------------
st.subheader("📊 Data Preview")

try:
    # Create DataFrame with explicit index
    df = pd.DataFrame({index_choice: data.values}, index=data.index)

    # Highlight latest row
    def highlight_latest(row):
        return ['background-color: yellow' if row.name == df.index[0] else '' for _ in row]

    st.dataframe(df.style.apply(highlight_latest, axis=1))

    # Forecasted values DataFrame
    if trend_future is not None:
        forecast_df = pd.DataFrame({
            index_choice: trend_future[-forecast_days:],
            "Type": ["Forecast"] * forecast_days
        }, index=future_dates)

        # Combined DataFrame for download
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
    else:
        st.warning("⚠️ Forecast data not available for download.")
except Exception as e:
    logger.error(f"Error generating data preview: {str(e)}")
    st.error(f"⚠️ Error generating data preview: {str(e)}")
    if debug_mode:
        st.write(f"Debug: Data preview failed. Error: {str(e)}")

# Display logs if debug mode is enabled
if debug_mode:
    st.subheader("Debug Logs")
    with open("logfile.log", "r") as log_file:
        st.text(log_file.read())
