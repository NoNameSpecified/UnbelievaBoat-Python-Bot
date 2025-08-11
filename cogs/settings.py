"""
Server Settings Management with UI for Enhanced UnbelievaBoat bot
"""

import asyncio
import logging
from typing import Dict, List, Optional

import discord
from discord.ext import commands
from discord import app_commands

from config import BotConfig
from utils.decorators import admin_required, database_required

logger = logging.getLogger(__name__)

class ServerSettings(commands.Cog):
    """Server configuration and settings management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        
    @property
    def display_emoji(self) -> str:
        return "⚙️"

    @commands.hybrid_group(name="settings")
    @admin_required
    async def settings_group(self, ctx):
        """Server settings management"""
        if ctx.invoked_subcommand is None:
            # Show settings interface
            view = SettingsView(self.bot, ctx.guild.id)
            embed = await view.create_main_embed(ctx.guild)
            await ctx.send(embed=embed, view=view)

    @settings_group.command(name="prefix")
    @app_commands.describe(new_prefix="New command prefix for this server")
    async def set_prefix(self, ctx, new_prefix: str):
        """Set server-specific command prefix"""
        if len(new_prefix) > 5:
            embed = discord.Embed(
                title="❌ Invalid Prefix",
                description="Prefix must be 5 characters or less.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Update database (would need to implement per-guild prefix support)
        # For now, show success message
        embed = discord.Embed(
            title="✅ Prefix Updated",
            description=f"Server prefix changed to `{new_prefix}`\n\n*Note: Per-server prefixes coming soon!*",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @settings_group.command(name="currency")
    @app_commands.describe(emoji="New currency emoji for this server") 
    async def set_currency(self, ctx, emoji: str):
        """Set server-specific currency emoji"""
        # Update database
        embed = discord.Embed(
            title="✅ Currency Updated", 
            description=f"Server currency emoji changed to {emoji}\n\n*Note: Per-server currency coming soon!*",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

class SettingsView(discord.ui.View):
    """Interactive settings interface"""
    
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.current_page = "main"
    
    async def create_main_embed(self, guild: discord.Guild) -> discord.Embed:
        """Create main settings overview embed"""
        embed = discord.Embed(
            title="⚙️ Server Settings",
            description="Click a button to edit the value.",
            color=discord.Color.blue()
        )
        
        # Economy Settings Section
        embed.add_field(
            name="💰 Economy Settings",
            value=(
                f"🔧 **Command Prefix**\n"
                f"*Description:* Bot command prefix for this server\n"
                f"*Value:* `{BotConfig.PREFIX}`\n\n"
                
                f"💱 **Currency Emoji**\n" 
                f"*Description:* Currency symbol used in embeds\n"
                f"*Value:* {BotConfig.DEFAULT_CURRENCY}\n\n"
                
                f"🏦 **Default Balance**\n"
                f"*Description:* Starting money for new users\n"
                f"*Value:* {BotConfig.DEFAULT_BALANCE:,}\n\n"
            ),
            inline=False
        )
        
        # Income Settings Section  
        embed.add_field(
            name="💼 Income Settings",
            value=(
                f"⏰ **Work Cooldown**\n"
                f"*Description:* Time between work commands\n"
                f"*Value:* {BotConfig.WORK_COOLDOWN // 60} minutes\n\n"
                
                f"😈 **Crime Cooldown**\n"
                f"*Description:* Time between crime commands\n"
                f"*Value:* {BotConfig.CRIME_COOLDOWN // 60} minutes\n\n"
                
                f"💬 **Chat Income**\n"
                f"*Description:* Money earned per message\n"
                f"*Value:* {BotConfig.PASSIVE_CHAT_INCOME:,}\n\n"
            ),
            inline=False
        )
        
        # Gambling Settings
        embed.add_field(
            name="🎲 Gambling Settings", 
            value=(
                f"💰 **Maximum Bet**\n"
                f"*Description:* Highest amount users can bet\n"
                f"*Value:* {BotConfig.MAX_BET:,}\n\n"
                
                f"💵 **Minimum Bet**\n"
                f"*Description:* Lowest amount users can bet\n"
                f"*Value:* {BotConfig.MIN_BET:,}\n\n"
                
                f"🃏 **Blackjack Cooldown**\n"
                f"*Description:* Time between blackjack games\n"
                f"*Value:* {BotConfig.BLACKJACK_COOLDOWN} seconds\n\n"
            ),
            inline=False
        )
        
        embed.set_footer(text="🏠 Select Page • Click buttons to modify settings")
        return embed
    
    async def create_economy_embed(self) -> discord.Embed:
        """Create economy settings embed"""
        embed = discord.Embed(
            title="💰 Economy Settings",
            description="Configure economy-related settings for your server.",
            color=discord.Color.green()
        )
        
        settings = [
            {
                "name": "🔧 Command Prefix",
                "description": "Set a custom command prefix for this server.",
                "value": f"`{BotConfig.PREFIX}`",
                "id": "prefix"
            },
            {
                "name": "💱 Currency Emoji", 
                "description": "Set the currency emoji shown in all embeds.",
                "value": f"{BotConfig.DEFAULT_CURRENCY}",
                "id": "currency"
            },
            {
                "name": "🏦 Default Balance",
                "description": "Starting money amount for new users.",
                "value": f"{BotConfig.DEFAULT_BALANCE:,}",
                "id": "default_balance"
            },
            {
                "name": "💬 Chat Income",
                "description": "Money earned per message in chat.",
                "value": f"{BotConfig.PASSIVE_CHAT_INCOME:,}",
                "id": "chat_income"
            }
        ]
        
        for setting in settings:
            embed.add_field(
                name=setting["name"],
                value=f"{setting['description']}\n**Current:** {setting['value']}",
                inline=False
            )
        
        embed.set_footer(text="Use the buttons below to modify these settings")
        return embed
    
    async def create_gambling_embed(self) -> discord.Embed:
        """Create gambling settings embed"""
        embed = discord.Embed(
            title="🎲 Gambling Settings",
            description="Configure gambling and betting limits.",
            color=discord.Color.red()
        )
        
        settings = [
            {
                "name": "💰 Maximum Bet",
                "description": "Highest amount users can bet in games.",
                "value": f"{BotConfig.MAX_BET:,}",
                "id": "max_bet"
            },
            {
                "name": "💵 Minimum Bet", 
                "description": "Lowest amount users can bet in games.",
                "value": f"{BotConfig.MIN_BET:,}",
                "id": "min_bet"
            },
            {
                "name": "🃏 Blackjack Cooldown",
                "description": "Seconds between blackjack games.",
                "value": f"{BotConfig.BLACKJACK_COOLDOWN}s",
                "id": "blackjack_cd"
            },
            {
                "name": "🎯 Roulette Cooldown",
                "description": "Seconds between roulette games.",
                "value": f"{BotConfig.ROULETTE_COOLDOWN}s", 
                "id": "roulette_cd"
            }
        ]
        
        for setting in settings:
            embed.add_field(
                name=setting["name"],
                value=f"{setting['description']}\n**Current:** {setting['value']}",
                inline=False
            )
        
        embed.set_footer(text="Use the buttons below to modify these settings")
        return embed
    
    @discord.ui.select(
        placeholder="🏠 Select Page",
        options=[
            discord.SelectOption(
                label="Main Overview",
                description="View all settings at once",
                emoji="🏠",
                value="main"
            ),
            discord.SelectOption(
                label="Economy Settings",
                description="Currency, balance, and income settings",
                emoji="💰",
                value="economy"  
            ),
            discord.SelectOption(
                label="Gambling Settings",
                description="Betting limits and game cooldowns",
                emoji="🎲",
                value="gambling"
            ),
            discord.SelectOption(
                label="Level Settings", 
                description="XP, levels, and reward settings",
                emoji="🏆",
                value="levels"
            ),
            discord.SelectOption(
                label="Moderation Settings",
                description="Warning limits and auto-moderation",
                emoji="🛡️",
                value="moderation"
            )
        ]
    )
    async def page_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.current_page = select.values[0]
        
        if self.current_page == "main":
            embed = await self.create_main_embed(interaction.guild)
        elif self.current_page == "economy":
            embed = await self.create_economy_embed()
        elif self.current_page == "gambling":
            embed = await self.create_gambling_embed()
        else:
            embed = discord.Embed(
                title="🚧 Coming Soon",
                description=f"{select.values[0].title()} settings page is under development!",
                color=discord.Color.orange()
            )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    # Setting modification buttons (these would open modals)
    @discord.ui.button(label="🔧 Prefix", style=discord.ButtonStyle.secondary, row=1)
    async def edit_prefix(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = PrefixModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="💱 Currency", style=discord.ButtonStyle.secondary, row=1) 
    async def edit_currency(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CurrencyModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="💰 Balances", style=discord.ButtonStyle.secondary, row=1)
    async def edit_balances(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = BalanceModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🎲 Gambling", style=discord.ButtonStyle.secondary, row=1) 
    async def edit_gambling(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = GamblingModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="⏰ Cooldowns", style=discord.ButtonStyle.secondary, row=1)
    async def edit_cooldowns(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CooldownModal()
        await interaction.response.send_modal(modal)

# Modal forms for editing settings
class PrefixModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="🔧 Edit Command Prefix")
        
        self.prefix_input = discord.ui.TextInput(
            label="New Command Prefix",
            placeholder="Enter new prefix (e.g., !, $, ?)",
            default=BotConfig.PREFIX,
            max_length=5
        )
        self.add_item(self.prefix_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        new_prefix = self.prefix_input.value.strip()
        
        embed = discord.Embed(
            title="✅ Prefix Updated",
            description=f"Command prefix changed to `{new_prefix}`\n\n*Note: This is a preview - per-server prefixes coming soon!*",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class CurrencyModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="💱 Edit Currency Emoji")
        
        self.currency_input = discord.ui.TextInput(
            label="New Currency Emoji",
            placeholder="Enter emoji (e.g., 💰, 🪙, 💎)",
            default=BotConfig.DEFAULT_CURRENCY,
            max_length=10
        )
        self.add_item(self.currency_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        new_currency = self.currency_input.value.strip()
        
        embed = discord.Embed(
            title="✅ Currency Updated",
            description=f"Currency emoji changed to {new_currency}\n\n*Note: This is a preview - per-server currency coming soon!*",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class BalanceModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="💰 Edit Balance Settings")
        
        self.default_balance = discord.ui.TextInput(
            label="Default Starting Balance",
            placeholder="Amount new users start with",
            default=str(BotConfig.DEFAULT_BALANCE)
        )
        
        self.chat_income = discord.ui.TextInput(
            label="Income Per Message",
            placeholder="Money earned per chat message",
            default=str(BotConfig.PASSIVE_CHAT_INCOME)
        )
        
        self.add_item(self.default_balance)
        self.add_item(self.chat_income)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            default_bal = int(self.default_balance.value)
            chat_inc = int(self.chat_income.value)
            
            embed = discord.Embed(
                title="✅ Balance Settings Updated",
                description=(
                    f"**Default Balance:** {default_bal:,}\n"
                    f"**Chat Income:** {chat_inc:,}\n\n"
                    "*Note: These are previews - database updates coming soon!*"
                ),
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Please enter valid numbers only.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class GamblingModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="🎲 Edit Gambling Settings")
        
        self.max_bet = discord.ui.TextInput(
            label="Maximum Bet Amount",
            placeholder="Highest amount users can bet",
            default=str(BotConfig.MAX_BET)
        )
        
        self.min_bet = discord.ui.TextInput(
            label="Minimum Bet Amount", 
            placeholder="Lowest amount users can bet",
            default=str(BotConfig.MIN_BET)
        )
        
        self.add_item(self.max_bet)
        self.add_item(self.min_bet)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            max_bet = int(self.max_bet.value)
            min_bet = int(self.min_bet.value)
            
            if min_bet >= max_bet:
                embed = discord.Embed(
                    title="❌ Invalid Range",
                    description="Minimum bet must be less than maximum bet.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="✅ Gambling Settings Updated",
                description=(
                    f"**Maximum Bet:** {max_bet:,}\n"
                    f"**Minimum Bet:** {min_bet:,}\n\n"
                    "*Note: These are previews - database updates coming soon!*"
                ),
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Please enter valid numbers only.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class CooldownModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="⏰ Edit Command Cooldowns")
        
        self.work_cooldown = discord.ui.TextInput(
            label="Work Cooldown (seconds)",
            placeholder="Time between work commands",
            default=str(BotConfig.WORK_COOLDOWN)
        )
        
        self.crime_cooldown = discord.ui.TextInput(
            label="Crime Cooldown (seconds)",
            placeholder="Time between crime commands", 
            default=str(BotConfig.CRIME_COOLDOWN)
        )
        
        self.add_item(self.work_cooldown)
        self.add_item(self.crime_cooldown)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            work_cd = int(self.work_cooldown.value)
            crime_cd = int(self.crime_cooldown.value)
            
            embed = discord.Embed(
                title="✅ Cooldown Settings Updated",
                description=(
                    f"**Work Cooldown:** {work_cd // 60}m {work_cd % 60}s\n"
                    f"**Crime Cooldown:** {crime_cd // 60}m {crime_cd % 60}s\n\n"
                    "*Note: These are previews - database updates coming soon!*"
                ),
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Please enter valid numbers only.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerSettings(bot))