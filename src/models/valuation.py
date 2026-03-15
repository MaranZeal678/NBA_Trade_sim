import numpy as np
from typing import List, Dict
from ..data.schema import Player
from ..features.quant_algorithms import simulate_recent_gamelog, extract_quant_features, predict_future_performance

class PlayerValueModel:
    """
    Predicts the 'Fair Market Value' of a player based on stats and age.
    
    Model Selection Rationale:
    Selected Gradient Boosting (XGBoost) over Linear Regression due to non-linear 
    aging curves and interaction effects between usage and efficiency.
    Neural Networks were rejected due to insufficient sample size (n < 5000 player-seasons usually)
    and need for interpretability.
    
    Current Implementation:
    Uses a deterministic heuristic (proxy for a pre-trained model) to ensure 
    simulation runs without external model weights file.
    """
    
    def __init__(self):
        self.dollar_per_eff = 1_800_000 # $1.8M per Efficiency Unit (approx)
        self.replacement_level = 8.0 # Bench player efficiency
        
    def predict_value(self, player: Player) -> float:
        """
        Returns estimated fair market value in USD based on Efficiency and Age.
        """
        # Feature extraction
        eff = player.stats.get('eff', 10.0) # Default to 10 if missing
        age = player.age
        
        # 1. Base Performance Value
        # Value = (Eff - Replacement) * $Multiplier
        marginal_val = (eff - self.replacement_level)
        if marginal_val < 0: marginal_val = 0 # Replacement level floor
        
        base_value = marginal_val * self.dollar_per_eff
        
        # --- QUANTITATIVE ALGORITHM MODIFIER ---
        # Generate a mock 30-game timeseries for the player based on their efficiency
        gamelog = simulate_recent_gamelog(eff, games=30, volatility=0.15)
        # Extract quantitative indicators (RSI, MACD, Bollinger Bands)
        quant_features = extract_quant_features(gamelog)
        # Apply the predictive model to adjust the base performance value
        quant_adjusted_base = predict_future_performance(base_value, quant_features)
        # ---------------------------------------
        
        # 2. Age / Potential Multiplier
        # Young players (Age < 25) get a premium for future upside
        # Old players (Age > 33) get a discount due to decline risk
        age_multiplier = 1.0
        
        if age < 23:
            age_multiplier = 1.3 # Huge premium for < 23 (Rookie scale stars)
        elif age < 26:
            age_multiplier = 1.15
        elif age > 33:
            age_multiplier = 0.8
            
        final_value = (quant_adjusted_base * age_multiplier) + 2_000_000 # Add base roster spot value
        
        # Cap/Floor
        final_value = max(final_value, 2_000_000) # Min
        final_value = min(final_value, 65_000_000) # Supermax
        
        return final_value

    def get_surplus(self, player: Player, season: int) -> float:
        """
        Returns (Fair_Value - Actual_Salary). Positive = Good Asset.
        """
        fair = self.predict_value(player)
        salary = player.contract.get_salary(season)
        return fair - salary
