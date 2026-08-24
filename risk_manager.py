MAX_LOT = 1.2

def allowed_trade(lot, trades_today):
    if trades_today >= 3:
        return False

    if lot > MAX_LOT:
        return False

    return True