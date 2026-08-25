import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = ""

# Expanded Forex, Commodities & Indices
FOREX_SYMBOLS = {
    # Forex Majors
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "CAD=X",
    "USDCHF": "CHF=X",
    "NZDUSD": "NZDUSD=X",
    # Commodities
    "XAUUSD (Gold)": "GC=F",
    "XAGUSD (Silver)": "SI=F",
    "USOIL (Crude)": "CL=F",
    # Global Indices
    "US30 (Dow Jones)": "^DJI",
    "NAS100 (Nasdaq)": "^IXIC",
    "SPX500 (S&P 500)": "^GSPC"
}

# Expanded Top Crypto Coins
CRYPTO_SYMBOLS = {
    "BTCUSD (Bitcoin)": "BTC-USD",
    "ETHUSD (Ethereum)": "ETH-USD",
    "SOLUSD (Solana)": "SOL-USD",
    "XRPUSD (Ripple)": "XRP-USD",
    "BNBUSD (Binance)": "BNB-USD",
    "ADAUSD (Cardano)": "ADA-USD",
    "DOGEUSD (Dogecoin)": "DOGE-USD",
    "AVAXUSD (Avalanche)": "AVAX-USD",
    "NEARUSD (Near)": "NEAR-USD"
}

DATA_PERIOD = "5d"
TIMEFRAME = "15m"
EMA_FAST = 20
EMA_SLOW = 50
RSI_PERIOD = 14