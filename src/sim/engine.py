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
        for tid, team in self.teams.items():
            wins = team.record['w']
            losses = team.record['l']
            total = wins + losses if (wins+losses) > 0 else 1
            pct = wins / total

            if pct > 0.45:
                team.strategy = "BUYER"
            elif pct < 0.35:
                team.strategy = "SELLER"
            else:
                team.strategy = "HOLD"
                    
    def calculate_utility(self, team: Team, received_players: List[Player], received_picks: List[DraftPick], 
                         lost_players: List[Player], lost_picks: List[DraftPick]) -> float:
        val_in_now = sum([self.valuation.predict_value(p) for p in received_players])
        val_out_now = sum([self.valuation.predict_value(p) for p in lost_players])

        future_val_in = sum([5_000_000 if p.round == 1 else 500_000 for p in received_picks])
        future_val_out = sum([5_000_000 if p.round == 1 else 500_000 for p in lost_picks])

        salary_change = sum([p.contract.get_salary(self.season) for p in received_players]) - \
                        sum([p.contract.get_salary(self.season) for p in lost_players])

        if team.strategy == "BUYER":
            util = (val_in_now - val_out_now) * 1.5 + (future_val_in - future_val_out) * 0.2

        elif team.strategy == "SELLER":
            util = (future_val_in - future_val_out) * 1.5 - (salary_change * 0.1)

        else:
            util = (val_in_now - val_out_now)

        return util

    def generate_trades(self, max_proposals=50) -> List[TradeProposal]:
        proposals = []
        
        buyers = [t for t in self.teams.values() if t.strategy == "BUYER"]
        sellers = [t for t in self.teams.values() if t.strategy == "SELLER"]

        if not buyers or not sellers:
            return proposals

        attempts = 0
        while len(proposals) < max_proposals and attempts < 1000:
            attempts += 1
            buyer = random.choice(buyers)
            seller = random.choice(sellers)

            trade_block = []
            for pid in seller.roster:
                if pid not in self.players:
                    continue
                p = self.players[pid]
                val = self.valuation.predict_value(p)

                is_young_core = (p.age < 25 and val > 15_000_000)
                if is_young_core:
                    continue

                if p.salary_current_year > 4_000_000:
                    trade_block.append(pid)

            if not trade_block:
                continue
            
            target = self.players[random.choice(trade_block)]
            target_val = self.valuation.predict_value(target)

            needed_salary = target.salary_current_year

            disposable = []
            assets = []

            for pid in buyer.roster:
                if pid in self.players:
                    p = self.players[pid]
                    if p.name == "LeBron James" or p.name == "Stephen Curry":
                        continue

                    surplus = self.valuation.get_surplus(p, self.season)
                    if surplus < 5_000_000:
                        disposable.append(p)
                    else:
                        assets.append(p)

            disposable.sort(key=lambda x: x.salary_current_year, reverse=True)
            assets.sort(key=lambda x: x.salary_current_year, reverse=True)

            out_assets = []
            curr_sal = 0

            min_goal = needed_salary * 0.75
            max_goal = needed_salary * 1.25

            for p in disposable:
                if curr_sal + p.salary_current_year <= max_goal + 2_000_000:
                    out_assets.append(p)
                    curr_sal += p.salary_current_year
                if curr_sal >= min_goal:
                    break

            if curr_sal < min_goal and target_val > 25_000_000:
                for p in assets:
                    if curr_sal + p.salary_current_year <= max_goal + 5_000_000:
                        out_assets.append(p)
                        curr_sal += p.salary_current_year
                    if curr_sal >= min_goal:
                        break

            if curr_sal < (needed_salary * 0.6):
                continue

            picks_out = []
            val_out = sum([self.valuation.predict_value(p) for p in out_assets])
            value_gap = target_val - val_out

            if value_gap > 5_000_000:
                pick = next((p for p in buyer.picks if p.round == 1 and p.year > self.season), None)
                if pick:
                    picks_out.append(pick)
            elif value_gap > -5_000_000:
                pick = next((p for p in buyer.picks if p.round == 2 and p.year > self.season), None)
                if pick:
                    picks_out.append(pick)

            prop = TradeProposal(
                team_a_id=buyer.id,
                team_b_id=seller.id,
                assets_a_to_b={'players': out_assets, 'picks': picks_out},
                assets_b_to_a={'players': [target], 'picks': []}
            )

            legal, reason = self.cba.validate_trade(prop, buyer, seller, self.players)
            if not legal:
                continue

            u_buyer = self.calculate_utility(buyer, [target], [], out_assets, picks_out)
            u_seller = self.calculate_utility(seller, out_assets, picks_out, [target], [])

            if u_buyer > 0 and u_seller > 0:
                prop.is_legal = True
                prop.success_probability = (u_buyer + u_seller) / 20_000_000
                prop.rationale = f"Buyer {buyer.name} acquires {target.name} for push; Seller {seller.name} acquires assets."
                proposals.append(prop)

        proposals.sort(key=lambda x: x.success_probability, reverse=True)
        return proposals
