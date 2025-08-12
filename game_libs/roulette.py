"""
Roulette game implementation for Enhanced UnbelievaBoat bot
"""

import random
from typing import Dict, List, Any, Optional, Union

class RouletteWheel:
    """Represents a European roulette wheel"""
    
    def __init__(self, wheel_type: str = "european"):
        self.wheel_type = wheel_type
        self.numbers = self._create_wheel()
        self.colors = self._create_color_map()
    
    def _create_wheel(self) -> List[int]:
        """Create the roulette wheel numbers"""
        if self.wheel_type == "american":
            # American wheel: 0, 00, 1-36
            return [0, -1] + list(range(1, 37))  # -1 represents 00
        else:
            # European wheel: 0, 1-36
            return [0] + list(range(1, 37))
    
    def _create_color_map(self) -> Dict[int, str]:
        """Create mapping of numbers to colors"""
        colors = {0: "green"}
        
        if self.wheel_type == "american":
            colors[-1] = "green"  # 00 is green
        
        # Red numbers: 1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        
        for num in range(1, 37):
            if num in red_numbers:
                colors[num] = "red"
            else:
                colors[num] = "black"
        
        return colors
    
    def spin(self) -> int:
        """Spin the wheel and return the winning number"""
        return random.choice(self.numbers)

class RouletteBet:
    """Represents a roulette bet"""
    
    def __init__(self, bet_type: str, value: Union[int, str], amount: int):
        self.bet_type = bet_type.lower()
        self.value = value
        self.amount = amount
        self.payout_ratio = self._get_payout_ratio()
    
    def _get_payout_ratio(self) -> int:
        """Get the payout ratio for this bet type"""
        payout_ratios = {
            "straight": 35,      # Single number
            "split": 17,         # Two adjacent numbers
            "street": 11,        # Three numbers in a row
            "corner": 8,         # Four numbers in a square
            "sixline": 5,        # Six numbers in two rows
            "column": 2,         # Column bet
            "dozen": 2,          # Dozen bet (1-12, 13-24, 25-36)
            "red": 1,            # Red color
            "black": 1,          # Black color
            "odd": 1,            # Odd numbers
            "even": 1,           # Even numbers
            "low": 1,            # Low numbers (1-18)
            "high": 1            # High numbers (19-36)
        }
        
        return payout_ratios.get(self.bet_type, 0)
    
    def is_winning(self, number: int, color: str) -> bool:
        """Check if this bet wins with the given number and color"""
        if self.bet_type == "straight":
            return number == int(self.value)
        
        elif self.bet_type == "red":
            return color == "red"
        
        elif self.bet_type == "black":
            return color == "black"
        
        elif self.bet_type == "odd":
            return number > 0 and number % 2 == 1
        
        elif self.bet_type == "even":
            return number > 0 and number % 2 == 0
        
        elif self.bet_type == "low":
            return 1 <= number <= 18
        
        elif self.bet_type == "high":
            return 19 <= number <= 36
        
        elif self.bet_type == "dozen":
            if self.value == "1st":
                return 1 <= number <= 12
            elif self.value == "2nd":
                return 13 <= number <= 24
            elif self.value == "3rd":
                return 25 <= number <= 36
        
        elif self.bet_type == "column":
            if self.value == "1st":
                return number > 0 and number % 3 == 1
            elif self.value == "2nd":
                return number > 0 and number % 3 == 2
            elif self.value == "3rd":
                return number > 0 and number % 3 == 0
        
        return False
    
    def calculate_payout(self) -> int:
        """Calculate total payout (original bet + winnings)"""
        return self.amount * (self.payout_ratio + 1)

