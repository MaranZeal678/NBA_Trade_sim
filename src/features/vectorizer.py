import numpy as np
from typing import List, Dict, Any
from ..data.schema import Player, Team, Contract

class FeatureEngineer:
    def __init__(self, current_year: int = 2025):
        self.year = current_year
        # Normalization constants (mocked based on historical ranges)
        self.max_age = 40
        self.max_salary_pct = 0.35
        self.max_bpm = 10.0
        self.min_bpm = -5.0
        
    def vectorize_player(self, p: Player, team_w_pct: float) -> np.ndarray:
        """
        Returns vector: [
            Age_Norm, 
            Salary_Cap_Pct, 
            Years_Left, 
            BPM_Norm, 
            Injury_Risk,
            Team_Performance_Context,
            Expiring_Status (Binary)
        ]
        """
        # 1. Age (20-40 normalized)
        age_norm = (p.age - 20) / 20.0
        
        # 2. Contract
        salary = p.contract.get_salary(self.year)
        cap_val = 155_000_000 # Using constant from CBA roughly
        sal_pct = min(salary / cap_val, 1.0)
        
        years_left = 0
        if p.contract and p.contract.years:
            years_left = len([y for y in p.contract.years if y.season > self.year])
        
        is_expiring = 1.0 if years_left == 0 else 0.0
            
        # 3. Performance
        bpm = p.stats.get('bpm', 0)
        bpm_norm = (bpm - self.min_bpm) / (self.max_bpm - self.min_bpm)
        
        return np.array([
            age_norm,
            sal_pct,
            years_left / 5.0, # Max contract length approx
            bpm_norm,
            p.injury_risk,
            team_w_pct,
            is_expiring
        ])
        
    def vectorize_team(self, t: Team, player_map: Dict[str, Player]) -> np.ndarray:
        """
        Returns vector: [
            Win_Pct,
            Payroll_Pct,
            Roster_Avg_Age_Norm,
            Asset_Inventory_Score
        ]
        """
        games = t.record['w'] + t.record['l']
        win_pct = t.record['w'] / games if games > 0 else 0.5
        
        payroll = t.current_payroll(player_map, self.year)
        pay_pct = payroll / 155_000_000
        
        # Roster Age
        ages = [player_map[pid].age for pid in t.roster if pid in player_map]
        avg_age = sum(ages)/len(ages) if ages else 25
        age_norm = (avg_age - 20) / 20.0
        
        # Asset Score (Simple heuristic: 1st rounders count more)
        asset_score = 0
        for p in t.picks:
            if p.year > self.year:
                asset_score += (4.0 if p.round == 1 else 1.0)
        
        asset_norm = min(asset_score / 30.0, 1.0)
        
        return np.array([
            win_pct,
            pay_pct,
            age_norm,
            asset_norm
        ])
