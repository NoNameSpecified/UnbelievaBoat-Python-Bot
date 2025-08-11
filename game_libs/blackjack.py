"""
Blackjack game implementation for Enhanced UnbelievaBoat bot
"""

import random
from typing import List, Dict, Any, Optional

class Card:
    """Represents a playing card"""
    
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        self.value = self._calculate_value()
    
    def _calculate_value(self) -> int:
        """Calculate the numeric value of the card"""
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11  # Aces are handled specially in hand calculation
        else:
            return int(self.rank)
    
    def __str__(self) -> str:
        """String representation of the card"""
        suit_emojis = {
            'Hearts': '♥️',
            'Diamonds': '♦️',
            'Clubs': '♣️',
            'Spades': '♠️'
        }
        return f"{self.rank}{suit_emojis.get(self.suit, self.suit)}"

class Deck:
    """Represents a deck of playing cards"""
    
    def __init__(self, num_decks: int = 1):
        self.cards = []
        self.num_decks = num_decks
        self._create_deck()
        self.shuffle()
    
    def _create_deck(self):
        """Create a standard 52-card deck (or multiple decks)"""
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        
        for _ in range(self.num_decks):
            for suit in suits:
                for rank in ranks:
                    self.cards.append(Card(suit, rank))
    
    def shuffle(self):
        """Shuffle the deck"""
        random.shuffle(self.cards)
    
    def deal_card(self) -> Optional[Card]:
        """Deal one card from the deck"""
        if len(self.cards) > 0:
            return self.cards.pop()
        return None
    
    def cards_remaining(self) -> int:
        """Get number of cards remaining in deck"""
        return len(self.cards)

class BlackjackHand:
    """Represents a blackjack hand"""
    
    def __init__(self):
        self.cards: List[Card] = []
    
    def add_card(self, card: Card):
        """Add a card to the hand"""
        self.cards.append(card)
    
    def get_value(self) -> int:
        """Calculate the best possible value of the hand"""
        value = 0
        aces = 0
        
        # First, add up all non-ace cards
        for card in self.cards:
            if card.rank == 'A':
                aces += 1
            else:
                value += card.value
        
        # Add aces (11 or 1)
        for _ in range(aces):
            if value + 11 <= 21:
                value += 11
            else:
                value += 1
        
        return value
    
    def is_blackjack(self) -> bool:
        """Check if hand is a natural blackjack (21 with 2 cards)"""
        return len(self.cards) == 2 and self.get_value() == 21
    
    def is_busted(self) -> bool:
        """Check if hand value exceeds 21"""
        return self.get_value() > 21
    
    def can_split(self) -> bool:
        """Check if hand can be split (two cards of same rank)"""
        return (len(self.cards) == 2 and 
                self.cards[0].rank == self.cards[1].rank)
    
    def display(self, hide_first: bool = False) -> str:
        """Display the hand as a string"""
        if hide_first and len(self.cards) > 0:
            # Show hidden card for dealer
            visible_cards = ['🂠'] + [str(card) for card in self.cards[1:]]
        else:
            visible_cards = [str(card) for card in self.cards]
        
        return ' '.join(visible_cards)
    
    def __len__(self) -> int:
        """Get number of cards in hand"""
        return len(self.cards)

