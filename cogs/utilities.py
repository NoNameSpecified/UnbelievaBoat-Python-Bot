"""
Utilities cog for Enhanced UnbelievaBoat bot
Handles help system, bot information, and utility commands
"""

import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from config import BotConfig

logger = logging.getLogger(__name__)

class Utilities(commands.Cog):
    """Utility commands and help system"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @property
    def display_emoji(self) -> str:
        return "🛠️"
    
    @commands.hybrid_command(name="help")
    @app_commands.describe(command="Specific command or category to get help for")
    async def help(self, ctx, *, command: Optional[str] = None):
        """Show help information for commands"""
        if command:
            # Show help for specific command or cog
            await self.show_command_help(ctx, command)
        else:
            # Show general help with all categories
            await self.show_general_help(ctx)
    
    async def show_general_help(self, ctx):
        """Show the main help embed with all command categories"""
        embed = discord.Embed(
            title=f"🤖 {BotConfig.BOT_NAME} Help",
            description=(
                f"Welcome to {BotConfig.BOT_NAME}! Here are all available command categories.\n"
                f"Use `{BotConfig.PREFIX}help <category>` for detailed commands in each category.\n"
                f"You can also use slash commands by typing `/` and selecting commands!"
            ),
            color=discord.Color.blue()
        )
        
        # Get all loaded cogs and their information
        cog_info = []
        for cog_name, cog in self.bot.cogs.items():
            if hasattr(cog, 'display_emoji'):
                emoji = cog.display_emoji
            else:
                emoji = "📋"
            
            # Count commands in this cog
            commands_count = len([cmd for cmd in cog.get_commands() if not cmd.hidden])
            
            if commands_count > 0:
                cog_info.append({
                    'name': cog_name,
                    'emoji': emoji,
                    'count': commands_count,
                    'description': cog.__doc__.split('\n')[0] if cog.__doc__ else "No description"
                })
        
        # Sort by name for consistent display
        cog_info.sort(key=lambda x: x['name'])
        
        # Add fields for each category
        for info in cog_info:
            embed.add_field(
                name=f"{info['emoji']} {info['name']}",
                value=f"{info['description']}\n*{info['count']} command(s)*",
                inline=True
            )
        
        # Add general information
        embed.add_field(
            name="💡 Quick Tips",
            value=(
                f"• Prefix: `{BotConfig.PREFIX}` or mention me\n"
                f"• Use `/` for slash commands\n"
                f"• Use `{BotConfig.PREFIX}help <command>` for specific help\n"
                f"• Currency: {BotConfig.DEFAULT_CURRENCY}"
            ),
            inline=False
        )
        
        embed.set_footer(text=f"Bot Version: {BotConfig.BOT_VERSION} | Total Commands: {len(self.bot.commands)}")
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    async def show_command_help(self, ctx, query: str):
        """Show help for a specific command or category"""
        query_lower = query.lower()
        
        # First, check if it's a cog name
        for cog_name, cog in self.bot.cogs.items():
            if cog_name.lower() == query_lower:
                await self.show_cog_help(ctx, cog_name, cog)
                return
        
        # Then check if it's a command
        command = self.bot.get_command(query_lower)
        if command:
            await self.show_specific_command_help(ctx, command)
            return
        
        # If not found, show suggestions
        embed = discord.Embed(
            title="❌ Command/Category Not Found",
            description=f"Could not find command or category '{query}'.",
            color=discord.Color.red()
        )
        
        # Suggest similar commands
        all_commands = [cmd.name for cmd in self.bot.commands]
        all_cogs = [name.lower() for name in self.bot.cogs.keys()]
        
        suggestions = []
        for cmd in all_commands:
            if query_lower in cmd or cmd in query_lower:
                suggestions.append(f"`{cmd}`")
        
        for cog in all_cogs:
            if query_lower in cog or cog in query_lower:
                suggestions.append(f"`{cog.title()}`")
        
        if suggestions:
            embed.add_field(
                name="💡 Did you mean?",
                value=", ".join(suggestions[:5]),
                inline=False
            )
        
        embed.add_field(
            name="📋 Available Categories",
            value=", ".join([f"`{name}`" for name in self.bot.cogs.keys()]),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    async def show_cog_help(self, ctx, cog_name: str, cog):
        """Show help for a specific cog (category)"""
        emoji = getattr(cog, 'display_emoji', '📋')
        
        embed = discord.Embed(
            title=f"{emoji} {cog_name} Commands",
            description=cog.__doc__.strip() if cog.__doc__ else "No description available",
            color=discord.Color.green()
        )
        
        # Get all commands in this cog
        commands_list = [cmd for cmd in cog.get_commands() if not cmd.hidden]
        commands_list.sort(key=lambda x: x.name)
        
        if not commands_list:
            embed.add_field(
                name="No Commands",
                value="This category has no available commands.",
                inline=False
            )
        else:
            # Group commands by type or show all
            command_descriptions = []
            for command in commands_list:
                # Get command signature
                signature = self.get_command_signature(command)
                
                # Get brief description
                description = command.short_doc or "No description"
                if len(description) > 50:
                    description = description[:47] + "..."
                
                command_descriptions.append(f"`{signature}` - {description}")
            
            # Split into multiple fields if too many commands
            if len(command_descriptions) <= 10:
                embed.add_field(
                    name="Commands",
                    value="\n".join(command_descriptions),
                    inline=False
                )
            else:
                # Split into chunks
                for i in range(0, len(command_descriptions), 10):
                    chunk = command_descriptions[i:i+10]
                    field_name = "Commands" if i == 0 else "Commands (continued)"
                    embed.add_field(
                        name=field_name,
                        value="\n".join(chunk),
                        inline=False
                    )
        
        embed.set_footer(
            text=f"Use '{BotConfig.PREFIX}help <command>' for detailed command information"
        )
        
        await ctx.send(embed=embed)
    
    async def show_specific_command_help(self, ctx, command):
        """Show detailed help for a specific command"""
        embed = discord.Embed(
            title=f"📖 Command: {command.name}",
            description=command.help or "No description available",
            color=discord.Color.blue()
        )
        
        # Command signature
        signature = self.get_command_signature(command)
        embed.add_field(
            name="📝 Usage",
            value=f"`{signature}`",
            inline=False
        )
        
        # Aliases
        if command.aliases:
            embed.add_field(
                name="🔄 Aliases",
                value=", ".join([f"`{alias}`" for alias in command.aliases]),
                inline=True
            )
        
        # Cooldown
        if command.cooldown:
            embed.add_field(
                name="⏰ Cooldown",
                value=f"{command.cooldown.per}s per {command.cooldown.rate} use(s)",
                inline=True
            )
        
        # Permissions required
        if hasattr(command, 'requires_permissions'):
            embed.add_field(
                name="🔐 Permissions",
                value="Requires special permissions",
                inline=True
            )
        
        # Parameters (if hybrid command with app_commands)
        if hasattr(command, 'app_command') and command.app_command:
            app_cmd = command.app_command
            if hasattr(app_cmd, 'parameters') and app_cmd.parameters:
                param_descriptions = []
                for param in app_cmd.parameters:
                    param_desc = f"`{param.name}`"
                    if param.description != "…":
                        param_desc += f" - {param.description}"
                    if not param.required:
                        param_desc += " (optional)"
                    param_descriptions.append(param_desc)
                
                if param_descriptions:
                    embed.add_field(
                        name="📋 Parameters",
                        value="\n".join(param_descriptions),
                        inline=False
                    )
        
        # Category
        if command.cog:
            cog_emoji = getattr(command.cog, 'display_emoji', '📋')
            embed.add_field(
                name="📂 Category",
                value=f"{cog_emoji} {command.cog.qualified_name}",
                inline=True
            )
        
        # Examples (if available in command help)
        if command.help and "Example:" in command.help:
            examples = command.help.split("Example:")[-1].strip()
            embed.add_field(
                name="💡 Example",
                value=f"```{examples}```",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    def get_command_signature(self, command):
        """Get the command signature with prefix"""
        signature = f"{BotConfig.PREFIX}{command.qualified_name}"
        
        if command.signature:
            signature += f" {command.signature}"
        
        return signature
    
    @commands.hybrid_command(name="ping")
    async def ping(self, ctx):
        """Check the bot's latency"""
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency: **{latency}ms**",
            color=discord.Color.green() if latency < 100 else discord.Color.orange() if latency < 200 else discord.Color.red()
        )
        
        # Add status indicators
        status_emoji = "🟢" if latency < 100 else "🟡" if latency < 200 else "🔴"
        embed.add_field(
            name="📊 Status",
            value=f"{status_emoji} {'Excellent' if latency < 100 else 'Good' if latency < 200 else 'Poor'}",
            inline=True
        )
        
        embed.add_field(
            name="🤖 Bot Status",
            value="🟢 Online",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="uptime")
    async def uptime(self, ctx):
        """Check how long the bot has been running"""
        if not hasattr(self.bot, 'start_time'):
            embed = discord.Embed(
                title="⏰ Uptime Unknown",
                description="Bot start time not recorded.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        
        import datetime
        uptime_duration = datetime.datetime.utcnow() - self.bot.start_time
        
        days = uptime_duration.days
        hours, remainder = divmod(uptime_duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_str = ""
        if days > 0:
            uptime_str += f"{days} day{'s' if days != 1 else ''}, "
        if hours > 0:
            uptime_str += f"{hours} hour{'s' if hours != 1 else ''}, "
        if minutes > 0:
            uptime_str += f"{minutes} minute{'s' if minutes != 1 else ''}, "
        uptime_str += f"{seconds} second{'s' if seconds != 1 else ''}"
        
        embed = discord.Embed(
            title="⏰ Bot Uptime",
            description=f"I've been running for **{uptime_str}**!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🚀 Started",
            value=f"<t:{int(self.bot.start_time.timestamp())}:R>",
            inline=True
        )
        
        embed.add_field(
            name="📊 Guilds Served",
            value=f"{len(self.bot.guilds):,}",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="serverinfo", aliases=["server", "guild"])
    async def serverinfo(self, ctx):
        """Display information about the current server"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"🏰 {guild.name}",
            color=discord.Color.blue()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Basic info
        embed.add_field(
            name="👑 Owner",
            value=guild.owner.mention if guild.owner else "Unknown",
            inline=True
        )
        
        embed.add_field(
            name="🆔 Server ID",
            value=f"`{guild.id}`",
            inline=True
        )
        
        embed.add_field(
            name="📅 Created",
            value=f"<t:{int(guild.created_at.timestamp())}:D>",
            inline=True
        )
        
        # Member stats
        total_members = guild.member_count
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        bot_count = sum(1 for member in guild.members if member.bot)
        
        embed.add_field(
            name="👥 Members",
            value=f"Total: {total_members:,}\nOnline: {online_members:,}\nBots: {bot_count:,}",
            inline=True
        )
        
        # Channel stats
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(
            name="📁 Channels",
            value=f"Text: {text_channels}\nVoice: {voice_channels}\nCategories: {categories}",
            inline=True
        )
        
        # Other info
        embed.add_field(
            name="🎭 Roles",
            value=f"{len(guild.roles):,}",
            inline=True
        )
        
        # Server features
        if guild.features:
            features = []
            feature_names = {
                'COMMUNITY': 'Community Server',
                'VERIFIED': 'Verified',
                'PARTNERED': 'Partnered',
                'VANITY_URL': 'Vanity URL',
                'BANNER': 'Banner',
                'ANIMATED_ICON': 'Animated Icon',
                'INVITE_SPLASH': 'Invite Splash'
            }
            
            for feature in guild.features:
                if feature in feature_names:
                    features.append(feature_names[feature])
            
            if features:
                embed.add_field(
                    name="✨ Features",
                    value="\n".join(features[:5]),
                    inline=False
                )
        
        # Verification level
        verification_levels = {
            discord.VerificationLevel.none: "None",
            discord.VerificationLevel.low: "Low",
            discord.VerificationLevel.medium: "Medium",
            discord.VerificationLevel.high: "High",
            discord.VerificationLevel.highest: "Highest"
        }
        
        embed.add_field(
            name="🔒 Verification Level",
            value=verification_levels.get(guild.verification_level, "Unknown"),
            inline=True
        )
        
        embed.set_footer(text=f"Server Region: {guild.region if hasattr(guild, 'region') else 'Unknown'}")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="userinfo", aliases=["user", "whois"])
    @app_commands.describe(user="User to get information about")
    async def userinfo(self, ctx, user: Optional[discord.Member] = None):
        """Display information about a user"""
        target_user = user or ctx.author
        
        embed = discord.Embed(
            title=f"👤 {target_user.display_name}",
            color=target_user.color if target_user.color.value != 0 else discord.Color.blue()
        )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        # Basic info
        embed.add_field(
            name="🏷️ Username",
            value=f"{target_user.name}#{target_user.discriminator}",
            inline=True
        )
        
        embed.add_field(
            name="🆔 User ID",
            value=f"`{target_user.id}`",
            inline=True
        )
        
        embed.add_field(
            name="🤖 Bot",
            value="Yes" if target_user.bot else "No",
            inline=True
        )
        
        # Dates
        embed.add_field(
            name="📅 Account Created",
            value=f"<t:{int(target_user.created_at.timestamp())}:D>",
            inline=True
        )
        
        embed.add_field(
            name="📥 Joined Server",
            value=f"<t:{int(target_user.joined_at.timestamp())}:D>" if target_user.joined_at else "Unknown",
            inline=True
        )
        
        # Status and activity
        status_emojis = {
            discord.Status.online: "🟢 Online",
            discord.Status.idle: "🟡 Idle",
            discord.Status.dnd: "🔴 Do Not Disturb",
            discord.Status.offline: "⚫ Offline"
        }
        
        embed.add_field(
            name="📊 Status",
            value=status_emojis.get(target_user.status, "❓ Unknown"),
            inline=True
        )
        
        # Roles (show top 10)
        if target_user.roles[1:]:  # Exclude @everyone
            roles = [role.mention for role in target_user.roles[1:]]
            roles.reverse()  # Show highest first
            
            if len(roles) > 10:
                roles_text = ", ".join(roles[:10]) + f" (+{len(roles) - 10} more)"
            else:
                roles_text = ", ".join(roles)
                
            embed.add_field(
                name=f"🎭 Roles ({len(target_user.roles) - 1})",
                value=roles_text,
                inline=False
            )
        
        # Permissions (if they have notable ones)
        if target_user.guild_permissions.administrator:
            embed.add_field(
                name="⚡ Key Permissions",
                value="👑 Administrator",
                inline=True
            )
        else:
            notable_perms = []
            if target_user.guild_permissions.manage_guild:
                notable_perms.append("Manage Server")
            if target_user.guild_permissions.manage_roles:
                notable_perms.append("Manage Roles")
            if target_user.guild_permissions.manage_channels:
                notable_perms.append("Manage Channels")
            if target_user.guild_permissions.kick_members:
                notable_perms.append("Kick Members")
            if target_user.guild_permissions.ban_members:
                notable_perms.append("Ban Members")
            
            if notable_perms:
                embed.add_field(
                    name="⚡ Key Permissions",
                    value=", ".join(notable_perms[:3]),
                    inline=True
                )
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function for loading the cog"""
    # Set bot start time for uptime tracking
    if not hasattr(bot, 'start_time'):
        import datetime
        bot.start_time = datetime.datetime.utcnow()
    
    await bot.add_cog(Utilities(bot))
