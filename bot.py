import json
import pandas as pd
import yfinance as yf
from google import genai
import config
import trader

# Setup Gemini Client
client = genai.Client(api_key="AIzaSyBw-x6naGifEJ69RM_0ZVRY0a-zd_rBBDw")

print("\n==========================================")
print("📊 SELECT MARKET TO SCAN:")
print("1. Forex, Commodities & Indices (Gold, Silver, Oil, US30, EURUSD...)")
print("2. Crypto (BTC, ETH, SOL, XRP, BNB, DOGE...)")
print("==========================================")

choice = input("Enter choice (1 or 2): ").strip()

if choice == "2":
    selected_market_type = "Crypto"
    SYMBOLS = config.CRYPTO_SYMBOLS
else:
    selected_market_type = "Forex & Commodities"
    SYMBOLS = config.FOREX_SYMBOLS

market_summary = {}

print(f"\n🔍 Advanced Price Action Scanning across {len(SYMBOLS)} markets ({selected_market_type})...")

for name, ticker in SYMBOLS.items():
    data = yf.download(tickers=ticker, period=config.DATA_PERIOD, interval=config.TIMEFRAME, progress=False)
    
    if data.empty or len(data) < 30:
        continue

    # Flatten MultiIndex columns if present
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # 1. Technical Indicators (EMA 20/50 & RSI 14)
    data['EMA20'] = data['Close'].ewm(span=config.EMA_FAST).mean()
    data['EMA50'] = data['Close'].ewm(span=config.EMA_SLOW).mean()

    delta = data['Close'].diff()
    gain = delta.clip(lower=0).rolling(config.RSI_PERIOD).mean()
    loss = (-delta.clip(upper=0)).rolling(config.RSI_PERIOD).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))

    # 2. Key Levels (Support & Resistance - 20 Period High/Low)
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

# 3. AI Price Action Analysis Prompt
prompt = f"""
You are a Senior Price Action & Technical Analyst.

Analyze the following live {selected_market_type} market data across multiple pairs:
{json.dumps(market_summary, indent=2, default=str)}

RULES FOR SELECTION:
1. Scan all provided pairs carefully.
2. Select ONE pair with the strongest high-probability setup (Price near Support/Resistance, EMA Trend Alignment, RSI Confluence, or Candlestick Rejection).
3. If no clear trade opportunity exists across any pair, set signal to "WAIT".
4. Risk-to-Reward Ratio MUST be 1:2 minimum based on Support and Resistance levels.

Return ONLY valid JSON format:
{{
  "selected_pair": "PAIR_NAME",
  "signal": "BUY" | "SELL" | "WAIT",
  "entry": 0.0,
  "stop_loss": 0.0,
  "take_profit": 0.0,
  "risk_reward": "1:2",
  "reason": "Clear technical breakdown explaining EMA alignment, Support/Resistance, and Candlestick action."
}}
"""

print("🤖 Gemini AI is evaluating all pairs for the best setup...\n")

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    result = json.loads(clean_text)

    # Display final result
    trader.process_signal(result)

except Exception as e:
    print("❌ Analysis Error:", e)