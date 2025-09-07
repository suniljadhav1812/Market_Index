# 📈 NIFTY & BANKNIFTY Tracker – Streamlit App

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.0-orange)](https://streamlit.io/)

A **Streamlit dashboard** to track and visualize **NIFTY 50** and **BANKNIFTY** index values. Users can select the number of days, apply normalization, reverse the timeline, and highlight the latest values. The app also provides a data table with a CSV download option.

---

## 📝 Features

- Select **NIFTY**, **BANKNIFTY**, or **both** indices.  
- Choose the **period**: 30, 90, 180, or 365 days.  
- Toggle **Normalization** (0–1 scale) on/off.  
- Toggle **Reverse Time** (latest → oldest).  
- Highlight the **latest value** on the chart and in the data table.  
- **Download CSV** of the displayed data.  
- Interactive Matplotlib chart embedded in Streamlit.

---

## ⚡ Requirements

- Python 3.9+
- Streamlit
- yfinance
- matplotlib
- pandas

Install dependencies via pip:

```bash
pip install streamlit yfinance matplotlib pandas
