
import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

# -------------------------------
# Helper functions
# -------------------------------
def fetch_data(symbol, days):
    data = yf.download(symbol, period=f"{days}d", interval="1d")
    return data['Close'].dropna()

def normalize(series):
    if series.empty:
        return series
    min_v = series.min().item()
    max_v = series.max().item()
    if max_v == min_v:
        return series * 0 + 0.5
    return (series - min_v) / (max_v - min_v)

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("📈 NIFTY & BANKNIFTY Tracker")

# Sidebar controls
days = st.sidebar.selectbox("Select period (days)", [30, 90, 180, 365], index=1)
normalize_opt = st.sidebar.checkbox("Normalize values (0–1 scale)", value=True)
reverse_opt = st.sidebar.checkbox("Reverse time (latest → oldest)", value=True)
index_choice = st.sidebar.multiselect(
    "Select Indices",
    ["NIFTY", "BANKNIFTY"],
    default=["NIFTY", "BANKNIFTY"]
)

# -------------------------------
# Fetch & prepare data
# -------------------------------
data_dict = {}
if "NIFTY" in index_choice:
    data_dict["NIFTY"] = fetch_data("^NSEI", days)
if "BANKNIFTY" in index_choice:
    data_dict["BANKNIFTY"] = fetch_data("^NSEBANK", days)

# If nothing selected
if not data_dict:
    st.warning("⚠️ Please select at least one index from the sidebar.")
    st.stop()

# Align on common dates if both selected
if len(data_dict) > 1:
    common_dates = set.intersection(*(set(v.index) for v in data_dict.values()))
    for k in data_dict:
        data_dict[k] = data_dict[k].loc[sorted(common_dates)]

# Apply normalization
if normalize_opt:
    for k in data_dict:
        data_dict[k] = normalize(data_dict[k])

# Reverse if selected
if reverse_opt:
    for k in data_dict:
        data_dict[k] = data_dict[k].iloc[::-1]

# -------------------------------
# Plot
# -------------------------------
fig, ax = plt.subplots(figsize=(12, 6))

for label, series in data_dict.items():
    ax.plot(series.index, series, label=label, marker="o")
    
    # Highlight latest value
    latest_date = series.index[0]  # newest (first if reversed)
    latest_val = float(series.iloc[0])  # force float
    ax.scatter(latest_date, latest_val, color='red', s=100, zorder=5)
    ax.annotate(f"{latest_val:.2f}", (latest_date, latest_val),
                textcoords="offset points", xytext=(0,10),
                ha='center', color='red', fontweight='bold')

ax.set_title(f"NIFTY / BANKNIFTY - Last {days} Days")
ax.set_xlabel("Date")
ax.set_ylabel("Normalized Value (0–1)" if normalize_opt else "Closing Price")
ax.legend()
plt.xticks(rotation=45)
st.pyplot(fig)
# -------------------------------
# Data Preview
# -------------------------------

st.subheader("📊 Data Preview")

if data_dict:
    df = pd.concat(data_dict.values(), axis=1)
    df.columns = list(data_dict.keys())

    # Highlight latest row
    def highlight_latest(row):
        if row.name == df.index[0]:  # first row is latest
            return ['background-color: yellow']*len(row)
        else:
            return ['']*len(row)

    st.dataframe(df.style.apply(highlight_latest, axis=1))

    # Download button
    csv = df.to_csv().encode("utf-8")
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"nifty_banknifty_{days}d.csv",
        mime="text/csv",
    )
else:
    st.warning("⚠️ No data available to display.")
