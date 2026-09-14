#Escenarios -> 1000 traders, 50 activos, 500 días

# Configuración de los 8 escenarios del proyecto. 
# Cada escenario define una población de traders — con rangos específicos de delta_i y kappa_i, generados de forma independiente entre sí.
#'hazard' -> el hazard rate de decisions.py (delta/kappa reales)
#'rebalancing' 
# 'mean_reversion' -> venta por creencia de reversión a la media

#En los escenarios 7 y 8 (los confounds) delta_i = kappa_i = 0 para TODOS los traders 
import numpy as np
import pandas as pd

from src.seeds import get_scenario_rngs
from src.market import simulate_market_factor
from src.traders import generate_traders
from src.portfolio import initialize_portfolios
from src.decisions import simulate_decisions
from src.costs import apply_transaction_cost

# 1. Definición de los 8 escenarios

SCENARIOS = {
    1: {
        'name': 'nulo',
        'description': 'Sin sesgos: delta=0, kappa=0. Línea base.',
        'delta_range': (0.0, 0.0),
        'kappa_range': (0.0, 0.0),
        'mechanism': 'hazard',
    },
    2: {
        'name': 'disposicion_baja',
        'description': 'Solo efecto disposición, intensidad baja (kappa=0).',
        'delta_range': (0.0, 0.3),
        'kappa_range': (0.0, 0.0),
        'mechanism': 'hazard',
    },
    3: {
        'name': 'disposicion_alta',
        'description': 'Solo efecto disposición, intensidad alta (kappa=0).',
        'delta_range': (0.7, 1.0),
        'kappa_range': (0.0, 0.0),
        'mechanism': 'hazard',
    },
    4: {
        'name': 'turnover_bajo',
        'description': 'Solo overconfidence/turnover, intensidad baja (delta=0).',
        'delta_range': (0.0, 0.0),
        'kappa_range': (0.0, 0.3),
        'mechanism': 'hazard',
    },
    5: {
        'name': 'turnover_alto',
        'description': 'Solo overconfidence/turnover, intensidad alta (delta=0).',
        'delta_range': (0.0, 0.0),
        'kappa_range': (0.7, 1.0),
        'mechanism': 'hazard',
    },
    6: {
        'name': 'ambos_activos',
        'description': 'Disposición y turnover activos a la vez, rango completo.',
        'delta_range': (0.0, 1.0),
        'kappa_range': (0.0, 1.0),
        'mechanism': 'hazard',
    },
    7: {
        'name': 'confound_rebalanceo',
        'description': (
            'Confound: delta=0, kappa=0. Las ventas las dispara una regla '
            'mecánica de rebalanceo por bandas de peso, no una preferencia '
            'psicológica. Debe salir PGR>PLR aunque delta_i=0 para todos.'
        ),
        'delta_range': (0.0, 0.0),
        'kappa_range': (0.0, 0.0),
        'mechanism': 'rebalancing',
        'rebalance_band': 0.20,
        'rebalance_interval': 21,
    },
    8: {
        'name': 'confound_reversion_media',
        'description': (
            'Confound: delta=0, kappa=0. Las ventas las dispara la creencia '
            '(posiblemente errónea) de reversión a la media: entre más ha '
            'subido una posición, más urgencia de vender esperando la '
            'reversión. Debe salir PGR>PLR aunque delta_i=0 para todos.'
        ),
        'delta_range': (0.0, 0.0),
        'kappa_range': (0.0, 0.0),
        'mechanism': 'mean_reversion',
        'mr_strength': 3.0,
        'mr_threshold': 0.10,
    },
}

# 2. Traders con rango de delta/kappa específico del escenario

def generate_scenario_traders(n_traders, delta_range, kappa_range, seed=None):
    """
    Igual que generate_traders, pero permite restringir el rango de donde
    se muestrean delta_i y kappa_i, para poder aislar cada sesgo por
    separado (escenarios 2-5) o apagarlos en los confounds.

    Reusa generate_traders para capital/target_positions (así no se
    duplica esa parte del diseño ni se toca traders.py)
    """
    base_df = generate_traders(n_traders=n_traders, seed=seed)

    rng = np.random.default_rng(seed)
    delta_i = rng.uniform(delta_range[0], delta_range[1], n_traders)
    kappa_i = rng.uniform(kappa_range[0], kappa_range[1], n_traders)

    base_df = base_df.copy()
    base_df['delta'] = delta_i
    base_df['kappa'] = kappa_i
    return base_df


