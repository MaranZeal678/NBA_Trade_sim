from typing import List, Dict, Tuple
from ..data.schema import Team, Player, TradeProposal, DraftPick

SALARY_CAP = 155_000_000
LUXURY_TAX = 188_000_000
FIRST_APRON = 196_000_000
SECOND_APRON = 208_000_000

class CBARulesEngine:
    def __init__(self, season: int = 2025):
        self.season = season

    def calculate_outgoing_salary(self, players: List[Player]) -> float:
        return sum(p.contract.get_salary(self.season) for p in players)

    def get_team_status(self, team: Team, player_map: Dict[str, Player]) -> str:
        payroll = team.current_payroll(player_map, self.season)
        if payroll > SECOND_APRON: return "SECOND_APRON"
        if payroll > FIRST_APRON: return "FIRST_APRON"
        if payroll > LUXURY_TAX: return "TAX"
        if payroll > SALARY_CAP: return "OVER_CAP"
        return "ROOM"

    def validate_salary_matching(self, team_a: Team, team_b: Team, 
                               prop: TradeProposal, player_map: Dict[str, Player]) -> Tuple[bool, str]:
        out_a = self.calculate_outgoing_salary(prop.assets_a_to_b.get('players', []))
        out_b = self.calculate_outgoing_salary(prop.assets_b_to_a.get('players', []))

        status_a = self.get_team_status(team_a, player_map)
        status_b = self.get_team_status(team_b, player_map)

        if status_a == "SECOND_APRON" and len(prop.assets_a_to_b.get('players', [])) > 1:
            return False, f"Team {team_a.name} is Second Apron and cannot aggregate salaries."
        if status_b == "SECOND_APRON" and len(prop.assets_b_to_a.get('players', [])) > 1:
            return False, f"Team {team_b.name} is Second Apron and cannot aggregate salaries."

        valid_a, msg_a = self._check_single_team_matching(status_a, out_a, out_b)
        if not valid_a: return False, f"{team_a.name} Fail: {msg_a}"

        valid_b, msg_b = self._check_single_team_matching(status_b, out_b, out_a)
        if not valid_b: return False, f"{team_b.name} Fail: {msg_b}"

        return True, "Salary Valid"

    def _check_single_team_matching(self, status: str, outgoing: float, incoming: float) -> Tuple[bool, str]:
        if status == "SECOND_APRON":
            if incoming > outgoing:
                return False, f"Second Apron team cannot take back more salary ({incoming} > {outgoing})"
            return True, "OK"

        elif status == "FIRST_APRON" or status == "TAX":
            limit = (outgoing * 1.10) + 100_000
            if incoming > limit:
                return False, f"Tax/Apron team exceeded 110% matching ({incoming} > {limit})"
            return True, "OK"

        else:
            limit = (outgoing * 1.25) + 250_000
            if incoming > limit:
                return False, f"Non-Tax team exceeded 125% matching ({incoming} > {limit})"
            return True, "OK"

    def validate_stepien(self, team: Team, proposal_picks_out: List[DraftPick]) -> Tuple[bool, str]:
        future_firsts_out = sorted([p.year for p in proposal_picks_out if p.round == 1 and p.year > self.season])

        if not future_firsts_out:
            return True, "No firsts traded"

        for i in range(len(future_firsts_out) - 1):
            if future_firsts_out[i+1] == future_firsts_out[i] + 1:
                return False, "Cannot trade consecutive future first round picks (Stepien Rule)"

        return True, "Stepien OK"

    def validate_trade(self, prop: TradeProposal, team_a: Team, team_b: Team, players: Dict[str, Player]) -> Tuple[bool, str]:
        sal_ok, sal_msg = self.validate_salary_matching(team_a, team_b, prop, players)
        if not sal_ok: return False, sal_msg

        picks_a = prop.assets_a_to_b.get('picks', [])
        step_a, step_msg_a = self.validate_stepien(team_a, picks_a)
        if not step_a: return False, f"Team A {step_msg_a}"

        picks_b = prop.assets_b_to_a.get('picks', [])
        step_b, step_msg_b = self.validate_stepien(team_b, picks_b)
        if not step_b: return False, f"Team B {step_msg_b}"
        
        return True, "Trade Legal"
