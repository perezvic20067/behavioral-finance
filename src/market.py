import numpy as np
import pandas as pd

def simulate_market_factor(n_assets=50, n_days=500, S0=100, mu=0.05, sigma=0.2,
                            betas=None, seed=None):
    rng = np.random.default_rng(seed)
    dt = 1 / 252

    if betas is None:
        betas = rng.uniform(0.4, 0.8, n_assets)
    betas = np.clip(betas, -0.99, 0.99)

    F = rng.standard_normal(n_days)
    eps = rng.standard_normal((n_days, n_assets))
    Z = betas[np.newaxis, :] * F[:, np.newaxis] + np.sqrt(1 - betas**2)[np.newaxis, :] * eps

    daily_returns = np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z)

    prices = np.zeros((n_days, n_assets))
    prices[0] = S0 * daily_returns[0]
    for t in range(1, n_days):
        prices[t] = prices[t - 1] * daily_returns[t]

    asset_names = [f"Asset_{i + 1}" for i in range(n_assets)]
    return pd.DataFrame(prices, columns=asset_names), betas
    