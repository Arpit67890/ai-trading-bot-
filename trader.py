def process_signal(result):
    """
    Terminal output Formatter.
    Displays clear, actionable analysis output without executing any actual trades.
    """
    symbol = result.get("selected_pair", "N/A")
    signal = result.get("signal", "WAIT")
    entry = result.get("entry", 0.0)
    sl = result.get("stop_loss", 0.0)
    tp = result.get("take_profit", 0.0)
    rr = result.get("risk_reward", "1:3")
    reason = result.get("reason", "No detailed reason provided.")

    print("\n==========================================")
    print(f"📊 BEST MARKET IDENTIFIED : {symbol}")
    print(f"🚦 SIGNAL TYPE           : {signal}")
    print("==========================================")

    if signal in ["BUY", "SELL"]:
        print(f"📍 ENTRY PRICE           : {entry}")
        print(f"🛑 STOP LOSS             : {sl}")
        print(f"🎯 TAKE PROFIT            : {tp}")
        print(f"⚖️ RISK / REWARD          : {rr}")
    else:
        print("🟡 STATUS                 : No high-probability setup found. NO TRADE recommended.")

    print(f"📝 ANALYSIS REASON        : {reason}")
    print("==========================================\n")