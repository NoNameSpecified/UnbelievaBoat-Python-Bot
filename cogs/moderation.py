"""
Moderation cog for Enhanced UnbelievaBoat bot
Handles moderation commands and auto-moderation features
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from config import BotConfig
from utils.decorators import database_required, moderator_required
from utils.helpers import parse_duration, format_duration

logger = logging.getLogger(__name__)

class Moderation(commands.Cog):
    """Moderation and server management commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        
    @property
    def display_emoji(self) -> str:
        return "🛡️"
    
    def cog_check(self, ctx):
        """Check if user has moderation permissions"""
        if ctx.guild is None:
            return False
        return (ctx.author.guild_permissions.moderate_members or 
                ctx.author.guild_permissions.kick_members or
                ctx.author.guild_permissions.ban_members or
                any(role.name.lower() == BotConfig.ADMIN_ROLE_NAME.lower() 
                    for role in ctx.author.roles))
    
    @commands.hybrid_command(name="warn")
    @app_commands.describe(
        user="User to warn",
        reason="Reason for the warning"
    )
    @database_required
    @moderator_required
    async def warn(self, ctx, user: discord.Member, *, reason: str = "No reason provided"):
        """Issue a warning to a user"""
        if user == ctx.author:
            embed = discord.Embed(
                title="❌ Invalid Action",
                description="You cannot warn yourself!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if user.bot:
            embed = discord.Embed(
                title="❌ Invalid Action",
                description="You cannot warn bots!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if user.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="You cannot warn users with equal or higher roles!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Add warning to database
            warning_id = await self.db.add_warning(
                ctx.guild.id, user.id, ctx.author.id, reason
            )
            
            # Get user's total warnings
            warnings = await self.db.get_user_warnings(ctx.guild.id, user.id)
            warning_count = len(warnings)
            
            # Create warning embed
            embed = discord.Embed(
                title="⚠️ Warning Issued",
                description=f"{user.mention} has been warned by {ctx.author.mention}",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="📝 Reason",
                value=reason,
                inline=False
            )
            
            embed.add_field(
                name="📊 Total Warnings",
                value=f"{warning_count} warning(s)",
                inline=True
            )
            
            embed.add_field(
                name="🆔 Warning ID",
                value=f"`{warning_id}`",
                inline=True
            )
            
            embed.set_footer(text=f"Moderator: {ctx.author.display_name}")
            embed.timestamp = datetime.utcnow()
            
            await ctx.send(embed=embed)
            
            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title=f"⚠️ Warning in {ctx.guild.name}",
                    description=f"You have been warned by {ctx.author.display_name}",
                    color=discord.Color.orange()
                )
                dm_embed.add_field(name="📝 Reason", value=reason, inline=False)
                dm_embed.add_field(
                    name="📊 Total Warnings", 
                    value=f"{warning_count} warning(s)", 
                    inline=True
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                await ctx.send("⚠️ Could not send DM to user.")
            
            # Check if automatic action should be taken
            if warning_count >= BotConfig.MAX_WARNS_BEFORE_ACTION:
                try:
                    await user.timeout(
                        timedelta(seconds=BotConfig.DEFAULT_MUTE_DURATION),
                        reason=f"Automatic timeout after {warning_count} warnings"
                    )
                    await ctx.send(f"🔇 {user.mention} has been automatically timed out for reaching {warning_count} warnings.")
                except discord.Forbidden:
                    await ctx.send("❌ Could not automatically timeout user (insufficient permissions).")
                    
        except Exception as e:
            logger.error(f"Error in warn command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to issue warning.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="warnings", aliases=["warns"])
    @app_commands.describe(user="User to check warnings for")
    @database_required
    @moderator_required
    async def warnings(self, ctx, user: discord.Member):
        """View a user's warnings"""
        try:
            warnings = await self.db.get_user_warnings(ctx.guild.id, user.id)
            
            if not warnings:
                embed = discord.Embed(
                    title="✅ Clean Record",
                    description=f"{user.display_name} has no warnings!",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"⚠️ {user.display_name}'s Warnings",
                description=f"Total: {len(warnings)} warning(s)",
                color=discord.Color.orange()
            )
            
            # Show recent warnings (up to 10)
            for i, warning in enumerate(warnings[:10], 1):
                moderator = self.bot.get_user(warning['moderator_id'])
                mod_name = moderator.display_name if moderator else "Unknown Moderator"
                
                timestamp = datetime.fromisoformat(warning['timestamp'])
                time_str = f"<t:{int(timestamp.timestamp())}:R>"
                
                embed.add_field(
                    name=f"Warning #{i} (ID: {warning['id']})",
                    value=f"**Reason:** {warning['reason']}\n**Moderator:** {mod_name}\n**Date:** {time_str}",
                    inline=False
                )
            
            if len(warnings) > 10:
                embed.set_footer(text=f"Showing 10 of {len(warnings)} warnings")
            
            embed.set_thumbnail(url=user.display_avatar.url)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in warnings command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to retrieve warnings.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="clear-warnings", aliases=["clearwarns"])
    @app_commands.describe(user="User to clear warnings for")
    @database_required
    @moderator_required
    async def clear_warnings(self, ctx, user: discord.Member):
        """Clear all warnings for a user"""
        try:
            warnings = await self.db.get_user_warnings(ctx.guild.id, user.id)
            
            if not warnings:
                embed = discord.Embed(
                    title="ℹ️ No Warnings",
                    description=f"{user.display_name} has no warnings to clear!",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            # Confirmation
            embed = discord.Embed(
                title="⚠️ Confirm Warning Clearance",
                description=(
                    f"Are you sure you want to clear **{len(warnings)} warning(s)** for {user.mention}?\n\n"
                    f"React with ✅ to confirm or ❌ to cancel."
                ),
                color=discord.Color.orange()
            )
            
            message = await ctx.send(embed=embed)
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            
            def check(reaction, react_user):
                return (react_user == ctx.author and 
                       str(reaction.emoji) in ["✅", "❌"] and 
                       reaction.message.id == message.id)
            
            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                if str(reaction.emoji) == "❌":
                    embed = discord.Embed(
                        title="❌ Cancelled",
                        description="Warning clearance cancelled.",
                        color=discord.Color.red()
                    )
                    await message.edit(embed=embed)
                    return
                
                # Clear warnings
                await self.db.clear_user_warnings(ctx.guild.id, user.id)
                
                embed = discord.Embed(
                    title="✅ Warnings Cleared",
                    description=f"Successfully cleared **{len(warnings)} warning(s)** for {user.mention}!",
                    color=discord.Color.green()
                )
                
                embed.set_footer(text=f"Action by: {ctx.author.display_name}")
                await message.edit(embed=embed)
                
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="⏰ Timeout",
                    description="Confirmation timed out. Warning clearance cancelled.",
                    color=discord.Color.red()
                )
                await message.edit(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in clear_warnings command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to clear warnings.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="timeout", aliases=["mute"])
    @app_commands.describe(
        user="User to timeout",
        duration="Duration of timeout (e.g., 10m, 1h, 2d)",
        reason="Reason for the timeout"
    )
    @moderator_required
    async def timeout(self, ctx, user: discord.Member, duration: str = "10m", *, reason: str = "No reason provided"):
        """Timeout a user for a specified duration"""
        if user == ctx.author:
            embed = discord.Embed(
                title="❌ Invalid Action",
                description="You cannot timeout yourself!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if user.bot:
            embed = discord.Embed(
                title="❌ Invalid Action",
                description="You cannot timeout bots!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if user.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="You cannot timeout users with equal or higher roles!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Parse duration
            duration_seconds = parse_duration(duration)
            if duration_seconds is None or duration_seconds <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Duration",
                    description="Please provide a valid duration (e.g., 10m, 1h, 2d).",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Discord timeout limit is 28 days
            max_duration = 28 * 24 * 60 * 60  # 28 days in seconds
            if duration_seconds > max_duration:
                duration_seconds = max_duration
                duration = "28d"
            
            # Apply timeout
            timeout_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
            await user.timeout(timedelta(seconds=duration_seconds), reason=reason)
            
            # Create success embed
            embed = discord.Embed(
                title="🔇 User Timed Out",
                description=f"{user.mention} has been timed out by {ctx.author.mention}",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="⏰ Duration",
                value=format_duration(duration_seconds),
                inline=True
            )
            
            embed.add_field(
                name="📅 Until",
                value=f"<t:{int(timeout_until.timestamp())}:F>",
                inline=True
            )
            
            embed.add_field(
                name="📝 Reason",
                value=reason,
                inline=False
            )
            
            embed.set_footer(text=f"Moderator: {ctx.author.display_name}")
            embed.timestamp = datetime.utcnow()
            
            await ctx.send(embed=embed)
            
            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title=f"🔇 Timed Out in {ctx.guild.name}",
                    description=f"You have been timed out by {ctx.author.display_name}",
                    color=discord.Color.red()
                )
                dm_embed.add_field(name="⏰ Duration", value=format_duration(duration_seconds), inline=True)
                dm_embed.add_field(name="📝 Reason", value=reason, inline=False)
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                await ctx.send("⚠️ Could not send DM to user.")
                
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="I don't have permission to timeout this user.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in timeout command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to timeout user.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="untimeout", aliases=["unmute"])
    @app_commands.describe(
        user="User to remove timeout from",
        reason="Reason for removing timeout"
    )
    @moderator_required
    async def untimeout(self, ctx, user: discord.Member, *, reason: str = "No reason provided"):
        """Remove timeout from a user"""
        try:
            if not user.is_timed_out():
                embed = discord.Embed(
                    title="ℹ️ Not Timed Out",
                    description=f"{user.display_name} is not currently timed out!",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            # Remove timeout
            await user.timeout(None, reason=reason)
            
            # Create success embed
            embed = discord.Embed(
                title="🔊 Timeout Removed",
                description=f"{user.mention}'s timeout has been removed by {ctx.author.mention}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📝 Reason",
                value=reason,
                inline=False
            )
            
            embed.set_footer(text=f"Moderator: {ctx.author.display_name}")
            embed.timestamp = datetime.utcnow()
            
            await ctx.send(embed=embed)
            
            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title=f"🔊 Timeout Removed in {ctx.guild.name}",
                    description=f"Your timeout has been removed by {ctx.author.display_name}",
                    color=discord.Color.green()
                )
                dm_embed.add_field(name="📝 Reason", value=reason, inline=False)
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # Ignore DM failures for untimeout
                
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="I don't have permission to remove timeout from this user.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in untimeout command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to remove timeout.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="kick")
    @app_commands.describe(
        user="User to kick",
        reason="Reason for the kick"
    )
    @moderator_required
    async def kick(self, ctx, user: discord.Member, *, reason: str = "No reason provided"):
        """Kick a user from the server"""
        if user == ctx.author:
            embed = discord.Embed(
                title="❌ Invalid Action",
                description="You cannot kick yourself!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if user.bot:
            embed = discord.Embed(
                title="❌ Invalid Action",
                description="You cannot kick bots!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if user.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="You cannot kick users with equal or higher roles!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Try to DM the user before kicking
            try:
                dm_embed = discord.Embed(
                    title=f"👢 Kicked from {ctx.guild.name}",
                    description=f"You have been kicked by {ctx.author.display_name}",
                    color=discord.Color.red()
                )
                dm_embed.add_field(name="📝 Reason", value=reason, inline=False)
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Kick the user
            await user.kick(reason=reason)
            
            # Create success embed
            embed = discord.Embed(
                title="👢 User Kicked",
                description=f"{user.display_name} has been kicked by {ctx.author.mention}",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="👤 User",
                value=f"{user.mention} ({user.id})",
                inline=True
            )
            
            embed.add_field(
                name="📝 Reason",
                value=reason,
                inline=False
            )
            
            embed.set_footer(text=f"Moderator: {ctx.author.display_name}")
            embed.timestamp = datetime.utcnow()
            
            await ctx.send(embed=embed)
                
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="I don't have permission to kick this user.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in kick command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to kick user.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="ban")
    @app_commands.describe(
        user="User to ban",
        reason="Reason for the ban",
        delete_days="Days of messages to delete (0-7)"
    )
    @moderator_required
    async def ban(self, ctx, user: discord.Member, delete_days: int = 0, *, reason: str = "No reason provided"):
        """Ban a user from the server"""
        if user == ctx.author:
            embed = discord.Embed(
                title="❌ Invalid Action",
                description="You cannot ban yourself!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if user.bot:
            embed = discord.Embed(
                title="❌ Invalid Action",
                description="You cannot ban bots!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if user.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="You cannot ban users with equal or higher roles!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if delete_days < 0 or delete_days > 7:
            delete_days = 0
        
        try:
            # Try to DM the user before banning
            try:
                dm_embed = discord.Embed(
                    title=f"🔨 Banned from {ctx.guild.name}",
                    description=f"You have been banned by {ctx.author.display_name}",
                    color=discord.Color.dark_red()
                )
                dm_embed.add_field(name="📝 Reason", value=reason, inline=False)
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Ban the user
            await user.ban(reason=reason, delete_message_days=delete_days)
            
            # Create success embed
            embed = discord.Embed(
                title="🔨 User Banned",
                description=f"{user.display_name} has been banned by {ctx.author.mention}",
                color=discord.Color.dark_red()
            )
            
            embed.add_field(
                name="👤 User",
                value=f"{user.mention} ({user.id})",
                inline=True
            )
            
            if delete_days > 0:
                embed.add_field(
                    name="🗑️ Messages Deleted",
                    value=f"{delete_days} day(s)",
                    inline=True
                )
            
            embed.add_field(
                name="📝 Reason",
                value=reason,
                inline=False
            )
            
            embed.set_footer(text=f"Moderator: {ctx.author.display_name}")
            embed.timestamp = datetime.utcnow()
            
            await ctx.send(embed=embed)
                
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="I don't have permission to ban this user.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in ban command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to ban user.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="unban")
    @app_commands.describe(
        user_id="ID of the user to unban",
        reason="Reason for the unban"
    )
    @moderator_required
    async def unban(self, ctx, user_id: str, *, reason: str = "No reason provided"):
        """Unban a user from the server"""
        try:
            # Validate user ID
            try:
                user_id = int(user_id)
            except ValueError:
                embed = discord.Embed(
                    title="❌ Invalid User ID",
                    description="Please provide a valid user ID.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Check if user is banned
            try:
                ban_entry = await ctx.guild.fetch_ban(discord.Object(id=user_id))
            except discord.NotFound:
                embed = discord.Embed(
                    title="❌ User Not Banned",
                    description=f"User with ID {user_id} is not banned from this server.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Unban the user
            await ctx.guild.unban(discord.Object(id=user_id), reason=reason)
            
            # Create success embed
            embed = discord.Embed(
                title="✅ User Unbanned",
                description=f"{ban_entry.user.display_name} has been unbanned by {ctx.author.mention}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="👤 User",
                value=f"{ban_entry.user.mention} ({user_id})",
                inline=True
            )
            
            embed.add_field(
                name="📝 Reason",
                value=reason,
                inline=False
            )
            
            embed.set_footer(text=f"Moderator: {ctx.author.display_name}")
            embed.timestamp = datetime.utcnow()
            
            await ctx.send(embed=embed)
                
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="I don't have permission to unban users.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in unban command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to unban user.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="purge", aliases=["clear"])
    @app_commands.describe(
        amount="Number of messages to delete (max 100)",
        user="Only delete messages from this user"
    )
    @moderator_required
    async def purge(self, ctx, amount: int, user: Optional[discord.Member] = None):
        """Delete multiple messages from the channel"""
        if amount <= 0 or amount > 100:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Amount must be between 1 and 100!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Delete the command message first
            if ctx.interaction is None:  # Prefix command
                await ctx.message.delete()
            
            # Purge messages
            if user:
                def check(message):
                    return message.author == user
                deleted = await ctx.channel.purge(limit=amount, check=check)
            else:
                deleted = await ctx.channel.purge(limit=amount)
            
            # Send confirmation (will auto-delete)
            embed = discord.Embed(
                title="🗑️ Messages Purged",
                description=f"Successfully deleted **{len(deleted)}** message(s)!",
                color=discord.Color.green()
            )
            
            if user:
                embed.add_field(
                    name="👤 Target User",
                    value=user.display_name,
                    inline=True
                )
            
            embed.set_footer(text=f"Moderator: {ctx.author.display_name}")
            
            confirmation = await ctx.send(embed=embed, delete_after=5)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="I don't have permission to delete messages in this channel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in purge command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to purge messages.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(Moderation(bot))
