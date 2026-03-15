import random
import uuid
from typing import List, Dict, Tuple
from .schema import Player, Team, Contract, ContractYear, DraftPick

# Extended list of real NBA players for realism
NAMES = [
    # Superstars & All-Stars
    "LeBron James", "Stephen Curry", "Kevin Durant", "Giannis Antetokounmpo", "Luka Doncic",
    "Nikola Jokic", "Joel Embiid", "Jayson Tatum", "Shai Gilgeous-Alexander", "Anthony Edwards",
    "Devin Booker", "Jimmy Butler", "Kawhi Leonard", "Paul George", "Damian Lillard",
    "Trae Young", "Ja Morant", "Zion Williamson", "Victor Wembanyama", "Chet Holmgren",
    "Paolo Banchero", "Scottie Barnes", "Tyrese Haliburton", "Tyrese Maxey", "Jalen Brunson",
    "Donovan Mitchell", "De'Aaron Fox", "Domantas Sabonis", "Bam Adebayo", "Anthony Davis",
    "Kyrie Irving", "James Harden", "Jaylen Brown", "Karl-Anthony Towns", "Rudy Gobert",
    "Lauri Markkanen", "Dejounte Murray", "Pascal Siakam", "Jamal Murray", "Brandon Ingram",
    "Zion Williamson", "LaMelo Ball", "Darius Garland", "Evan Mobley", "Jaren Jackson Jr.",
    "Desmond Bane", "Alperen Sengun", "Franz Wagner", "Cade Cunningham", "Jalen Williams",
    
    # High Level Starters / Vets
    "Jrue Holiday", "Derrick White", "Kristaps Porzingis", "Bradley Beal", "Khris Middleton",
    "Brook Lopez", "Myles Turner", "CJ McCollum", "Jerami Grant", "Anfernee Simons",
    "Kyle Kuzma", "Fred VanVleet", "Dillon Brooks", "Deandre Ayton", "Mikal Bridges",
    "Cam Johnson", "Nic Claxton", "Tyler Herro", "Terry Rozier", "Julius Randle",
    "OG Anunoby", "Josh Hart", "Aaron Gordon", "Michael Porter Jr.", "Kentavious Caldwell-Pope",
    "Austin Reaves", "D'Angelo Russell", "Rui Hachimura", "Draymond Green", "Andrew Wiggins",
    "Jonathan Kuminga", "Klay Thompson", "Chris Paul", "Malik Monk", "Keegan Murray",
    "Herbert Jones", "Trey Murphy III", "Clint Capela", "Bogdan Bogdanovic", "De'Andre Hunter",
    "Miles Bridges", "Mark Williams", "Nikola Vucevic", "Coby White", "Alex Caruso",
    "Jarrett Allen", "Caris LeVert", "Deni Avdija", "Daniel Gafford", "PJ Washington"
]

TEAMS = [
    ("ATL", "Hawks"), ("BOS", "Celtics"), ("BKN", "Nets"), ("CHA", "Hornets"), ("CHI", "Bulls"),
    ("CLE", "Cavaliers"), ("DAL", "Mavericks"), ("DEN", "Nuggets"), ("DET", "Pistons"), ("GSW", "Warriors"),
    ("HOU", "Rockets"), ("IND", "Pacers"), ("LAC", "Clippers"), ("LAL", "Lakers"), ("MEM", "Grizzlies"),
    ("MIA", "Heat"), ("MIL", "Bucks"), ("MIN", "Timberwolves"), ("NOP", "Pelicans"), ("NYK", "Knicks"),
    ("OKC", "Thunder"), ("ORL", "Magic"), ("PHI", "76ers"), ("PHX", "Suns"), ("POR", "Trail Blazers"),
    ("SAC", "Kings"), ("SAS", "Spurs"), ("TOR", "Raptors"), ("UTA", "Jazz"), ("WAS", "Wizards")
]

FIRST_NAMES = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles", "Chris", "Dan", "Paul", "Mark", "George", "Isaiah", "Jalen", "DeByron", "Tariq", "Kobe", "Shaedon", "Scoot", "Keyonte", "Gradey"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White"]

def generate_random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def generate_mock_salary(tier: str) -> List[float]:
    # Returns 4 years of salary
    base = 0
    if tier == 'SUPERMAX': base = 55_000_000
    elif tier == 'MAX': base = 40_000_000
    elif tier == 'STARTER': base = 20_000_000
    elif tier == 'ROTATION': base = 8_000_000
    else: base = 2_000_000 # Min
    
    # 5% raises
    return [base * (1.05 ** i) for i in range(5)]

def create_mock_league(current_year: int = 2025) -> Tuple[Dict[str, Team], Dict[str, Player]]:
    teams = {}
    players = {}
    
    # Shuffle names so different players end up on different teams each run
    available_names = NAMES[:]
    random.shuffle(available_names)
    
    # Create Teams
    for tid, tname in TEAMS:
        teams[tid] = Team(id=tid, name=tname, roster=[], picks=[])
        
        # Add future picks
        for y in range(current_year, current_year + 7):
            teams[tid].picks.append(DraftPick(y, 1, tid, tid))
            teams[tid].picks.append(DraftPick(y, 2, tid, tid))
            
    # Create Players
    # Distribute defined stars
    for tid in teams:
        # Each team gets 15 players
        roster_size = 15
        
        # 1. Assign 2-3 "Real" players from the list per team (Star/Starter)
        for _ in range(3):
            if available_names:
                name = available_names.pop(0)
                # Determine tier randomly but weighted
                tier = 'STARTER'
                if random.random() < 0.3: tier = 'MAX'
                if random.random() < 0.1: tier = 'SUPERMAX'
                
                pid = str(uuid.uuid4())
                salaries = generate_mock_salary(tier)
                contract = Contract(years=[
                    ContractYear(current_year + i, int(s), int(s), 'NONE') for i, s in enumerate(salaries)
                ])
                
                p = Player(
                    id=pid,
                    name=name,
                    age=random.randint(22, 35),
                    positions=[random.choice(['PG', 'SG', 'SF', 'PF', 'C'])],
                    current_team_id=tid,
                    contract=contract,
                    stats={'bpm': random.uniform(1, 8), 'ws': random.uniform(3, 12)},
                    injury_risk=random.random() * 0.2
                )
                players[pid] = p
                teams[tid].roster.append(pid)
        
        # 2. Fill the rest with generated realistic names
        current_roster_count = len(teams[tid].roster)
        missing = roster_size - current_roster_count
        
        for _ in range(missing):
            pid = str(uuid.uuid4())
            role_roll = random.random()
            if role_roll < 0.1: qt = 'STARTER'
            elif role_roll < 0.5: qt = 'ROTATION'
            else: qt = 'MIN'
            
            salaries = generate_mock_salary(qt)
            contract = Contract(years=[
                ContractYear(current_year + i, int(s), int(s), 'NONE') for i, s in enumerate(salaries)
            ])
            
            p = Player(
                id=pid,
                name=generate_random_name(),
                age=random.randint(19, 38),
                positions=[random.choice(['PG', 'SG', 'SF', 'PF', 'C'])],
                current_team_id=tid,
                contract=contract,
                stats={'bpm': random.uniform(-4, 2), 'ws': random.uniform(-1, 4)},
                injury_risk=random.random() * 0.1
            )
            players[pid] = p
            teams[tid].roster.append(pid)
            
    return teams, players
