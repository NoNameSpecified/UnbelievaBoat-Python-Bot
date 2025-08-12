"""
Income commands for Enhanced UnbelievaBoat bot
"""

import asyncio
import random
import logging
from typing import List, Dict, Any

import discord
from discord.ext import commands
from discord import app_commands

from config import BotConfig
from utils.decorators import database_required, ensure_user_exists, cooldown_check
from utils.helpers import format_currency

logger = logging.getLogger(__name__)

class Income(commands.Cog):
    """Income generation commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        
    @property
    def display_emoji(self) -> str:
        return "💼"

    # Work command with variety
    @commands.hybrid_command(name="work")
    @database_required
    @ensure_user_exists  
    @cooldown_check("work", BotConfig.WORK_COOLDOWN)
    async def work(self, ctx):
        """Work to earn money"""
        
        # Work scenarios with different payouts
        work_scenarios = [
            {"job": "delivered packages", "min": 150, "max": 400, "emoji": "📦"},
            {"job": "fixed computers", "min": 200, "max": 500, "emoji": "💻"},
            {"job": "served coffee", "min": 80, "max": 250, "emoji": "☕"},
            {"job": "walked dogs", "min": 120, "max": 300, "emoji": "🐕"},
            {"job": "tutored students", "min": 250, "max": 600, "emoji": "📚"},
            {"job": "designed websites", "min": 300, "max": 800, "emoji": "🎨"},
            {"job": "drove for rideshare", "min": 180, "max": 450, "emoji": "🚗"},
            {"job": "cleaned offices", "min": 100, "max": 280, "emoji": "🧹"},
            {"job": "cooked at restaurant", "min": 160, "max": 380, "emoji": "👨‍🍳"},
            {"job": "sold products", "min": 140, "max": 420, "emoji": "🛒"},
        ]
        
        # Random scenario
        scenario = random.choice(work_scenarios)
        earnings = random.randint(scenario["min"], scenario["max"])
        
        # Bonus chance (15% chance for 50% more money)
        bonus_multiplier = 1.0
        bonus_text = ""
        
        if random.random() < 0.15:
            bonus_multiplier = 1.5
            bonus_text = "\n🌟 **BONUS!** You did exceptional work!"
            earnings = int(earnings * bonus_multiplier)
        
        # Add money to user's cash
        await self.db.update_user_balance(
            ctx.author.id, ctx.guild.id,
            cash_change=earnings
        )
        
        # Create success embed
        embed = discord.Embed(
            title=f"{scenario['emoji']} Work Complete!",
            description=f"You {scenario['job']} and earned {format_currency(earnings)}!{bonus_text}",
            color=discord.Color.green()
        )
        
        embed.set_footer(text=f"💼 Use +work again in {BotConfig.WORK_COOLDOWN // 60} minutes")
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="crime")
    @database_required
    @ensure_user_exists
    @cooldown_check("crime", BotConfig.CRIME_COOLDOWN)
    async def crime(self, ctx):
        """Commit a crime for high risk, high reward money"""
        
        # Crime scenarios
        crime_scenarios = [
            {"crime": "robbed a convenience store", "success_min": 400, "success_max": 1200, "fail_min": 200, "fail_max": 600},
            {"crime": "hacked into a bank", "success_min": 800, "success_max": 2000, "fail_min": 300, "fail_max": 800},
            {"crime": "pickpocketed tourists", "success_min": 200, "success_max": 800, "fail_min": 100, "fail_max": 400},
            {"crime": "sold stolen goods", "success_min": 300, "success_max": 1000, "fail_min": 150, "fail_max": 500},
            {"crime": "smuggled contraband", "success_min": 600, "success_max": 1500, "fail_min": 250, "fail_max": 700},
        ]
        
        scenario = random.choice(crime_scenarios)
        success_rate = 0.65  # 65% success rate
        
        if random.random() < success_rate:
            # Success
            earnings = random.randint(scenario["success_min"], scenario["success_max"])
            
            await self.db.update_user_balance(
                ctx.author.id, ctx.guild.id,
                cash_change=earnings
            )
            
            embed = discord.Embed(
                title="😈 Crime Successful!",
                description=f"You {scenario['crime']} and got away with {format_currency(earnings)}!",
                color=discord.Color.red()
            )
            
        else:
            # Failure - lose money as fine
            fine = random.randint(scenario["fail_min"], scenario["fail_max"])
            
            # Check user's cash
            user_data = await self.db.get_user(ctx.author.id, ctx.guild.id)
            cash = user_data.get('cash', 0)
            
            # Can't lose more than they have
            actual_fine = min(fine, cash)
            
            await self.db.update_user_balance(
                ctx.author.id, ctx.guild.id,
                cash_change=-actual_fine
            )
            
            embed = discord.Embed(
                title="🚔 Crime Failed!",
                description=f"You tried to {scenario['crime'].replace('robbed', 'rob').replace('hacked', 'hack').replace('sold', 'sell')} but got caught! You paid a fine of {format_currency(actual_fine)}.",
                color=discord.Color.red()
            )
        
        embed.set_footer(text=f"🚔 Use +crime again in {BotConfig.CRIME_COOLDOWN // 60} minutes")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="slut")
    @database_required
    @ensure_user_exists
    @cooldown_check("slut", BotConfig.SLUT_COOLDOWN)
    async def slut(self, ctx):
        """Adult work for money (risky)"""
        
        # Adult work scenarios (keeping it PG-13)
        scenarios = [
            {"work": "worked as a model", "min": 300, "max": 1000},
            {"work": "performed at a club", "min": 200, "max": 800},
            {"work": "did adult photoshoot", "min": 400, "max": 1200},
            {"work": "worked at a casino", "min": 250, "max": 900},
        ]
        
        scenario = random.choice(scenarios)
        success_rate = 0.7  # 70% success rate
        
        if random.random() < success_rate:
            earnings = random.randint(scenario["min"], scenario["max"])
            
            await self.db.update_user_balance(
                ctx.author.id, ctx.guild.id,
                cash_change=earnings
            )
            
            embed = discord.Embed(
                title="💋 Work Successful!",
                description=f"You {scenario['work']} and earned {format_currency(earnings)}!",
                color=discord.Color.magenta()
            )
            
        else:
            # Failure - no money earned, some lost
            loss = random.randint(100, 300)
            user_data = await self.db.get_user(ctx.author.id, ctx.guild.id)
            cash = user_data.get('cash', 0)
            actual_loss = min(loss, cash)
            
            await self.db.update_user_balance(
                ctx.author.id, ctx.guild.id,
                cash_change=-actual_loss
            )
            
            embed = discord.Embed(
                title="💔 Work Failed!",
                description=f"Your work didn't go as planned and you lost {format_currency(actual_loss)}.",
                color=discord.Color.red()
            )
        
        embed.set_footer(text=f"💋 Use +slut again in {BotConfig.SLUT_COOLDOWN // 60} minutes")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="rob")
    @app_commands.describe(user="User to rob")
    @database_required
    @ensure_user_exists
    @cooldown_check("rob", BotConfig.ROB_COOLDOWN)
    async def rob(self, ctx, user: discord.Member):
        """Rob another user's cash"""
        if user == ctx.author:
            embed = discord.Embed(
                title="❌ Invalid Target",
                description="You can't rob yourself!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if user.bot:
            embed = discord.Embed(
                title="❌ Invalid Target", 
                description="You can't rob bots!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Get both users' data
        robber_data = await self.db.get_user(ctx.author.id, ctx.guild.id)
        target_data = await self.db.get_user(user.id, ctx.guild.id)
        
        target_cash = target_data.get('cash', 0)
        robber_cash = robber_data.get('cash', 0)
        
        # Target must have at least 100 cash
        if target_cash < 100:
            embed = discord.Embed(
                title="💸 Target Too Poor",
                description=f"{user.display_name} doesn't have enough cash to rob (minimum {format_currency(100)})!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        
        # Robber must have at least 50 cash (potential fine)
        if robber_cash < 50:
            embed = discord.Embed(
                title="💸 Not Enough Cash",
                description="You need at least 💰 50 cash to attempt robbery (for potential fines)!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Success rate depends on cash difference
        base_success_rate = 0.5
        wealth_factor = min(robber_cash / max(target_cash, 1), 2) * 0.1
        success_rate = min(base_success_rate + wealth_factor, 0.8)
        
        if random.random() < success_rate:
            # Successful robbery
            stolen_amount = random.randint(int(target_cash * 0.1), int(target_cash * 0.4))
            stolen_amount = min(stolen_amount, target_cash)  # Can't steal more than they have
            
            # Transfer money
            await self.db.update_user_balance(
                user.id, ctx.guild.id,
                cash_change=-stolen_amount
            )
            
            await self.db.update_user_balance(
                ctx.author.id, ctx.guild.id,
                cash_change=stolen_amount
            )
            
            embed = discord.Embed(
                title="🔫 Robbery Successful!",
                description=f"You robbed {format_currency(stolen_amount)} from {user.display_name}!",
                color=discord.Color.red()
            )
            
        else:
            # Failed robbery - pay fine
            fine = random.randint(100, min(robber_cash, 500))
            
            await self.db.update_user_balance(
                ctx.author.id, ctx.guild.id,
                cash_change=-fine
            )
            
            embed = discord.Embed(
                title="🚔 Robbery Failed!",
                description=f"You got caught trying to rob {user.display_name} and paid a fine of {format_currency(fine)}!",
                color=discord.Color.red()
            )
        
        embed.set_footer(text=f"🔫 Use +rob again in {BotConfig.ROB_COOLDOWN // 60} minutes")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="daily")
    @database_required
    @ensure_user_exists
    @cooldown_check("daily", 86400)  # 24 hours
    async def daily(self, ctx):
        """Claim your daily reward"""
        base_amount = 500
        
        # Streak bonus (would need to implement streak tracking)
        bonus_amount = random.randint(100, 300)
        total_amount = base_amount + bonus_amount
        
        await self.db.update_user_balance(
            ctx.author.id, ctx.guild.id,
            cash_change=total_amount
        )
        
        embed = discord.Embed(
            title="🎁 Daily Reward Claimed!",
            description=f"You received your daily reward of {format_currency(total_amount)}!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="💰 Base Reward",
            value=format_currency(base_amount),
            inline=True
        )
        
        embed.add_field(
            name="🎲 Bonus",
            value=format_currency(bonus_amount), 
            inline=True
        )
        
        embed.set_footer(text="🕐 Daily reward resets every 24 hours")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Income(bot))