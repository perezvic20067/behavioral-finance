def apply_transaction_cost(price, shares, side, commission_rate=0.0005, spread_pct=0.002):
    half_spread = spread_pct / 2

    if side == "buy":
        exec_price = price * (1 + half_spread)
        cash_flow = -(shares * exec_price) * (1 + commission_rate)
    elif side == "sell":
        exec_price = price * (1 - half_spread)
        cash_flow = (shares * exec_price) * (1 - commission_rate)
    else:
        raise ValueError("side debe ser 'buy' o 'sell'")

    return cash_flow, exec_price