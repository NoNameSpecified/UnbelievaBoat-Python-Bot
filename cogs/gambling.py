"""
Gambling cog for Enhanced UnbelievaBoat bot
Handles blackjack, roulette, and other gambling games
"""

import asyncio
import logging
import random
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from config import BotConfig
from utils.decorators import database_required, cooldown_check
from utils.helpers import format_currency, parse_amount
from game_libs.blackjack import BlackjackGame
from game_libs.roulette import RouletteGame

logger = logging.getLogger(__name__)

class Gambling(commands.Cog):
    """Gambling and casino games"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.active_games = {}  # Track active games per user
        
    @property
    def display_emoji(self) -> str:
        return "🎰"
    
    @commands.hybrid_command(name="blackjack", aliases=["bj"])
    @app_commands.describe(bet="Amount to bet")
    @database_required
    @cooldown_check("blackjack", BotConfig.BLACKJACK_COOLDOWN)
    async def blackjack(self, ctx, bet: str):
        """Play a game of blackjack"""
        try:
            bet_amount = parse_amount(bet)
            if bet_amount is None:
                raise ValueError("Invalid bet amount")
                
            if not BotConfig.validate_bet(bet_amount):
                embed = discord.Embed(
                    title="❌ Invalid Bet",
                    description=BotConfig.ERROR_MESSAGES['invalid_bet'],
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
                
            # Check user balance
            user_data = await self.db.get_user(ctx.author.id, ctx.guild.id)
            cash = user_data.get('cash', 0)
            
            if cash < bet_amount:
                embed = discord.Embed(
                    title="❌ Insufficient Funds",
                    description=f"You need {format_currency(bet_amount)} but only have {format_currency(cash)}!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Check if user already has an active game
            if ctx.author.id in self.active_games:
                embed = discord.Embed(
                    title="🎮 Game in Progress",
                    description="You already have an active game! Finish it first.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
                return
            
            # Create new blackjack game
            game = BlackjackGame(bet_amount)
            self.active_games[ctx.author.id] = game
            
            # Create initial game embed
            embed = discord.Embed(
                title="🃏 Blackjack Game",
                description=f"**Bet:** {format_currency(bet_amount)}",
                color=discord.Color.blue()
            )
            
            # Add dealer cards (hide one)
            embed.add_field(
                name="🎩 Dealer's Hand",
                value=f"{game.get_dealer_display(hidden=True)} (Value: ?)",
                inline=False
            )
            
            # Add player cards
            embed.add_field(
                name="👤 Your Hand",
                value=f"{game.get_player_display()} (Value: {game.get_player_value()})",
                inline=False
            )
            
            # Check for immediate blackjack
            if game.player_has_blackjack():
                # Remove active game
                del self.active_games[ctx.author.id]
                
                if game.dealer_has_blackjack():
                    # Push - return bet
                    embed.title = "🤝 Push!"
                    embed.description += f"\n\nBoth have blackjack! Your bet of {format_currency(bet_amount)} has been returned."
                    embed.color = discord.Color.orange()
                    # No balance change needed
                else:
                    # Player blackjack wins
                    winnings = int(bet_amount * 1.5)  # 3:2 payout
                    await self.db.update_user_balance(
                        ctx.author.id, ctx.guild.id, 
                        cash_change=winnings
                    )
                    
                    embed.title = "🎉 Blackjack!"
                    embed.description += f"\n\nYou won {format_currency(winnings)}!"
                    embed.color = discord.Color.green()
                
                # Reveal dealer cards
                embed.set_field_at(
                    0,
                    name="🎩 Dealer's Hand",
                    value=f"{game.get_dealer_display()} (Value: {game.get_dealer_value()})",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                return
            
            # Add action buttons
            view = BlackjackView(self, ctx.author.id, bet_amount)
            await ctx.send(embed=embed, view=view)
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Bet",
                description="Please provide a valid bet amount.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in blackjack command: {e}")
            # Clean up active game if it exists
            if ctx.author.id in self.active_games:
                del self.active_games[ctx.author.id]
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to start blackjack game.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="roulette", aliases=["roul"])
    @app_commands.describe(
        bet="Amount to bet",
        choice="What to bet on (red, black, odd, even, or number 0-36)"
    )
    @database_required
    @cooldown_check("roulette", BotConfig.ROULETTE_COOLDOWN)
    async def roulette(self, ctx, bet: str, choice: str):
        """Play roulette"""
        try:
            bet_amount = parse_amount(bet)
            if bet_amount is None:
                raise ValueError("Invalid bet amount")
                
            if not BotConfig.validate_bet(bet_amount):
                embed = discord.Embed(
                    title="❌ Invalid Bet",
                    description=BotConfig.ERROR_MESSAGES['invalid_bet'],
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Check user balance
            user_data = await self.db.get_user(ctx.author.id, ctx.guild.id)
            cash = user_data.get('cash', 0)
            
            if cash < bet_amount:
                embed = discord.Embed(
                    title="❌ Insufficient Funds",
                    description=f"You need {format_currency(bet_amount)} but only have {format_currency(cash)}!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Create roulette game
            game = RouletteGame()
            result = game.spin()
            win_amount = game.calculate_winnings(choice.lower(), bet_amount)
            
            # Create result embed
            embed = discord.Embed(
                title="🎰 Roulette Results",
                color=discord.Color.blue()
            )
            
            # Add game info
            embed.add_field(
                name="🎯 Your Bet",
                value=f"{format_currency(bet_amount)} on **{choice.upper()}**",
                inline=False
            )
            
            embed.add_field(
                name="🎲 Result",
                value=f"**{result['number']}** ({result['color'].upper()})",
                inline=False
            )
            
            if win_amount > 0:
                # Player wins
                net_winnings = win_amount - bet_amount
                await self.db.update_user_balance(
                    ctx.author.id, ctx.guild.id,
                    cash_change=net_winnings
                )
                
                embed.add_field(
                    name="🎉 You Won!",
                    value=f"Winnings: {format_currency(win_amount)}\nProfit: {format_currency(net_winnings)}",
                    inline=False
                )
                embed.color = discord.Color.green()
            else:
                # Player loses
                await self.db.update_user_balance(
                    ctx.author.id, ctx.guild.id,
                    cash_change=-bet_amount
                )
                
                embed.add_field(
                    name="💸 You Lost!",
                    value=f"Lost: {format_currency(bet_amount)}",
                    inline=False
                )
                embed.color = discord.Color.red()
            
            # Add remaining balance
            new_balance = cash + (win_amount - bet_amount if win_amount > 0 else -bet_amount)
            embed.set_footer(text=f"Remaining cash: {format_currency(new_balance)}")
            
            await ctx.send(embed=embed)
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Please provide a valid bet amount and choice (red, black, odd, even, or number 0-36).",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in roulette command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to play roulette.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

class BlackjackView(discord.ui.View):
    """Interactive view for blackjack games"""
    
    def __init__(self, cog, user_id, bet_amount):
        super().__init__(timeout=300)  # 5 minute timeout
        self.cog = cog
        self.user_id = user_id
        self.bet_amount = bet_amount
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the game owner to interact"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This isn't your game!", ephemeral=True
            )
            return False
        return True
    
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green, emoji="🃏")
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Hit button - draw another card"""
        if self.user_id not in self.cog.active_games:
            await interaction.response.send_message(
                "Game not found!", ephemeral=True
            )
            return
            
        game = self.cog.active_games[self.user_id]
        game.hit()
        
        # Create updated embed
        embed = discord.Embed(
            title="🃏 Blackjack Game",
            description=f"**Bet:** {format_currency(self.bet_amount)}",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🎩 Dealer's Hand",
            value=f"{game.get_dealer_display(hidden=True)} (Value: ?)",
            inline=False
        )
        
        embed.add_field(
            name="👤 Your Hand",
            value=f"{game.get_player_display()} (Value: {game.get_player_value()})",
            inline=False
        )
        
        # Check if player busted
        if game.player_busted():
            await self._end_game(interaction, embed, game, busted=True)
        else:
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.red, emoji="✋")
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Stand button - end turn"""
        if self.user_id not in self.cog.active_games:
            await interaction.response.send_message(
                "Game not found!", ephemeral=True
            )
            return
            
        game = self.cog.active_games[self.user_id]
        
        # Dealer plays
        game.dealer_play()
        
        # Create final embed
        embed = discord.Embed(
            title="🃏 Blackjack Results",
            description=f"**Bet:** {format_currency(self.bet_amount)}",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🎩 Dealer's Hand",
            value=f"{game.get_dealer_display()} (Value: {game.get_dealer_value()})",
            inline=False
        )
        
        embed.add_field(
            name="👤 Your Hand", 
            value=f"{game.get_player_display()} (Value: {game.get_player_value()})",
            inline=False
        )
        
        await self._end_game(interaction, embed, game)
    
    async def _end_game(self, interaction, embed, game, busted=False):
        """End the game and update balance"""
        # Remove from active games
        if self.user_id in self.cog.active_games:
            del self.cog.active_games[self.user_id]
        
        # Determine winner and update balance
        if busted:
            # Player busted
            await self.cog.db.update_user_balance(
                self.user_id, interaction.guild.id,
                cash_change=-self.bet_amount
            )
            embed.add_field(
                name="💸 Busted!",
                value=f"You went over 21! Lost {format_currency(self.bet_amount)}.",
                inline=False
            )
            embed.color = discord.Color.red()
        else:
            winner = game.get_winner()
            if winner == "player":
                # Player wins
                await self.cog.db.update_user_balance(
                    self.user_id, interaction.guild.id,
                    cash_change=self.bet_amount
                )
                embed.add_field(
                    name="🎉 You Win!",
                    value=f"Won {format_currency(self.bet_amount)}!",
                    inline=False
                )
                embed.color = discord.Color.green()
            elif winner == "dealer":
                # Dealer wins
                await self.cog.db.update_user_balance(
                    self.user_id, interaction.guild.id,
                    cash_change=-self.bet_amount
                )
                embed.add_field(
                    name="💸 Dealer Wins!",
                    value=f"Lost {format_currency(self.bet_amount)}.",
                    inline=False
                )
                embed.color = discord.Color.red()
            else:
                # Push/tie
                embed.add_field(
                    name="🤝 Push!",
                    value=f"It's a tie! Your bet of {format_currency(self.bet_amount)} has been returned.",
                    inline=False
                )
                embed.color = discord.Color.orange()
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def on_timeout(self):
        """Handle view timeout"""
        if self.user_id in self.cog.active_games:
            del self.cog.active_games[self.user_id]

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(Gambling(bot))
