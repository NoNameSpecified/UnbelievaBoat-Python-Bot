"""
Decorators for Enhanced UnbelievaBoat bot
Provides common functionality like permission checks, cooldowns, and database requirements
"""

import asyncio
import functools
import logging
from typing import Any, Callable, Optional

import discord
from discord.ext import commands

from config import BotConfig

logger = logging.getLogger(__name__)

def database_required(func: Callable) -> Callable:
    """Decorator to ensure database is available before command execution"""
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        if not hasattr(self.bot, 'db') or self.bot.db is None:
            embed = discord.Embed(
                title="❌ Database Error",
                description="Database is not available. Please try again later.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            return await func(self, ctx, *args, **kwargs)
        except Exception as e:
            logger.error(f"Database error in {func.__name__}: {e}")
            embed = discord.Embed(
                title="❌ Database Error",
                description="A database error occurred. Please try again later.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    return wrapper

def admin_required(func: Callable) -> Callable:
    """Decorator to check if user has admin permissions"""
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        # Guild owners always have permission
        if ctx.author == ctx.guild.owner:
            return await func(self, ctx, *args, **kwargs)
        
        # Check for administrator permission
        if ctx.author.guild_permissions.administrator:
            return await func(self, ctx, *args, **kwargs)
        
        # Check for admin role
        admin_role = discord.utils.get(ctx.author.roles, name=BotConfig.ADMIN_ROLE_NAME)
        if admin_role:
            return await func(self, ctx, *args, **kwargs)
        
        # Check for alternative admin role names (case insensitive)
        for role in ctx.author.roles:
            if role.name.lower() in ['admin', 'administrator', 'owner', 'botmaster']:
                return await func(self, ctx, *args, **kwargs)
        
        # No permission found
        embed = discord.Embed(
            title="🚫 Access Denied",
            description=f"You need administrator permissions or the `{BotConfig.ADMIN_ROLE_NAME}` role to use this command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    
    return wrapper

def moderator_required(func: Callable) -> Callable:
    """Decorator to check if user has moderation permissions"""
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        # Guild owners and administrators always have permission
        if (ctx.author == ctx.guild.owner or 
            ctx.author.guild_permissions.administrator):
            return await func(self, ctx, *args, **kwargs)
        
        # Check for specific moderation permissions
        required_perms = [
            ctx.author.guild_permissions.kick_members,
            ctx.author.guild_permissions.ban_members,
            ctx.author.guild_permissions.manage_messages,
            ctx.author.guild_permissions.moderate_members
        ]
        
        if any(required_perms):
            return await func(self, ctx, *args, **kwargs)
        
        # Check for moderator-related roles
        mod_role_names = ['moderator', 'mod', 'staff', BotConfig.ADMIN_ROLE_NAME.lower()]
        for role in ctx.author.roles:
            if role.name.lower() in mod_role_names:
                return await func(self, ctx, *args, **kwargs)
        
        # No permission found
        embed = discord.Embed(
            title="🚫 Access Denied",
            description="You need moderation permissions to use this command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    
    return wrapper

def cooldown_check(command_name: str, cooldown_seconds: int):
    """Decorator to implement custom cooldowns using database storage"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            # Check if database is available
            if not hasattr(self.bot, 'db') or self.bot.db is None:
                return await func(self, ctx, *args, **kwargs)
            
            try:
                # Check cooldown
                remaining_time = await self.bot.db.check_cooldown(
                    ctx.author.id, ctx.guild.id, command_name
                )
                
                if remaining_time is not None:
                    # User is on cooldown
                    minutes, seconds = divmod(int(remaining_time), 60)
                    
                    if minutes > 0:
                        time_str = f"{minutes}m {seconds}s"
                    else:
                        time_str = f"{seconds}s"
                    
                    embed = discord.Embed(
                        title="⏰ Command on Cooldown",
                        description=f"You can use this command again in **{time_str}**.",
                        color=discord.Color.orange()
                    )
                    await ctx.send(embed=embed, delete_after=10)
                    return
                
                # Execute the command
                result = await func(self, ctx, *args, **kwargs)
                
                # Set cooldown after successful execution
                await self.bot.db.set_cooldown(
                    ctx.author.id, ctx.guild.id, command_name, cooldown_seconds
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Cooldown check error for {command_name}: {e}")
                # If cooldown check fails, allow command to proceed
                return await func(self, ctx, *args, **kwargs)
        
        return wrapper
    return decorator

def guild_only(func: Callable) -> Callable:
    """Decorator to ensure command is only used in guilds"""
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        if ctx.guild is None:
            embed = discord.Embed(
                title="❌ Guild Only",
                description="This command can only be used in servers, not in DMs.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        return await func(self, ctx, *args, **kwargs)
    
    return wrapper

def bot_has_permissions(**perms):
    """Decorator to check if bot has required permissions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            if ctx.guild is None:
                return await func(self, ctx, *args, **kwargs)
            
            bot_perms = ctx.guild.me.guild_permissions
            missing_perms = []
            
            for perm, value in perms.items():
                if getattr(bot_perms, perm, None) != value:
                    missing_perms.append(perm.replace('_', ' ').title())
            
            if missing_perms:
                embed = discord.Embed(
                    title="🤖 Bot Missing Permissions",
                    description=f"I need the following permissions to run this command:\n• {', '.join(missing_perms)}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            return await func(self, ctx, *args, **kwargs)
        
        return wrapper
    return decorator

def user_has_permissions(**perms):
    """Decorator to check if user has required permissions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            if ctx.guild is None:
                return await func(self, ctx, *args, **kwargs)
            
            user_perms = ctx.author.guild_permissions
            missing_perms = []
            
            for perm, value in perms.items():
                if getattr(user_perms, perm, None) != value:
                    missing_perms.append(perm.replace('_', ' ').title())
            
            if missing_perms:
                embed = discord.Embed(
                    title="🚫 Missing Permissions",
                    description=f"You need the following permissions to use this command:\n• {', '.join(missing_perms)}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            return await func(self, ctx, *args, **kwargs)
        
        return wrapper
    return decorator

def ensure_user_exists(func: Callable) -> Callable:
    """Decorator to ensure user exists in database before command execution"""
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        if hasattr(self.bot, 'db') and self.bot.db is not None:
            try:
                # This will create the user if they don't exist
                await self.bot.db.get_user(ctx.author.id, ctx.guild.id)
            except Exception as e:
                logger.error(f"Error ensuring user exists: {e}")
        
        return await func(self, ctx, *args, **kwargs)
    
    return wrapper

def typing_indicator(func: Callable) -> Callable:
    """Decorator to show typing indicator during command execution"""
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        async with ctx.typing():
            return await func(self, ctx, *args, **kwargs)
    
    return wrapper

def log_command_usage(func: Callable) -> Callable:
    """Decorator to log command usage"""
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        logger.info(
            f"Command {func.__name__} used by {ctx.author} ({ctx.author.id}) "
            f"in {ctx.guild.name if ctx.guild else 'DM'} ({ctx.guild.id if ctx.guild else 'DM'})"
        )
        return await func(self, ctx, *args, **kwargs)
    
    return wrapper

def delete_after(seconds: int = 10):
    """Decorator to automatically delete command response after specified time"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            result = await func(self, ctx, *args, **kwargs)
            
            # If the function returned a message, delete it after specified time
            if isinstance(result, discord.Message):
                try:
                    await result.delete(delay=seconds)
                except discord.NotFound:
                    pass  # Message already deleted
                except discord.Forbidden:
                    pass  # No permission to delete
            
            return result
        
        return wrapper
    return decorator

class RateLimiter:
    """Simple rate limiter for commands"""
    
    def __init__(self):
        self.cooldowns = {}
    
    def is_rate_limited(self, user_id: int, command: str, rate: int, per: int) -> Optional[float]:
        """Check if user is rate limited. Returns remaining cooldown time or None"""
        import time
        
        now = time.time()
        key = f"{user_id}:{command}"
        
        if key not in self.cooldowns:
            self.cooldowns[key] = []
        
        # Remove old entries
        self.cooldowns[key] = [timestamp for timestamp in self.cooldowns[key] if now - timestamp < per]
        
        # Check if rate limit exceeded
        if len(self.cooldowns[key]) >= rate:
            oldest = min(self.cooldowns[key])
            return per - (now - oldest)
        
        # Add current timestamp
        self.cooldowns[key].append(now)
        return None

# Global rate limiter instance
_rate_limiter = RateLimiter()

def rate_limit(rate: int, per: int):
    """Decorator for rate limiting (e.g., @rate_limit(5, 60) = 5 uses per 60 seconds)"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            remaining = _rate_limiter.is_rate_limited(ctx.author.id, func.__name__, rate, per)
            
            if remaining is not None:
                embed = discord.Embed(
                    title="⏰ Rate Limited",
                    description=f"You're using this command too frequently. Try again in {remaining:.1f} seconds.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed, delete_after=10)
                return
            
            return await func(self, ctx, *args, **kwargs)
        
        return wrapper
    return decorator
