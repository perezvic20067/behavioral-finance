import numpy as np
import pandas as pd

def generate_traders(n_traders=1000, seed=None):
    rng = np.random.default_rng(seed)

    # 1. Parametros
    delta_i = rng.uniform(0, 1, n_traders)  # Efecto disposición
    kappa_i = rng.uniform(0, 1, n_traders)  # Overprecision / churn intensity
    # Restricciones
    w_i = rng.uniform(10000, 500000, n_traders)  # Capital de 10,000 a 500,000 por trader
    n_positions_i = rng.integers(5, 31, n_traders)  # 5 a 30 posiciones por trader

    # 3. DataFrame de traders con sus parametros respectivos
    traders_df = pd.DataFrame({
        'trader_id': range(n_traders),
        'delta': delta_i,
        'kappa': kappa_i,
        'capital': w_i,
        'target_positions': n_positions_i
    })

    return traders_df