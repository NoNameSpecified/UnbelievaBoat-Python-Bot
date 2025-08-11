"""
Configuration settings for the Enhanced UnbelievaBoat bot
"""
import os
from typing import List, Optional

class BotConfig:
    """Central configuration for the bot"""
    
    # Bot Settings
    PREFIX: str = os.getenv('BOT_PREFIX', '+')
    BOT_VERSION: str = "3.0.0"
    BOT_NAME: str = "Enhanced UnbelievaBoat"
    
    # Discord Settings
    SYNC_COMMANDS_ON_STARTUP: bool = os.getenv('SYNC_COMMANDS', 'false').lower() == 'true'
    SETUP_CHANNEL_ID: Optional[int] = int(os.getenv('SETUP_CHANNEL_ID', '0')) or None
    
    # Database Settings
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', 'database/economy.db')
    
    # Economy Settings
    DEFAULT_BALANCE: int = int(os.getenv('DEFAULT_BALANCE', '1000'))
    DEFAULT_CURRENCY: str = os.getenv('CURRENCY_EMOJI', '💰')
    MAX_BET: int = int(os.getenv('MAX_BET', '1000000'))
    MIN_BET: int = int(os.getenv('MIN_BET', '10'))
    
    # Income Settings
    WORK_COOLDOWN: int = int(os.getenv('WORK_COOLDOWN', '300'))  # 5 minutes
    CRIME_COOLDOWN: int = int(os.getenv('CRIME_COOLDOWN', '600'))  # 10 minutes
    SLUT_COOLDOWN: int = int(os.getenv('SLUT_COOLDOWN', '900'))  # 15 minutes
    ROB_COOLDOWN: int = int(os.getenv('ROB_COOLDOWN', '1200'))  # 20 minutes
    
    # Gambling Settings  
    BLACKJACK_COOLDOWN: int = int(os.getenv('BLACKJACK_COOLDOWN', '30'))
    ROULETTE_COOLDOWN: int = int(os.getenv('ROULETTE_COOLDOWN', '60'))
    
    # Leveling Settings
    XP_PER_MESSAGE: int = int(os.getenv('XP_PER_MESSAGE', '15'))
    XP_COOLDOWN: int = int(os.getenv('XP_COOLDOWN', '60'))  # 1 minute
    PASSIVE_CHAT_INCOME: int = int(os.getenv('PASSIVE_CHAT_INCOME', '5'))
    
    # Admin Settings
    ADMIN_ROLE_NAME: str = os.getenv('ADMIN_ROLE_NAME', 'botmaster')
    
    # Moderation Settings
    MAX_WARNS_BEFORE_ACTION: int = int(os.getenv('MAX_WARNS', '3'))
    DEFAULT_MUTE_DURATION: int = int(os.getenv('DEFAULT_MUTE_DURATION', '600'))  # 10 minutes
    
    # Error Messages
    ERROR_MESSAGES = {
        'insufficient_funds': "You don't have enough money for this action!",
        'invalid_amount': "Please provide a valid amount!",
        'user_not_found': "User not found in the database!",
        'item_not_found': "Item not found!",
        'no_permission': "You don't have permission to use this command!",
        'cooldown_active': "This command is on cooldown. Please wait before using it again.",
        'database_error': "A database error occurred. Please try again later.",
        'invalid_bet': f"Bet must be between {MIN_BET:,} and {MAX_BET:,}!",
    }
    
    # Success Messages  
    SUCCESS_MESSAGES = {
        'money_added': "Money successfully added to {user}'s account!",
        'money_removed': "Money successfully removed from {user}'s account!",
        'item_created': "Item '{item}' successfully created!",
        'item_given': "Item '{item}' given to {user}!",
        'role_updated': "Income role successfully updated!",
    }
    
    @classmethod
    def get_currency_display(cls, amount: int) -> str:
        """Format currency for display"""
        return f"{cls.DEFAULT_CURRENCY} {amount:,}"
    
    @classmethod
    def validate_bet(cls, amount: int) -> bool:
        """Validate if bet amount is within limits"""
        return cls.MIN_BET <= amount <= cls.MAX_BET