# 3. Mecanismos de venta para los confounds (7 y 8)

def simulate_decisions_rebalancing(portfolios_df, traders_df, prices_df,
                                    rebalance_band=0.20, rebalance_interval=21):

    """
Cada cierto tiempo, el trader revisa sus acciones. 
Si una subió tanto de precio que ahora sobrepasa el límite permitido en su portafolio, la vende completa para asegurar la ganancia.
Las acciones perdedoras no se tocan. Si una acción cae de precio, no se hace nada con ella. Como el sistema no permite meter más dinero ni recomprar acciones, las perdedoras se quedan congeladas en el portafolio.
La métrica PGR/PLR solo analiza las ventas realizadas. Al vender únicamente las acciones ganadoras para rebalancear, el modelo estadístico cree que el trader tiene el "efecto disposición" (vender lo que gana y aguantar lo que pierde).
Aunque en realidad no tenga ningún sesgo (δ=0) y solo esté aplicando una regla automática.
    """

    n_days = prices_df.shape[0]
    positions = portfolios_df.copy()
    positions['status'] = 'open'
    positions['exit_day'] = np.nan
    positions['exit_price'] = np.nan

    n_pos_map = traders_df.set_index('trader_id')['target_positions']
    positions['target_weight'] = 1.0 / positions['trader_id'].map(n_pos_map)

    for day in range(rebalance_interval, n_days, rebalance_interval):
        open_mask = positions['status'] == 'open'
        if not open_mask.any():
            break

        open_idx = positions.index[open_mask]
        day_prices = prices_df.iloc[day]

        current_prices = day_prices.loc[positions.loc[open_idx, 'asset']].to_numpy()
        shares = positions.loc[open_idx, 'shares'].to_numpy()
        position_value = shares * current_prices

        temp = pd.DataFrame({
            'trader_id': positions.loc[open_idx, 'trader_id'].to_numpy(),
            'position_value': position_value,
        })
        total_value_by_trader = temp.groupby('trader_id')['position_value'].transform('sum').to_numpy()

        weight = position_value / total_value_by_trader
        target_weight = positions.loc[open_idx, 'target_weight'].to_numpy()

        sell_mask = weight > target_weight * (1 + rebalance_band)
        sold_idx = open_idx[sell_mask]
        sold_prices = current_prices[sell_mask]

        for idx, price in zip(sold_idx, sold_prices):
            sh = positions.at[idx, 'shares']
            _, exec_price = apply_transaction_cost(price, sh, "sell")
            positions.at[idx, 'status'] = 'closed'
            positions.at[idx, 'exit_day'] = day
            positions.at[idx, 'exit_price'] = exec_price

    return positions.drop(columns=['target_weight'])


def simulate_decisions_mean_reversion(portfolios_df, traders_df, prices_df,
                                       h0=0.002, mr_strength=3.0,
                                       mr_threshold=0.10, seed=None):
    """
    El trader cree firmemente que las acciones que subieron demasiado van a caer pronto, y que las que se cayeron van a rebotar.
    Entre más alto sea el precio actual comparado con el precio de compra, más prisa tiene el trader por vender para asegurar la cima antes de que la acción vuelva a bajar.
    Si la acción está en números rojos, el trader no la vende. La conserva pacientemente esperando a que regrese a su nivel normal.
    El exceso de confianza (κi) solo determina qué tan activo o acelerado es el trader en general, afectando el ritmo general de sus operaciones por igual.
    Aunque la persona no tiene ningún miedo psicológico a perder dinero y solo sigue una estrategia de reversión a la media.
    El resultado estadístico se ve exactamente igual al efecto disposición: vende rápido las ganadoras y aguanta las perdedoras.

    """
    rng = np.random.default_rng(seed)
    n_days = prices_df.shape[0]

    positions = portfolios_df.copy()
    positions['status'] = 'open'
    positions['exit_day'] = np.nan
    positions['exit_price'] = np.nan

    kappa_map = traders_df.set_index('trader_id')['kappa']
    positions['kappa'] = positions['trader_id'].map(kappa_map)

    for day in range(1, n_days):
        open_mask = positions['status'] == 'open'
        if not open_mask.any():
            break

        open_idx = positions.index[open_mask]
        day_prices = prices_df.iloc[day]

        current_prices = day_prices.loc[positions.loc[open_idx, 'asset']].to_numpy()
        entry_prices = positions.loc[open_idx, 'entry_price'].to_numpy()
        excess_return = (current_prices / entry_prices) - 1

        kappa = positions.loc[open_idx, 'kappa'].to_numpy()

        gain_pressure = np.where(
            excess_return > 0,
            1 + mr_strength * np.clip(excess_return / mr_threshold, 0, None),
            1.0,
        )
        hazard = h0 * (1 + kappa) * gain_pressure
        hazard = np.clip(hazard, 0.0, 0.95)

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

    return positions.drop(columns=['kappa'])


