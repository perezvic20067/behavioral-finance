from numpy.random import SeedSequence

def get_scenario_rngs(scenario_id, base_seed=42):
    ss = SeedSequence(base_seed, spawn_key=(scenario_id,))
    market_seed, traders_seed = ss.spawn(2)
    return market_seed, traders_seed
    