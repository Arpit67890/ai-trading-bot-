import json
import time
import requests
import pandas as pd
import yfinance as yf
import streamlit as st
import streamlit.components.v1 as components
from google import genai
import config

# Streamlit Page Setup
st.set_page_config(
    page_title="Pro Trading Terminal | High-R:R Scalper",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .stApp {
        background-color: #080b10;
        color: #d1dbe5;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    footer {visibility: hidden;}
    
    header {
        visibility: visible !important;
        background-color: transparent !important;
    }
    
    button[aria-label="Toggle sidebar"], button[data-testid="baseButton-header"] {
        background-color: #0f141c !important;
        border: 1px solid #00c6ff !important;
        color: #00c6ff !important;
        border-radius: 6px !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #0b0f17 !important;
        border-right: 1px solid #1a2230;
    }

    .brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 15px;
        border-bottom: 1px solid #1a2230;
        margin-bottom: 25px;
    }
    .brand-title {
        font-size: 1.8rem;
        font-weight: 900;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .control-card {
        background: #0f141c;
        border: 1px solid #1e2638;
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 25px;
    }

    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
        color: #ffffff !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        padding: 10px 20px !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0, 198, 255, 0.25);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        box-shadow: 0 6px 20px rgba(0, 198, 255, 0.45);
    }

    .metric-card {
        background: #121824;
        border: 1px solid #1f2a3e;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        color: #6b7c93;
        font-weight: 700;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: 800;
        color: #ffffff;
        margin-top: 5px;
    }

    .badge-buy {
        background-color: rgba(16, 185, 129, 0.12);
        color: #10b981;
        border: 1px solid #10b981;
        padding: 8px 20px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 1.2rem;
        text-align: center;
    }
    .badge-sell {
        background-color: rgba(239, 68, 68, 0.12);
        color: #ef4444;
        border: 1px solid #ef4444;
        padding: 8px 20px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 1.2rem;
        text-align: center;
    }
    .badge-wait {
        background-color: rgba(245, 158, 11, 0.12);
        color: #f59e0b;
        border: 1px solid #f59e0b;
        padding: 8px 20px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 1.2rem;
        text-align: center;
    }

    .reason-box {
        background: #0f141c;
        border: 1px solid #1e2638;
        border-left: 4px solid #00c6ff;
        border-radius: 8px;
        padding: 20px;
        margin-top: 20px;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# Safe API Key retrieval
api_key = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

if not api_key:
    api_key = getattr(config, "GEMINI_API_KEY", None)

client = genai.Client(api_key=api_key)

# Session State Initialization
if "scan_history" not in st.session_state:
    st.session_state.scan_history = []
if "telegram_bot_token" not in st.session_state:
    st.session_state.telegram_bot_token = ""
if "telegram_chat_id" not in st.session_state:
    st.session_state.telegram_chat_id = ""

# Sidebar Navigation Panel
st.sidebar.markdown("## ⚡ **Quant Navigation**")
selected_tab = st.sidebar.radio(
    "Select Feature Module",
    (
        "⚡ Quick Scalp Engine",
        "🧮 Risk & Lot Calculator",
        "📰 News & Volatility Radar",
        "📊 Analytics & Telegram Alerts"
    )
)

st.sidebar.markdown("---")
st.sidebar.markdown("**System Mode:** ⚡ `Ultra-Short Scalper (3m/5m)`")
st.sidebar.markdown("**Min Target R:R:** 🎯 `1:2.5+ High Reward`")

# Helper Functions
def send_telegram_alert(signal_data):
    token = st.session_state.telegram_bot_token
    chat_id = st.session_state.telegram_chat_id
    if token and chat_id:
        msg = f"""🚨 **FAST SCALP SIGNAL ALERT** 🚨
        
**Asset:** {signal_data.get('selected_pair')}
**Signal:** {signal_data.get('signal')}
**Entry:** {signal_data.get('entry')}
**Tight Stop Loss:** {signal_data.get('stop_loss')}
**Target Profit:** {signal_data.get('take_profit')}
**Risk/Reward:** {signal_data.get('risk_reward')}

**Rationale:** {signal_data.get('reason')}"""
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
        except Exception:
            pass

def get_tv_symbol(pair_name):
    clean_name = pair_name.split()[0].replace('/', '').replace('=', '')
    if "BTC" in clean_name: return "BINANCE:BTCUSDT"
    if "ETH" in clean_name: return "BINANCE:ETHUSDT"
    if "SOL" in clean_name: return "BINANCE:SOLUSDT"
    if "XRP" in clean_name: return "BINANCE:XRPUSDT"
    if "EURUSD" in clean_name: return "FX:EURUSD"
    if "GBPUSD" in clean_name: return "FX:GBPUSD"
    if "USDJPY" in clean_name: return "FX:USDJPY"
    if "XAUUSD" in clean_name: return "OANDA:XAUUSD"
    return f"FX:{clean_name}"

def compute_indicators(df):
    df['EMA9'] = df['Close'].ewm(span=9).mean()
    df['EMA21'] = df['Close'].ewm(span=21).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# ==========================================
# TAB 1: ULTRA FAST SCALPER ENGINE
# ==========================================
if selected_tab == "⚡ Quick Scalp Engine":
    st.markdown('''
    <div class="brand-header">
        <div class="brand-title">⚡ ULTRA-SHORT HIGH PROBABILITY SCALPER</div>
        <div style="color: #6b7c93; font-weight: 600; font-size: 0.9rem;">Tight Risk • Large Profit Targets • Fast Duration</div>
    </div>
    ''', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="control-card">', unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1:
            market_choice = st.radio(
                "Select Asset Market:",
                ("Forex, Commodities & Indices", "Crypto"),
                horizontal=True
            )
        with c2:
            st.write(" ")
            scan_btn = st.button("🚀 SCAN SCALP SETUPS")
        st.markdown('</div>', unsafe_allow_html=True)

    SYMBOLS = config.CRYPTO_SYMBOLS if market_choice == "Crypto" else config.FOREX_SYMBOLS
    market_type = "Crypto" if market_choice == "Crypto" else "Forex & Commodities"

    if scan_btn:
        st.markdown("### 🔍 Live Fast-Scalp Screener (5m Execution / 15m Trend)")
        live_status_container = st.container()
        progress_bar = st.progress(0)
        
        market_summary = {}
        total_symbols = len(SYMBOLS)
        
        for idx, (name, ticker) in enumerate(SYMBOLS.items()):
            with live_status_container:
                col_s1, col_s2, col_s3 = st.columns([2, 2, 2])
                try:
                    # Fetching 5m execution & 15m trend for fast trade setups
                    df_5m = yf.download(tickers=ticker, period="1d", interval="5m", progress=False)
                    df_15m = yf.download(tickers=ticker, period="5d", interval="15m", progress=False)
                    
                    if not df_5m.empty and not df_15m.empty:
                        if isinstance(df_5m.columns, pd.MultiIndex): df_5m.columns = df_5m.columns.get_level_values(0)
                        if isinstance(df_15m.columns, pd.MultiIndex): df_15m.columns = df_15m.columns.get_level_values(0)

                        df_5m = compute_indicators(df_5m)
                        df_15m = compute_indicators(df_15m)

                        latest_price = float(df_5m['Close'].iloc[-1])
                        rsi_5m = float(df_5m['RSI'].iloc[-1])
                        trend_15m = "BULLISH SCALP" if df_15m['EMA9'].iloc[-1] > df_15m['EMA21'].iloc[-1] else "BEARISH SCALP"
                        
                        support_tight = float(df_5m['Low'].tail(15).min())
                        resistance_tight = float(df_5m['High'].tail(15).max())

                        market_summary[name] = {
                            "current_price": latest_price,
                            "5m_rsi": rsi_5m,
                            "15m_trend": trend_15m,
                            "tight_support": support_tight,
                            "tight_resistance": resistance_tight,
                            "recent_5m_candles": df_5m[['Open', 'High', 'Low', 'Close', 'EMA9', 'EMA21', 'RSI']].tail(5).to_dict(orient='records')
                        }

                        with col_s1:
                            st.markdown(f"**Asset:** `{name}`")
                        with col_s2:
                            st.markdown(f"**Live Price:** `{latest_price:.4f}` | **5m RSI:** `{rsi_5m:.1f}`")
                        with col_s3:
                            st.markdown(f"**15m Trend:** `{trend_15m}` 🟢" if "BULLISH" in trend_15m else f"**15m Trend:** `{trend_15m}` 🔴")

                except Exception:
                    st.caption(f"Skipped {name}")

            progress_bar.progress((idx + 1) / total_symbols)

        st.markdown("---")
        st.markdown("🤖 **Gemini AI calculating tight SL & high R:R Scalp entry...**")

        prompt = f"""
        You are an Institutional Scalper specializing in short duration, high profit-to-risk ratio setups.
        Data: {json.dumps(market_summary, indent=2, default=str)}

        SCALPING RULES:
        1. Setup must complete quickly (5m timeframe execution, short hold duration).
        2. Set TIGHT Stop Loss (just beyond recent 15-period support/resistance).
        3. Target Profit MUST be at least 2.5x to 3x of Stop Loss distance (Min R:R = 1:2.5).
        4. If no pair offers tight risk with strong momentum, signal MUST be "WAIT".

        Return ONLY valid JSON:
        {{
          "selected_pair": "PAIR_NAME",
          "signal": "BUY" | "SELL" | "WAIT",
          "entry": 0.0,
          "stop_loss": 0.0,
          "take_profit": 0.0,
          "risk_reward": "1:2.5",
          "reason": "Fast scalp breakout with tight SL and 1:2.5 Risk-to-Reward target"
        }}
        """

        models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        response = None
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                if response: break
            except Exception:
                time.sleep(1)
                continue

        if response:
            try:
                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                result = json.loads(clean_text)

                history_item = {
                    "Time": time.strftime("%H:%M:%S"),
                    "Asset": result.get("selected_pair", "N/A"),
                    "Signal": result.get("signal", "WAIT"),
                    "Entry": result.get("entry", 0.0),
                    "SL": result.get("stop_loss", 0.0),
                    "TP": result.get("take_profit", 0.0),
                    "R:R": result.get("risk_reward", "1:2.5"),
                    "Reason": result.get("reason", "")
                }
                st.session_state.scan_history.insert(0, history_item)
                send_telegram_alert(result)

                signal = result.get("signal", "WAIT")
                pair = result.get("selected_pair", "N/A")

                st.markdown("---")
                col_pair, col_badge = st.columns([3, 1])
                with col_pair:
                    st.markdown(f"## High Reward Scalp Setup: **{pair}**")
                with col_badge:
                    if signal == "BUY":
                        st.markdown('<div class="badge-buy">🟢 ACCURATE SCALP BUY</div>', unsafe_allow_html=True)
                    elif signal == "SELL":
                        st.markdown('<div class="badge-sell">🔴 ACCURATE SCALP SELL</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="badge-wait">🟡 WAIT / NO HIGH R:R SCALP</div>', unsafe_allow_html=True)

                st.write("")
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Scalp Entry</div><div class="metric-value">{result.get("entry", 0.0)}</div></div>', unsafe_allow_html=True)
                with m2:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Tight Stop Loss</div><div class="metric-value" style="color:#ef4444;">{result.get("stop_loss", 0.0)}</div></div>', unsafe_allow_html=True)
                with m3:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">High Take Profit</div><div class="metric-value" style="color:#10b981;">{result.get("take_profit", 0.0)}</div></div>', unsafe_allow_html=True)
                with m4:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Risk / Reward</div><div class="metric-value" style="color:#00c6ff;">{result.get("risk_reward", "1:2.5")}</div></div>', unsafe_allow_html=True)

                st.write("")
                col_chart, col_details = st.columns([3, 2])
                with col_chart:
                    st.markdown("### 📊 5-Min Live Scalp Chart")
                    tv_symbol = get_tv_symbol(pair)
                    tv_widget = f"""
                    <div class="tradingview-widget-container" style="height:450px;">
                      <iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_1&symbol={tv_symbol}&interval=5&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=0b0e14&theme=dark&style=1&timezone=Etc%2FUTC" width="100%" height="450" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
                    </div>
                    """
                    components.html(tv_widget, height=460)

                with col_details:
                    st.markdown("### 📝 Scalping Setup Breakdown")
                    st.markdown(f'''
                    <div class="reason-box">
                        <strong style="color: #00c6ff;">AI Scalp Strategy Logic:</strong><br><br>
                        {result.get("reason", "No detailed rationale provided.")}
                    </div>
                    ''', unsafe_allow_html=True)

            except Exception as err:
                st.error(f"Scalp parsing error: {err}")

    else:
        st.markdown("""
        <div style="text-align: center; padding: 40px 20px; color: #5a6e85;">
            <h3>Click <strong>🚀 SCAN SCALP SETUPS</strong> to run 5-minute High R:R technical analysis</h3>
            <p>Targeting small stop loss with 1:2.5+ profit potential for quick trade completion.</p>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.scan_history:
        st.markdown("---")
        st.markdown("### 📜 Scan History & Past Scalps")
        history_df = pd.DataFrame(st.session_state.scan_history)
        st.dataframe(
            history_df[["Time", "Asset", "Signal", "Entry", "SL", "TP", "R:R", "Reason"]],
            use_container_width=True,
            hide_index=True
        )

# ==========================================
# OTHER TABS
# ==========================================
elif selected_tab == "🧮 Risk & Lot Calculator":
    st.markdown("## 🧮 Position & Lot Size Calculator")
    account_balance = st.number_input("Account Balance ($)", value=1000.0, step=100.0)
    risk_percent = st.slider("Risk Per Scalp (%)", min_value=0.5, max_value=3.0, value=1.0, step=0.5)
    entry_p = st.number_input("Entry Price", value=1.0850, format="%.5f")
    sl_p = st.number_input("Tight Stop Loss", value=1.0835, format="%.5f")
    
    risk_amount = account_balance * (risk_percent / 100)
    pip_distance = abs(entry_p - sl_p)
    if pip_distance > 0:
        pips = pip_distance * 10000 if entry_p < 500 else pip_distance
        recommended_lot = risk_amount / (pips * 10) if entry_p < 500 else risk_amount / pip_distance
        st.markdown(f"**Recommended Scalp Position:** `{max(0.01, round(recommended_lot, 2))} Lots` (Risked Capital: `${risk_amount:.2f}`)")

elif selected_tab == "📰 News & Volatility Radar":
    st.markdown("## 📰 Economic News Radar")
    vix_df = yf.download("^VIX", period="5d", interval="1d", progress=False)
    if not vix_df.empty:
        if isinstance(vix_df.columns, pd.MultiIndex): vix_df.columns = vix_df.columns.get_level_values(0)
        st.metric("CBOE Volatility Index (VIX)", f"{vix_df['Close'].iloc[-1]:.2f}")

elif selected_tab == "📊 Analytics & Telegram Alerts":
    st.markdown("## 📊 Performance Analytics & Live Alerts")
    t_token = st.text_input("Telegram Bot Token", value=st.session_state.telegram_bot_token, type="password")
    t_cid = st.text_input("Telegram Chat ID", value=st.session_state.telegram_chat_id)
    if st.button("Save Telegram Config"):
        st.session_state.telegram_bot_token = t_token
        st.session_state.telegram_chat_id = t_cid
        st.success("Telegram Alert Configuration Saved!")