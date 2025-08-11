"""
Items cog for Enhanced UnbelievaBoat bot
Handles item system, inventory, shop, and item transactions
"""

import asyncio
import json
import logging
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from config import BotConfig
from utils.decorators import database_required, admin_required
from utils.helpers import format_currency, parse_amount

logger = logging.getLogger(__name__)

class Items(commands.Cog):
    """Item system and inventory management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        
    @property
    def display_emoji(self) -> str:
        return "🎁"
    
    @commands.hybrid_command(name="inventory", aliases=["inv"])
    @app_commands.describe(
        user="User to check inventory for (defaults to yourself)",
        page="Page number to view"
    )
    @database_required
    async def inventory(self, ctx, user: Optional[discord.Member] = None, page: int = 1):
        """View your or another user's inventory"""
        target_user = user or ctx.author
        
        try:
            inventory_data = await self.db.get_user_inventory(
                target_user.id, ctx.guild.id, page=page, per_page=10
            )
            
            if not inventory_data:
                embed = discord.Embed(
                    title=f"🎒 {target_user.display_name}'s Inventory",
                    description="Inventory is empty!",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"🎒 {target_user.display_name}'s Inventory",
                description=f"Page {page}",
                color=discord.Color.blue()
            )
            
            # Add inventory items
            for item_name, quantity, item_data in inventory_data:
                item_description = item_data.get('description', 'No description')
                item_emoji = item_data.get('emoji', '📦')
                
                embed.add_field(
                    name=f"{item_emoji} {item_name}",
                    value=f"**Quantity:** {quantity:,}\n{item_description[:100]}{'...' if len(item_description) > 100 else ''}",
                    inline=True
                )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.set_footer(text=f"Use '{BotConfig.PREFIX}inventory {page + 1}' for next page")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in inventory command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to retrieve inventory.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="user-inventory")
    @app_commands.describe(
        user="User to check inventory for",
        page="Page number to view"
    )
    @database_required
    async def user_inventory(self, ctx, user: discord.Member, page: int = 1):
        """View another user's inventory (admin command)"""
        await self.inventory(ctx, user, page)
    
    @commands.hybrid_command(name="catalog", aliases=["shop", "store"])
    @app_commands.describe(item="Specific item to view details for")
    @database_required
    async def catalog(self, ctx, *, item: Optional[str] = None):
        """View the item catalog or details of a specific item"""
        try:
            if item:
                # Show specific item details
                item_data = await self.db.get_item(item.lower(), ctx.guild.id)
                
                if not item_data:
                    embed = discord.Embed(
                        title="❌ Item Not Found",
                        description=f"No item named '{item}' found in the catalog.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                    return
                
                embed = discord.Embed(
                    title=f"{item_data.get('emoji', '📦')} {item_data['name']}",
                    description=item_data.get('description', 'No description available'),
                    color=discord.Color.green()
                )
                
                if item_data.get('price'):
                    embed.add_field(
                        name="💰 Price",
                        value=format_currency(item_data['price']),
                        inline=True
                    )
                
                if item_data.get('category'):
                    embed.add_field(
                        name="📂 Category",
                        value=item_data['category'],
                        inline=True
                    )
                
                if item_data.get('usable'):
                    embed.add_field(
                        name="✅ Usable",
                        value="Yes" if item_data['usable'] else "No",
                        inline=True
                    )
                
                # Add item effects if any
                if item_data.get('effects'):
                    effects_text = []
                    for effect_type, value in item_data['effects'].items():
                        effects_text.append(f"**{effect_type.title()}:** {value}")
                    
                    embed.add_field(
                        name="⚡ Effects",
                        value="\n".join(effects_text),
                        inline=False
                    )
                
                await ctx.send(embed=embed)
            else:
                # Show all items catalog
                catalog_items = await self.db.get_all_items(ctx.guild.id)
                
                if not catalog_items:
                    embed = discord.Embed(
                        title="🏪 Item Catalog",
                        description="No items available yet! Admins can create items with the `create-item` command.",
                        color=discord.Color.blue()
                    )
                    await ctx.send(embed=embed)
                    return
                
                embed = discord.Embed(
                    title="🏪 Item Catalog",
                    description=f"Use `{BotConfig.PREFIX}catalog <item_name>` for details",
                    color=discord.Color.blue()
                )
                
                # Group items by category
                categories = {}
                for item_data in catalog_items:
                    category = item_data.get('category', 'Miscellaneous')
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(item_data)
                
                # Add each category as a field
                for category, items in categories.items():
                    item_list = []
                    for item in items[:10]:  # Limit to 10 items per category
                        emoji = item.get('emoji', '📦')
                        price_text = f" - {format_currency(item['price'])}" if item.get('price') else ""
                        item_list.append(f"{emoji} {item['name']}{price_text}")
                    
                    if len(items) > 10:
                        item_list.append(f"... and {len(items) - 10} more")
                    
                    embed.add_field(
                        name=f"📂 {category}",
                        value="\n".join(item_list) if item_list else "No items",
                        inline=True
                    )
                
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in catalog command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to retrieve catalog.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="buy-item", aliases=["buy"])
    @app_commands.describe(
        item="Name of the item to buy",
        amount="Quantity to buy (default: 1)"
    )
    @database_required
    async def buy_item(self, ctx, item: str, amount: int = 1):
        """Buy an item from the catalog"""
        try:
            if amount <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description="Amount must be positive!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Get item data
            item_data = await self.db.get_item(item.lower(), ctx.guild.id)
            
            if not item_data:
                embed = discord.Embed(
                    title="❌ Item Not Found",
                    description=f"No item named '{item}' found in the catalog.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Check if item is purchasable
            if not item_data.get('price'):
                embed = discord.Embed(
                    title="❌ Not For Sale",
                    description="This item is not available for purchase.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            total_cost = item_data['price'] * amount
            
            # Check user balance
            user_data = await self.db.get_user(ctx.author.id, ctx.guild.id)
            cash = user_data.get('cash', 0)
            
            if cash < total_cost:
                embed = discord.Embed(
                    title="❌ Insufficient Funds",
                    description=(
                        f"You need {format_currency(total_cost)} but only have {format_currency(cash)}!\n"
                        f"**Item:** {item_data['name']}\n"
                        f"**Price:** {format_currency(item_data['price'])} each\n"
                        f"**Quantity:** {amount:,}"
                    ),
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Process purchase
            await self.db.update_user_balance(
                ctx.author.id, ctx.guild.id, cash_change=-total_cost
            )
            
            await self.db.add_user_item(
                ctx.author.id, ctx.guild.id, item_data['name'], amount
            )
            
            # Create success embed
            embed = discord.Embed(
                title="✅ Purchase Successful",
                description=(
                    f"Successfully bought **{amount:,}x {item_data['name']}**!\n"
                    f"Total cost: {format_currency(total_cost)}"
                ),
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="💵 Remaining Cash",
                value=format_currency(cash - total_cost),
                inline=True
            )
            
            item_emoji = item_data.get('emoji', '📦')
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            embed.add_field(
                name=f"{item_emoji} Item",
                value=item_data['name'],
                inline=True
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in buy_item command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to process purchase.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="use")
    @app_commands.describe(
        item="Name of the item to use",
        amount="Quantity to use (default: 1)"
    )
    @database_required
    async def use_item(self, ctx, item: str, amount: int = 1):
        """Use an item from your inventory"""
        try:
            if amount <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description="Amount must be positive!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Check if user has the item
            user_inventory = await self.db.get_user_item(
                ctx.author.id, ctx.guild.id, item.lower()
            )
            
            if not user_inventory or user_inventory['quantity'] < amount:
                available = user_inventory['quantity'] if user_inventory else 0
                embed = discord.Embed(
                    title="❌ Insufficient Items",
                    description=(
                        f"You don't have enough **{item}**!\n"
                        f"Required: {amount:,}\n"
                        f"Available: {available:,}"
                    ),
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Get item data to check if usable
            item_data = await self.db.get_item(item.lower(), ctx.guild.id)
            
            if not item_data or not item_data.get('usable', False):
                embed = discord.Embed(
                    title="❌ Item Not Usable",
                    description=f"**{item}** cannot be used.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Remove items from inventory
            await self.db.remove_user_item(
                ctx.author.id, ctx.guild.id, item_data['name'], amount
            )
            
            # Apply item effects
            effects_applied = []
            if item_data.get('effects'):
                for effect_type, value in item_data['effects'].items():
                    if effect_type == 'cash':
                        await self.db.update_user_balance(
                            ctx.author.id, ctx.guild.id, cash_change=value * amount
                        )
                        effects_applied.append(f"Gained {format_currency(value * amount)} cash")
                    elif effect_type == 'xp':
                        # Handle XP gain (will be implemented in levels cog)
                        effects_applied.append(f"Gained {value * amount:,} XP")
                    else:
                        effects_applied.append(f"{effect_type.title()}: {value * amount}")
            
            # Create success embed
            embed = discord.Embed(
                title="✅ Item Used",
                description=f"Successfully used **{amount:,}x {item_data['name']}**!",
                color=discord.Color.green()
            )
            
            if effects_applied:
                embed.add_field(
                    name="⚡ Effects",
                    value="\n".join(effects_applied),
                    inline=False
                )
            
            # Show remaining quantity
            remaining = user_inventory['quantity'] - amount
            embed.add_field(
                name="📦 Remaining",
                value=f"{remaining:,}x {item_data['name']}",
                inline=True
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in use_item command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to use item.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="give-item")
    @app_commands.describe(
        user="User to give the item to",
        item="Name of the item to give",
        amount="Quantity to give (default: 1)"
    )
    @database_required
    async def give_item(self, ctx, user: discord.Member, item: str, amount: int = 1):
        """Give an item to another user"""
        if user == ctx.author:
            embed = discord.Embed(
                title="❌ Invalid Action",
                description="You cannot give items to yourself!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if user.bot:
            embed = discord.Embed(
                title="❌ Invalid Action",
                description="You cannot give items to bots!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            if amount <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description="Amount must be positive!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Check if sender has the item
            sender_inventory = await self.db.get_user_item(
                ctx.author.id, ctx.guild.id, item.lower()
            )
            
            if not sender_inventory or sender_inventory['quantity'] < amount:
                available = sender_inventory['quantity'] if sender_inventory else 0
                embed = discord.Embed(
                    title="❌ Insufficient Items",
                    description=(
                        f"You don't have enough **{item}**!\n"
                        f"Required: {amount:,}\n"
                        f"Available: {available:,}"
                    ),
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Get item data
            item_data = await self.db.get_item(item.lower(), ctx.guild.id)
            
            if not item_data:
                embed = discord.Embed(
                    title="❌ Item Not Found",
                    description=f"Item '{item}' not found in catalog.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Transfer the item
            await self.db.remove_user_item(
                ctx.author.id, ctx.guild.id, item_data['name'], amount
            )
            
            await self.db.add_user_item(
                user.id, ctx.guild.id, item_data['name'], amount
            )
            
            # Create success embed
            embed = discord.Embed(
                title="🎁 Item Transfer Successful",
                description=(
                    f"{ctx.author.mention} gave **{amount:,}x {item_data['name']}** to {user.mention}!"
                ),
                color=discord.Color.green()
            )
            
            item_emoji = item_data.get('emoji', '📦')
            embed.add_field(
                name=f"{item_emoji} Item",
                value=item_data['name'],
                inline=True
            )
            
            remaining = sender_inventory['quantity'] - amount
            embed.add_field(
                name="📦 Your Remaining",
                value=f"{remaining:,}x {item_data['name']}",
                inline=True
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in give_item command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to transfer item.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    # Admin commands for item management
    
    @commands.hybrid_command(name="create-item")
    @database_required
    @admin_required
    async def create_item(self, ctx):
        """Create a new item (interactive setup)"""
        try:
            # Interactive item creation
            embed = discord.Embed(
                title="🔧 Item Creation Wizard",
                description="Creating a new item. Please answer the following questions:",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            
            def check(message):
                return message.author == ctx.author and message.channel == ctx.channel
            
            # Get item name
            await ctx.send("📝 What should the item be called?")
            try:
                name_msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                item_name = name_msg.content.strip()
                
                if len(item_name) > 50:
                    await ctx.send("❌ Item name too long! Maximum 50 characters.")
                    return
                
                # Check if item already exists
                existing_item = await self.db.get_item(item_name.lower(), ctx.guild.id)
                if existing_item:
                    await ctx.send(f"❌ Item '{item_name}' already exists!")
                    return
            except asyncio.TimeoutError:
                await ctx.send("⏰ Timed out. Item creation cancelled.")
                return
            
            # Get description
            await ctx.send("📖 What's the description for this item?")
            try:
                desc_msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                description = desc_msg.content.strip()
                
                if len(description) > 200:
                    await ctx.send("❌ Description too long! Maximum 200 characters.")
                    return
            except asyncio.TimeoutError:
                description = "No description provided."
            
            # Get emoji
            await ctx.send("😀 What emoji should represent this item? (or 'skip' for default)")
            try:
                emoji_msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                emoji = emoji_msg.content.strip()
                if emoji.lower() == 'skip':
                    emoji = '📦'
            except asyncio.TimeoutError:
                emoji = '📦'
            
            # Get price
            await ctx.send("💰 What should the price be? (or 'skip' for non-purchasable)")
            try:
                price_msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                price_text = price_msg.content.strip()
                
                if price_text.lower() == 'skip':
                    price = None
                else:
                    price = parse_amount(price_text)
                    if price is None or price < 0:
                        await ctx.send("❌ Invalid price! Using no price.")
                        price = None
            except asyncio.TimeoutError:
                price = None
            
            # Get category
            await ctx.send("📂 What category is this item? (or 'skip' for Miscellaneous)")
            try:
                category_msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                category = category_msg.content.strip()
                if category.lower() == 'skip':
                    category = "Miscellaneous"
            except asyncio.TimeoutError:
                category = "Miscellaneous"
            
            # Get usability
            await ctx.send("🔧 Is this item usable? (yes/no)")
            try:
                usable_msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                usable = usable_msg.content.strip().lower() in ['yes', 'y', 'true', '1']
            except asyncio.TimeoutError:
                usable = False
            
            # Create item data
            item_data = {
                'name': item_name,
                'description': description,
                'emoji': emoji,
                'price': price,
                'category': category,
                'usable': usable,
                'effects': {}
            }
            
            # Add effects if usable
            if usable:
                await ctx.send("⚡ What effects should this item have when used? (Format: 'cash:100' or 'skip')")
                try:
                    effects_msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                    effects_text = effects_msg.content.strip()
                    
                    if effects_text.lower() != 'skip':
                        # Parse effects (simple format: type:value)
                        for effect in effects_text.split(','):
                            if ':' in effect:
                                effect_type, effect_value = effect.strip().split(':', 1)
                                try:
                                    item_data['effects'][effect_type.strip()] = int(effect_value.strip())
                                except ValueError:
                                    item_data['effects'][effect_type.strip()] = effect_value.strip()
                except asyncio.TimeoutError:
                    pass
            
            # Save item to database
            await self.db.create_item(ctx.guild.id, item_data)
            
            # Create confirmation embed
            embed = discord.Embed(
                title="✅ Item Created Successfully!",
                description=f"**{emoji} {item_name}** has been added to the catalog.",
                color=discord.Color.green()
            )
            
            embed.add_field(name="📖 Description", value=description, inline=False)
            if price:
                embed.add_field(name="💰 Price", value=format_currency(price), inline=True)
            embed.add_field(name="📂 Category", value=category, inline=True)
            embed.add_field(name="🔧 Usable", value="Yes" if usable else "No", inline=True)
            
            if item_data['effects']:
                effects_text = []
                for effect_type, value in item_data['effects'].items():
                    effects_text.append(f"**{effect_type}:** {value}")
                embed.add_field(
                    name="⚡ Effects",
                    value="\n".join(effects_text),
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in create_item command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to create item.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="delete-item")
    @app_commands.describe(item="Name of the item to delete")
    @database_required
    @admin_required
    async def delete_item(self, ctx, *, item: str):
        """Delete an item from the catalog"""
        try:
            # Check if item exists
            item_data = await self.db.get_item(item.lower(), ctx.guild.id)
            
            if not item_data:
                embed = discord.Embed(
                    title="❌ Item Not Found",
                    description=f"No item named '{item}' found in the catalog.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Confirmation
            embed = discord.Embed(
                title="⚠️ Confirm Item Deletion",
                description=(
                    f"Are you sure you want to delete **{item_data['name']}**?\n"
                    f"This will also remove it from all user inventories!\n\n"
                    f"React with ✅ to confirm or ❌ to cancel."
                ),
                color=discord.Color.orange()
            )
            
            message = await ctx.send(embed=embed)
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
                        description="Item deletion cancelled.",
                        color=discord.Color.red()
                    )
                    await message.edit(embed=embed)
                    return
                
                # Delete the item
                await self.db.delete_item(item_data['name'], ctx.guild.id)
                
                embed = discord.Embed(
                    title="✅ Item Deleted",
                    description=f"**{item_data['name']}** has been permanently deleted from the catalog and all inventories.",
                    color=discord.Color.green()
                )
                
                embed.set_footer(text=f"Action by: {ctx.author.display_name}")
                await message.edit(embed=embed)
                
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="⏰ Timeout",
                    description="Confirmation timed out. Deletion cancelled.",
                    color=discord.Color.red()
                )
                await message.edit(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in delete_item command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to delete item.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="spawn-item")
    @app_commands.describe(
        user="User to give the item to",
        item="Name of the item to spawn",
        amount="Quantity to spawn (default: 1)"
    )
    @database_required
    @admin_required
    async def spawn_item(self, ctx, user: discord.Member, item: str, amount: int = 1):
        """Spawn an item directly into a user's inventory"""
        try:
            if amount <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description="Amount must be positive!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Check if item exists
            item_data = await self.db.get_item(item.lower(), ctx.guild.id)
            
            if not item_data:
                embed = discord.Embed(
                    title="❌ Item Not Found",
                    description=f"No item named '{item}' found in the catalog.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Add item to user's inventory
            await self.db.add_user_item(
                user.id, ctx.guild.id, item_data['name'], amount
            )
            
            embed = discord.Embed(
                title="✅ Item Spawned",
                description=f"Spawned **{amount:,}x {item_data['name']}** in {user.mention}'s inventory!",
                color=discord.Color.green()
            )
            
            item_emoji = item_data.get('emoji', '📦')
            embed.add_field(
                name=f"{item_emoji} Item",
                value=item_data['name'],
                inline=True
            )
            
            embed.set_footer(text=f"Action by: {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in spawn_item command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to spawn item.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="remove-user-item")
    @app_commands.describe(
        user="User to remove items from",
        item="Name of the item to remove",
        amount="Quantity to remove"
    )
    @database_required
    @admin_required
    async def remove_user_item(self, ctx, user: discord.Member, item: str, amount: int):
        """Remove items from a user's inventory"""
        try:
            if amount <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description="Amount must be positive!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Check if user has the item
            user_inventory = await self.db.get_user_item(
                user.id, ctx.guild.id, item.lower()
            )
            
            if not user_inventory:
                embed = discord.Embed(
                    title="❌ Item Not Found",
                    description=f"{user.display_name} doesn't have any **{item}**!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Cap removal at available quantity
            actual_removal = min(amount, user_inventory['quantity'])
            
            # Remove items
            await self.db.remove_user_item(
                user.id, ctx.guild.id, user_inventory['item_name'], actual_removal
            )
            
            embed = discord.Embed(
                title="✅ Items Removed",
                description=f"Removed **{actual_removal:,}x {user_inventory['item_name']}** from {user.mention}'s inventory!",
                color=discord.Color.orange()
            )
            
            if actual_removal < amount:
                embed.add_field(
                    name="⚠️ Note",
                    value=f"User only had {user_inventory['quantity']:,}, so that's all that was removed.",
                    inline=False
                )
            
            remaining = user_inventory['quantity'] - actual_removal
            embed.add_field(
                name="📦 Remaining",
                value=f"{remaining:,}x {user_inventory['item_name']}",
                inline=True
            )
            
            embed.set_footer(text=f"Action by: {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in remove_user_item command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to remove items.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(Items(bot))
