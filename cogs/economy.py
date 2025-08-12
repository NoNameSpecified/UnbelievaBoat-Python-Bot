"""
Economy cog for Enhanced UnbelievaBoat bot
Handles balance, transactions, and basic economy commands
"""

import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from config import BotConfig
from utils.decorators import database_required
from utils.helpers import format_currency, parse_amount

logger = logging.getLogger(__name__)

class Economy(commands.Cog):
    """Economy system commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        
    @property
    def display_emoji(self) -> str:
        return "💰"
    
    @commands.hybrid_command(name="balance", aliases=["bal", "money"])
    @app_commands.describe(user="User to check balance for (defaults to yourself)")
    @database_required
    async def balance(self, ctx, user: Optional[discord.Member] = None):
        """Check your or another user's balance"""
        target_user = user or ctx.author
        
        try:
            user_data = await self.db.get_user(target_user.id, ctx.guild.id)
            
            embed = discord.Embed(
                title=f"{target_user.display_name}'s Balance",
                color=discord.Color.green()
            )
            
            # Add balance information
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
                name="💎 Total Worth",
                value=format_currency(total),
                inline=True
            )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in balance command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to retrieve balance information.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="deposit", aliases=["dep"])
    @app_commands.describe(amount="Amount to deposit (use 'all' for maximum)")
    @database_required
    async def deposit(self, ctx, amount: str):
        """Deposit money from cash to bank"""
        try:
            user_data = await self.db.get_user(ctx.author.id, ctx.guild.id)
            cash = user_data.get('cash', 0)
            
            if amount.lower() == 'all':
                deposit_amount = cash
            else:
                deposit_amount = parse_amount(amount)
                if deposit_amount is None:
                    raise ValueError("Invalid amount")
            
            if deposit_amount <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description="Amount must be positive!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
                
            if cash < deposit_amount:
                embed = discord.Embed(
                    title="❌ Insufficient Funds",
                    description=f"You only have {format_currency(cash)} in cash!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
                
            # Update balances
            await self.db.update_user_balance(
                ctx.author.id, 
                ctx.guild.id,
                cash_change=-deposit_amount,
                bank_change=deposit_amount
            )
            
            # Create success embed
            embed = discord.Embed(
                title="🏦 Deposit Successful",
                description=f"Successfully deposited {format_currency(deposit_amount)}!",
                color=discord.Color.green()
            )
            
            # Add updated balance info
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
            
            await ctx.send(embed=embed)
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Please provide a valid amount or 'all'.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in deposit command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to process deposit.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="withdraw", aliases=["with"])
    @app_commands.describe(amount="Amount to withdraw (use 'all' for maximum)")
    @database_required
    async def withdraw(self, ctx, amount: str):
        """Withdraw money from bank to cash"""
        try:
            user_data = await self.db.get_user(ctx.author.id, ctx.guild.id)
            bank = user_data.get('bank', 0)
            
            if amount.lower() == 'all':
                withdraw_amount = bank
            else:
                withdraw_amount = parse_amount(amount)
                if withdraw_amount is None:
                    raise ValueError("Invalid amount")
            
            if withdraw_amount <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Amount", 
                    description="Amount must be positive!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
                
            if bank < withdraw_amount:
                embed = discord.Embed(
                    title="❌ Insufficient Funds",
                    description=f"You only have {format_currency(bank)} in the bank!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
                
            # Update balances
            await self.db.update_user_balance(
                ctx.author.id,
                ctx.guild.id, 
                cash_change=withdraw_amount,
                bank_change=-withdraw_amount
            )
            
            # Create success embed
            embed = discord.Embed(
                title="💵 Withdrawal Successful",
                description=f"Successfully withdrew {format_currency(withdraw_amount)}!",
                color=discord.Color.green()
            )
            
            # Add updated balance info
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
            
            await ctx.send(embed=embed)
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Please provide a valid amount or 'all'.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in withdraw command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to process withdrawal.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="give", aliases=["pay"])
    @app_commands.describe(
        user="User to give money to",
        amount="Amount to give (use 'all' for all cash)"
    )
    @database_required
    async def give(self, ctx, user: discord.Member, amount: str):
        """Give money to another user"""
        if user == ctx.author:
            embed = discord.Embed(
                title="❌ Invalid Action",
                description="You cannot give money to yourself!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        if user.bot:
            embed = discord.Embed(
                title="❌ Invalid Action", 
                description="You cannot give money to bots!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        try:
            # Get sender data
            sender_data = await self.db.get_user(ctx.author.id, ctx.guild.id)
            sender_cash = sender_data.get('cash', 0)
            
            if amount.lower() == 'all':
                give_amount = sender_cash
            else:
                give_amount = parse_amount(amount)
                if give_amount is None:
                    raise ValueError("Invalid amount")
            
            if give_amount <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description="Amount must be positive!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
                
            if sender_cash < give_amount:
                embed = discord.Embed(
                    title="❌ Insufficient Funds",
                    description=f"You only have {format_currency(sender_cash)} in cash!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Process transaction
            await self.db.update_user_balance(
                ctx.author.id,
                ctx.guild.id,
                cash_change=-give_amount
            )
            
            await self.db.update_user_balance(
                user.id,
                ctx.guild.id,
                cash_change=give_amount
            )
            
            # Create success embed
            embed = discord.Embed(
                title="💸 Money Sent!",
                description=f"{ctx.author.mention} gave {format_currency(give_amount)} to {user.mention}!",
                color=discord.Color.green()
            )
            
            embed.set_footer(text=f"Your remaining cash: {format_currency(sender_cash - give_amount)}")
            
            await ctx.send(embed=embed)
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Please provide a valid amount or 'all'.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in give command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to transfer money.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="leaderboard", aliases=["lb", "top"])
    @app_commands.describe(
        page="Page number to view",
        sort_type="How to sort the leaderboard (cash/bank/total)"
    )
    @database_required
    async def leaderboard(self, ctx, page: int = 1, sort_type: str = "total"):
        """View the server's wealth leaderboard"""
        valid_sorts = ['cash', 'bank', 'total']
        if sort_type.lower() not in valid_sorts:
            sort_type = 'total'
        else:
            sort_type = sort_type.lower()
            
        try:
            leaderboard_data = await self.db.get_leaderboard(
                ctx.guild.id, 
                sort_by=sort_type,
                page=page,
                per_page=10
            )
            
            if not leaderboard_data:
                embed = discord.Embed(
                    title="📊 Leaderboard",
                    description="No data available yet!",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            # Create leaderboard embed
            embed = discord.Embed(
                title=f"💰 {ctx.guild.name} Wealth Leaderboard",
                description=f"Sorted by: **{sort_type.title()}** | Page {page}",
                color=discord.Color.gold()
            )
            
            # Add leaderboard entries
            description_lines = []
            for i, (user_id, cash, bank, total) in enumerate(leaderboard_data, start=(page-1)*10 + 1):
                user = self.bot.get_user(user_id) or f"Unknown User ({user_id})"
                username = user.display_name if hasattr(user, 'display_name') else str(user)
                
                if sort_type == 'cash':
                    value = format_currency(cash)
                elif sort_type == 'bank':
                    value = format_currency(bank)
                else:  # total
                    value = format_currency(total)
                
                # Add ranking emoji for top 3
                if i == 1:
                    rank = "🥇"
                elif i == 2:
                    rank = "🥈" 
                elif i == 3:
                    rank = "🥉"
                else:
                    rank = f"**#{i}**"
                    
                description_lines.append(f"{rank} **{username}** - {value}")
            
            embed.description += "\n\n" + "\n".join(description_lines)
            
            # Add navigation info
            embed.set_footer(text=f"Use '{BotConfig.PREFIX}leaderboard {page + 1}' for the next page")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in leaderboard command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to retrieve leaderboard data.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="stats")
    @database_required  
    async def stats(self, ctx):
        """View server economy statistics"""
        try:
            stats_data = await self.db.get_economy_stats(ctx.guild.id)
            
            embed = discord.Embed(
                title=f"📊 {ctx.guild.name} Economy Statistics",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="👥 Active Users",
                value=f"{stats_data.get('total_users', 0):,}",
                inline=True
            )
            
            embed.add_field(
                name="💰 Total Cash",
                value=format_currency(stats_data.get('total_cash', 0)),
                inline=True
            )
            
            embed.add_field(
                name="🏦 Total Banked",
                value=format_currency(stats_data.get('total_bank', 0)),
                inline=True
            )
            
            embed.add_field(
                name="💎 Total Wealth",
                value=format_currency(stats_data.get('total_wealth', 0)),
                inline=True
            )
            
            embed.add_field(
                name="🏆 Richest User",
                value=format_currency(stats_data.get('richest_amount', 0)),
                inline=True
            )
            
            embed.add_field(
                name="📈 Average Wealth",
                value=format_currency(stats_data.get('average_wealth', 0)),
                inline=True
            )
            
            embed.set_footer(text=f"Currency: {BotConfig.DEFAULT_CURRENCY}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in stats command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to retrieve statistics.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(Economy(bot))
