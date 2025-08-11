"""
Transaction and leaderboard commands for Enhanced UnbelievaBoat bot
"""

import asyncio
import logging
from typing import List, Dict, Any

import discord
from discord.ext import commands
from discord import app_commands

from config import BotConfig
from utils.decorators import database_required
from utils.helpers import format_currency

logger = logging.getLogger(__name__)

class Transactions(commands.Cog):
    """Transaction and leaderboard commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        
    @property
    def display_emoji(self) -> str:
        return "📊"

    @commands.hybrid_command(name="leaderboard", aliases=["lb", "top"])
    @app_commands.describe(
        sort_by="What to sort by: cash, bank, or total",
        page="Page number to view"
    )
    @database_required
    async def leaderboard(self, ctx, sort_by: str = "total", page: int = 1):
        """View the server wealth leaderboard"""
        
        if sort_by not in ['cash', 'bank', 'total']:
            sort_by = 'total'
        
        if page < 1:
            page = 1
        
        # Get leaderboard data
        leaderboard_data = await self.db.get_leaderboard(
            ctx.guild.id, sort_by=sort_by, page=page, per_page=10
        )
        
        if not leaderboard_data:
            embed = discord.Embed(
                title="📊 Leaderboard",
                description="No users found with money in this server.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        # Create embed
        sort_emoji = {
            'cash': '💵',
            'bank': '🏦', 
            'total': '💰'
        }
        
        embed = discord.Embed(
            title=f"{sort_emoji[sort_by]} {sort_by.title()} Leaderboard - Page {page}",
            color=discord.Color.gold()
        )
        
        description_lines = []
        
        for i, (user_id, cash, bank, total) in enumerate(leaderboard_data):
            rank = (page - 1) * 10 + i + 1
            
            # Get user object
            user = self.bot.get_user(user_id)
            if not user:
                try:
                    user = await self.bot.fetch_user(user_id)
                except:
                    user = None
            
            username = user.display_name if user else f"Unknown User#{user_id}"
            
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
                amount = format_currency(cash)
            elif sort_by == 'bank':
                amount = format_currency(bank)
            else:
                amount = format_currency(total)
            
            description_lines.append(f"{medal}`#{rank:2}` **{username}** • {amount}")
        
        embed.description = "\n".join(description_lines)
        
        # Add pagination info
        embed.set_footer(text=f"💡 Use +leaderboard {sort_by} {page + 1} for next page")
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="economy-stats", aliases=["eco-stats", "stats"])
    @database_required
    async def economy_stats(self, ctx):
        """View server economy statistics"""
        
        stats = await self.db.get_economy_stats(ctx.guild.id)
        
        if not stats or stats.get('total_users', 0) == 0:
            embed = discord.Embed(
                title="📈 Economy Statistics",
                description="No economic activity found in this server.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="📈 Server Economy Statistics",
            color=discord.Color.green()
        )
        
        # Basic stats
        embed.add_field(
            name="👥 Active Users",
            value=f"{stats['total_users']:,}",
            inline=True
        )
        
        embed.add_field(
            name="💵 Total Cash",
            value=format_currency(stats['total_cash']),
            inline=True
        )
        
        embed.add_field(
            name="🏦 Total Banked",
            value=format_currency(stats['total_bank']),
            inline=True
        )
        
        embed.add_field(
            name="💰 Total Wealth",
            value=format_currency(stats['total_wealth']),
            inline=True
        )
        
        embed.add_field(
            name="💎 Richest User",
            value=format_currency(stats['richest_amount']),
            inline=True
        )
        
        embed.add_field(
            name="📊 Average Wealth",
            value=format_currency(stats['average_wealth']),
            inline=True
        )
        
        # Add server info
        embed.set_footer(
            text=f"Economy stats for {ctx.guild.name}",
            icon_url=ctx.guild.icon.url if ctx.guild.icon else None
        )
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="transactions", aliases=["trans", "history"])
    @app_commands.describe(user="User to check transaction history for")
    @database_required 
    async def transaction_history(self, ctx, user: discord.Member = None):
        """View transaction history (if implemented in database)"""
        target_user = user or ctx.author
        
        # This would require a transactions table in the database
        # For now, show a placeholder
        embed = discord.Embed(
            title=f"📋 Transaction History - {target_user.display_name}",
            description="Transaction history feature is coming soon!\n\nThis will show:\n• Money transfers\n• Income earned\n• Gambling results\n• Item purchases",
            color=discord.Color.blue()
        )
        
        embed.set_footer(text="💡 Feature in development")
        await ctx.send(embed=embed)

class LeaderboardView(discord.ui.View):
    """Interactive leaderboard with pagination"""
    
    def __init__(self, bot, guild_id: int, sort_by: str = "total"):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.sort_by = sort_by
        self.current_page = 1
    
    async def update_embed(self, interaction: discord.Interaction):
        """Update the leaderboard embed"""
        # Get leaderboard data
        leaderboard_data = await self.bot.db.get_leaderboard(
            self.guild_id, sort_by=self.sort_by, page=self.current_page, per_page=10
        )
        
        if not leaderboard_data:
            embed = discord.Embed(
                title="📊 Leaderboard",
                description="No users found.",
                color=discord.Color.blue()
            )
            await interaction.response.edit_message(embed=embed, view=self)
            return
        
        # Create embed (similar to above but with interaction)
        sort_emoji = {'cash': '💵', 'bank': '🏦', 'total': '💰'}
        
        embed = discord.Embed(
            title=f"{sort_emoji[self.sort_by]} {self.sort_by.title()} Leaderboard - Page {self.current_page}",
            color=discord.Color.gold()
        )
        
        description_lines = []
        
        for i, (user_id, cash, bank, total) in enumerate(leaderboard_data):
            rank = (self.current_page - 1) * 10 + i + 1
            
            user = self.bot.get_user(user_id)
            username = user.display_name if user else f"Unknown User#{user_id}"
            
            medal = ""
            if rank == 1:
                medal = "🥇 "
            elif rank == 2:
                medal = "🥈 "
            elif rank == 3:
                medal = "🥉 "
            
            if self.sort_by == 'cash':
                amount = format_currency(cash)
            elif self.sort_by == 'bank':
                amount = format_currency(bank)
            else:
                amount = format_currency(total)
            
            description_lines.append(f"{medal}`#{rank:2}` **{username}** • {amount}")
        
        embed.description = "\n".join(description_lines)
        embed.set_footer(text=f"Page {self.current_page} • Use buttons to navigate")
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.blurple, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        if self.current_page <= 1:
            button.disabled = True
        
        # Enable next button
        for item in self.children:
            if hasattr(item, 'label') and 'Next' in item.label:
                item.disabled = False
        
        await self.update_embed(interaction)
    
    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        
        # Enable previous button
        for item in self.children:
            if hasattr(item, 'label') and 'Previous' in item.label:
                item.disabled = False
        
        # Check if this page has data
        leaderboard_data = await self.bot.db.get_leaderboard(
            self.guild_id, sort_by=self.sort_by, page=self.current_page + 1, per_page=10
        )
        
        if not leaderboard_data:
            button.disabled = True
        
        await self.update_embed(interaction)
    
    @discord.ui.select(
        placeholder="Choose sorting method...",
        options=[
            discord.SelectOption(label="Total Wealth", value="total", emoji="💰"),
            discord.SelectOption(label="Cash", value="cash", emoji="💵"),
            discord.SelectOption(label="Bank", value="bank", emoji="🏦"),
        ]
    )
    async def sort_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.sort_by = select.values[0]
        self.current_page = 1
        
        # Reset pagination buttons
        for item in self.children:
            if hasattr(item, 'label'):
                if 'Previous' in item.label:
                    item.disabled = True
                elif 'Next' in item.label:
                    item.disabled = False
        
        await self.update_embed(interaction)

async def setup(bot):
    await bot.add_cog(Transactions(bot))