class BlackjackGame:
    """Main blackjack game class"""
    
    def __init__(self, bet_amount: int, num_decks: int = 6):
        self.bet_amount = bet_amount
        self.deck = Deck(num_decks)
        self.player_hand = BlackjackHand()
        self.dealer_hand = BlackjackHand()
        self.game_over = False
        self.winner = None
        
        # Deal initial cards
        self._deal_initial_cards()
    
    def _deal_initial_cards(self):
        """Deal initial two cards to player and dealer"""
        # Deal two cards to player
        self.player_hand.add_card(self.deck.deal_card())
        self.player_hand.add_card(self.deck.deal_card())
        
        # Deal two cards to dealer
        self.dealer_hand.add_card(self.deck.deal_card())
        self.dealer_hand.add_card(self.deck.deal_card())
    
    def hit(self) -> bool:
        """Player hits (takes another card). Returns True if game continues, False if busted"""
        if self.game_over:
            return False
        
        card = self.deck.deal_card()
        if card:
            self.player_hand.add_card(card)
        
        # Check if player busted
        if self.player_hand.is_busted():
            self.game_over = True
            self.winner = "dealer"
            return False
        
        return True
    
    def stand(self):
        """Player stands - dealer plays their hand"""
        if self.game_over:
            return
        
        self.dealer_play()
        self.game_over = True
    
    def dealer_play(self):
        """Dealer plays according to standard rules (hit on 16, stand on 17)"""
        while self.dealer_hand.get_value() < 17:
            card = self.deck.deal_card()
            if card:
                self.dealer_hand.add_card(card)
        
        # Determine winner
        self._determine_winner()
    
    def _determine_winner(self):
        """Determine the winner of the game"""
        player_value = self.player_hand.get_value()
        dealer_value = self.dealer_hand.get_value()
        
        # Check for busts
        if self.player_hand.is_busted():
            self.winner = "dealer"
        elif self.dealer_hand.is_busted():
            self.winner = "player"
        # Check for blackjacks
        elif self.player_hand.is_blackjack() and not self.dealer_hand.is_blackjack():
            self.winner = "player_blackjack"
        elif self.dealer_hand.is_blackjack() and not self.player_hand.is_blackjack():
            self.winner = "dealer"
        elif self.player_hand.is_blackjack() and self.dealer_hand.is_blackjack():
            self.winner = "push"
        # Compare values
        elif player_value > dealer_value:
            self.winner = "player"
        elif dealer_value > player_value:
            self.winner = "dealer"
        else:
            self.winner = "push"
    
    def get_winner(self) -> Optional[str]:
        """Get the winner of the game"""
        return self.winner
    
    def player_has_blackjack(self) -> bool:
        """Check if player has blackjack"""
        return self.player_hand.is_blackjack()
    
    def dealer_has_blackjack(self) -> bool:
        """Check if dealer has blackjack"""
        return self.dealer_hand.is_blackjack()
    
    def player_busted(self) -> bool:
        """Check if player busted"""
        return self.player_hand.is_busted()
    
    def dealer_busted(self) -> bool:
        """Check if dealer busted"""
        return self.dealer_hand.is_busted()
    
    def get_player_value(self) -> int:
        """Get player hand value"""
        return self.player_hand.get_value()
    
    def get_dealer_value(self) -> int:
        """Get dealer hand value"""
        return self.dealer_hand.get_value()
    
    def get_player_display(self) -> str:
        """Get player hand display string"""
        return self.player_hand.display()
    
    def get_dealer_display(self, hidden: bool = False) -> str:
        """Get dealer hand display string"""
        return self.dealer_hand.display(hide_first=hidden)
    
    def can_hit(self) -> bool:
        """Check if player can hit"""
        return not self.game_over and not self.player_hand.is_busted()
    
    def can_stand(self) -> bool:
        """Check if player can stand"""
        return not self.game_over
    
    def can_double_down(self) -> bool:
        """Check if player can double down (only on first two cards)"""
        return (not self.game_over and 
                len(self.player_hand) == 2 and 
                not self.player_hand.is_blackjack())
    
    def double_down(self) -> bool:
        """Player doubles down - doubles bet and takes exactly one more card"""
        if not self.can_double_down():
            return False
        
        # Double the bet
        self.bet_amount *= 2
        
        # Take exactly one card
        card = self.deck.deal_card()
        if card:
            self.player_hand.add_card(card)
        
        # Check if busted, otherwise dealer plays
        if self.player_hand.is_busted():
            self.game_over = True
            self.winner = "dealer"
        else:
            self.dealer_play()
            self.game_over = True
        
        return True
    
    def can_split(self) -> bool:
        """Check if player can split their hand"""
        return (not self.game_over and 
                len(self.player_hand) == 2 and 
                self.player_hand.can_split())
    
    def get_game_state(self) -> Dict[str, Any]:
        """Get complete game state as dictionary"""
        return {
            'bet_amount': self.bet_amount,
            'game_over': self.game_over,
            'winner': self.winner,
            'player_hand': {
                'cards': [str(card) for card in self.player_hand.cards],
                'value': self.player_hand.get_value(),
                'is_blackjack': self.player_hand.is_blackjack(),
                'is_busted': self.player_hand.is_busted()
            },
            'dealer_hand': {
                'cards': [str(card) for card in self.dealer_hand.cards],
                'value': self.dealer_hand.get_value(),
                'is_blackjack': self.dealer_hand.is_blackjack(),
                'is_busted': self.dealer_hand.is_busted()
            },
            'actions_available': {
                'can_hit': self.can_hit(),
                'can_stand': self.can_stand(),
                'can_double_down': self.can_double_down(),
                'can_split': self.can_split()
            }
        }
    
    def calculate_payout(self) -> int:
        """Calculate payout based on game result"""
        if self.winner == "player_blackjack":
            return int(self.bet_amount * 2.5)  # 3:2 payout for blackjack
        elif self.winner == "player":
            return self.bet_amount * 2  # 1:1 payout for regular win
        elif self.winner == "push":
            return self.bet_amount  # Return original bet
        else:  # dealer wins
            return 0  # Lose bet
    
    def get_result_message(self) -> str:
        """Get a descriptive message about the game result"""
        if self.winner == "player_blackjack":
            return "🎉 Blackjack! You win!"
        elif self.winner == "player":
            return "🎉 You win!"
        elif self.winner == "dealer":
            if self.player_hand.is_busted():
                return "💥 Busted! Dealer wins."
            else:
                return "😔 Dealer wins."
        elif self.winner == "push":
            return "🤝 Push! It's a tie."
        else:
            return "🎮 Game in progress..."
