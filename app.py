import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
import openpyxl
from openpyxl.styles import PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from io import BytesIO
import time

st.set_page_config(page_title="Stock Thesis Monitor", layout="wide", page_icon="📈")

st.markdown("""
<style>
.status-strongbuy { color: #28a745; font-size: 1.8em; font-weight: 800; }
.status-hold      { color: #ffc107; font-size: 1.8em; font-weight: 800; }
.status-monitor   { color: #17a2b8; font-size: 1.8em; font-weight: 800; }
.status-sell      { color: #dc3545; font-size: 1.8em; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Stock Thesis Monitor")
st.caption("Automated thesis builder • Entry / Mid / High Level • Custom triggers • GitHub-ready")

# ====================== API KEYS ======================
st.sidebar.header("🔑 API Keys (pre-filled)")
fmp_key = st.sidebar.text_input("FMP API Key", value="KoegUYuz7Ig5PiZNhen3I2byMyf6elWz", type="password")
alpha_key = st.sidebar.text_input("Alpha Vantage API Key", value="US6OIYAJTOK8CXX7", type="password")

# Show FMP remaining calls
if fmp_key:
    try:
        usage = requests.get(f"https://financialmodelingprep.com/api/v3/usage?apikey={fmp_key}", timeout=10).json()
        remaining = usage.get('dailyLimit', 250) - usage.get('dailyUsage', 0)
        st.sidebar.success(f"**FMP calls left today: {remaining}**")
    except:
        st.sidebar.info("FMP remaining calls: (could not fetch)")

ticker = st.sidebar.text_input("Enter Ticker (e.g. AAPL, TSLA, BHP.AX)", value="AAPL").upper().strip()

if st.sidebar.button("Generate Thesis"):
    with st.spinner(f"Fetching data for {ticker}..."):
        info = None
        source = "None"
        stock = None

        # 1. Yahoo Finance (fast but often rate-limited)
        for attempt in range(3):
            try:
                session = requests.Session()
                session.headers.update({'User-Agent': 'Mozilla/5.0'})
                stock = yf.Ticker(ticker, session=session)
                info = stock.info
                source = "Yahoo Finance"
                st.success("✅ Loaded from Yahoo Finance")
                break
            except:
                time.sleep(2)

        # 2. FMP - Primary reliable source
        if not info and fmp_key:
            try:
                profile = requests.get(f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={fmp_key}", timeout=10).json()
                quote = requests.get(f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}", timeout=10).json()
                if isinstance(profile, list) and len(profile) > 0:
                    p = profile[0]
                    q = quote[0] if isinstance(quote, list) and len(quote) > 0 else {}
                    info = {
                        'longName': p.get('companyName'),
                        'sector': p.get('sector'),
                        'industry': p.get('industry'),
                        'longBusinessSummary': p.get('description'),
                        'currentPrice': q.get('price'),
                        'marketCap': q.get('marketCap'),
                        'fiftyTwoWeekHigh': q.get('yearHigh'),
                        'fiftyTwoWeekLow': q.get('yearLow'),
                        'forwardPE': p.get('forwardPE'),
                        'earningsGrowth': p.get('earningsGrowth'),
                        'revenueGrowth': p.get('revenueGrowth'),
                        'dividendYield': p.get('dividendYield'),
                        'returnOnEquity': p.get('roe'),
                        'debtToEquity': p.get('debtToEquity'),
                        'freeCashflow': q.get('freeCashFlow'),
                        'heldPercentInsiders': p.get('heldPercentInsiders'),
                        'targetMeanPrice': p.get('targetPrice'),
                        'recommendationKey': p.get('recommendation'),
                        'regularMarketChangePercent': q.get('changePercent'),
                    }
                    source = "Financial Modeling Prep (FMP)"
                    st.success("✅ Loaded from FMP (primary backup)")
            except Exception as e:
                st.warning(f
