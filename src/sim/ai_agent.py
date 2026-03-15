import random

class AITradeEvaluator:
    """
    An AI Agent representing an intelligent General Manager / Analyst.
    In a full production environment, this agent would ping an LLM (like GPT-4 or Claude)
    to generate natural language evaluations of trades.
    For this simulation, it uses a heuristic rule-based "AI" to assign grades and provide
    persona-driven rationale for the proposed trades.
    """
    
    def __init__(self):
        self.personas = ["Aggressive Buyer", "Cautious Rebuilder", "Analytics Nerd"]
        
    def evaluate_trade(self, team_a_name: str, team_a_strategy: str, team_a_received_value: float,
                       team_b_name: str, team_b_strategy: str, team_b_received_value: float) -> dict:
        """
        The AI Agent evaluates the trade based on the strategies and value exchanged.
        Returns a dictionary with 'grade_a', 'grade_b', and an 'ai_analysis' string.
        """
        
        # Calculate relative value (1.0 means perfectly even)
        # Avoid division by zero
        val_a = max(team_a_received_value, 0.1)
        val_b = max(team_b_received_value, 0.1)
        
        ratio = val_a / val_b
        
        # Determine Grades
        if ratio > 1.2:
            grade_a = "A"
            grade_b = "C-"
        elif ratio > 1.05:
            grade_a = "A-"
            grade_b = "B-"
        elif ratio > 0.95:
            grade_a = "B+"
            grade_b = "B+"
        elif ratio > 0.8:
            grade_a = "B-"
            grade_b = "A-"
        else:
            grade_a = "C-"
            grade_b = "A"
            
        persona = random.choice(self.personas)
        
        if persona == "Analytics Nerd":
            analysis = f"[AI Analyst]: Quant models love the value {team_a_name} is getting. The expected surplus value here makes this a very efficient allocation of cap space."
        elif persona == "Aggressive Buyer":
            analysis = f"[AI Aggressive GM]: {team_a_name} is in WIN NOW mode. You have to overpay sometimes to get the piece that pushes you over the top. Good trade."
        else:
            analysis = f"[AI Rebuilder]: {team_b_name} is doing the right thing. Liquidate veteran assets for future draft capital. It hurts now, but it's the right long-term play."
            
        return {
            "grade_a": grade_a,
            "grade_b": grade_b,
            "ai_analysis": analysis
        }
