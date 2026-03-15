from dataclasses import dataclass, field
from typing import List, Dict, Optional
import datetime

@dataclass
class ContractYear:
    season: int
    amount: float
    guaranteed: float
    option: Optional[str] = None  # 'TEAM', 'PLAYER', 'ETO', 'NONE'

@dataclass
class Contract:
    years: List[ContractYear]
    
    def get_salary(self, season: int) -> float:
        for y in self.years:
            if y.season == season:
                return y.amount
        return 0.0

@dataclass
class DraftPick:
    year: int
    round: int
    owner_id: str
    original_owner_id: str
    protections: str = "Unprotected"  # e.g., "Top-4 Protected"

    def __repr__(self):
        return f"{self.year} Rd{self.round} ({self.original_owner_id})"

@dataclass
class Player:
    id: str
    name: str
    age: int
    positions: List[str]
    current_team_id: str
    contract: Contract
    stats: Dict[str, float]  # e.g., {'bpm': 2.5, 'vorp': 1.2, 'ws': 4.5}
    injury_risk: float = 0.0  # 0 to 1 scale
    years_service: int = 0
    
    @property
    def salary_current_year(self) -> float:
        # Assuming current context year is passed externally or handled by a manager,
        # but for simple access lets grab the first relevant year or 0
        if self.contract and self.contract.years:
            return self.contract.years[0].amount
        return 0.0

@dataclass
class Team:
    id: str
    name: str
    roster: List[str]  # Player IDs
    picks: List[DraftPick]
    cap_space: Dict[str, float] = field(default_factory=dict) # {'salary': X, 'tax': Y, 'apron_1': Z}
    record: Dict[str, int] = field(default_factory=lambda: {'w': 0, 'l': 0})
    strategy: str = "NEUTRAL"  # BUYER, SELLER, HOLD
    
    # State tracking
    def current_payroll(self, player_map: Dict[str, Player], season: int) -> float:
        total = 0.0
        for pid in self.roster:
            if pid in player_map:
                total += player_map[pid].contract.get_salary(season)
        return total

@dataclass
class TradeProposal:
    team_a_id: str
    team_b_id: str
    assets_a_to_b: Dict[str, List] = field(default_factory=lambda: {'players': [], 'picks': [], 'cash': 0})
    assets_b_to_a: Dict[str, List] = field(default_factory=lambda: {'players': [], 'picks': [], 'cash': 0})
    is_legal: bool = False
    failure_reason: str = ""
    success_probability: float = 0.0
    rationale: str = ""