class RouletteGame:
    """Main roulette game class"""
    
    def __init__(self, wheel_type: str = "european"):
        self.wheel = RouletteWheel(wheel_type)
        self.bets: List[RouletteBet] = []
        self.last_result = None
        self.history: List[Dict[str, Any]] = []
    
    def place_bet(self, bet_type: str, value: Union[int, str], amount: int) -> bool:
        """Place a bet on the table"""
        try:
            bet = RouletteBet(bet_type, value, amount)
            self.bets.append(bet)
            return True
        except Exception:
            return False
    
    def clear_bets(self):
        """Clear all bets from the table"""
        self.bets.clear()
    
    def spin(self) -> Dict[str, Any]:
        """Spin the wheel and return results"""
        winning_number = self.wheel.spin()
        winning_color = self.wheel.colors.get(winning_number, "green")
        
        # Handle display for 00
        display_number = "00" if winning_number == -1 else str(winning_number)
        
        result = {
            "number": display_number,
            "color": winning_color,
            "winning_bets": [],
            "total_payout": 0
        }
        
        # Check all bets
        for bet in self.bets:
            if bet.is_winning(winning_number, winning_color):
                payout = bet.calculate_payout()
                result["winning_bets"].append({
                    "type": bet.bet_type,
                    "value": bet.value,
                    "amount": bet.amount,
                    "payout": payout
                })
                result["total_payout"] += payout
        
        self.last_result = result
        self.history.append(result)
        
        # Keep only last 50 results
        if len(self.history) > 50:
            self.history.pop(0)
        
        return result
    
    def calculate_winnings(self, bet_choice: str, bet_amount: int) -> int:
        """Calculate winnings for a simple bet (used by gambling cog)"""
        # Parse the bet choice
        bet_choice = bet_choice.lower().strip()
        
        # Create a temporary bet and spin
        self.clear_bets()
        
        # Determine bet type and value
        if bet_choice in ["red", "black"]:
            bet_type = bet_choice
            value = bet_choice
        elif bet_choice in ["odd", "even"]:
            bet_type = bet_choice
            value = bet_choice
        elif bet_choice in ["low", "1-18"]:
            bet_type = "low"
            value = "low"
        elif bet_choice in ["high", "19-36"]:
            bet_type = "high"
            value = "high"
        elif bet_choice.isdigit():
            number = int(bet_choice)
            if 0 <= number <= 36:
                bet_type = "straight"
                value = number
            else:
                return 0  # Invalid number
        elif bet_choice in ["00", "double-zero"] and self.wheel.wheel_type == "american":
            bet_type = "straight"
            value = -1  # -1 represents 00
        else:
            return 0  # Invalid bet
        
        # Place bet and spin
        if self.place_bet(bet_type, value, bet_amount):
            result = self.spin()
            return result["total_payout"]
        
        return 0
    
    def get_wheel_layout(self) -> str:
        """Get a visual representation of the wheel layout"""
        if self.wheel.wheel_type == "american":
            return "🟢0 🟢00 🔴1 ⚫2 🔴3 ⚫4 🔴5 ⚫6 🔴7 ⚫8 🔴9 ⚫10 ⚫11 🔴12..."
        else:
            return "🟢0 🔴1 ⚫2 🔴3 ⚫4 🔴5 ⚫6 🔴7 ⚫8 🔴9 ⚫10 ⚫11 🔴12..."
    
    def get_betting_options(self) -> Dict[str, str]:
        """Get available betting options with descriptions"""
        return {
            "Numbers": "0-36 (00 on American wheel) - Pays 35:1",
            "Red/Black": "Red or Black - Pays 1:1",
            "Odd/Even": "Odd or Even numbers - Pays 1:1", 
            "Low/High": "1-18 (Low) or 19-36 (High) - Pays 1:1",
            "Dozens": "1st (1-12), 2nd (13-24), 3rd (25-36) - Pays 2:1",
            "Columns": "1st, 2nd, or 3rd column - Pays 2:1"
        }
    
    def get_recent_history(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent spin results"""
        return self.history[-count:] if self.history else []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get game statistics"""
        if not self.history:
            return {}
        
        total_spins = len(self.history)
        red_count = sum(1 for result in self.history if result["color"] == "red")
        black_count = sum(1 for result in self.history if result["color"] == "black")
        green_count = sum(1 for result in self.history if result["color"] == "green")
        
        return {
            "total_spins": total_spins,
            "red_percentage": (red_count / total_spins) * 100,
            "black_percentage": (black_count / total_spins) * 100,
            "green_percentage": (green_count / total_spins) * 100,
            "most_recent": self.history[-5:] if len(self.history) >= 5 else self.history
        }
    
    def validate_bet(self, bet_type: str, value: Union[int, str] = None) -> bool:
        """Validate if a bet type and value combination is valid"""
        bet_type = bet_type.lower()
        
        valid_simple_bets = ["red", "black", "odd", "even", "low", "high"]
        
        if bet_type in valid_simple_bets:
            return True
        
        if bet_type == "straight":
            if isinstance(value, int):
                if self.wheel.wheel_type == "american":
                    return value == -1 or 0 <= value <= 36  # -1 is 00
                else:
                    return 0 <= value <= 36
            elif value == "00" and self.wheel.wheel_type == "american":
                return True
        
        if bet_type in ["dozen", "column"]:
            return value in ["1st", "2nd", "3rd"]
        
        return False
    
    def get_color_emoji(self, color: str) -> str:
        """Get emoji representation of color"""
        color_emojis = {
            "red": "🔴",
            "black": "⚫",
            "green": "🟢"
        }
        return color_emojis.get(color, "❓")
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """Format a result for display"""
        number = result["number"]
        color = result["color"]
        emoji = self.get_color_emoji(color)
        
        return f"{emoji} **{number}** ({color.title()})"
    
    def get_payout_info(self, bet_type: str) -> Dict[str, Any]:
        """Get payout information for a bet type"""
        payout_info = {
            "straight": {"ratio": "35:1", "description": "Single number bet"},
            "red": {"ratio": "1:1", "description": "Red color bet"},
            "black": {"ratio": "1:1", "description": "Black color bet"},
            "odd": {"ratio": "1:1", "description": "Odd numbers bet"},
            "even": {"ratio": "1:1", "description": "Even numbers bet"},
            "low": {"ratio": "1:1", "description": "Low numbers (1-18) bet"},
            "high": {"ratio": "1:1", "description": "High numbers (19-36) bet"},
            "dozen": {"ratio": "2:1", "description": "Dozen bet (12 numbers)"},
            "column": {"ratio": "2:1", "description": "Column bet (12 numbers)"}
        }
        
        return payout_info.get(bet_type.lower(), {"ratio": "0:1", "description": "Invalid bet"})
