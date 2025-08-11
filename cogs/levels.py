"""
Levels cog for Enhanced UnbelievaBoat bot
Handles XP system, leveling, and level rewards
"""

import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from config import BotConfig
from utils.decorators import database_required, admin_required
from utils.helpers import format_currency

logger = logging.getLogger(__name__)

class Levels(commands.Cog):
    """Level and XP system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.xp_cooldowns = {}  # Track XP cooldowns per user
        
    @property
    def display_emoji(self) -> str:
        return "🆙"
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Award XP for messages"""
        if message.author.bot or not message.guild:
            return
            
        user_id = message.author.id
        guild_id = message.guild.id
        
        # Check XP cooldown
        cooldown_key = f"{user_id}_{guild_id}"
        current_time = message.created_at.timestamp()
        
        if cooldown_key in self.xp_cooldowns:
            if current_time - self.xp_cooldowns[cooldown_key] < BotConfig.XP_COOLDOWN:
                return
        
        self.xp_cooldowns[cooldown_key] = current_time
        
        try:
            # Award XP
            await self.db.add_user_xp(user_id, guild_id, BotConfig.XP_PER_MESSAGE)
            
            # Award passive chat income if configured
            if BotConfig.PASSIVE_CHAT_INCOME > 0:
                await self.db.update_user_balance(
                    user_id, guild_id, bank_change=BotConfig.PASSIVE_CHAT_INCOME
                )
            
            # Check for level up
            user_data = await self.db.get_user(user_id, guild_id)
            current_xp = user_data.get('xp', 0)
            current_level = user_data.get('level', 1)
            
            new_level = self.calculate_level(current_xp)
            
            if new_level > current_level:
                await self.handle_level_up(message, user_data, new_level)
                
        except Exception as e:
            logger.error(f"Error processing XP for user {user_id}: {e}")
    
    def calculate_level(self, xp: int) -> int:
        """Calculate level based on XP using a scaling formula"""
        # Level formula: level = floor(0.1 * sqrt(xp))
        # This means level 1 = 100 XP, level 2 = 400 XP, level 3 = 900 XP, etc.
        if xp < 100:
            return 1
        return int(0.1 * (xp ** 0.5))
    
    def calculate_xp_for_level(self, level: int) -> int:
        """Calculate XP required for a specific level"""
        return (level * 10) ** 2
    
    async def handle_level_up(self, message, user_data, new_level):
        """Handle level up rewards and notifications"""
        try:
            user_id = message.author.id
            guild_id = message.guild.id
            old_level = user_data.get('level', 1)
            
            # Update user level in database
            await self.db.update_user_level(user_id, guild_id, new_level)
            
            # Get level rewards
            level_rewards = await self.db.get_level_rewards(guild_id, new_level)
            
            # Create level up embed
            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"{message.author.mention} reached **Level {new_level}**!",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="📊 Progress",
                value=f"Level {old_level} → **Level {new_level}**",
                inline=True
            )
            
            current_xp = user_data.get('xp', 0)
            next_level_xp = self.calculate_xp_for_level(new_level + 1)
            embed.add_field(
                name="⭐ Next Level",
                value=f"{current_xp:,} / {next_level_xp:,} XP",
                inline=True
            )
            
            # Apply rewards
            rewards_text = []
            if level_rewards:
                # Money rewards
                if level_rewards.get('money', 0) > 0:
                    await self.db.update_user_balance(
                        user_id, guild_id, cash_change=level_rewards['money']
                    )
                    rewards_text.append(f"💰 {format_currency(level_rewards['money'])}")
                
                # Role rewards
                if level_rewards.get('roles_add'):
                    for role_id in level_rewards['roles_add']:
                        role = message.guild.get_role(role_id)
                        if role and role not in message.author.roles:
                            try:
                                await message.author.add_roles(role, reason=f"Level {new_level} reward")
                                rewards_text.append(f"🎭 {role.name}")
                            except discord.Forbidden:
                                logger.warning(f"Cannot add role {role.name} to {message.author}")
                
                # Item rewards
                if level_rewards.get('items'):
                    for item_name, quantity in level_rewards['items'].items():
                        try:
                            await self.db.add_user_item(user_id, guild_id, item_name, quantity)
                            rewards_text.append(f"📦 {quantity}x {item_name}")
                        except Exception as e:
                            logger.error(f"Error giving item reward: {e}")
            
            if rewards_text:
                embed.add_field(
                    name="🎁 Rewards",
                    value="\n".join(rewards_text),
                    inline=False
                )
            
            embed.set_thumbnail(url=message.author.display_avatar.url)
            
            await message.channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error handling level up: {e}")
    
    @commands.hybrid_command(name="level", aliases=["lvl", "rank"])
    @app_commands.describe(user="User to check level for (defaults to yourself)")
    @database_required
    async def level(self, ctx, user: Optional[discord.Member] = None):
        """Check your or another user's level and XP"""
        target_user = user or ctx.author
        
        try:
            user_data = await self.db.get_user(target_user.id, ctx.guild.id)
            
            current_xp = user_data.get('xp', 0)
            current_level = user_data.get('level', 1)
            
            # Calculate progress to next level
            current_level_xp = self.calculate_xp_for_level(current_level)
            next_level_xp = self.calculate_xp_for_level(current_level + 1)
            progress_xp = current_xp - current_level_xp
            required_xp = next_level_xp - current_level_xp
            
            # Calculate progress percentage
            progress_percent = min(100, (progress_xp / required_xp) * 100) if required_xp > 0 else 100
            
            # Create progress bar
            progress_bar_length = 20
            filled_length = int(progress_bar_length * progress_percent / 100)
            progress_bar = "█" * filled_length + "░" * (progress_bar_length - filled_length)
            
            embed = discord.Embed(
                title=f"📊 {target_user.display_name}'s Level",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="🆙 Current Level",
                value=f"**Level {current_level}**",
                inline=True
            )
            
            embed.add_field(
                name="⭐ Total XP",
                value=f"{current_xp:,}",
                inline=True
            )
            
            embed.add_field(
                name="📈 Progress",
                value=f"{progress_percent:.1f}%",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Next Level Progress",
                value=f"`{progress_bar}` {progress_xp:,}/{required_xp:,} XP",
                inline=False
            )
            
            # Get user's server rank
            try:
                rank = await self.db.get_user_xp_rank(target_user.id, ctx.guild.id)
                embed.add_field(
                    name="🏆 Server Rank",
                    value=f"#{rank:,}",
                    inline=True
                )
            except Exception:
                pass  # Rank calculation failed, skip it
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.set_footer(text=f"Gain {BotConfig.XP_PER_MESSAGE} XP per message")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in level command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to retrieve level information.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="level-lb", aliases=["levellb", "xlb"])
    @app_commands.describe(page="Page number to view")
    @database_required
    async def level_leaderboard(self, ctx, page: int = 1):
        """View the server's XP leaderboard"""
        try:
            leaderboard_data = await self.db.get_xp_leaderboard(
                ctx.guild.id, page=page, per_page=10
            )
            
            if not leaderboard_data:
                embed = discord.Embed(
                    title="📊 XP Leaderboard",
                    description="No data available yet!",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"🏆 {ctx.guild.name} XP Leaderboard",
                description=f"Page {page}",
                color=discord.Color.gold()
            )
            
            # Add leaderboard entries
            description_lines = []
            for i, (user_id, xp, level) in enumerate(leaderboard_data, start=(page-1)*10 + 1):
                user = self.bot.get_user(user_id) or f"Unknown User ({user_id})"
                username = user.display_name if hasattr(user, 'display_name') else str(user)
                
                # Add ranking emoji for top 3
                if i == 1:
                    rank = "🥇"
                elif i == 2:
                    rank = "🥈"
                elif i == 3:
                    rank = "🥉"
                else:
                    rank = f"**#{i}**"
                
                description_lines.append(
                    f"{rank} **{username}** - Level {level} ({xp:,} XP)"
                )
            
            embed.description += "\n\n" + "\n".join(description_lines)
            embed.set_footer(text=f"Use '{BotConfig.PREFIX}level-lb {page + 1}' for the next page")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in level_leaderboard command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to retrieve leaderboard data.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="all-levels")
    @database_required
    async def all_levels(self, ctx):
        """View all level rewards and thresholds"""
        try:
            all_level_rewards = await self.db.get_all_level_rewards(ctx.guild.id)
            
            if not all_level_rewards:
                embed = discord.Embed(
                    title="📊 Level Rewards",
                    description="No level rewards configured yet!",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="ℹ️ Info",
                    value=f"Admins can set up level rewards using `{BotConfig.PREFIX}change-levels`",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="📊 Level Rewards & Thresholds",
                description=f"XP per message: {BotConfig.XP_PER_MESSAGE}",
                color=discord.Color.blue()
            )
            
            # Show first 10 levels with their requirements and rewards
            for level in range(1, min(11, max(all_level_rewards.keys()) + 1)):
                xp_required = self.calculate_xp_for_level(level)
                
                field_value = f"**Required XP:** {xp_required:,}"
                
                if level in all_level_rewards:
                    rewards = all_level_rewards[level]
                    reward_text = []
                    
                    if rewards.get('money', 0) > 0:
                        reward_text.append(f"💰 {format_currency(rewards['money'])}")
                    
                    if rewards.get('roles_add'):
                        role_names = []
                        for role_id in rewards['roles_add']:
                            role = ctx.guild.get_role(role_id)
                            if role:
                                role_names.append(role.name)
                        if role_names:
                            reward_text.append(f"🎭 {', '.join(role_names)}")
                    
                    if rewards.get('items'):
                        item_text = []
                        for item_name, quantity in rewards['items'].items():
                            item_text.append(f"{quantity}x {item_name}")
                        if item_text:
                            reward_text.append(f"📦 {', '.join(item_text)}")
                    
                    if reward_text:
                        field_value += f"\n**Rewards:** {', '.join(reward_text)}"
                
                embed.add_field(
                    name=f"🆙 Level {level}",
                    value=field_value,
                    inline=True
                )
            
            if max(all_level_rewards.keys(), default=0) > 10:
                embed.set_footer(text="... and more levels with rewards!")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in all_levels command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to retrieve level information.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    # Admin commands
    
    @commands.hybrid_command(name="add-xp")
    @app_commands.describe(
        user="User to give XP to",
        amount="Amount of XP to add"
    )
    @database_required
    @admin_required
    async def add_xp(self, ctx, user: discord.Member, amount: int):
        """Add XP to a user"""
        try:
            if amount <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description="XP amount must be positive!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Get user's current data
            user_data = await self.db.get_user(user.id, ctx.guild.id)
            old_level = user_data.get('level', 1)
            old_xp = user_data.get('xp', 0)
            
            # Add XP
            await self.db.add_user_xp(user.id, ctx.guild.id, amount)
            
            # Calculate new level
            new_xp = old_xp + amount
            new_level = self.calculate_level(new_xp)
            
            # Update level if needed
            if new_level > old_level:
                await self.db.update_user_level(user.id, ctx.guild.id, new_level)
            
            embed = discord.Embed(
                title="✅ XP Added",
                description=f"Added **{amount:,} XP** to {user.mention}!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📊 New Stats",
                value=f"**XP:** {old_xp:,} → {new_xp:,}\n**Level:** {old_level} → {new_level}",
                inline=True
            )
            
            if new_level > old_level:
                embed.add_field(
                    name="🎉 Level Up!",
                    value=f"User leveled up to **Level {new_level}**!",
                    inline=True
                )
            
            embed.set_footer(text=f"Action by: {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in add_xp command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to add XP.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="remove-xp")
    @app_commands.describe(
        user="User to remove XP from",
        amount="Amount of XP to remove"
    )
    @database_required
    @admin_required
    async def remove_xp(self, ctx, user: discord.Member, amount: int):
        """Remove XP from a user"""
        try:
            if amount <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description="XP amount must be positive!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Get user's current data
            user_data = await self.db.get_user(user.id, ctx.guild.id)
            old_level = user_data.get('level', 1)
            old_xp = user_data.get('xp', 0)
            
            # Calculate removal (don't go below 0)
            actual_removal = min(amount, old_xp)
            new_xp = old_xp - actual_removal
            
            if actual_removal > 0:
                # Remove XP
                await self.db.add_user_xp(user.id, ctx.guild.id, -actual_removal)
                
                # Calculate new level
                new_level = self.calculate_level(new_xp)
                
                # Update level if needed
                if new_level != old_level:
                    await self.db.update_user_level(user.id, ctx.guild.id, new_level)
            else:
                new_level = old_level
            
            embed = discord.Embed(
                title="✅ XP Removed",
                description=f"Removed **{actual_removal:,} XP** from {user.mention}!",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="📊 New Stats",
                value=f"**XP:** {old_xp:,} → {new_xp:,}\n**Level:** {old_level} → {new_level}",
                inline=True
            )
            
            if actual_removal < amount:
                embed.add_field(
                    name="⚠️ Note",
                    value=f"User only had {old_xp:,} XP, so that's all that was removed.",
                    inline=True
                )
            
            embed.set_footer(text=f"Action by: {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in remove_xp command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to remove XP.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="change-levels")
    @database_required
    @admin_required
    async def change_levels(self, ctx):
        """Configure level rewards (interactive setup)"""
        try:
            embed = discord.Embed(
                title="🔧 Level Rewards Configuration",
                description="Configure rewards for reaching specific levels.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            
            def check(message):
                return message.author == ctx.author and message.channel == ctx.channel
            
            # Get level to configure
            await ctx.send("📊 Which level would you like to configure? (1-100)")
            try:
                level_msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                target_level = int(level_msg.content.strip())
                
                if target_level < 1 or target_level > 100:
                    await ctx.send("❌ Level must be between 1 and 100!")
                    return
                    
            except (asyncio.TimeoutError, ValueError):
                await ctx.send("❌ Invalid input or timeout. Configuration cancelled.")
                return
            
            # Check current rewards
            current_rewards = await self.db.get_level_rewards(ctx.guild.id, target_level)
            if current_rewards:
                embed = discord.Embed(
                    title=f"📊 Current Level {target_level} Rewards",
                    color=discord.Color.blue()
                )
                
                if current_rewards.get('money', 0) > 0:
                    embed.add_field(
                        name="💰 Money",
                        value=format_currency(current_rewards['money']),
                        inline=True
                    )
                
                if current_rewards.get('roles_add'):
                    role_names = []
                    for role_id in current_rewards['roles_add']:
                        role = ctx.guild.get_role(role_id)
                        if role:
                            role_names.append(role.name)
                    if role_names:
                        embed.add_field(
                            name="🎭 Roles",
                            value=", ".join(role_names),
                            inline=True
                        )
                
                await ctx.send(embed=embed)
            
            # Get money reward
            await ctx.send("💰 How much money should be rewarded? (or 'skip' for no money)")
            try:
                money_msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                money_text = money_msg.content.strip()
                
                if money_text.lower() == 'skip':
                    money_reward = 0
                else:
                    money_reward = int(money_text)
                    if money_reward < 0:
                        money_reward = 0
            except (asyncio.TimeoutError, ValueError):
                money_reward = 0
            
            # Get role rewards
            await ctx.send("🎭 Which roles should be added? (mention roles or 'skip')")
            try:
                roles_msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                
                if roles_msg.content.strip().lower() == 'skip':
                    role_rewards = []
                else:
                    role_rewards = [role.id for role in roles_msg.role_mentions]
            except asyncio.TimeoutError:
                role_rewards = []
            
            # Save level rewards
            reward_data = {
                'money': money_reward,
                'roles_add': role_rewards,
                'items': {}  # Items can be added later if needed
            }
            
            await self.db.set_level_rewards(ctx.guild.id, target_level, reward_data)
            
            # Create confirmation embed
            embed = discord.Embed(
                title="✅ Level Rewards Updated",
                description=f"Successfully configured rewards for **Level {target_level}**!",
                color=discord.Color.green()
            )
            
            xp_required = self.calculate_xp_for_level(target_level)
            embed.add_field(
                name="📊 Level Info",
                value=f"**Level:** {target_level}\n**XP Required:** {xp_required:,}",
                inline=True
            )
            
            if money_reward > 0:
                embed.add_field(
                    name="💰 Money Reward",
                    value=format_currency(money_reward),
                    inline=True
                )
            
            if role_rewards:
                role_names = []
                for role_id in role_rewards:
                    role = ctx.guild.get_role(role_id)
                    if role:
                        role_names.append(role.name)
                if role_names:
                    embed.add_field(
                        name="🎭 Role Rewards",
                        value=", ".join(role_names),
                        inline=False
                    )
            
            embed.set_footer(text=f"Action by: {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in change_levels command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to configure level rewards.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="set-passive-chat-income")
    @app_commands.describe(amount="Amount of passive income per message")
    @database_required
    @admin_required
    async def set_passive_chat_income(self, ctx, amount: int):
        """Set passive chat income amount"""
        try:
            if amount < 0:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description="Passive income cannot be negative!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Update configuration (this would typically be stored in database)
            BotConfig.PASSIVE_CHAT_INCOME = amount
            
            embed = discord.Embed(
                title="✅ Passive Chat Income Updated",
                description=f"Passive chat income set to **{format_currency(amount)}** per message!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="ℹ️ Info",
                value=(
                    f"Users will now receive {format_currency(amount)} in their bank "
                    f"for each message they send (with {BotConfig.XP_COOLDOWN}s cooldown)."
                ),
                inline=False
            )
            
            embed.set_footer(text=f"Action by: {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in set_passive_chat_income command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to update passive chat income.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(Levels(bot))
