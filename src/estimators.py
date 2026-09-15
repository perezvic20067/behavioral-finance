"""
Estimadores del proyecto:

  1. PGR / PLR (Odean, 1998) con bootstrap POR CUENTA (no por transacción).
  2. Diagnóstico de overconfidence: regresión de retorno contra turnover,
     corrida dos veces (retorno bruto vs. neto) y comparada.
"""
from math import erf, sqrt

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 1. PGR / PLR
# ---------------------------------------------------------------------------

def compute_pgr_plr_events(positions_df, prices_df):
    """
    Metodología Odean (1998): para cada venta, se compara contra las
    DEMÁS posiciones que ese mismo trader tenía abiertas ese mismo día.
    La posición vendida se clasifica como ganancia/pérdida REALIZADA; las
    demás posiciones abiertas ese día se clasifican como ganancia/pérdida
    EN PAPEL. Regresa un DataFrame a nivel evento:
        trader_id, day, kind in {realized_gain, realized_loss, paper_gain, paper_loss}
    A partir de este DataFrame se puede calcular PGR/PLR agregado y
    bootstrapear por cuenta re-muestreando trader_id.
    """
    if (positions_df['status'] == 'closed').sum() == 0:
        return pd.DataFrame(columns=['trader_id', 'day', 'kind'])

    events = []
    price_matrix = prices_df.to_numpy()
    asset_col_idx = {a: i for i, a in enumerate(prices_df.columns)}

    for trader_id, trader_pos in positions_df.groupby('trader_id'):
        if (trader_pos['status'] == 'closed').sum() == 0:
            continue

        trader_pos = trader_pos.reset_index(drop=True)
        entry_prices = trader_pos['entry_price'].to_numpy()
        asset_idx = trader_pos['asset'].map(asset_col_idx).to_numpy()
        exit_days = trader_pos['exit_day'].to_numpy(dtype=float)
        statuses = trader_pos['status'].to_numpy()
        exit_prices = trader_pos['exit_price'].to_numpy()

        exit_days_filled = np.nan_to_num(exit_days, nan=np.inf)

        for pos_row in range(len(trader_pos)):
            if statuses[pos_row] != 'closed':
                continue

            day = int(exit_days[pos_row])
            is_gain = exit_prices[pos_row] > entry_prices[pos_row]
            events.append({
                'trader_id': trader_id, 'day': day,
                'kind': 'realized_gain' if is_gain else 'realized_loss',
            })

            open_that_day = (statuses == 'open') | (exit_days_filled > day)
            open_that_day[pos_row] = False
            if not open_that_day.any():
                continue

            other_asset_idx = asset_idx[open_that_day]
            other_entry = entry_prices[open_that_day]
            current_prices = price_matrix[day, other_asset_idx]
            is_paper_gain = current_prices > other_entry

            events.extend(
                {'trader_id': trader_id, 'day': day,
                 'kind': 'paper_gain' if pg else 'paper_loss'}
                for pg in is_paper_gain
            )

    return pd.DataFrame(events)


def compute_pgr_plr(events_df):
    """PGR/PLR agregados a partir de un DataFrame de eventos."""
    counts = events_df['kind'].value_counts()
    rg = counts.get('realized_gain', 0)
    rl = counts.get('realized_loss', 0)
    pg = counts.get('paper_gain', 0)
    pl = counts.get('paper_loss', 0)

    pgr = rg / (rg + pg) if (rg + pg) > 0 else np.nan
    plr = rl / (rl + pl) if (rl + pl) > 0 else np.nan
    diff = pgr - plr if not (np.isnan(pgr) or np.isnan(plr)) else np.nan

    return {
        'PGR': pgr, 'PLR': plr, 'PGR_minus_PLR': diff,
        'n_realized_gains': int(rg), 'n_realized_losses': int(rl),
        'n_paper_gains': int(pg), 'n_paper_losses': int(pl),
    }


