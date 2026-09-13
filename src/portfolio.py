import numpy as np
import pandas as pd
from src.costs import apply_transaction_cost


def initialize_portfolios(traders_df, prices_df, seed=None):
    rng = np.random.default_rng(seed)
    asset_names = prices_df.columns.to_numpy()
    day0_prices = prices_df.iloc[0]

    rows = []
    for _, trader in traders_df.iterrows():
        n_pos = int(trader['target_positions'])
        chosen_assets = rng.choice(asset_names, size=n_pos, replace=False)
        capital_per_position = trader['capital'] / n_pos

        for asset in chosen_assets:
            price = day0_prices[asset]
            cost_flow_per_share, exec_price = apply_transaction_cost(price, 1, "buy")
            cost_per_share = -cost_flow_per_share
            shares = capital_per_position / cost_per_share

            rows.append({
                'trader_id': trader['trader_id'],
                'asset': asset,
                'shares': shares,
                'entry_price': exec_price,
                'entry_day': 0,
            })

    return pd.DataFrame(rows)