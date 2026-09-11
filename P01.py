import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Planteamos la simulación con los parámetros usando MBG (VALORES ARBITRARIOS DUDA PROFE)

def simulate_market_gbm(n_assets=50, n_days=500, S0=100, mu=0.05, sigma=0.2):
    # Asumiendo 252 días de trading al año
    dt = 1 / 252

    # Matriz de dimensiones (500x50)
    Z = np.random.standard_normal((n_days, n_assets))

    # Calculamos los retornos diarios
    daily_returns = np.exp((mu - 0.5 * sigma ** 2) * dt + sigma * np.sqrt(dt) * Z)

    # Matriz para almacenar los precios
    prices = np.zeros((n_days, n_assets))
    prices[0] = S0  # Precio inicial

    # Simulamos los precios acumulando los retornos
    for t in range(1, n_days):
        prices[t] = prices[t - 1] * daily_returns[t]

    # Pasamos a DataFrame
    asset_names = [f"Asset_{i + 1}" for i in range(n_assets)] # Activo
    prices_df = pd.DataFrame(prices, columns=asset_names) # Precios

    return prices_df

# Prueba Mercado
if __name__ == "__main__":
    np.random.seed(42)
    market_prices = simulate_market_gbm(n_assets=50, n_days=500) # Generado de Mercado

    print("\nPrimeros 5 días de los primeros 5 activos:")
    print(market_prices.iloc[:5, :5])

    # Visualización rápida de los primeros 5 activos para comprobar el comportamiento
    market_prices.iloc[:, :5].plot(title="Simulación Mercado - Primeros 5 Activos", figsize=(10, 5))
    plt.xlabel("Días de Trading")
    plt.ylabel("Precio")
    plt.show()

# Generamos los traders

def generate_traders(n_traders=1000):
    # 1. Parametros
    delta_i = np.random.uniform(0, 1, n_traders) # Efecto disposición
    kappa_i = np.random.uniform(0, 1, n_traders) # Sobrepresición (Overconfidence)
    # Restricciones
    w_i = np.random.uniform(10000, 500000, n_traders) # Capital de 10,000 a 500,000 por trader
    n_positions_i = np.random.randint(5, 31, n_traders) # 5 a 30 posiciones por trader

    # 3. DataFrame de traders con sus paremetros respectivos
    traders_df = pd.DataFrame({
        'trader_id': range(n_traders),
        'delta': delta_i,
        'kappa': kappa_i,
        'capital': w_i,
        'target_positions': n_positions_i
    })

    return traders_df


# Prueba de traders
if __name__ == "__main__":
    np.random.seed(42)
    traders = generate_traders(n_traders=1000)

    print(f"\nPrimeros 5 traders")
    print(traders.head())

    # Verificamos independencia
    realized_corr = traders['delta'].corr(traders['kappa'])
    print(f"\nCorrelación entre kappa y delta: {realized_corr:.4f}")
