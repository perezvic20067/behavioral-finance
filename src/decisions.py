import numpy as np
from src.costs import apply_transaction_cost


def simulate_decisions(portfolios_df, traders_df, prices_df, h0=0.002, seed=None):
    rng = np.random.default_rng(seed)
    n_days = prices_df.shape[0]

    positions = portfolios_df.copy()
    positions['status'] = 'open'
    positions['exit_day'] = np.nan
    positions['exit_price'] = np.nan

    delta_map = traders_df.set_index('trader_id')['delta']
    kappa_map = traders_df.set_index('trader_id')['kappa']
    positions['delta'] = positions['trader_id'].map(delta_map)
    positions['kappa'] = positions['trader_id'].map(kappa_map)

    for day in range(1, n_days):
        open_mask = positions['status'] == 'open'
        if not open_mask.any():
            break

        open_idx = positions.index[open_mask]
        day_prices = prices_df.iloc[day]

        current_prices = day_prices.loc[positions.loc[open_idx, 'asset']].to_numpy()
        entry_prices = positions.loc[open_idx, 'entry_price'].to_numpy()
        is_gain = current_prices > entry_prices

        delta = positions.loc[open_idx, 'delta'].to_numpy()
        kappa = positions.loc[open_idx, 'kappa'].to_numpy()
        multiplier = np.where(is_gain, 1 + delta, 1 - delta)
        hazard = h0 * (1 + kappa) * multiplier

        draws = rng.uniform(0, 1, size=len(open_idx))
        sold_mask = draws < hazard

        sold_idx = open_idx[sold_mask]
        sold_prices = current_prices[sold_mask]

        for idx, price in zip(sold_idx, sold_prices):
            shares = positions.at[idx, 'shares']
            _, exec_price = apply_transaction_cost(price, shares, "sell")
            positions.at[idx, 'status'] = 'closed'
            positions.at[idx, 'exit_day'] = day
            positions.at[idx, 'exit_price'] = exec_price

    return positions