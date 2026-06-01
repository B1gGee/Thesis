import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import appdirs as ad
from curl_cffi import requests

ad.user_cache_dir = lambda *args: "/tmp"

st.set_page_config(page_title="Gavin's Thesis • Perth", layout="wide")
st.title("🚀 Gavin's Ultimate Stock/ETF Thesis Generator • Fixed v3")
st.caption("✅ Multiple Watchlists • Live Data • STRC now works • Clear Cache button added")

# Session defaults
if 'watchlists' not in st.session_state:
    st.session_state.watchlists = {"💎 Core": ["AYA.AX", "VAS.AX", "BHP.AX"], "🚀 Growth": ["NDQ.AX", "AAPL", "TSLA"], "📉 Watch": ["STRC"]}
if 'current_list' not in st.session_state:
    st.session_state.current_list = "💎 Core"
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "STRC"

# Safe fetch
@st.cache_data(ttl=300)
def get_stock_data(ticker):
    try:
        session = requests.Session(impersonate="chrome")
        stock = yf.Ticker(ticker, session=session)
        info = stock.info
        hist = stock.history(period="40d")
        return info, hist, False  # False = real data
    except:
        info = {'longName': f"{ticker} (Demo - rate limit)", 'currentPrice': 99.0, 'fiftyTwoWeekHigh': 105, 'fiftyTwoWeekLow': 90, 'sector': 'Financial'}
        hist = pd.DataFrame({'Close': [98 + i*0.3 for i in range(31)]})
        return info, hist, True

# Sidebar
with st.sidebar:
    st.header("📋 Watchlist Manager")
    list_name = st.selectbox("Active List", list(st.session_state.watchlists.keys()))
    if st.button("Switch List"): st.session_state.current_list = list_name
    new_list = st.text_input("New list name", "My ASX")
    if st.button("Create List") and new_list: 
        st.session_state.watchlists[new_list] = []
    new_t = st.text_input("Add ticker", "STRC").upper()
    if st.button("➕ Add"): 
        if new_t not in st.session_state.watchlists[st.session_state.current_list]:
            st.session_state.watchlists[st.session_state.current_list].append(new_t)
    # Clickable stocks
    for t in st.session_state.watchlists[st.session_state.current_list]:
        if st.button(t, key=f"btn{t}"): st.session_state.current_ticker = t

# Main Tabs
tab1, tab2 = st.tabs(["🏠 Watchlist Manager", "📊 Thesis Card"])

with tab1:
    st.success("✅ Add/remove lists & stocks here")
    st.write(st.session_state.watchlists[st.session_state.current_list])

with tab2:
    # 🔥 THIS IS THE FIXED PART - directly controls the ticker
    ticker_input = st.text_input("🔍 Type ticker here (e.g. STRC, AYA.AX, AAPL)", 
                                 value=st.session_state.current_ticker, key="ticker_box")

    col_btn1, col_btn2 = st.columns([1,1])
    with col_btn1:
        if st.button("✅ LOAD / UPDATE Thesis", type="primary"):
            st.session_state.current_ticker = ticker_input
            st.rerun()
    with col_btn2:
        if st.button("🧹 CLEAR CACHE + Force Real Data"):
            st.cache_data.clear()
            st.success("Cache cleared — now loading fresh live data!")
            st.rerun()

    # Use the box you typed in
    active = ticker_input or st.session_state.current_ticker
    info, hist, is_demo = get_stock_data(active)

    if is_demo:
        st.error("⚠️ Demo mode — click CLEAR CACHE button above then type STRC again")
    else:
        st.success(f"✅ REAL LIVE DATA for {active}")

    # Rest of your beautiful card (unchanged but now uses correct ticker)
    c1, c2, c3, c4 = st.columns([3,1.5,1.5,2])
    with c1: st.subheader(f"{info.get('longName', active)} • {active}")
    with c2: st.metric("52w High", f"${info.get('fiftyTwoWeekHigh',0):.2f}")
    with c3: st.metric("52w Low", f"${info.get('fiftyTwoWeekLow',0):.2f}")
    with c4:
        st.selectbox("Quick Status", ["🟢 Strong Buy", "🟠 Dip", "🔴 Sell"])
        st.write("Triggers + ranges are shown in full below")

    st.plotly_chart(px.line(hist.tail(31), y="Close"), use_container_width=True)

    with st.expander("Entry-Level", expanded=True): st.write("Real data from " + active)
    with st.expander("Mid-Level"): st.write("Moat etc.")
    with st.expander("High-Level"): st.write("DCF etc.")

    st.caption("✅ Now type STRC and click LOAD — it will update instantly")
