import pandas as pd
import numpy as np

# 1. Define Historical Salary Caps
salary_cap_history = {
    2010: 58044000, 2011: 58044000, 2012: 58044000, 2013: 58679000,
    2014: 63065000, 2015: 70000000, 2016: 94143000, 2017: 99093000,
    2018: 101869000, 2019: 109140000, 2020: 109140000, 2021: 112414000,
    2022: 123655000, 2023: 136021000, 2024: 140588000, 2025: 154646000 # Projected
}

def get_cap_pct(salary, year):
    """Normalizes salary based on that year's cap."""
    cap = salary_cap_history.get(year, 140588000)
    return (salary / cap) * 100

# 2. Mock Oracle Model -> Quant Oracle Model
class QuantOracle:
    def predict(self, features_df):
        from src.features.quant_algorithms import simulate_recent_gamelog, extract_quant_features, predict_future_performance
        
        predicted_vals = []
        for _, row in features_df.iterrows():
            # Base value heuristic
            base_val = row.get('pts', 10) + row.get('ast', 2) + row.get('trb', 3) 
            
            # Simulate a 30-game timeseries for the player to feed the quant indicators
            # This mimics having real game-by-game data
            gamelog = simulate_recent_gamelog(base_val, games=30, volatility=0.2)
            
            # Extract Quant Indicators (RSI, MACD, etc)
            quant_features = extract_quant_features(gamelog)
            
            # Predict modified future performance
            final_pred = predict_future_performance(base_val, quant_features)
            predicted_vals.append(final_pred)
            
        return np.array(predicted_vals)

oracle = QuantOracle()

# 3. Helper Functions
def simulate_team_performance(team_stats, rosters, continuity_dict):
    """
    Simulates win/loss records based on Net Rating and Chemistry.
    """
    results = []
    for team in team_stats:
        # 1. Get Base Net Rating (Offense - Defense)
        base_net_rating = team['ortg'] - team['drtg']
        
        # 2. Apply Chemistry Multiplier
        continuity = continuity_dict.get(team['id'], 0.5)
        chemistry_boost = (continuity - 0.5) * 2.0
        
        adj_net_rating = base_net_rating + chemistry_boost
        
        # 3. Convert Net Rating to Pythagorean Win %
        exp_win_pct = 0.5 + (0.03 * adj_net_rating)
        
        # 4. Predict Record at Game 50
        predicted_wins = round(50 * exp_win_pct)
        results.append({
            'team_id': team['id'],
            'wins': predicted_wins,
            'losses': 50 - predicted_wins,
            'net_rating': adj_net_rating,
            'tax': team.get('tax', 0),
            'gm_tenure': team.get('gm_tenure', 5)
        })
    return pd.DataFrame(results)

def calculate_desperation(predicted_wins, luxury_tax_bill, gm_tenure):
    """
    Quantifies how likely a GM is to make a "risky" trade.
    """
    win_gap = max(0, 45 - predicted_wins)
    tax_pressure = np.log1p(luxury_tax_bill)
    tenure_multiplier = 1.5 if gm_tenure < 2 else 1.0
    desperation_score = (win_gap * tax_pressure) * tenure_multiplier
    return desperation_score

def is_cba_compliant(team_a_out, team_b_out, team_a_status, team_b_status):
    """
    Validates if a trade is legal under 2026 CBA rules.
    """
    if team_a_status == 'Second_Apron' and len(team_a_out) > 1:
        return False, "Second Apron teams cannot aggregate salaries."
    
    val_a = sum([p['salary'] for p in team_a_out])
    val_b = sum([p['salary'] for p in team_b_out])
    
    if team_a_status == 'Second_Apron':
        if val_b > val_a: return False, "Second Apron: Cannot take back more salary."
    elif team_a_status == 'First_Apron':
        if val_b > (val_a * 1.10): return False, "First Apron: 110% limit exceeded."
    else: # Below Apron
        if val_b > (val_a * 1.25 + 250000): return False, "Under Apron: 125% limit exceeded."
        
    return True, "Trade is legal."

def calculate_roster_alpha(roster):
    # Mock alpha calculation
    return sum([p.get('alpha', 0) for p in roster])

def simulate_wins(roster):
    # Mock win simulation based on roster
    return len(roster) * 2 # Just a dummy value

