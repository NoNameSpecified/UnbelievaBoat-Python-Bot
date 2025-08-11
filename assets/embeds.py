"""
Custom embed templates and utilities for Enhanced UnbelievaBoat bot
"""

import discord
from typing import Dict, List, Optional, Any
from config import BotConfig

class EmbedTemplates:
    """Pre-designed embed templates with consistent styling"""
    
    @staticmethod
    def success(title: str, description: str, **kwargs) -> discord.Embed:
        """Create a success embed"""
        embed = discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=discord.Color.green(),
            **kwargs
        )
        return embed
    
    @staticmethod
    def error(title: str, description: str, **kwargs) -> discord.Embed:
        """Create an error embed"""
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=discord.Color.red(),
            **kwargs
        )
        return embed
    
    @staticmethod
    def warning(title: str, description: str, **kwargs) -> discord.Embed:
        """Create a warning embed"""
        embed = discord.Embed(
            title=f"⚠️ {title}",
            description=description,
            color=discord.Color.orange(),
            **kwargs
        )
        return embed
    
    @staticmethod
    def info(title: str, description: str, **kwargs) -> discord.Embed:
        """Create an info embed"""
        embed = discord.Embed(
            title=f"ℹ️ {title}",
            description=description,
            color=discord.Color.blue(),
            **kwargs
        )
        return embed
    
    @staticmethod
    def economy(title: str, description: str, **kwargs) -> discord.Embed:
        """Create an economy-themed embed"""
        embed = discord.Embed(
            title=f"💰 {title}",
            description=description,
            color=discord.Color.green(),
            **kwargs
        )
        return embed
    
    @staticmethod
    def gambling(title: str, description: str, **kwargs) -> discord.Embed:
        """Create a gambling-themed embed"""
        embed = discord.Embed(
            title=f"🎲 {title}",
            description=description,
            color=discord.Color.red(),
            **kwargs
        )
        return embed

class EmbedBuilder:
    """Advanced embed builder with fluent interface"""
    
    def __init__(self, title: str = None, description: str = None, color: discord.Color = None):
        self.embed = discord.Embed(title=title, description=description, color=color)
        
    def set_title(self, title: str, emoji: str = None) -> 'EmbedBuilder':
        """Set embed title with optional emoji"""
        if emoji:
            self.embed.title = f"{emoji} {title}"
        else:
            self.embed.title = title
        return self
    
    def set_description(self, description: str) -> 'EmbedBuilder':
        """Set embed description"""
        self.embed.description = description
        return self
    
    def set_color(self, color: discord.Color) -> 'EmbedBuilder':
        """Set embed color"""
        self.embed.color = color
        return self
    
    def add_field(self, name: str, value: str, inline: bool = True, emoji: str = None) -> 'EmbedBuilder':
        """Add field with optional emoji"""
        if emoji:
            name = f"{emoji} {name}"
        self.embed.add_field(name=name, value=value, inline=inline)
        return self
    
    def set_thumbnail(self, url: str) -> 'EmbedBuilder':
        """Set embed thumbnail"""
        self.embed.set_thumbnail(url=url)
        return self
    
    def set_footer(self, text: str, icon_url: str = None) -> 'EmbedBuilder':
        """Set embed footer"""
        self.embed.set_footer(text=text, icon_url=icon_url)
        return self
    
    def set_author(self, name: str, icon_url: str = None, url: str = None) -> 'EmbedBuilder':
        """Set embed author"""
        self.embed.set_author(name=name, icon_url=icon_url, url=url)
        return self
    
    def build(self) -> discord.Embed:
        """Build and return the embed"""
        return self.embed

def create_balance_embed(user: discord.Member, cash: int, bank: int, rank: int = None) -> discord.Embed:
    """Create a standardized balance embed"""
    total = cash + bank
    
    embed = EmbedBuilder()
    embed.set_title(f"{user.display_name}'s Balance", "💰")
    embed.set_color(discord.Color.green())
    embed.set_thumbnail(user.display_avatar.url)
    
    embed.add_field("Cash", f"{BotConfig.DEFAULT_CURRENCY} {cash:,}", True, "💵")
    embed.add_field("Bank", f"{BotConfig.DEFAULT_CURRENCY} {bank:,}", True, "🏦")  
    embed.add_field("Net Worth", f"{BotConfig.DEFAULT_CURRENCY} {total:,}", True, "💎")
    
    if rank:
        embed.add_field("Server Rank", f"#{rank}", True, "📊")
    
    embed.set_footer("Use +deposit or +withdraw to manage your money")
    
    return embed.build()

