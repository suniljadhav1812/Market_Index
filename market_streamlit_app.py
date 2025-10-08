import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import timedelta, datetime
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename="app.log", filemode="a")
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
            return pd.Series(dtype=float)
        # Explicitly extract Close as a Series and ensure 1D
        close_data = data['Close'].dropna()
        if isinstance(close_data, pd.DataFrame):
            close_data = close_data.iloc[:, 0]  # Take first column if DataFrame
        logger.debug(f"Fetched {len(close_data)} data points for {symbol}, type: {type(close_data)}, shape: {close_data.shape}")
        return close_data
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return pd.Series(dtype=float)

def generate_dummy_data(days):
    """Generate dummy data for testing if yfinance fails."""
    logger.debug("Generating dummy data")
    dates = pd.date_range(end=datetime.now(), periods=days, freq="D")
    values = np.random.normal(10000, 1000, days)  # Random prices
    return pd.Series(values, index=dates)

def fit_trend_line(dates, values, forecast_days):
    """Fit a linear trend line and extend for forecasting."""
    try:
        x = np.arange(len(dates))
        values = np.asarray(values).flatten()  # Ensure 1D
        coeffs = np.polyfit(x, values, 1)
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
index_choice = st.sidebar.radio("Select Index", ["NIFTY", "BANKNIFTY"], index=1)
days = st.sidebar.selectbox("Select period (days)", [30, 90, 180, 365], index=1)
forecast_days = st.sidebar.number_input("Forecast days into future", min_value=1, max_value=30, value=5, step=1)
debug_mode = st.sidebar.checkbox("Enable Debug Mode", value=False)
use_dummy_data = st.sidebar.checkbox("Use Dummy Data (for testing)", value=False)

# -------------------------------
# Fetch & prepare data
# -------------------------------
symbol = "^NSEI" if index_choice == "NIFTY" else "^NSEBANK"
if use_dummy_data:
    st.warning("Using dummy data for testing.")
    data = generate_dummy_data(days)
else:
    data = fetch_data(symbol, days)

if data.empty:
    st.error(f"⚠️ No data available for {index_choice}. Try using dummy data or a different period.")
    if debug_mode:
        st.write("Debug: Data fetching failed. Check app.log for details.")
    st.stop()

# Log data details
if debug_mode:
    st.write(f"Debug: Data type: {type(data)}, Shape: {data.shape}, Index type: {type(data.index)}")
    st.write(f"Debug: First 5 data points:\n{data.head().to_string()}")

# Ensure data is a Series with datetime index
try:
    data = pd.Series(data.values.flatten(), index=pd.to_datetime(data.index))
    data = data.iloc[::-1]  # Reverse (latest to oldest)
    dates = data.index
except Exception as e:
    logger.error(f"Error processing data for {index_choice}: {str(e)}")
    st.error(f"⚠️ Error processing data for {index_choice}: {str(e)}")
    if debug_mode:
        st.write(f"Debug: Data processing failed. Error: {str(e)}")
    st.stop()

# -------------------------------
# Plot
# -------------------------------
try:
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, data, label=index_choice, marker="o", color="blue")

    # Highlight latest value
    latest_date = dates[0]
    latest_val = float(data.iloc[0])
    ax.scatter(latest_date, latest_val, color='red', s=100, zorder=5)
    ax.annotate(f"{latest_val:.2f}", (latest_date, latest_val),
                textcoords="offset points", xytext=(0, 10),
                ha='center', color='red', fontweight='bold')

    # Fit and plot trend line
    x, trend_line, x_future, trend_future = fit_trend_line(dates, data, forecast_days)
    if trend_line is None:
        st.warning("⚠️ Could not generate trend line. Displaying data only.")
    else:
        future_dates = [dates[0] + timedelta(days=i) for i in range(1, forecast_days + 1)]
        all_dates = list(dates) + future_dates
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
    df = pd.DataFrame({index_choice: data}, index=data.index)

    def highlight_latest(row):
        return ['background-color: yellow' if row.name == df.index[0] else '' for _ in row]

    st.dataframe(df.style.apply(highlight_latest, axis=1))

    if trend_future is not None:
        forecast_df = pd.DataFrame({
            index_choice: trend_future[-forecast_days:],
            "Type": ["Forecast"] * forecast_days
        }, index=future_dates)
        df["Type"] = "Actual"
        combined_df = pd.concat([df, forecast_df])

        st.subheader(f"📅 Forecasted Values (Next {forecast_days} Days)")
        st.dataframe(forecast_df[[index_choice]])

        csv = combined_df.to_csv().encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{index_choice.lower()}_{days}d_with_forecast.csv",
            mime="text/csv",
        )
    else:
        st.warning("⚠️ Forecast data not available.")
except Exception as e:
    logger.error(f"Error generating data preview: {str(e)}")
    st.error(f"⚠️ Error generating data preview: {str(e)}")
    if debug_mode:
        st.write(f"Debug: Data preview failed. Error: {str(e)}")

# Show logs in debug mode
if debug_mode:
    st.subheader("Debug Logs")
    try:
        with open("app.log", "r") as log_file:
            st.text(log_file.read())
    except FileNotFoundError:
        st.write("Debug: Log file not found.")