# orquestador: corre un escenario completo de punta a punta

def run_scenario(scenario_id, n_traders=1000, n_assets=50, n_days=500,
                  base_seed=42, h0=0.002):
    """
    mercado -> traders -> portafolios -> decisiones para un escenario completo, usando siempre una población fresca derivada de
    get_scenario_rngs(scenario_id, base_seed). 
    Se simula el comportamiento y precio de las acciones. Es 100% independiente, lo que significa que las acciones de los inversionistas no alteran los precios del mercado.
    Se crea un grupo completamente nuevo de inversionistas con sus portafolios iniciales para evitar que la información de un escenario contamine a otro.
    Se simulan las decisiones diarias de compra y venta de cada trader sobre el mercado previamente generado.
    Todo el proceso utiliza una semilla aleatoria propia para cada escenario (get_scenario_rngs), lo que asegura que si vuelves a ejecutar la simulación, obtendrás exactamente los mismos resultados.
    """

    if scenario_id not in SCENARIOS:
        raise ValueError(f"scenario_id debe estar entre 1 y {len(SCENARIOS)}")

    config = SCENARIOS[scenario_id]
    market_seed, traders_seed = get_scenario_rngs(scenario_id, base_seed=base_seed)

    # traders_seed es un SeedSequence
    # streams independientes para generación de traders, selección de portafolio inicial y decisiones de venta, sin mezclar aleatoriedad entre esas tres cosas.
    # genera un canal aleatorio exclusivo para definir la personalidad de los traders, otro para armar sus portafolios de inicio y un tercero para simular sus ventas diarias.

    trader_gen_seed, portfolio_seed, decision_seed = traders_seed.spawn(3)

    prices_df, betas = simulate_market_factor(n_assets=n_assets, n_days=n_days, seed=market_seed)

    traders_df = generate_scenario_traders(
        n_traders=n_traders,
        delta_range=config['delta_range'],
        kappa_range=config['kappa_range'],
        seed=trader_gen_seed,
    )

    portfolios_df = initialize_portfolios(traders_df, prices_df, seed=portfolio_seed)

    mechanism = config['mechanism']
    if mechanism == 'hazard':
        positions_df = simulate_decisions(portfolios_df, traders_df, prices_df,
                                           h0=h0, seed=decision_seed)
    elif mechanism == 'rebalancing':
        positions_df = simulate_decisions_rebalancing(
            portfolios_df, traders_df, prices_df,
            rebalance_band=config['rebalance_band'],
            rebalance_interval=config['rebalance_interval'],
        )
    elif mechanism == 'mean_reversion':
        positions_df = simulate_decisions_mean_reversion(
            portfolios_df, traders_df, prices_df, h0=h0,
            mr_strength=config['mr_strength'],
            mr_threshold=config['mr_threshold'],
            seed=decision_seed,
        )
    else:
        raise ValueError(f"mecanismo desconocido: {mechanism}")

    return {
        'scenario_id': scenario_id,
        'name': config['name'],
        'description': config['description'],
        'prices_df': prices_df,
        'betas': betas,
        'traders_df': traders_df,
        'portfolios_df': portfolios_df,
        'positions_df': positions_df,
    }


def run_all_scenarios(**kwargs):
    """Corre los 8 escenarios y regresa un dict {scenario_id: resultado}."""
    return {sid: run_scenario(sid, **kwargs) for sid in SCENARIOS}