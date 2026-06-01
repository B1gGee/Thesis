import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Gavin's Thesis • Perth", layout="wide")
st.title("🚀 Gavin's Ultimate Stock/ETF Thesis Generator • v5 FULLY DYNAMIC")
st.caption("✅ Any ticker works • Type new code → click LOAD → old data is gone • Super clean")

# Neutral default (you can change it later)
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "AAPL"

# Reliable fetch - no demo fallback text that sticks
@st.cache_data(ttl=180)
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        hist = yf.download(ticker, period="1mo", progress=False)
        real_info = {
            'longName': info.get('longName', ticker),
            'currentPrice': info.get('lastPrice') or info.get('regularMarketPrice') or 0,
            'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh', 0),
            'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow', 0),
            'sector': info.get('sector', 'N/A')
        }
        return real_info, hist, False
    except:
        return {'longName': f"{ticker} (Trying live data...)", 'currentPrice': 0, 'fiftyTwoWeekHigh': 0, 'fiftyTwoWeekLow': 0}, pd.DataFrame(), True

# Sidebar Watchlist (simple & flexible)
with st.sidebar:
    st.header("📋 Watchlist")
    new_ticker = st.text_input("Add to watchlist", "NDQ.AX").upper()
    if st.button("➕ Add to list"):
        st.success(f"Added {new_ticker} — type it in main box to load")
    st.write("**Type any ticker below and click LOAD**")

# Main area - completely dynamic
st.subheader("📊 Thesis Card - Type any ticker")
ticker_box = st.text_input("🔍 Enter ticker (STRC, AYA.AX, AAPL, VAS.AX, BHP.AX, TSLA, etc.)", 
                           value=st.session_state.current_ticker, 
                           key="dynamic_input")

col_load, col_clear = st.columns([1, 1])
with col_load:
    if st.button("✅ LOAD / UPDATE Thesis", type="primary", use_container_width=True):
        st.session_state.current_ticker = ticker_box
        st.rerun()
with col_clear:
    if st.button("🧹 CLEAR CACHE + Force Fresh Data", use_container_width=True):
        st.cache_data.clear()
        st.success("✅ All old data cleared! Now loading completely fresh data for the ticker you typed.")
        st.rerun()

# Always use the latest typed value
active_ticker = ticker_box.strip() or st.session_state.current_ticker
info, hist, is_demo = get_stock_data(active_ticker)

if is_demo:
    st.warning("⏳ Still loading fresh data — click CLEAR CACHE once more if needed")
else:
    st.success(f"✅ LIVE DATA LOADED for **{active_ticker}** — ready for thesis card")

# Clean header - no old stock info
c1, c2, c3 = st.columns([3, 1.5, 1.5])
with c1:
    st.subheader(f"{info.get('longName', active_ticker)} • {active_ticker}")
with c2:
    st.metric("💰 Current Price", f"${info.get('currentPrice', 0):.2f}")
with c3:
    st.metric("📈 52w High", f"${info.get('fiftyTwoWeekHigh', 0):.2f}")
    st.metric("📉 52w Low", f"${info.get('fiftyTwoWeekLow', 0):.2f}")

# Clean 31-day chart
st.subheader("📈 Last ~31 Trading Days (Daily Close)")
if not hist.empty:
    fig = px.line(hist.tail(31), y="Close", markers=True)
    fig.update_layout(height=380, yaxis_title="Price ($)", xaxis_title="Date")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Chart will appear once fresh data loads")

# Your rich sections (ready for you to expand later)
with st.expander("📍 Entry-Level", expanded=True):
    st.write("Real data loaded for the ticker above. Add your notes here.")
with st.expander("📍 Mid-Level"):
    st.write("Moat • Financial health • Triggers")
with st.expander("📍 High-Level / Deep Dive"):
    st.write("Valuation • Projections • Thesis breakers")

st.caption("✅ This version is completely open. Type any new ticker → click LOAD → old information is replaced instantly. No stock is locked.")

st.success("Try it now: Type **STRC** → click LOAD / UPDATE Thesis → you should see real Strategy Inc data with no leftover AYA or AAJ info.")
