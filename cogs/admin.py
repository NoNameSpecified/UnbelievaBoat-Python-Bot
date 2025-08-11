"""
Admin cog for Enhanced UnbelievaBoat bot
Handles administrative commands and bot management
"""

import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from config import BotConfig
from utils.decorators import admin_required, database_required
from utils.helpers import format_currency, parse_amount

logger = logging.getLogger(__name__)

class Admin(commands.Cog):
    """Administrative commands for bot management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        
    @property 
    def display_emoji(self) -> str:
        return "⚙️"
    
    def cog_check(self, ctx):
        """Check if user has admin permissions for this cog"""
        if ctx.guild is None:
            return False
        return any(role.name.lower() == BotConfig.ADMIN_ROLE_NAME.lower() 
                  for role in ctx.author.roles) or ctx.author.guild_permissions.administrator
    
    @commands.hybrid_command(name="add-money")
    @app_commands.describe(
        user="User to give money to",
        amount="Amount to add",
        location="Where to add money (cash/bank)"
    )
    @database_required
    @admin_required
    async def add_money(self, ctx, user: discord.Member, amount: str, location: str = "bank"):
        """Add money to a user's balance"""
        try:
            add_amount = parse_amount(amount)
            if add_amount is None or add_amount <= 0:
                raise ValueError("Invalid amount")
            
            location = location.lower()
            if location not in ['cash', 'bank']:
                embed = discord.Embed(
                    title="❌ Invalid Location",
                    description="Location must be 'cash' or 'bank'.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Update user balance
            if location == 'cash':
                await self.db.update_user_balance(
                    user.id, ctx.guild.id, cash_change=add_amount
                )
            else:
                await self.db.update_user_balance(
                    user.id, ctx.guild.id, bank_change=add_amount
                )
            
            embed = discord.Embed(
                title="✅ Money Added",
                description=f"Added {format_currency(add_amount)} to {user.mention}'s {location}.",
                color=discord.Color.green()
            )
            
            # Log the action
            embed.set_footer(text=f"Action by: {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Please provide a valid positive amount.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in add_money command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to add money.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="remove-money")
    @app_commands.describe(
        user="User to remove money from",
        amount="Amount to remove", 
        location="Where to remove from (cash/bank)"
    )
    @database_required
    @admin_required
    async def remove_money(self, ctx, user: discord.Member, amount: str, location: str = "bank"):
        """Remove money from a user's balance"""
        try:
            remove_amount = parse_amount(amount)
            if remove_amount is None or remove_amount <= 0:
                raise ValueError("Invalid amount")
            
            location = location.lower()
            if location not in ['cash', 'bank']:
                embed = discord.Embed(
                    title="❌ Invalid Location",
                    description="Location must be 'cash' or 'bank'.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Get current balance to check if removal is possible
            user_data = await self.db.get_user(user.id, ctx.guild.id)
            current_amount = user_data.get(location, 0)
            
            if current_amount < remove_amount:
                # Cap removal at current balance
                remove_amount = current_amount
            
            # Update user balance
            if location == 'cash':
                await self.db.update_user_balance(
                    user.id, ctx.guild.id, cash_change=-remove_amount
                )
            else:
                await self.db.update_user_balance(
                    user.id, ctx.guild.id, bank_change=-remove_amount
                )
            
            embed = discord.Embed(
                title="✅ Money Removed",
                description=f"Removed {format_currency(remove_amount)} from {user.mention}'s {location}.",
                color=discord.Color.orange()
            )
            
            if current_amount < parse_amount(amount):
                embed.add_field(
                    name="⚠️ Note",
                    value=f"User only had {format_currency(current_amount)}, so that's all that was removed.",
                    inline=False
                )
            
            # Log the action
            embed.set_footer(text=f"Action by: {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Please provide a valid positive amount.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in remove_money command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to remove money.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="add-money-role")
    @app_commands.describe(
        role="Role to add money to all members",
        amount="Amount to add to each member"
    )
    @database_required
    @admin_required
    async def add_money_role(self, ctx, role: discord.Role, amount: str):
        """Add money to all members with a specific role"""
        try:
            add_amount = parse_amount(amount)
            if add_amount is None or add_amount <= 0:
                raise ValueError("Invalid amount")
            
            # Get members with the role
            members = [member for member in role.members if not member.bot]
            
            if not members:
                embed = discord.Embed(
                    title="❌ No Members",
                    description="No non-bot members found with that role.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Confirmation embed
            confirm_embed = discord.Embed(
                title="⚠️ Confirm Action",
                description=(
                    f"About to add {format_currency(add_amount)} to **{len(members)}** members.\n"
                    f"Total cost: {format_currency(add_amount * len(members))}\n\n"
                    f"React with ✅ to confirm or ❌ to cancel."
                ),
                color=discord.Color.orange()
            )
            
            message = await ctx.send(embed=confirm_embed)
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            
            def check(reaction, user):
                return (user == ctx.author and 
                       str(reaction.emoji) in ["✅", "❌"] and 
                       reaction.message.id == message.id)
            
            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                if str(reaction.emoji) == "❌":
                    embed = discord.Embed(
                        title="❌ Cancelled",
                        description="Money addition cancelled.",
                        color=discord.Color.red()
                    )
                    await message.edit(embed=embed)
                    return
                
                # Process the addition
                success_count = 0
                for member in members:
                    try:
                        await self.db.update_user_balance(
                            member.id, ctx.guild.id, bank_change=add_amount
                        )
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to add money to {member}: {e}")
                
                embed = discord.Embed(
                    title="✅ Bulk Money Addition Complete",
                    description=(
                        f"Successfully added {format_currency(add_amount)} to **{success_count}** members.\n"
                        f"Role: {role.mention}"
                    ),
                    color=discord.Color.green()
                )
                
                embed.set_footer(text=f"Action by: {ctx.author.display_name}")
                await message.edit(embed=embed)
                
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="⏰ Timeout",
                    description="Confirmation timed out. Action cancelled.",
                    color=discord.Color.red()
                )
                await message.edit(embed=embed)
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Please provide a valid positive amount.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in add_money_role command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to process bulk money addition.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="remove-money-role")
    @app_commands.describe(
        role="Role to remove money from all members",
        amount="Amount to remove from each member"
    )
    @database_required
    @admin_required
    async def remove_money_role(self, ctx, role: discord.Role, amount: str):
        """Remove money from all members with a specific role"""
        try:
            remove_amount = parse_amount(amount)
            if remove_amount is None or remove_amount <= 0:
                raise ValueError("Invalid amount")
            
            # Get members with the role
            members = [member for member in role.members if not member.bot]
            
            if not members:
                embed = discord.Embed(
                    title="❌ No Members",
                    description="No non-bot members found with that role.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Confirmation embed
            confirm_embed = discord.Embed(
                title="⚠️ Confirm Action",
                description=(
                    f"About to remove {format_currency(remove_amount)} from **{len(members)}** members.\n"
                    f"This will remove from their bank balance.\n\n"
                    f"React with ✅ to confirm or ❌ to cancel."
                ),
                color=discord.Color.orange()
            )
            
            message = await ctx.send(embed=confirm_embed)
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            
            def check(reaction, user):
                return (user == ctx.author and 
                       str(reaction.emoji) in ["✅", "❌"] and 
                       reaction.message.id == message.id)
            
            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                if str(reaction.emoji) == "❌":
                    embed = discord.Embed(
                        title="❌ Cancelled",
                        description="Money removal cancelled.",
                        color=discord.Color.red()
                    )
                    await message.edit(embed=embed)
                    return
                
                # Process the removal
                success_count = 0
                for member in members:
                    try:
                        # Get current balance and cap removal
                        user_data = await self.db.get_user(member.id, ctx.guild.id)
                        current_bank = user_data.get('bank', 0)
                        actual_removal = min(remove_amount, current_bank)
                        
                        if actual_removal > 0:
                            await self.db.update_user_balance(
                                member.id, ctx.guild.id, bank_change=-actual_removal
                            )
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to remove money from {member}: {e}")
                
                embed = discord.Embed(
                    title="✅ Bulk Money Removal Complete",
                    description=(
                        f"Successfully processed removal for **{success_count}** members.\n"
                        f"Role: {role.mention}\n"
                        f"Amount: {format_currency(remove_amount)} (or available balance)"
                    ),
                    color=discord.Color.orange()
                )
                
                embed.set_footer(text=f"Action by: {ctx.author.display_name}")
                await message.edit(embed=embed)
                
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="⏰ Timeout",
                    description="Confirmation timed out. Action cancelled.",
                    color=discord.Color.red()
                )
                await message.edit(embed=embed)
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Please provide a valid positive amount.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in remove_money_role command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to process bulk money removal.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="clear-db")
    @database_required
    @admin_required
    async def clear_db(self, ctx):
        """Remove users who left the server from the database"""
        try:
            # Get all user IDs in database for this guild
            all_user_ids = await self.db.get_all_user_ids(ctx.guild.id)
            
            # Check which users are no longer in the guild
            removed_users = []
            for user_id in all_user_ids:
                member = ctx.guild.get_member(user_id)
                if member is None:  # User not in guild anymore
                    removed_users.append(user_id)
            
            if not removed_users:
                embed = discord.Embed(
                    title="✅ Database Clean",
                    description="No users to remove from the database.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
            
            # Confirmation embed
            confirm_embed = discord.Embed(
                title="⚠️ Confirm Database Cleanup",
                description=(
                    f"Found **{len(removed_users)}** users who left the server.\n"
                    f"This will **permanently** remove their data.\n\n"
                    f"React with ✅ to confirm or ❌ to cancel."
                ),
                color=discord.Color.orange()
            )
            
            message = await ctx.send(embed=confirm_embed)
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            
            def check(reaction, user):
                return (user == ctx.author and 
                       str(reaction.emoji) in ["✅", "❌"] and 
                       reaction.message.id == message.id)
            
            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                if str(reaction.emoji) == "❌":
                    embed = discord.Embed(
                        title="❌ Cancelled",
                        description="Database cleanup cancelled.",
                        color=discord.Color.red()
                    )
                    await message.edit(embed=embed)
                    return
                
                # Remove the users
                success_count = 0
                for user_id in removed_users:
                    try:
                        await self.db.remove_user(user_id, ctx.guild.id)
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to remove user {user_id}: {e}")
                
                embed = discord.Embed(
                    title="✅ Database Cleanup Complete",
                    description=f"Successfully removed **{success_count}** users from the database.",
                    color=discord.Color.green()
                )
                
                embed.set_footer(text=f"Action by: {ctx.author.display_name}")
                await message.edit(embed=embed)
                
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="⏰ Timeout",
                    description="Confirmation timed out. Cleanup cancelled.",
                    color=discord.Color.red()
                )
                await message.edit(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in clear_db command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to clean database.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="bot-info")
    async def info_bot(self, ctx):
        """Display bot information and statistics"""
        embed = discord.Embed(
            title=f"🤖 {BotConfig.BOT_NAME} Information",
            description=f"Version {BotConfig.BOT_VERSION}",
            color=discord.Color.blue()
        )
        
        # Bot stats
        embed.add_field(
            name="📊 Statistics",
            value=(
                f"**Guilds:** {len(self.bot.guilds):,}\n"
                f"**Users:** {sum(guild.member_count for guild in self.bot.guilds):,}\n"
                f"**Commands:** {len(self.bot.commands):,}\n"
                f"**Cogs:** {len(self.bot.cogs):,}"
            ),
            inline=True
        )
        
        # System info
        embed.add_field(
            name="⚙️ System",
            value=(
                f"**Python:** {discord.__version__}\n"
                f"**Prefix:** `{BotConfig.PREFIX}`\n"
                f"**Currency:** {BotConfig.DEFAULT_CURRENCY}"
            ),
            inline=True
        )
        
        # Links and credits
        embed.add_field(
            name="🔗 Links",
            value=(
                f"[Original Repository](https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot)\n"
                f"[Enhanced Version](https://github.com/savvythunder/UnbelievaBoat-Python-Bot)"
            ),
            inline=False
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Enhanced UnbelievaBoat - Open Source Discord Bot")
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(Admin(bot))