def bootstrap_pgr_plr(events_df, n_boot=1000, seed=None, ci=0.90):
    """
    Bootstrap POR CUENTA (no por transacción): en cada réplica se
    re-muestrean trader_id CON REEMPLAZO (mismo tamaño que la población
    original) y se junta TODO el historial de eventos de esos traders
    para recalcular PGR/PLR. Esto respeta que las transacciones dentro de
    una misma cuenta están correlacionadas entre sí (no son eventos
    independientes) — muestrear por transacción subestimaría el error
    estándar.
    """
    rng = np.random.default_rng(seed)
    point_estimate = compute_pgr_plr(events_df)

    if events_df.empty:
        empty = np.array([np.nan] * n_boot)
        return {
            'point_estimate': point_estimate,
            'PGR_ci': (np.nan, np.nan), 'PLR_ci': (np.nan, np.nan),
            'PGR_minus_PLR_ci': (np.nan, np.nan),
            'boot_pgr': empty, 'boot_plr': empty, 'boot_diff': empty,
        }

    trader_ids = events_df['trader_id'].unique()
    n_traders = len(trader_ids)
    grouped = {tid: g for tid, g in events_df.groupby('trader_id')}

    boot_pgr = np.empty(n_boot)
    boot_plr = np.empty(n_boot)
    boot_diff = np.empty(n_boot)

    for b in range(n_boot):
        sampled_ids = rng.choice(trader_ids, size=n_traders, replace=True)
        sample_df = pd.concat([grouped[tid] for tid in sampled_ids], ignore_index=True)
        stats = compute_pgr_plr(sample_df)
        boot_pgr[b] = stats['PGR']
        boot_plr[b] = stats['PLR']
        boot_diff[b] = stats['PGR_minus_PLR']

    alpha = 1 - ci

    def _ci(arr):
        arr = arr[~np.isnan(arr)]
        if len(arr) == 0:
            return (np.nan, np.nan)
        lo, hi = np.percentile(arr, [100 * alpha / 2, 100 * (1 - alpha / 2)])
        return (lo, hi)

    return {
        'point_estimate': point_estimate,
        'PGR_ci': _ci(boot_pgr), 'PLR_ci': _ci(boot_plr),
        'PGR_minus_PLR_ci': _ci(boot_diff),
        'boot_pgr': boot_pgr, 'boot_plr': boot_plr, 'boot_diff': boot_diff,
    }


# ---------------------------------------------------------------------------
# 2. Retornos bruto/neto y turnover por trader
# ---------------------------------------------------------------------------

def compute_trader_returns(portfolios_df, positions_df, traders_df, prices_df,
                            commission_rate=0.0005):
    """
    Retorno BRUTO y NETO por trader (promedio simple entre sus posiciones,
    válido porque portfolio.py reparte el capital en partes iguales entre
    ellas), más turnover (fracción de posiciones cerradas).

    - Bruto: cuántas acciones se hubieran comprado el día 0 SIN spread ni
      comisión (capital_per_position / precio limpio del día 0), valuadas
      al precio limpio de mercado (sin costos) en el día de venta si se
      vendió, o al último día si sigue abierta. Aísla el efecto de los
      costos de transacción por completo.
    - Neto: las acciones REALMENTE compradas (ya vienen reducidas por el
      costo de compra en portfolio.py) y, si se vendió, el precio de
      ejecución (ya trae el spread) menos la comisión de venta; si sigue
      abierta se valúa al precio limpio (no se ha pagado costo de venta
      todavía).
    - Turnover: fracción de las posiciones del trader que se vendieron
      durante la ventana de simulación (n_cerradas / target_positions).
      OJO: turnover en DÓLARES vendidos ($ vendido / capital) se ve tentador
      pero queda mecánicamente contaminado por el tamaño de la ganancia
      (una posición que subió mucho "cuenta más" turnover sólo por eso,
      generando una correlación espuria retorno-turnover). Por eso se usa
      conteo de posiciones, que es independiente del retorno logrado.
    """
    last_day = prices_df.shape[0] - 1
    day0_prices = prices_df.iloc[0]
    price_matrix = prices_df.to_numpy()
    asset_col_idx = {a: i for i, a in enumerate(prices_df.columns)}

    capital_map = traders_df.set_index('trader_id')['capital']
    n_pos_map = traders_df.set_index('trader_id')['target_positions']

    df = positions_df.copy()
    df['capital_per_position'] = (
        df['trader_id'].map(capital_map) / df['trader_id'].map(n_pos_map)
    )

    is_closed = (df['status'] == 'closed').to_numpy()
    valuation_day = np.where(is_closed, df['exit_day'].to_numpy(), last_day).astype(int)
    asset_idx = df['asset'].map(asset_col_idx).to_numpy()

    entry_price_raw = day0_prices.loc[df['asset']].to_numpy()
    raw_valuation_price = price_matrix[valuation_day, asset_idx]

    capital_pp = df['capital_per_position'].to_numpy()
    shares_gross = capital_pp / entry_price_raw
    gross_value = shares_gross * raw_valuation_price
    gross_return = gross_value / capital_pp - 1

    shares_actual = df['shares'].to_numpy()
    exit_price = df['exit_price'].to_numpy()
    net_value = np.where(
        is_closed,
        shares_actual * exit_price * (1 - commission_rate),
        shares_actual * raw_valuation_price,
    )
    net_return = net_value / capital_pp - 1

    df['gross_return'] = gross_return
    df['net_return'] = net_return
    df['is_closed'] = is_closed

    trader_stats = df.groupby('trader_id').agg(
        gross_return=('gross_return', 'mean'),
        net_return=('net_return', 'mean'),
        n_closed=('is_closed', 'sum'),
        n_positions=('is_closed', 'size'),
    ).reset_index()

    trader_stats['turnover'] = trader_stats['n_closed'] / trader_stats['n_positions']

    return trader_stats


