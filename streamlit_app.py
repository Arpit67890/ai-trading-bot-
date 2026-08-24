import json
import time
import pandas as pd
import yfinance as yf
import streamlit as st
import streamlit.components.v1 as components
from google import genai
import config

# Streamlit Page Setup
st.set_page_config(
    page_title="Pro Trading Terminal | AI Quant Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling (Dark Mode Terminal Aesthetics)
st.markdown("""
<style>
    .stApp {
        background-color: #080b10;
        color: #d1dbe5;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    header, footer {visibility: hidden;}

    /* Top Title Header */
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

    /* Control Box */
    .control-card {
        background: #0f141c;
        border: 1px solid #1e2638;
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 25px;
    }

    /* Primary Action Button */
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

    /* Metric Cards */
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

    /* Signal Badges */
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

    /* Reason Box */
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

# Top Bar
st.markdown('''
<div class="brand-header">
    <div class="brand-title">⚡ QUANT QUANT AI TERMINAL</div>
    <div style="color: #6b7c93; font-weight: 600; font-size: 0.9rem;">Multi-Pair Confluence Engine</div>
</div>
''', unsafe_allow_html=True)

# API Key retrieval logic (Fallback to Streamlit Secrets for Cloud Deployment)
api_key = st.secrets.get("AIzaSyBw-x6naGifEJ69RM_0ZVRY0a-zd_rBBDw") if ""AIzaSyBw-x6naGifEJ69RM_0ZVRY0a-zd_rBBDw"" in st.secrets else config.GEMINI_API_KEY

# Client initialization
client = genai.Client(api_key="AIzaSyBw-x6naGifEJ69RM_0ZVRY0a-zd_rBBDw")

# Top Control Deck
with st.container():
    st.markdown('<div class="control-card">', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        market_choice = st.radio(
            "Target Asset Class:",
            ("Forex, Commodities & Indices", "Crypto"),
            horizontal=True
        )
    with c2:
        st.write(" ")
        scan_btn = st.button("🚀 SCAN ALL PAIRS")
    st.markdown('</div>', unsafe_allow_html=True)

if market_choice == "Crypto":
    SYMBOLS = config.CRYPTO_SYMBOLS
    market_type = "Crypto"
else:
    SYMBOLS = config.FOREX_SYMBOLS
    market_type = "Forex & Commodities"

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

def run_analysis():
    market_summary = {}
    progress_bar = st.progress(0)
    status_text = st.empty()

    total_symbols = len(SYMBOLS)
    
    for idx, (name, ticker) in enumerate(SYMBOLS.items()):
        status_text.markdown(f"Fetching Live Feed: `{name}`...")
        try:
            data = yf.download(tickers=ticker, period=config.DATA_PERIOD, interval=config.TIMEFRAME, progress=False)
            if not data.empty and len(data) >= 30:
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)

                data['EMA20'] = data['Close'].ewm(span=config.EMA_FAST).mean()
                data['EMA50'] = data['Close'].ewm(span=config.EMA_SLOW).mean()

                delta = data['Close'].diff()
                gain = delta.clip(lower=0).rolling(config.RSI_PERIOD).mean()
                loss = (-delta.clip(upper=0)).rolling(config.RSI_PERIOD).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))

                support = float(data['Low'].tail(20).min())
                resistance = float(data['High'].tail(20).max())
                latest_price = float(data['Close'].iloc[-1])

                recent_candles = data[['Open', 'High', 'Low', 'Close', 'EMA20', 'EMA50', 'RSI']].tail(5).to_dict(orient='records')

                market_summary[name] = {
                    "current_price": latest_price,
                    "support_20p": support,
                    "resistance_20p": resistance,
                    "recent_candles": recent_candles
                }
        except Exception:
            pass
        
        progress_bar.progress((idx + 1) / total_symbols)

    status_text.markdown("🤖 **Gemini AI evaluating best setup across all charts...**")

    prompt = f"""
    You are a Senior Technical Analyst. Analyze live {market_type} market data:
    {json.dumps(market_summary, indent=2, default=str)}

    RULES:
    1. Select ONE pair with highest probability setup (EMA Trend, S/R Bounce/Breakout, RSI).
    2. If market is uncertain, set signal to "WAIT".
    3. R:R Ratio MUST be 1:2 minimum.

    Return ONLY valid JSON:
    {{
      "selected_pair": "PAIR_NAME",
      "signal": "BUY" | "SELL" | "WAIT",
      "entry": 0.0,
      "stop_loss": 0.0,
      "take_profit": 0.0,
      "risk_reward": "1:2",
      "reason": "Technical breakdown"
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_text)
        status_text.empty()
        progress_bar.empty()
        return result
    except Exception as e:
        status_text.empty()
        progress_bar.empty()
        st.error(f"Execution Error: {e}")
        return None

if scan_btn:
    result = run_analysis()
    
    if result:
        signal = result.get("signal", "WAIT")
        pair = result.get("selected_pair", "N/A")

        st.markdown("---")
        
        col_pair, col_badge = st.columns([3, 1])
        with col_pair:
            st.markdown(f"## Selected Asset: **{pair}**")
        with col_badge:
            if signal == "BUY":
                st.markdown('<div class="badge-buy">🟢 BUY SIGNAL</div>', unsafe_allow_html=True)
            elif signal == "SELL":
                st.markdown('<div class="badge-sell">🔴 SELL SIGNAL</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="badge-wait">🟡 WAIT / NO TRADE</div>', unsafe_allow_html=True)

        st.write("")

        # 4 Metric Cards
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Entry Price</div><div class="metric-value">{result.get("entry", 0.0)}</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Stop Loss</div><div class="metric-value" style="color:#ef4444;">{result.get("stop_loss", 0.0)}</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Take Profit</div><div class="metric-value" style="color:#10b981;">{result.get("take_profit", 0.0)}</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Risk / Reward</div><div class="metric-value" style="color:#00c6ff;">{result.get("risk_reward", "1:2")}</div></div>', unsafe_allow_html=True)

        st.write("")

        # Two Column Split: Chart + Analysis
        col_chart, col_details = st.columns([3, 2])

        with col_chart:
            st.markdown("### 📊 Live Interactive Chart")
            tv_symbol = get_tv_symbol(pair)
            tv_widget = f"""
            <div class="tradingview-widget-container" style="height:450px;">
              <iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_1&symbol={tv_symbol}&interval=15&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=0b0e14&theme=dark&style=1&timezone=Etc%2FUTC" width="100%" height="450" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
            </div>
            """
            components.html(tv_widget, height=460)

        with col_details:
            st.markdown("### 📝 Technical Rationale")
            st.markdown(f'''
            <div class="reason-box">
                <strong style="color: #00c6ff;">AI Confluence Breakdown:</strong><br><br>
                {result.get("reason", "No detailed rationale provided.")}
            </div>
            ''', unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px; color: #5a6e85;">
        <h3>Click <strong>🚀 SCAN ALL PAIRS</strong> above to execute multi-pair analysis</h3>
        <p>Real-time data feeds across Forex & Crypto will be scanned for High-Probability Price Action setups.</p>
    </div>
    """, unsafe_allow_html=True)