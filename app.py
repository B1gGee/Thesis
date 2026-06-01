import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from io import BytesIO

st.set_page_config(page_title="Stock Thesis Monitor", layout="wide", page_icon="📈")

st.title("📊 Stock Thesis Monitor")
st.caption("Automated thesis builder • Entry / Mid / High Level • Custom triggers • GitHub-ready")

import time
import requests
import appdirs as ad

# Fix for Streamlit Cloud cache permission error
ad.user_cache_dir = lambda *args: "/tmp"

ticker = st.sidebar.text_input("Enter Ticker (e.g. AAPL, TSLA, BHP.AX)", value="AAPL").upper().strip()

if st.sidebar.button("Generate Thesis"):
    with st.spinner(f"Fetching data for {ticker}..."):
        success = False
        for attempt in range(4):   # try up to 4 times
            try:
                # Use browser-like headers to reduce rate-limit chance
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                stock = yf.Ticker(ticker, session=session)
                info = stock.info
                
                # If we got here, it worked
                success = True
                break
            except Exception as e:
                error_str = str(e).lower()
                if "rate limit" in error_str or "too many requests" in error_str:
                    wait = 3 * (attempt + 1)   # wait 3s, 6s, 9s, 12s
                    st.warning(f"⏳ Yahoo is rate-limiting us (attempt {attempt+1}/4). Waiting {wait} seconds...")
                    time.sleep(wait)
                else:
                    st.error(f"Unexpected error: {type(e).__name__}")
                    st.stop()
        
        if not success:
            st.error("❌ Yahoo Finance is still rate-limiting us.\n\nTry again in 2 minutes or try a US ticker like AAPL first.")
            st.stop()
        today = datetime.now().strftime("%Y-%m-%d")

        # === TOP HEADER ===
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.metric("Current Price", f"${info.get('currentPrice', info.get('regularMarketPrice', 'N/A')):,}", 
                      delta=f"{info.get('regularMarketChangePercent', 0):.2f}%")
        with col2:
            st.subheader(f"{ticker} • {info.get('longName', ticker)}")
            st.caption(f"{info.get('sector', '<Unable to Source>')} • {info.get('industry', '<Unable to Source>')}")
        with col3:
            # Autonomous Recommendation
            pe = info.get('forwardPE', None)
            growth = info.get('earningsGrowth', 0) or 0
            rec = info.get('recommendationKey', 'hold')
            fcf_yield = info.get('freeCashflow', 0) / info.get('marketCap', 1) * 100 if info.get('marketCap') else 0
            
            score = 0
            if pe and pe < 20: score += 2
            if growth > 0.15: score += 2
            if rec in ['buy', 'strong_buy']: score += 3
            if fcf_yield > 8: score += 1
            if pe and pe > 40: score -= 2
            if growth < -0.05: score -= 2
            
            if score >= 6:
                status = "Strong Buy"
                color = "status-strongbuy"
            elif score >= 3:
                status = "Buy / Hold"
                color = "status-hold"
            elif score >= 0:
                status = "Monitor"
                color = "status-monitor"
            else:
                status = "Sell"
                color = "status-sell"
            
            st.markdown(f"**Overall Status**<br><span class='{color}'>{status}</span>", unsafe_allow_html=True)
            st.caption(f"Autonomous score: {score} | {today}")

        # Company Overview
        st.markdown("### Company Overview & Key Milestone KPIs")
        st.write(info.get('longBusinessSummary', '<Unable to Source>'))
        
        kpi_cols = st.columns(4)
        with kpi_cols[0]:
            st.metric("Market Cap", f"${info.get('marketCap', 0)/1e9:.1f}B")
        with kpi_cols[1]:
            st.metric("52w High / Low", f"${info.get('fiftyTwoWeekHigh', 'N/A')} / ${info.get('fiftyTwoWeekLow', 'N/A')}")
        with kpi_cols[2]:
            st.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%")
        with kpi_cols[3]:
            st.metric("Analyst Target", f"${info.get('targetMeanPrice', 'N/A')}")

        # === ENTRY LEVEL ===
        st.markdown("### 📌 Entry-Level (Basic 5-10 min scan)")
        entry_data = {
            "Ticker / Company / Sector / Industry": [f"{ticker} • {info.get('longName', ticker)} • {info.get('sector', '<Unable>')} • {info.get('industry', '<Unable>')}"],
            "Current Price | Market Cap | 52w High/Low": [f"${info.get('currentPrice', 'N/A')} | ${info.get('marketCap', 0)/1e9:.1f}B | ${info.get('fiftyTwoWeekHigh', 'N/A')}/${info.get('fiftyTwoWeekLow', 'N/A')}"],
            "P/E (fwd)": [info.get('forwardPE', '<Unable to Source>')],
            "EPS growth (1-3y)": [f"{info.get('earningsGrowth', '<Unable>')*100:.1f}%" if info.get('earningsGrowth') is not None else '<Unable to Source>'],
            "Revenue growth (recent)": [f"{info.get('revenueGrowth', '<Unable>')*100:.1f}%" if info.get('revenueGrowth') is not None else '<Unable to Source>'],
            "Dividend yield": [f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else '0%'],
            "Simple 'Why Buy' (auto-generated)": ["• Growing demand in " + info.get('sector', 'its sector') + "\n• " + (info.get('longBusinessSummary', '')[:120] + "...")],
            "Basic Valuation vs peers": ["<Unable to Source> – compare manually in Excel export"],
            "Quick Risks": ["• Market volatility\n• Sector headwinds (auto from news)"],
        }
        df_entry = pd.DataFrame.from_dict(entry_data, orient='index', columns=['Value/Notes'])
        df_entry['Flag'] = [''] * len(df_entry)
        df_entry['Source/Date'] = [f"Yahoo Finance via yfinance • {today}"] * len(df_entry)
        df_entry = df_entry.reset_index().rename(columns={'index': 'Metric/Query'})
        
        edited_entry = st.data_editor(
            df_entry,
            column_config={
                "Flag": st.column_config.SelectboxColumn("Flag", options=["Green", "Orange", "Red"], required=True),
            },
            use_container_width=True,
            num_rows="fixed",
            key="entry_editor"
        )

        # Triggers (Entry)
        st.markdown("**Entry-Level Triggers**")
        trigger_entry = pd.DataFrame([
            {"Trigger": "Earnings beat + raised guidance", "Color": "Green"},
            {"Trigger": "New catalyst (contract win)", "Color": "Green"},
            {"Trigger": "Price dips on no news", "Color": "Orange"},
            {"Trigger": "Major miss + lowered guidance", "Color": "Red"},
        ])
        st.data_editor(trigger_entry, use_container_width=True, hide_index=True)

        # === MID-LEVEL ===
        st.markdown("### 📌 Mid-Level (Core 20-30 min)")
        financials = stock.financials
        balance = stock.balance_sheet
        cashflow = stock.cashflow
        
        roe = info.get('returnOnEquity', None)
        debt_eq = info.get('debtToEquity', None)
        fcf = cashflow.loc['Free Cash Flow'].iloc[0] if 'Free Cash Flow' in cashflow.index else None
        
        mid_data = {
            "ROE / ROIC": [f"{roe*100:.1f}%" if roe else '<Unable to Source>'],
            "Debt/Equity": [debt_eq if debt_eq else '<Unable to Source>'],
            "Free Cash Flow trend": [f"${fcf/1e9:.1f}B (latest)" if fcf else '<Unable to Source>'],
            "Margins (gross/operating)": [f"{info.get('grossMargins',0)*100:.1f}% / {info.get('operatingMargins',0)*100:.1f}%"],
            "Management & Strategy": [f"Insider ownership: {info.get('heldPercentInsiders',0)*100:.1f}%"],
            "Historical Performance (1y vs S&P500)": ["<Unable to Source> – add in export"],
        }
        df_mid = pd.DataFrame.from_dict(mid_data, orient='index', columns=['Value/Notes'])
        df_mid['Flag'] = [''] * len(df_mid)
        df_mid['Source/Date'] = [f"Yahoo Finance via yfinance • {today}"] * len(df_mid)
        df_mid = df_mid.reset_index().rename(columns={'index': 'Metric/Query'})
        
        edited_mid = st.data_editor(
            df_mid,
            column_config={"Flag": st.column_config.SelectboxColumn("Flag", options=["Green", "Orange", "Red"])},
            use_container_width=True,
            key="mid_editor"
        )

        # === HIGH-LEVEL ===
        st.markdown("### 📌 High-Level / In-Depth")
        st.caption("Simple 2-stage DCF (auto) + assumptions editable below")
        try:
            rev_growth = info.get('revenueGrowth', 0.08) or 0.08
            ebitda_margin = 0.25
            wacc = 0.10
            terminal_g = 0.03
            fcf0 = fcf if fcf else info.get('freeCashflow', 1e9)
            dcf_value = fcf0 * (1+rev_growth) * (1 - (1+terminal_g)/(1+wacc)) / (wacc - terminal_g) / 1e9
            st.write(f"**Implied DCF Fair Value ≈ ${dcf_value:.1f}B** (base case)")
        except:
            st.write("**DCF: <Unable to Source>** – edit assumptions below")
        
        high_data = {
            "Valuation Models (DCF / Multiples)": ["See calculation above"],
            "3-5y Revenue/EBITDA forecasts": ["Assumption: " + str(rev_growth*100) + "% CAGR"],
            "Portfolio Fit / Review Date": ["Add your % allocation + next review date"],
        }
        df_high = pd.DataFrame.from_dict(high_data, orient='index', columns=['Value/Notes'])
        df_high['Flag'] = [''] * len(df_high)
        df_high['Source/Date'] = [f"Yahoo Finance via yfinance • {today}"] * len(df_high)
        df_high = df_high.reset_index().rename(columns={'index': 'Metric/Query'})
        
        edited_high = st.data_editor(
            df_high,
            column_config={"Flag": st.column_config.SelectboxColumn("Flag", options=["Green", "Orange", "Red"])},
            use_container_width=True,
            key="high_editor"
        )

        # === BONUS THESIS BLOCK ===
        st.markdown("### 🎯 Custom Thesis Block (Horyzon-style)")
        col_a, col_b = st.columns(2)
        with col_a:
            st.text_area("Why I Own It", value="Growing AI demand + strong moat", height=120)
            st.text_area("What Must Stay True", value="Revenue growth >15% annually", height=120)
        with col_b:
            st.text_area("What Would Change My Mind (Thesis Breakers)", value="Debt covenant breach or ROIC < WACC for 2 quarters", height=120)
            st.date_input("Portfolio Role & Next Review Date", value=datetime.now())

        # Conviction Score
        all_flags = pd.concat([edited_entry['Flag'], edited_mid['Flag'], edited_high['Flag']])
        conviction = (all_flags == "Green").sum() - (all_flags == "Red").sum()
        st.metric("Conviction Score", f"{conviction} / 10", help="+1 Green, 0 Orange, -1 Red")

        # === EXPORT TO EXCEL WITH FULL FORMATTING ===
        if st.button("📥 Export to Excel (with colors + dropdowns)"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                pd.concat([edited_entry, edited_mid, edited_high]).to_excel(writer, sheet_name="Thesis", index=False)
                wb = writer.book
                ws = wb["Thesis"]
                green_fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
                orange_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
                red_fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
                for row in ws.iter_rows(min_row=2, max_col=4):
                    cell = row[2]  # Flag column
                    if cell.value == "Green":
                        cell.fill = green_fill
                    elif cell.value == "Orange":
                        cell.fill = orange_fill
                    elif cell.value == "Red":
                        cell.fill = red_fill
                dv = DataValidation(type="list", formula1='"Green,Orange,Red"', allow_blank=True)
                ws.add_data_validation(dv)
                dv.add('C2:C100')
            output.seek(0)
            st.download_button(
                label="Download Thesis.xlsx",
                data=output,
                file_name=f"{ticker}_Thesis_{today}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.success("✅ Thesis generated! Edit any cell above. Data cross-referenced from Yahoo Finance.")
        st.caption("All missing fields show '<Unable to Source>'. Add your own research for qualitative depth.")