# ---------------------------------------------------------------------------
# 3. Regresión de overconfidence (bruto vs. neto)
# ---------------------------------------------------------------------------

def _ols_simple(x, y):
    """OLS de un solo regresor, con SE/t/p-valor de la pendiente. Sin
    dependencias externas (no asume statsmodels instalado)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]
    n = len(x)

    X = np.column_stack([np.ones(n), x])
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    intercept, slope = beta

    y_hat = X @ beta
    resid = y - y_hat
    dof = n - 2
    sigma2 = (resid @ resid) / dof
    xtx_inv = np.linalg.inv(X.T @ X)
    se_intercept, se_slope = np.sqrt(np.diag(sigma2 * xtx_inv))

    t_slope = slope / se_slope
    p_slope = 2 * (1 - 0.5 * (1 + erf(abs(t_slope) / sqrt(2))))

    ss_tot = ((y - y.mean()) ** 2).sum()
    ss_res = (resid ** 2).sum()
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan

    return {
        'n': n, 'intercept': intercept, 'slope': slope,
        'se_intercept': se_intercept, 'se_slope': se_slope,
        't_slope': t_slope, 'p_slope': p_slope, 'r_squared': r_squared,
    }


def estimate_overconfidence_regression(trader_stats_df):
    """
    Corre retorno ~ turnover dos veces (bruto y neto). La comparación
    entre las dos pendientes es el diagnóstico: si turnover no predice el
    retorno bruto pero sí predice (negativamente) el retorno neto, la
    relación viene de los COSTOS de transacción y no de que quienes
    voltean más el portafolio elijan sistemáticamente peor (Barber &
    Odean, 2000).
    """
    gross_fit = _ols_simple(trader_stats_df['turnover'], trader_stats_df['gross_return'])
    net_fit = _ols_simple(trader_stats_df['turnover'], trader_stats_df['net_return'])

    return {
        'gross': gross_fit,
        'net': net_fit,
        'slope_gap': net_fit['slope'] - gross_fit['slope'],
    }


# ---------------------------------------------------------------------------
# 4. Wrapper: corre todo el diagnóstico sobre un resultado de run_scenario
# ---------------------------------------------------------------------------

def estimate_scenario(scenario_result, n_boot=1000, seed=None, commission_rate=0.0005):
    """Toma el dict que regresa scenarios.run_scenario() y calcula PGR/PLR
    (con bootstrap por cuenta) + la regresión de overconfidence."""
    positions_df = scenario_result['positions_df']
    portfolios_df = scenario_result['portfolios_df']
    traders_df = scenario_result['traders_df']
    prices_df = scenario_result['prices_df']

    events_df = compute_pgr_plr_events(positions_df, prices_df)
    pgr_plr = bootstrap_pgr_plr(events_df, n_boot=n_boot, seed=seed)

    trader_stats_df = compute_trader_returns(
        portfolios_df, positions_df, traders_df, prices_df,
        commission_rate=commission_rate,
    )
    regression = estimate_overconfidence_regression(trader_stats_df)

    return {
        'scenario_id': scenario_result['scenario_id'],
        'name': scenario_result['name'],
        'pgr_plr': pgr_plr,
        'trader_stats': trader_stats_df,
        'regression': regression,
    }