def attempt_negotiation(b_id, s_id, player_data):
    """
    Mock negotiation logic.
    """
    buyer_players = player_data[player_data['team_id'] == b_id].to_dict('records')
    seller_players = player_data[player_data['team_id'] == s_id].to_dict('records')
    
    if not buyer_players or not seller_players:
        return {'legal': False}
    
    # Try a simple 1-for-1 swap for the sake of simulation
    p_a = buyer_players[0]
    p_b = seller_players[0]
    
    legal, reason = is_cba_compliant([p_a], [p_b], 'Below', 'Below')
    
    return {
        'legal': legal,
        'team_a': b_id,
        'team_b': s_id,
        'team_a_name': f"Team {b_id}",
        'team_b_name': f"Team {s_id}",
        'team_a_out': [p_a],
        'team_b_out': [p_b],
        'impact': {
            'team_a': {'win_gain': 2.1, 'alpha_gain': 1.5},
            'team_b': {'win_gain': -1.2, 'alpha_gain': 5.0}
        },
        'persona_logic': "Mutually beneficial swap.",
        'new_roster': {b_id: [], s_id: []}, # Placeholder
        'old_alpha': {b_id: 10, s_id: 15}, # Placeholder
        'old_wins': {b_id: 30, s_id: 20} # Placeholder
    }

# 4. Main Simulation Function
features = ['age', 'pts', 'ast', 'trb', 'bpm', 'usg_pct', 'ts_pct', 'per']

def run_trade_deadline_simulation(player_data, team_metadata, current_year=2026):
    print(f"--- Starting NBA Trade Deadline Engine ({current_year}) ---")
    
    # Reset columns to lowercase to match logic
    api_mapping = {
        'PLAYER_AGE': 'age',
        'PTS': 'pts',
        'AST': 'ast',
        'REB': 'trb',
        'USG_PCT': 'usg_pct',
        'TS_PCT': 'ts_pct'
    }
    player_data = player_data.rename(columns=api_mapping)
    
    # Ensure all features exist
    for f in features:
        if f not in player_data.columns:
            player_data[f] = 0
            
    # STEP 1: Data Normalization
    player_data['cap_pct'] = player_data.apply(
        lambda x: get_cap_pct(x['salary'], current_year), axis=1
    )
    
    # STEP 2: The Oracle Valuation
    player_data['predicted_val'] = oracle.predict(player_data[features])
    player_data['alpha'] = player_data['predicted_val'] - player_data['cap_pct']
    
    # STEP 3: Season Simulation
    # Creating mock inputs for simulate_team_performance
    team_stats = team_metadata.to_dict('records')
    rosters = {} # Mock
    continuity_dict = {t['id']: 0.8 for t in team_stats}
    
    standings = simulate_team_performance(team_stats, rosters, continuity_dict)
    
    # STEP 4: Strategy Assignment
    team_strategies = {}
    for _, team in standings.iterrows():
        desperation = calculate_desperation(team['wins'], team['tax'], team['gm_tenure'])
        if team['wins'] > 30: # Lowered threshold for mock variety
            team_strategies[team['team_id']] = {'mode': 'BUYER', 'risk': desperation}
        else:
            team_strategies[team['team_id']] = {'mode': 'SELLER', 'risk': desperation}
            
    # STEP 5: Matching Engine
    proposed_trades = []
    buyers = [t for t, s in team_strategies.items() if s['mode'] == 'BUYER']
    sellers = [t for t, s in team_strategies.items() if s['mode'] == 'SELLER']
    
    for b_id in buyers:
        for s_id in sellers:
            trade = attempt_negotiation(b_id, s_id, player_data)
            if trade['legal']:
                proposed_trades.append(trade)
                
    return proposed_trades

# 5. Initialization and Execution
if __name__ == "__main__":
    # Create Mock Data
    mock_players = pd.DataFrame({
        'name': ['LeBron James', 'Kevin Durant', 'Steph Curry', 'Luka Doncic', 'Nikola Jokic'],
        'team_id': [1, 2, 3, 4, 5],
        'salary': [47607350, 47607350, 51915615, 40064220, 47607350],
        'age': [39, 35, 36, 25, 29],
        'pts': [25.7, 27.1, 26.4, 33.9, 26.4],
        'ast': [8.3, 5.0, 5.1, 9.8, 9.0],
        'trb': [7.3, 6.6, 4.5, 9.2, 12.4],
        'ts_pct': [0.6, 0.6, 0.6, 0.6, 0.6],
        'usg_pct': [30, 30, 30, 35, 30]
    })
    
    mock_teams = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Lakers', 'Suns', 'Warriors', 'Mavericks', 'Nuggets'],
        'ortg': [115, 118, 117, 120, 119],
        'drtg': [114, 115, 116, 118, 112],
        'tax': [50000000, 40000000, 100000000, 0, 20000000],
        'gm_tenure': [3, 1, 1, 4, 6]
    })
    
    results = run_trade_deadline_simulation(mock_players, mock_teams)
    
    print("\n--- Simulation Results ---")
    print(f"Total trades found: {len(results)}")
    for t in results:
        print(f"TRADE: {t['team_a_name']} receives {t['team_b_out'][0]['name']}, {t['team_b_name']} receives {t['team_a_out'][0]['name']}")
        print(f"  Reason: {t['persona_logic']}")
