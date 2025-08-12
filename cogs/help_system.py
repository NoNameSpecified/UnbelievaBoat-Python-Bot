"""
Advanced Help System with UI for Enhanced UnbelievaBoat bot
"""

import asyncio
import logging
from typing import Dict, List, Optional

import discord
from discord.ext import commands
from discord import app_commands

from config import BotConfig

logger = logging.getLogger(__name__)

class HelpSystem(commands.Cog):
    """Advanced help system with interactive UI"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @property
    def display_emoji(self) -> str:
        return "❓"

    @commands.hybrid_command(name="bothelp")
    @app_commands.describe(command="Specific command to get help for")
    async def help_command(self, ctx, command: Optional[str] = None):
        """Display bot help with interactive interface"""
        
        if command:
            # Show specific command help
            await self.show_command_help(ctx, command)
        else:
            # Show main help menu with UI
            view = HelpView(self.bot)
            embed = await view.create_main_embed(ctx)
            await ctx.send(embed=embed, view=view)
    
    async def show_command_help(self, ctx, command_name: str):
        """Show help for a specific command"""
        cmd = self.bot.get_command(command_name)
        if not cmd:
            embed = discord.Embed(
                title="❌ Command Not Found",
                description=f"No command named `{command_name}` found.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"📖 Command: {BotConfig.PREFIX}{cmd.name}",
            description=cmd.help or "No description available.",
            color=discord.Color.blue()
        )
        
        # Aliases
        if hasattr(cmd, 'aliases') and cmd.aliases:
            embed.add_field(
                name="🔗 Aliases",
                value=", ".join([f"`{BotConfig.PREFIX}{alias}`" for alias in cmd.aliases]),
                inline=False
            )
        
        # Usage
        if hasattr(cmd, 'signature'):
            embed.add_field(
                name="💬 Usage",
                value=f"`{BotConfig.PREFIX}{cmd.name} {cmd.signature}`",
                inline=False
            )
        
        # Examples (if we add them to commands)
        embed.set_footer(text=f"Use {BotConfig.PREFIX}help for all commands")
        
        await ctx.send(embed=embed)

class HelpView(discord.ui.View):
    """Interactive help interface"""
    
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot
        self.current_category = "main"
    
    async def create_main_embed(self, ctx) -> discord.Embed:
        """Create the main help embed"""
        embed = discord.Embed(
            title="🍋 Welcome to Enhanced UnbelievaBoat",
            description="Enhanced UnbelievaBoat is a comprehensive Discord economy bot with advanced features!",
            color=discord.Color.green()
        )
        
        # Bot stats
        guild_count = len(self.bot.guilds)
        user_count = sum(guild.member_count or 0 for guild in self.bot.guilds)
        
        embed.add_field(
            name="📊 Bot Statistics",
            value=f"**Servers:** {guild_count:,}\n**Users:** {user_count:,}\n**Prefix:** `{BotConfig.PREFIX}`",
            inline=True
        )
        
        embed.add_field(
            name="💰 Economy Features",
            value="• Balance Management\n• Income Commands\n• Gambling Games\n• Item System",
            inline=True
        )
        
        embed.add_field(
            name="🎮 Fun Features", 
            value="• Leveling System\n• Leaderboards\n• Mini Games\n• Social Commands",
            inline=True
        )
        
        embed.add_field(
            name="⚙️ Admin Features",
            value="• Money Management\n• Server Settings\n• Role Configuration\n• Moderation Tools",
            inline=True
        )
        
        embed.add_field(
            name="🔧 Utility Features",
            value="• Server Information\n• User Profiles\n• Help System\n• Statistics",
            inline=True
        )
        
        embed.add_field(
            name="🎲 Gambling Games",
            value="• Blackjack\n• Roulette\n• Slots (Coming Soon)\n• Sports Betting",
            inline=True
        )
        
        # Quick commands
        embed.add_field(
            name="🚀 Quick Start Commands",
            value=(
                f"`{BotConfig.PREFIX}balance` - Check your money\n"
                f"`{BotConfig.PREFIX}work` - Earn money\n"
                f"`{BotConfig.PREFIX}blackjack` - Play blackjack\n"
                f"`{BotConfig.PREFIX}leaderboard` - View rankings"
            ),
            inline=False
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Select a category below to explore commands • Use buttons to navigate")
        
        return embed
    
    async def create_category_embed(self, category: str) -> discord.Embed:
        """Create embed for specific category"""
        
        if category == "economy":
            embed = discord.Embed(
                title="💰 Economy Commands",
                description="Manage your money and economy",
                color=discord.Color.green()
            )
            
            commands = [
                ("balance", "Check your or another user's balance", "💰"),
                ("deposit", "Move money from cash to bank", "🏦"),
                ("withdraw", "Move money from bank to cash", "💵"),
                ("give", "Give money to another user", "💸"),
                ("work", "Work for money", "💼"),
                ("crime", "Risky crime for money", "😈"),
                ("daily", "Claim daily reward", "🎁"),
                ("rob", "Rob another user's cash", "🔫"),
            ]
            
        elif category == "gambling":
            embed = discord.Embed(
                title="🎲 Gambling Commands",
                description="Try your luck with various games",
                color=discord.Color.red()
            )
            
            commands = [
                ("blackjack", "Play blackjack against the dealer", "🃏"),
                ("roulette", "Bet on roulette wheel", "🎯"),
                ("slots", "Spin the slot machine", "🎰"),
                ("coinflip", "Flip a coin for double or nothing", "🪙"),
            ]
            
        elif category == "levels":
            embed = discord.Embed(
                title="🏆 Level Commands",
                description="Level up and earn rewards",
                color=discord.Color.purple()
            )
            
            commands = [
                ("rank", "Check your level and XP", "📊"),
                ("leaderboard xp", "View XP leaderboard", "🏆"),
                ("level-rewards", "View level rewards", "🎁"),
            ]
            
        elif category == "items":
            embed = discord.Embed(
                title="🎒 Item Commands", 
                description="Manage items and inventory",
                color=discord.Color.orange()
            )
            
            commands = [
                ("inventory", "View your inventory", "🎒"),
                ("shop", "View available items", "🛒"),
                ("buy", "Purchase an item", "💳"),
                ("use", "Use an item from inventory", "✨"),
                ("sell", "Sell items back", "💰"),
            ]
            
        elif category == "admin":
            embed = discord.Embed(
                title="⚙️ Admin Commands",
                description="Administrative and configuration commands",
                color=discord.Color.gold()
            )
            
            commands = [
                ("add-money", "Add money to user", "➕"),
                ("remove-money", "Remove money from user", "➖"),
                ("create-item", "Create a new item", "🛠️"),
                ("delete-item", "Delete an item", "🗑️"),
                ("bot-settings", "Configure bot settings", "⚙️"),
                ("economy-reset", "Reset server economy", "🔄"),
            ]
            
        elif category == "moderation":
            embed = discord.Embed(
                title="🛡️ Moderation Commands",
                description="Keep your server safe and organized",
                color=discord.Color.blue()
            )
            
            commands = [
                ("warn", "Warn a user", "⚠️"),
                ("warnings", "View user warnings", "📋"),
                ("timeout", "Timeout a user", "⏰"),
                ("clear-warnings", "Clear user warnings", "🧹"),
            ]
            
        else:  # utilities
            embed = discord.Embed(
                title="🔧 Utility Commands",
                description="Helpful utility and information commands",
                color=discord.Color.blurple()
            )
            
            commands = [
                ("ping", "Check bot latency", "🏓"),
                ("serverinfo", "Server information", "📊"),
                ("userinfo", "User information", "👤"),
                ("bot-info", "Bot information", "🤖"),
                ("stats", "Economy statistics", "📈"),
            ]
        
        # Add command fields
        for cmd_name, cmd_desc, emoji in commands:
            embed.add_field(
                name=f"{emoji} {BotConfig.PREFIX}{cmd_name}",
                value=cmd_desc,
                inline=True
            )
        
        embed.set_footer(text="Click 'Main Menu' to go back • Commands are case-insensitive")
        return embed
    
    @discord.ui.select(
        placeholder="📂 Select a command category...",
        options=[
            discord.SelectOption(
                label="Economy", 
                description="Money, work, and income commands",
                emoji="💰",
                value="economy"
            ),
            discord.SelectOption(
                label="Gambling", 
                description="Casino games and betting",
                emoji="🎲", 
                value="gambling"
            ),
            discord.SelectOption(
                label="Levels & XP",
                description="Leveling system and rewards",
                emoji="🏆",
                value="levels"
            ),
            discord.SelectOption(
                label="Items & Shop",
                description="Inventory and item management", 
                emoji="🎒",
                value="items"
            ),
            discord.SelectOption(
                label="Administration",
                description="Admin and configuration commands",
                emoji="⚙️",
                value="admin"
            ),
            discord.SelectOption(
                label="Moderation", 
                description="Moderation and safety tools",
                emoji="🛡️",
                value="moderation"
            ),
            discord.SelectOption(
                label="Utilities",
                description="Information and utility commands",
                emoji="🔧",
                value="utilities"
            ),
        ]
    )
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.current_category = select.values[0]
        embed = await self.create_category_embed(self.current_category)
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🏠 Main Menu", style=discord.ButtonStyle.green)
    async def main_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_category = "main"
        embed = await self.create_main_embed(interaction)
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🔗 Links", style=discord.ButtonStyle.secondary)
    async def links_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔗 Useful Links",
            description="Here are some helpful links:",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📊 Top.gg", 
            value="[Vote for the bot](https://top.gg)",
            inline=False
        )
        embed.add_field(
            name="💎 Invite Bot",
            value="[Add to your server](https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=139586817088&scope=applications.commands%20bot)",
            inline=False
        )
        embed.add_field(
            name="🆘 Support Server",
            value="[Join for help](https://discord.gg/YOUR_SUPPORT_SERVER)",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def on_timeout(self):
        # Disable all items when the view times out
        for item in self.children:
            item.disabled = True

async def setup(bot):
    await bot.add_cog(HelpSystem(bot))