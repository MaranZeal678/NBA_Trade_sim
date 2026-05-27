from dataclasses import dataclass, field
from typing import List, Dict, Optional
import datetime

@dataclass
class ContractYear:
    season: int
    amount: float
    guaranteed: float
    option: Optional[str] = None

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
    protections: str = "Unprotected"

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
    stats: Dict[str, float]
    injury_risk: float = 0.0
    years_service: int = 0

    @property
    def salary_current_year(self) -> float:
        if self.contract and self.contract.years:
            return self.contract.years[0].amount
        return 0.0

@dataclass
class Team:
    id: str
    name: str
    roster: List[str]
    picks: List[DraftPick]
    cap_space: Dict[str, float] = field(default_factory=dict)
    record: Dict[str, int] = field(default_factory=lambda: {'w': 0, 'l': 0})
    strategy: str = "NEUTRAL"

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
