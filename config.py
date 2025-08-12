"""
Configuration settings for the Enhanced UnbelievaBoat bot
"""
import os
from typing import List, Optional

class BotConfig:
    """Central configuration for the bot"""
    # Bot Token
    Token = "Put your Discord bot token here"
    # Bot Settings
    PREFIX: str = '+'
    BOT_VERSION: str = "3.0.0"
    BOT_NAME: str = "Enhanced UnbelievaBoat"
    
    # Discord Settings
    SYNC_COMMANDS_ON_STARTUP: bool = False  # This will sync commands with Discord on startup
    SETUP_CHANNEL_ID: Optional[int] = None  # Channel ID for setup messages

    # Database Settings
    DATABASE_PATH: str = 'database/economy.db'
    
    # Economy Settings
    DEFAULT_BALANCE: int = 1000
    DEFAULT_CURRENCY: str = '💰'
    MAX_BET: int = 1000000
    MIN_BET: int = 10
    
    # Income Settings
    WORK_COOLDOWN: int = 300  # 5 minutes
    CRIME_COOLDOWN: int = 600  # 10 minutes
    SLUT_COOLDOWN: int = 900  # 15 minutes
    ROB_COOLDOWN: int = 1200  # 20 minutes
    
    # Gambling Settings  
    BLACKJACK_COOLDOWN: int = 30
    ROULETTE_COOLDOWN: int = 60
    
    # Leveling Settings
    XP_PER_MESSAGE: int = 15
    XP_COOLDOWN: int = 60  # 1 minute
    PASSIVE_CHAT_INCOME: int = 5
    
    # Admin Settings
    ADMIN_ROLE_NAME: str = 'botmaster'
    
    # Moderation Settings
    MAX_WARNS_BEFORE_ACTION: int = 3
    DEFAULT_MUTE_DURATION: int = 600  # 10 minutes
    
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
