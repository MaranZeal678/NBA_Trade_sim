import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from src.data.live_loader import LiveDataLoader
except ImportError:
    LiveDataLoader = None

from src.data.mock_data import create_mock_league
from src.sim.engine import TradeSimulationEngine
from src.sim.ai_agent import AITradeEvaluator

def load_data():
    if LiveDataLoader is None:
        print("nba_api not installed. Using mock league data.")
        return create_mock_league()

    try:
        loader = LiveDataLoader()
        teams, players = loader.load_league()
        if not teams or not players:
            raise RuntimeError("empty live data")
        return teams, players
    except Exception as exc:
        print(f"Live data failed: {exc}")
        print("Using mock league data.")
        return create_mock_league()

def main():
    print("--- NBA QUANT TRADE SIMULATOR ---")
    print("Loading league data...")

    teams, players = load_data()
    print(f"Loaded {len(teams)} teams and {len(players)} players.")

    engine = TradeSimulationEngine(teams, players, 2025)

    print("Assigning Team Strategies (Buyer/Seller/Hold)...")
    for tid, t in teams.items():
        if tid in ['BOS', 'DEN', 'OKC', 'MIN']: 
            t.record = {'w': 45, 'l': 15}
        elif tid in ['WAS', 'DET', 'POR', 'CHA']:
            t.record = {'w': 15, 'l': 45}
        else:
            import random
            w = random.randint(25, 35)
            t.record = {'w':w, 'l': 60-w}
            
    engine.assign_strategies()

    print("\n=== PROJECTED STANDINGS (Game 60) ===")
    sorted_teams = sorted(teams.values(), key=lambda x: x.record['w'], reverse=True)
    print(f"{'TEAM':<20} {'W-L':<10} {'STRATEGY':<10}")
    print("-" * 45)
    for t in sorted_teams:
        print(f"{t.name:<20} {t.record['w']}-{t.record['l']:<5} {t.strategy}")
    print("-" * 45)
    
    buyers = [t.id for t in teams.values() if t.strategy == 'BUYER']
    sellers = [t.id for t in teams.values() if t.strategy == 'SELLER']
    print(f"Market State: {len(buyers)} Buyers, {len(sellers)} Sellers.")

    print("Running Monte Carlo Trade Search (checking CBA Legality)...")
    trades = engine.generate_trades(max_proposals=10)

    print("AI Agent evaluating the final trade proposals...")
    ai_evaluator = AITradeEvaluator()

    print(f"\nFound {len(trades)} CBA-Legal, Mutually Beneficial Trades.\n")
    print("=== TOP RECOMMENDED TRADES ===")

    for i, t in enumerate(trades[:5]):
        t_a = teams[t.team_a_id]
        t_b = teams[t.team_b_id]
        
        print(f"\n#{i+1} [Prob: {t.success_probability:.2f}]")
        print(f"{t_a.name} ({t_a.strategy}) gets:")
        for p in t.assets_b_to_a['players']:
            print(f" - {p.name} (${p.salary_current_year:,.0f}) [BPM: {p.stats['bpm']:.1f}]")
            
        print(f"{t_b.name} ({t_b.strategy}) gets:")
        for p in t.assets_a_to_b['players']:
            print(f" - {p.name} (${p.salary_current_year:,.0f})")
        for pick in t.assets_a_to_b['picks']:
            print(f" - {pick}")
            
        in_a = sum(p.salary_current_year for p in t.assets_b_to_a['players'])
        out_a = sum(p.salary_current_year for p in t.assets_a_to_b['players'])
        match_pct = (in_a / out_a) * 100 if out_a else 0
        print(f"Salary Math: {t_a.id} sends ${out_a:,.0f} -> receives ${in_a:,.0f} ({match_pct:.1f}%)")
        print(f"Engine Rationale: {t.rationale}")

        val_a = sum(p.stats.get('bpm', 1) for p in t.assets_b_to_a['players'])
        val_b = sum(p.stats.get('bpm', 1) for p in t.assets_a_to_b['players'])

        eval_result = ai_evaluator.evaluate_trade(
            team_a_name=t_a.name, team_a_strategy=t_a.strategy, team_a_received_value=val_a,
            team_b_name=t_b.name, team_b_strategy=t_b.strategy, team_b_received_value=val_b
        )
        print("\nAI Agent Analysis:")
        print(f"Grade {t_a.name}: {eval_result['grade_a']} | Grade {t_b.name}: {eval_result['grade_b']}")
        print(eval_result['ai_analysis'])
        print("-" * 50)

if __name__ == "__main__":
    main()
