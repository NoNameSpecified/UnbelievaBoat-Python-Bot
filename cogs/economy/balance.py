"""
Balance management commands for Enhanced UnbelievaBoat bot
"""

import asyncio
import logging
from typing import Optional, Union

import discord
from discord.ext import commands
from discord import app_commands

from config import BotConfig
from utils.decorators import database_required, ensure_user_exists
from utils.helpers import format_currency, parse_amount

logger = logging.getLogger(__name__)

class Balance(commands.Cog):
    """Balance management commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        
    @property
    def display_emoji(self) -> str:
        return "💰"

    @commands.hybrid_command(name="balance", aliases=["bal", "money"])
    @app_commands.describe(user="User to check balance for (optional)")
    @database_required
    @ensure_user_exists
    async def balance(self, ctx, user: Optional[discord.Member] = None):
        """Check your or another user's balance"""
        target_user = user or ctx.author
        
        # Get user data
        user_data = await self.db.get_user(target_user.id, ctx.guild.id)
        
        # Create main embed
        embed = discord.Embed(
            title=f"💰 {target_user.display_name}'s Balance",
            color=discord.Color.green()
        )
        
        # Cash and Bank fields with fancy formatting
        cash = user_data.get('cash', 0)
        bank = user_data.get('bank', 0)
        total = cash + bank
        
        embed.add_field(
            name="💵 Cash",
            value=format_currency(cash),
            inline=True
        )
        
        embed.add_field(
            name="🏦 Bank", 
            value=format_currency(bank),
            inline=True
        )
        
        embed.add_field(
            name="💎 Net Worth",
            value=format_currency(total),
            inline=True
        )
        
        # Get user's rank
        try:
            leaderboard = await self.db.get_leaderboard(ctx.guild.id, sort_by="total", page=1, per_page=100)
            rank = 1
            for i, (user_id, _, _, _) in enumerate(leaderboard):
                if user_id == target_user.id:
                    rank = i + 1
                    break
            
            embed.add_field(
                name="📊 Server Rank",
                value=f"#{rank}",
                inline=True
            )
        except Exception:
            pass
        
        # Add avatar and footer
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        if target_user == ctx.author:
            embed.set_footer(text="Use +deposit or +withdraw to manage your money")
        else:
            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="deposit", aliases=["dep"])
    @app_commands.describe(amount="Amount to deposit (use 'all' for everything)")
    @database_required
    @ensure_user_exists
    async def deposit(self, ctx, amount: str):
        """Deposit money from cash to bank"""
        # Get user data
        user_data = await self.db.get_user(ctx.author.id, ctx.guild.id)
        cash = user_data.get('cash', 0)
        
        if cash <= 0:
            embed = discord.Embed(
                title="❌ No Cash",
                description="You don't have any cash to deposit!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Parse amount
        if amount.lower() == 'all':
            deposit_amount = cash
        else:
            deposit_amount = parse_amount(amount)
            if deposit_amount is None or deposit_amount <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description="Please provide a valid positive amount or 'all'.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            if deposit_amount > cash:
                deposit_amount = cash
        
        # Update balances
        await self.db.update_user_balance(
            ctx.author.id, ctx.guild.id,
            cash_change=-deposit_amount,
            bank_change=deposit_amount
        )
        
        # Success embed
        embed = discord.Embed(
            title="🏦 Deposit Successful",
            description=f"Deposited {format_currency(deposit_amount)} to your bank!",
            color=discord.Color.green()
        )
        
        # Show new balances
        new_cash = cash - deposit_amount
        new_bank = user_data.get('bank', 0) + deposit_amount
        
        embed.add_field(
            name="💵 New Cash Balance",
            value=format_currency(new_cash),
            inline=True
        )
        
        embed.add_field(
            name="🏦 New Bank Balance", 
            value=format_currency(new_bank),
            inline=True
        )
        
        embed.set_footer(text="Your money is safer in the bank!")
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="withdraw", aliases=["with"])
    @app_commands.describe(amount="Amount to withdraw (use 'all' for everything)")
    @database_required
    @ensure_user_exists
    async def withdraw(self, ctx, amount: str):
        """Withdraw money from bank to cash"""
        # Get user data
        user_data = await self.db.get_user(ctx.author.id, ctx.guild.id)
        bank = user_data.get('bank', 0)
        
        if bank <= 0:
            embed = discord.Embed(
                title="❌ No Bank Money",
                description="You don't have any money in the bank to withdraw!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Parse amount
        if amount.lower() == 'all':
            withdraw_amount = bank
        else:
            withdraw_amount = parse_amount(amount)
            if withdraw_amount is None or withdraw_amount <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description="Please provide a valid positive amount or 'all'.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            if withdraw_amount > bank:
                withdraw_amount = bank
        
        # Update balances
        await self.db.update_user_balance(
            ctx.author.id, ctx.guild.id,
            cash_change=withdraw_amount,
            bank_change=-withdraw_amount
        )
        
        # Success embed
        embed = discord.Embed(
            title="💵 Withdrawal Successful",
            description=f"Withdrew {format_currency(withdraw_amount)} from your bank!",
            color=discord.Color.green()
        )
        
        # Show new balances
        new_cash = user_data.get('cash', 0) + withdraw_amount
        new_bank = bank - withdraw_amount
        
        embed.add_field(
            name="💵 New Cash Balance",
            value=format_currency(new_cash),
            inline=True
        )
        
        embed.add_field(
            name="🏦 New Bank Balance",
            value=format_currency(new_bank), 
            inline=True
        )
        
        embed.set_footer(text="Spend your cash wisely!")
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="give", aliases=["pay"])
    @app_commands.describe(
        user="User to give money to",
        amount="Amount to give"
    )
    @database_required
    @ensure_user_exists
    async def give_money(self, ctx, user: discord.Member, amount: str):
        """Give money to another user"""
        if user == ctx.author:
            embed = discord.Embed(
                title="❌ Invalid Target",
                description="You can't give money to yourself!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if user.bot:
            embed = discord.Embed(
                title="❌ Invalid Target",
                description="You can't give money to bots!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Parse amount
        give_amount = parse_amount(amount)
        if give_amount is None or give_amount <= 0:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Please provide a valid positive amount.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Check if user has enough cash
        user_data = await self.db.get_user(ctx.author.id, ctx.guild.id)
        cash = user_data.get('cash', 0)
        
        if cash < give_amount:
            embed = discord.Embed(
                title="💸 Insufficient Cash",
                description=f"You need {format_currency(give_amount)} but only have {format_currency(cash)} in cash!",
                color=discord.Color.red()
            )
            embed.set_footer(text="Use +withdraw to get cash from your bank")
            await ctx.send(embed=embed)
            return
        
        # Calculate tax (5% for transactions)
        tax_amount = int(give_amount * 0.05)
        received_amount = give_amount - tax_amount
        
        # Ensure target user exists
        await self.db.get_user(user.id, ctx.guild.id)
        
        # Perform transaction
        await self.db.update_user_balance(
            ctx.author.id, ctx.guild.id,
            cash_change=-give_amount
        )
        
        await self.db.update_user_balance(
            user.id, ctx.guild.id,
            cash_change=received_amount
        )
        
        # Success embed
        embed = discord.Embed(
            title="💸 Money Transferred",
            description=f"{ctx.author.mention} gave {format_currency(received_amount)} to {user.mention}!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="💰 Amount Sent",
            value=format_currency(give_amount),
            inline=True
        )
        
        embed.add_field(
            name="💵 Amount Received",
            value=format_currency(received_amount),
            inline=True
        )
        
        embed.add_field(
            name="💼 Transaction Tax",
            value=format_currency(tax_amount),
            inline=True
        )
        
        embed.set_footer(text="A 5% transaction tax was applied")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Balance(bot))