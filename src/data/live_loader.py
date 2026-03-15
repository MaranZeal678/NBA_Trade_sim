import time
import random
import json
import os
from typing import Dict, Tuple, List
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster, playerprofilev2, leaguestandingsv3, leaguedashplayerstats
from .schema import Team, Player, Contract, ContractYear, DraftPick

class LiveDataLoader:
    def __init__(self, season="2024-25"):
        self.season = season
        self.cache_dir = "data_cache"
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_all_teams(self) -> List[Dict]:
        return teams.get_teams()
        
    def _fetch_standings(self) -> Dict[str, Dict[str, int]]:
        """Returns map of TeamID -> {'w': int, 'l': int}"""
        print("Fetching Live Standings...")
        try:
            standings = leaguestandingsv3.LeagueStandingsV3(season=self.season)
            data = standings.get_normalized_dict()['Standings']
            res = {}
            for row in data:
                tid = str(row['TeamID'])
                res[tid] = {'w': int(row['WINS']), 'l': int(row['LOSSES'])}
            return res
        except Exception as e:
            print(f"Error fetching standings: {e}")
            return {}

    def _fetch_stats(self) -> Dict[str, Dict[str, float]]:
        """Returns map of PlayerID -> {'bpm': float, 'ws': float, 'ppg': float, ...}"""
        print("Fetching League Player Stats...")
        try:
            stats = leaguedashplayerstats.LeagueDashPlayerStats(season=self.season)
            data = stats.get_normalized_dict()['LeagueDashPlayerStats']
            res = {}
            for row in data:
                pid = str(row['PLAYER_ID'])
                gp = row['GP'] if row['GP'] > 0 else 1
                
                # Simple Efficiency Calculation
                # (PTS + REB + AST + STL + BLK - Missed FG - Missed FT - TO) / GP
                eff = (row['PTS'] + row['REB'] + row['AST'] + row['STL'] + row['BLK'] 
                       - (row['FGA'] - row['FGM']) 
                       - (row['FTA'] - row['FTM']) 
                       - row['TOV']) / gp
                
                # Normalize 'BPM' proxy using Efficiency
                # Avg Eff is approx 15. Scale to -5 to +10 range roughly.
                bpm_proxy = (eff - 10) / 2.0 
                
                res[pid] = {
                    'ppg': row['PTS'] / gp,
                    'rpg': row['REB'] / gp,
                    'apg': row['AST'] / gp,
                    'eff': eff,
                    'bpm': bpm_proxy,
                    'ws': row['NBA_FANTASY_PTS'] / 100.0 # Rough proxy
                }
            return res
        except Exception as e:
            print(f"Error fetching stats: {e}")
            return {}

    def get_roster(self, team_id: int) -> List[Dict]:
        """Fetches roster for a team with simple caching."""
        cache_path = f"{self.cache_dir}/roster_{team_id}.json"
        
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                return json.load(f)
                
        # Fetch from API
        print(f"Fetching roster for Team {team_id}...")
        try:
            roster = commonteamroster.CommonTeamRoster(team_id=team_id, season=self.season)
            data = roster.get_normalized_dict()['CommonTeamRoster']
            time.sleep(0.600) # Rate limit respect
            
            with open(cache_path, 'w') as f:
                json.dump(data, f)
            return data
        except Exception as e:
            print(f"Error serving {team_id}: {e}")
            return []

    def estimate_contract(self, player_name: str, age: int, stats: Dict[str, float]) -> Contract:
        """
        Estimates salary based on Performance (PPG) and Age.
        """
        # 1. Hardcoded Superstars (to be safe)
        superstars = {
            "Stephen Curry": 55_000_000, "Joel Embiid": 51_000_000, "Nikola Jokic": 51_000_000,
            "Bradley Beal": 50_000_000, "Kevin Durant": 49_000_000, "Devin Booker": 49_000_000,
            "Karl-Anthony Towns": 49_000_000, "Paul George": 49_000_000, "Kawhi Leonard": 49_000_000,
            "Jimmy Butler": 48_000_000, "Giannis Antetokounmpo": 48_000_000, "LeBron James": 48_000_000,
            "Damian Lillard": 48_000_000, "Luka Doncic": 43_000_000, "Trae Young": 43_000_000,
            "Zach LaVine": 43_000_000, "Fred VanVleet": 42_000_000, "Anthony Davis": 40_000_000,
            "Kyrie Irving": 40_000_000, "Rudy Gobert": 41_000_000, "Jaylen Brown": 49_000_000
        }
        
        salary = superstars.get(player_name)
        
        if not salary:
            # 2. Performance Heuristic
            ppg = stats.get('ppg', 0)
            
            if ppg > 22.0: 
                salary = 35_000_000 # Max Tier
            elif ppg > 18.0:
                salary = 25_000_000 # High Starter
            elif ppg > 14.0:
                salary = 18_000_000 # Solid Starter
            elif ppg > 10.0:
                salary = 12_000_000 # Rotation
            elif ppg > 6.0:
                salary = 6_000_000 # Bench
            else:
                salary = 2_500_000 # Min
                
            # Rookie Scale Adjustment
            if age < 23 and salary > 10_000_000:
                salary = 10_000_000 # Cap rookie deals roughly
            
        contract_years = []
        for i in range(4):
            amt = int(salary * (1.05 ** i))
            contract_years.append(ContractYear(2025+i, amt, amt, "NONE"))
            
        return Contract(years=contract_years)

    def load_league(self) -> Tuple[Dict[str, Team], Dict[str, Player]]:
        nba_teams = self.get_all_teams()
        league_teams = {}
        league_players = {}
        
        standings_map = self._fetch_standings()
        stats_map = self._fetch_stats()
        
        for t in nba_teams:
            tid_int = t['id']
            tid_str = str(tid_int)
            abbr = t['abbreviation']
            name = t['nickname']
            
            # Create Team Object
            record = standings_map.get(tid_str, {'w': 0, 'l': 0})
            new_team = Team(id=abbr, name=name, roster=[], picks=[], record=record)
            
            # Add Picks
            current_year = 2025
            for y in range(current_year, current_year + 7):
                new_team.picks.append(DraftPick(y, 1, abbr, abbr))
                new_team.picks.append(DraftPick(y, 2, abbr, abbr))
            
            # Get Roster
            roster_data = self.get_roster(tid_int)
            
            for p_data in roster_data:
                p_name = p_data['PLAYER']
                pid = str(p_data['PLAYER_ID'])
                age = int(float(p_data['AGE'])) if p_data['AGE'] else 25
                
                # Get Stats
                # Default to replacement level
                p_stats = stats_map.get(pid, {'bpm': -2.0, 'ws': 0.1, 'eff': 8.0, 'ppg': 5.0}) 
                
                # Create Player Object
                contract = self.estimate_contract(p_name, age, p_stats)
                
                player = Player(
                    id=pid,
                    name=p_name,
                    age=age,
                    positions=[p_data['POSITION']] if p_data['POSITION'] else ['SF'],
                    current_team_id=abbr,
                    contract=contract,
                    stats=p_stats,
                    injury_risk=0.05
                )
                
                league_players[pid] = player
                new_team.roster.append(pid)
            
            league_teams[abbr] = new_team
            
        return league_teams, league_players

if __name__ == "__main__":
    loader = LiveDataLoader()
    t, p = loader.load_league()
    print(f"Loaded {len(t)} teams and {len(p)} players from NBA API.")
    print(f"Sample: {p[list(p.keys())[0]].name} plays for {p[list(p.keys())[0]].current_team_id}")
