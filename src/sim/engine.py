import random
from typing import List, Dict, Tuple
from ..data.schema import Team, Player, TradeProposal, DraftPick
from ..legal.cba_rules import CBARulesEngine
from ..models.valuation import PlayerValueModel
from ..features.vectorizer import FeatureEngineer
import uuid

class TradeSimulationEngine:
    def __init__(self, teams: Dict[str, Team], players: Dict[str, Player], season: int = 2025):
        self.teams = teams
        self.players = players
        self.season = season
        self.cba = CBARulesEngine(season)
        self.valuation = PlayerValueModel()
        self.vectorizer = FeatureEngineer(season)
        
    def assign_strategies(self):
        """
        Classifies teams as BUYERS, SELLERS, or HOLDERS based on record and payroll.
        """
        for tid, team in self.teams.items():
            wins = team.record['w']
            losses = team.record['l']
            total = wins + losses if (wins+losses) > 0 else 1
            pct = wins / total
            
            # Simple Logic Rule
            if pct > 0.45: # Lowered to capture Play-In buyers
                team.strategy = "BUYER"
            elif pct < 0.35:
                team.strategy = "SELLER"
            else:
                # Mediocre - check payroll
                # With live data, payroll might be inaccurate, so default to HOLD/SELLER mix
                team.strategy = "HOLD"
                    
    def calculate_utility(self, team: Team, received_players: List[Player], received_picks: List[DraftPick], 
                         lost_players: List[Player], lost_picks: List[DraftPick]) -> float:
        """
        Calculates net change in utility for a team.
        Buyer Utility = Added Wins (Short term value)
        Seller Utility = Added Future Value (Picks + Young Talent) - Lost Salary
        """
        
        val_in_now = sum([self.valuation.predict_value(p) for p in received_players])
        val_out_now = sum([self.valuation.predict_value(p) for p in lost_players])
        
        future_val_in = sum([5_000_000 if p.round == 1 else 500_000 for p in received_picks]) # Heuristic pick val
        future_val_out = sum([5_000_000 if p.round == 1 else 500_000 for p in lost_picks])
        
        salary_change = sum([p.contract.get_salary(self.season) for p in received_players]) - \
                        sum([p.contract.get_salary(self.season) for p in lost_players])
                        
        if team.strategy == "BUYER":
            # Buyers care about Immediate Value, willing to pay Picks
            # Utility = (Val_In_Now - Val_Out_Now) * 1.5 + (Future_In - Future_Out) * 0.5
            util = (val_in_now - val_out_now) * 1.5 + (future_val_in - future_val_out) * 0.2
            
        elif team.strategy == "SELLER":
            # Sellers care about Future Value and Shedding Salary
            # Utility = (Future_In - Future_Out) * 2.0 - (Salary_Change * 0.5)
            util = (future_val_in - future_val_out) * 1.5 - (salary_change * 0.1)
            
        else: # HOLD
            util = (val_in_now - val_out_now) # Pure value trade
            
        return util

    def generate_trades(self, max_proposals=50) -> List[TradeProposal]:
        proposals = []
        
        buyers = [t for t in self.teams.values() if t.strategy == "BUYER"]
        sellers = [t for t in self.teams.values() if t.strategy == "SELLER"]
        
        # Monte Carlo Search (Simplified)
        attempts = 0
        while len(proposals) < max_proposals and attempts < 1000:
            attempts += 1
            buyer = random.choice(buyers)
            seller = random.choice(sellers)
            
            
            # Seller Logic: Protect Young Core
            # Only trade players who are NOT (Age < 25 AND Value > 15M)
            # Prioritize trading Expiring or Old Vets
            trade_block = []
            for pid in seller.roster:
                if pid not in self.players: continue
                p = self.players[pid]
                val = self.valuation.predict_value(p)
                
                is_young_core = (p.age < 25 and val > 15_000_000)
                if is_young_core: continue # Untouchable
                
                if p.salary_current_year > 4_000_000:
                    trade_block.append(pid)
                    
            if not trade_block: continue
            
            target = self.players[random.choice(trade_block)]
            target_val = self.valuation.predict_value(target)
            
            # Buyer needs to match salary
            needed_salary = target.salary_current_year
            
            # Smart Package Builder
            # 1. Identify "Disposable" assets (Low Surplus)
            # 2. Identify "Assets" (High Surplus)
            disposable = []
            assets = []
            
            for pid in buyer.roster:
                if pid in self.players:
                    p = self.players[pid]
                    if p.name == "LeBron James" or p.name == "Stephen Curry": continue # Untouchable icons
                    
                    surplus = self.valuation.get_surplus(p, self.season)
                    if surplus < 5_000_000:
                        disposable.append(p)
                    else:
                        assets.append(p)
            
            # Sort disposable by salary desc to fill bulk
            disposable.sort(key=lambda x: x.salary_current_year, reverse=True)
            assets.sort(key=lambda x: x.salary_current_year, reverse=True)
            
            # Match Logic: Try to match with Disposable first
            out_assets = []
            curr_sal = 0
            
            # Target range: 80% to 120% of salary roughly
            min_goal = needed_salary * 0.75
            max_goal = needed_salary * 1.25
            
            # Phase 1: Fill with Disposable
            for p in disposable:
                if curr_sal + p.salary_current_year <= max_goal + 2_000_000:
                    out_assets.append(p)
                    curr_sal += p.salary_current_year
                if curr_sal >= min_goal: break
                
            # Phase 2: If target is a STAR (Value > 25M), allow using Assets to finish match
            if curr_sal < min_goal and target_val > 25_000_000:
                for p in assets:
                    if curr_sal + p.salary_current_year <= max_goal + 5_000_000:
                        out_assets.append(p)
                        curr_sal += p.salary_current_year
                    if curr_sal >= min_goal: break
            
            # If still failing, skip
            if curr_sal < (needed_salary * 0.6):
                continue
                
            # Add a pick from Buyer to sweeten if Value Gap exists
            picks_out = []
            val_out = sum([self.valuation.predict_value(p) for p in out_assets])
            value_gap = target_val - val_out
            
            if value_gap > 5_000_000:
                # Add 1st
                 pick = next((p for p in buyer.picks if p.round == 1 and p.year > self.season), None)
                 if pick: picks_out.append(pick)
            elif value_gap > -5_000_000: # Neutral gap
                 pick = next((p for p in buyer.picks if p.round == 2 and p.year > self.season), None)
                 if pick: picks_out.append(pick)

                
            # Construct Proposal
            prop = TradeProposal(
                team_a_id=buyer.id,
                team_b_id=seller.id,
                assets_a_to_b={'players': out_assets, 'picks': picks_out},
                assets_b_to_a={'players': [target], 'picks': []}
            )
            
            # Check Legality
            legal, reason = self.cba.validate_trade(prop, buyer, seller, self.players)
            if not legal:
                continue
                
            # Check Utility
            u_buyer = self.calculate_utility(buyer, [target], [], out_assets, picks_out)
            u_seller = self.calculate_utility(seller, out_assets, picks_out, [target], [])
            
            if u_buyer > 0 and u_seller > 0:
                prop.is_legal = True
                prop.success_probability = (u_buyer + u_seller) / 20_000_000 # Normalize arbitrary utility
                prop.rationale = f"Buyer {buyer.name} acquires {target.name} for push; Seller {seller.name} acquires assets."
                proposals.append(prop)
                
        # Sort by Utility
        proposals.sort(key=lambda x: x.success_probability, reverse=True)
        return proposals
