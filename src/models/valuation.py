import numpy as np
from typing import List, Dict
from ..data.schema import Player
from ..features.quant_algorithms import simulate_recent_gamelog, extract_quant_features, predict_future_performance

class PlayerValueModel:
    def __init__(self):
        self.dollar_per_eff = 1_800_000
        self.replacement_level = 8.0

    def predict_value(self, player: Player) -> float:
        eff = player.stats.get('eff', 10.0)
        age = player.age

        marginal_val = (eff - self.replacement_level)
        if marginal_val < 0:
            marginal_val = 0

        base_value = marginal_val * self.dollar_per_eff

        gamelog = simulate_recent_gamelog(eff, games=30, volatility=0.15)
        quant_features = extract_quant_features(gamelog)
        quant_adjusted_base = predict_future_performance(base_value, quant_features)

        age_multiplier = 1.0

        if age < 23:
            age_multiplier = 1.3
        elif age < 26:
            age_multiplier = 1.15
        elif age > 33:
            age_multiplier = 0.8

        final_value = (quant_adjusted_base * age_multiplier) + 2_000_000

        final_value = max(final_value, 2_000_000)
        final_value = min(final_value, 65_000_000)

        return final_value

    def get_surplus(self, player: Player, season: int) -> float:
        fair = self.predict_value(player)
        salary = player.contract.get_salary(season)
        return fair - salary
