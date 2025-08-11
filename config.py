#!/usr/bin/env python3
"""
Enhanced UnbelievaBoat Python Bot - Refactored with Discord.py Cogs
Original repository: https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot
Refactored by: Enhanced Bot Team

This is the main entry point for the bot. It loads all cogs and handles
basic bot initialization and error handling.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import discord
from discord.ext import commands

# Import configuration and database
from config import BotConfig
from database.manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

logger = logging.getLogger(__name__)

class EnhancedUnbelievaBot(commands.Bot):
    """Enhanced UnbelievaBoat bot with cogs architecture"""
    
    def __init__(self):
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True
        
        super().__init__(
            command_prefix=commands.when_mentioned_or(BotConfig.PREFIX),
            intents=intents,
            help_command=None,  # We'll implement custom help
            case_insensitive=True,
            strip_after_prefix=True
        )
        
        self.config = BotConfig
        self.db = None
        self.initial_extensions = [
            'cogs.economy',
            'cogs.gambling', 
            'cogs.admin',
            'cogs.items',
            'cogs.levels',
            'cogs.moderation',
            'cogs.utilities'
        ]
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Setting up bot...")
        
        # Initialize database
        self.db = DatabaseManager()
        await self.db.initialize()
        logger.info("Database initialized successfully")
        
        # Load all cogs
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")
                
        # Sync slash commands if in development
        if BotConfig.SYNC_COMMANDS_ON_STARTUP:
            try:
                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} command(s)")
            except Exception as e:
                logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when bot is ready and logged in"""
        logger.info(f"{self.user.name} (ID: {self.user.id}) is ready!")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        logger.info(f"Serving {sum(guild.member_count for guild in self.guilds)} users")
        
        # Set bot status
        activity = discord.Game(name=f"{BotConfig.PREFIX}help | Economy & Fun!")
        await self.change_presence(status=discord.Status.online, activity=activity)
        
    async def on_guild_join(self, guild):
        """Called when bot joins a new guild"""
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id}) with {guild.member_count} members")
        
        # Initialize guild settings in database
        await self.db.initialize_guild(guild.id)
        
        # Send welcome message to setup channel if configured
        if BotConfig.SETUP_CHANNEL_ID:
            channel = self.get_channel(BotConfig.SETUP_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="🎉 Thank you for adding me!",
                    description=(
                        f"I'm **{self.user.name}**, your new economy and moderation bot!\n\n"
                        f"**Quick Start:**\n"
                        f"• Use `{BotConfig.PREFIX}help` to see all commands\n"
                        f"• Set up income roles with `{BotConfig.PREFIX}add-income-role`\n"
                        f"• Configure settings with admin commands\n\n"
                        f"**Need help?** Contact the bot admins or check the documentation!"
                    ),
                    color=discord.Color.green()
                )
                await channel.send(embed=embed)
    
    async def on_command_error(self, ctx, error):
        """Global error handler for prefix commands"""
        # Ignore command not found errors
        if isinstance(error, commands.CommandNotFound):
            return
            
        # Handle cooldown errors
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Command on Cooldown",
                description=f"Please wait {error.retry_after:.1f} seconds before using this command again.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed, delete_after=10)
            return
            
        # Handle missing permissions
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="🚫 Missing Permissions",
                description=f"You don't have permission to use this command.\nRequired: {', '.join(error.missing_permissions)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
            return
            
        # Handle bot missing permissions
        if isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(
                title="🤖 Bot Missing Permissions",
                description=f"I don't have the required permissions.\nNeeded: {', '.join(error.missing_permissions)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
            return
            
        # Handle user input errors
        if isinstance(error, (commands.BadArgument, commands.MissingRequiredArgument)):
            embed = discord.Embed(
                title="❌ Invalid Command Usage",
                description=f"**Error:** {str(error)}\n\nUse `{BotConfig.PREFIX}help {ctx.command.name}` for proper usage.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=15)
            return
            
        # Log unexpected errors
        logger.error(f"Unhandled error in command {ctx.command}: {error}", exc_info=error)
        
        # Send generic error message
        embed = discord.Embed(
            title="💥 Something went wrong!",
            description="An unexpected error occurred. The incident has been logged.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=10)

async def main():
    """Main entry point"""
    # Check if token is provided
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN environment variable not found!")
        logger.info("Please set your Discord bot token in the environment variables.")
        return
    
    # Create and run bot
    bot = EnhancedUnbelievaBot()
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
        await bot.close()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown")