def create_leaderboard_embed(data: List[tuple], sort_by: str, page: int, guild_name: str) -> discord.Embed:
    """Create a standardized leaderboard embed"""
    sort_emoji = {
        'cash': '💵',
        'bank': '🏦', 
        'total': '💰'
    }
    
    embed = EmbedBuilder()
    embed.set_title(f"{sort_by.title()} Leaderboard - Page {page}", sort_emoji.get(sort_by, "📊"))
    embed.set_color(discord.Color.gold())
    
    description_lines = []
    for i, (user_id, cash, bank, total) in enumerate(data):
        rank = (page - 1) * 10 + i + 1
        
        # Medal emojis for top 3
        medal = ""
        if rank == 1:
            medal = "🥇 "
        elif rank == 2:
            medal = "🥈 "
        elif rank == 3:
            medal = "🥉 "
        
        # Format amount based on sort type
        if sort_by == 'cash':
            amount = f"{BotConfig.DEFAULT_CURRENCY} {cash:,}"
        elif sort_by == 'bank':
            amount = f"{BotConfig.DEFAULT_CURRENCY} {bank:,}"
        else:
            amount = f"{BotConfig.DEFAULT_CURRENCY} {total:,}"
        
        description_lines.append(f"{medal}`#{rank:2}` **User#{user_id}** • {amount}")
    
    embed.set_description("\n".join(description_lines))
    embed.set_footer(f"Leaderboard for {guild_name}")
    
    return embed.build()

def create_game_embed(game_name: str, result: str, payout: int = None, bet: int = None) -> discord.Embed:
    """Create a standardized gambling game result embed"""
    color = discord.Color.green() if payout and payout > (bet or 0) else discord.Color.red()
    
    embed = EmbedBuilder()
    embed.set_title(f"{game_name} Result", "🎲")
    embed.set_color(color)
    embed.set_description(result)
    
    if bet:
        embed.add_field("Bet Amount", f"{BotConfig.DEFAULT_CURRENCY} {bet:,}", True, "💰")
    
    if payout is not None:
        if payout > 0:
            embed.add_field("Payout", f"{BotConfig.DEFAULT_CURRENCY} {payout:,}", True, "💵")
        else:
            embed.add_field("Loss", f"{BotConfig.DEFAULT_CURRENCY} {abs(payout):,}", True, "💸")
    
    return embed.build()

def create_help_category_embed(category: str, commands: List[Dict[str, str]]) -> discord.Embed:
    """Create a help category embed"""
    category_info = {
        'economy': {'emoji': '💰', 'color': discord.Color.green(), 'desc': 'Money management commands'},
        'gambling': {'emoji': '🎲', 'color': discord.Color.red(), 'desc': 'Casino and betting games'},
        'levels': {'emoji': '🏆', 'color': discord.Color.purple(), 'desc': 'Leveling and XP system'},
        'items': {'emoji': '🎒', 'color': discord.Color.orange(), 'desc': 'Inventory and shop system'},
        'admin': {'emoji': '⚙️', 'color': discord.Color.gold(), 'desc': 'Administrative commands'},
        'moderation': {'emoji': '🛡️', 'color': discord.Color.blue(), 'desc': 'Moderation tools'},
        'utilities': {'emoji': '🔧', 'color': discord.Color.blurple(), 'desc': 'Utility commands'}
    }
    
    info = category_info.get(category, {'emoji': '📚', 'color': discord.Color.blue(), 'desc': 'Commands'})
    
    embed = EmbedBuilder()
    embed.set_title(f"{category.title()} Commands", info['emoji'])
    embed.set_color(info['color'])
    embed.set_description(info['desc'])
    
    for cmd in commands:
        embed.add_field(
            f"{cmd.get('emoji', '•')} {BotConfig.PREFIX}{cmd['name']}", 
            cmd['description'], 
            True
        )
    
    embed.set_footer("Commands are case-insensitive • Use +help <command> for details")
    
    return embed.build()