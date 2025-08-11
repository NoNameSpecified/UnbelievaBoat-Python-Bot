"""
Helper functions for Enhanced UnbelievaBoat bot
"""

import re
from typing import Optional, Union
from config import BotConfig

def format_currency(amount: int) -> str:
    """Format an amount with currency emoji and commas"""
    return f"{BotConfig.DEFAULT_CURRENCY} {amount:,}"

def parse_amount(amount_str: str) -> Optional[int]:
    """Parse an amount string into integer"""
    if not amount_str:
        return None
    
    amount_str = amount_str.strip().lower()
    
    # Handle 'all' case
    if amount_str == 'all':
        return None  # Special case, handled by calling function
    
    # Remove currency symbols and spaces
    amount_str = re.sub(r'[^\d.,kmbt]', '', amount_str)
    
    if not amount_str:
        return None
    
    try:
        # Handle suffixes
        multipliers = {
            'k': 1_000,
            'm': 1_000_000,
            'b': 1_000_000_000,
            't': 1_000_000_000_000
        }
        
        suffix = amount_str[-1]
        if suffix in multipliers:
            number_part = amount_str[:-1]
            multiplier = multipliers[suffix]
        else:
            number_part = amount_str
            multiplier = 1
        
        # Remove commas and convert to float, then to int
        number = float(number_part.replace(',', ''))
        result = int(number * multiplier)
        
        return max(0, result)  # Ensure non-negative
    except (ValueError, IndexError):
        return None

def parse_duration(duration_str: str) -> Optional[int]:
    """Parse a duration string into seconds"""
    if not duration_str:
        return None
    
    duration_str = duration_str.strip().lower()
    
    # Pattern to match numbers followed by time units
    pattern = r'(\d+)([smhdw]?)'
    matches = re.findall(pattern, duration_str)
    
    if not matches:
        return None
    
    total_seconds = 0
    
    for number_str, unit in matches:
        try:
            number = int(number_str)
        except ValueError:
            return None
        
        # Default to seconds if no unit
        if not unit or unit == 's':
            seconds = number
        elif unit == 'm':
            seconds = number * 60
        elif unit == 'h':
            seconds = number * 3600
        elif unit == 'd':
            seconds = number * 86400
        elif unit == 'w':
            seconds = number * 604800
        else:
            return None
        
        total_seconds += seconds
    
    return total_seconds if total_seconds > 0 else None

def format_duration(seconds: int) -> str:
    """Format seconds into a human-readable duration"""
    if seconds <= 0:
        return "0 seconds"
    
    units = [
        (604800, 'week'),
        (86400, 'day'),
        (3600, 'hour'),
        (60, 'minute'),
        (1, 'second')
    ]
    
    parts = []
    
    for unit_seconds, unit_name in units:
        if seconds >= unit_seconds:
            count = seconds // unit_seconds
            seconds %= unit_seconds
            
            if count == 1:
                parts.append(f"{count} {unit_name}")
            else:
                parts.append(f"{count} {unit_name}s")
    
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    else:
        return ", ".join(parts[:-1]) + f", and {parts[-1]}"

def sanitize_input(text: str, max_length: int = 100) -> str:
    """Sanitize user input for database storage"""
    if not text:
        return ""
    
    # Strip whitespace and limit length
    text = text.strip()[:max_length]
    
    # Remove/replace potentially dangerous characters
    text = re.sub(r'[<>@&]', '', text)
    
    return text

def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a percentage with specified decimal places"""
    return f"{value:.{decimals}f}%"

def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def format_list(items: list, max_items: int = 10, conjunction: str = "and") -> str:
    """Format a list of items into a readable string"""
    if not items:
        return "none"
    
    if len(items) == 1:
        return str(items[0])
    
    if len(items) <= max_items:
        if len(items) == 2:
            return f"{items[0]} {conjunction} {items[1]}"
        else:
            return f"{', '.join(str(item) for item in items[:-1])}, {conjunction} {items[-1]}"
    else:
        visible_items = items[:max_items]
        remaining = len(items) - max_items
        return f"{', '.join(str(item) for item in visible_items)}, {conjunction} {remaining} more"

def get_progress_bar(current: int, maximum: int, length: int = 20, fill: str = "█", empty: str = "░") -> str:
    """Generate a progress bar string"""
    if maximum <= 0:
        return empty * length
    
    percentage = min(1.0, current / maximum)
    filled_length = int(length * percentage)
    
    return fill * filled_length + empty * (length - filled_length)

def validate_user_input(input_str: str, input_type: str = "general") -> bool:
    """Validate user input based on type"""
    if not input_str or len(input_str.strip()) == 0:
        return False
    
    input_str = input_str.strip()
    
    if input_type == "item_name":
        # Item names should be alphanumeric with spaces, hyphens, underscores
        return bool(re.match(r'^[a-zA-Z0-9\s\-_]+$', input_str)) and len(input_str) <= 50
    
    elif input_type == "description":
        # Descriptions allow more characters but limit length
        return len(input_str) <= 200
    
    elif input_type == "emoji":
        # Basic emoji validation (Unicode emoji or Discord custom emoji)
        emoji_pattern = r'^(\p{So}|<a?:\w+:\d+>)$'
        return bool(re.match(emoji_pattern, input_str)) or input_str in ['📦', '💰', '🎁']
    
    elif input_type == "amount":
        # Numeric amounts with possible suffixes
        return parse_amount(input_str) is not None
    
    else:  # general
        # General validation - no dangerous characters
        dangerous_chars = ['<', '>', '@', '&', '`', '|']
        return not any(char in input_str for char in dangerous_chars) and len(input_str) <= 100

def calculate_tax(amount: int, tax_rate: float = 0.05) -> tuple[int, int]:
    """Calculate tax amount and net amount"""
    tax = int(amount * tax_rate)
    net = amount - tax
    return tax, net

def format_timestamp(timestamp: float, format_type: str = "relative") -> str:
    """Format timestamp for Discord"""
    timestamp_int = int(timestamp)
    
    format_codes = {
        "relative": "R",
        "short_date": "d",
        "long_date": "D",
        "short_time": "t",
        "long_time": "T",
        "short_datetime": "f",
        "long_datetime": "F"
    }
    
    format_code = format_codes.get(format_type, "R")
    return f"<t:{timestamp_int}:{format_code}>"

def chunk_list(lst: list, chunk_size: int) -> list:
    """Split a list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def normalize_string(text: str) -> str:
    """Normalize string for comparison (lowercase, no extra spaces)"""
    return " ".join(text.lower().split())

def is_mention(text: str) -> bool:
    """Check if text is a Discord mention"""
    mention_patterns = [
        r'^<@!?\d+>$',  # User mention
        r'^<#\d+>$',    # Channel mention
        r'^<@&\d+>$'    # Role mention
    ]
    
    return any(re.match(pattern, text) for pattern in mention_patterns)

def extract_id_from_mention(mention: str) -> Optional[int]:
    """Extract ID from Discord mention"""
    if not is_mention(mention):
        return None
    
    # Extract numbers from mention
    numbers = re.findall(r'\d+', mention)
    if numbers:
        try:
            return int(numbers[0])
        except ValueError:
            return None
    
    return None
