"""
Database manager for Enhanced UnbelievaBoat bot
Handles all database operations using SQLite
"""

import asyncio
import aiosqlite
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from config import BotConfig

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages all database operations for the bot"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or BotConfig.DATABASE_PATH or 'database/economy.db'
        self._ensure_directory()
        
    def _ensure_directory(self):
        """Ensure the database directory exists"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize the database with all required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Enable foreign keys
            await db.execute("PRAGMA foreign_keys = ON")
            
            # Users table - main user data
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    cash INTEGER DEFAULT 0,
                    bank INTEGER DEFAULT 0,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    last_daily TIMESTAMP,
                    last_work TIMESTAMP,
                    last_crime TIMESTAMP,
                    last_slut TIMESTAMP,
                    last_rob TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            
            # Items table - available items
            await db.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    emoji TEXT DEFAULT '📦',
                    price INTEGER,
                    category TEXT DEFAULT 'Miscellaneous',
                    usable BOOLEAN DEFAULT FALSE,
                    effects TEXT, -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, name)
                )
            """)
            
            # User inventory table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_inventory (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    item_name TEXT NOT NULL,
                    quantity INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, guild_id, item_name),
                    FOREIGN KEY (guild_id, item_name) REFERENCES items(guild_id, name) ON DELETE CASCADE
                )
            """)
            
            # Income roles table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS income_roles (
                    guild_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    income INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, role_id)
                )
            """)
            
            # Level rewards table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS level_rewards (
                    guild_id INTEGER NOT NULL,
                    level INTEGER NOT NULL,
                    money INTEGER DEFAULT 0,
                    roles_add TEXT, -- JSON array of role IDs
                    roles_remove TEXT, -- JSON array of role IDs
                    items TEXT, -- JSON object of item_name: quantity
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, level)
                )
            """)
            
            # Warnings table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Guild settings table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    prefix TEXT DEFAULT '+',
                    currency_emoji TEXT DEFAULT '💰',
                    income_reset BOOLEAN DEFAULT TRUE,
                    passive_chat_income INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Cooldowns table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cooldowns (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    command_name TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    PRIMARY KEY (user_id, guild_id, command_name)
                )
            """)
            
            # Create indexes for performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_guild_id ON users(guild_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_xp ON users(guild_id, xp DESC)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_total_wealth ON users(guild_id, (cash + bank) DESC)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_warnings_user ON warnings(guild_id, user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_cooldowns_expires ON cooldowns(expires_at)")
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    async def get_user(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Get user data, creating entry if it doesn't exist"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(
                "SELECT * FROM users WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            )
            row = await cursor.fetchone()
            
            if row:
                return dict(row)
            else:
                # Create new user with default balance
                await db.execute("""
                    INSERT INTO users (user_id, guild_id, cash, bank, xp, level)
                    VALUES (?, ?, ?, 0, 0, 1)
                """, (user_id, guild_id, BotConfig.DEFAULT_BALANCE))
                await db.commit()
                
                return {
                    'user_id': user_id,
                    'guild_id': guild_id,
                    'cash': BotConfig.DEFAULT_BALANCE,
                    'bank': 0,
                    'xp': 0,
                    'level': 1
                }
    
    async def update_user_balance(self, user_id: int, guild_id: int, cash_change: int = 0, bank_change: int = 0):
        """Update user's cash and/or bank balance"""
        await self.get_user(user_id, guild_id)  # Ensure user exists
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users 
                SET cash = MAX(0, cash + ?), 
                    bank = MAX(0, bank + ?),
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND guild_id = ?
            """, (cash_change, bank_change, user_id, guild_id))
            await db.commit()
    
    async def add_user_xp(self, user_id: int, guild_id: int, xp_amount: int):
        """Add XP to a user"""
        await self.get_user(user_id, guild_id)  # Ensure user exists
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users 
                SET xp = xp + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND guild_id = ?
            """, (xp_amount, user_id, guild_id))
            await db.commit()
    
    async def update_user_level(self, user_id: int, guild_id: int, new_level: int):
        """Update user's level"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users 
                SET level = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND guild_id = ?
            """, (new_level, user_id, guild_id))
            await db.commit()
    
    async def get_leaderboard(self, guild_id: int, sort_by: str = "total", page: int = 1, per_page: int = 10) -> List[Tuple]:
        """Get wealth leaderboard for a guild"""
        offset = (page - 1) * per_page
        
        if sort_by == "cash":
            order_clause = "ORDER BY cash DESC"
        elif sort_by == "bank":
            order_clause = "ORDER BY bank DESC"
        else:  # total
            order_clause = "ORDER BY (cash + bank) DESC"
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(f"""
                SELECT user_id, cash, bank, (cash + bank) as total
                FROM users 
                WHERE guild_id = ? AND (cash > 0 OR bank > 0)
                {order_clause}
                LIMIT ? OFFSET ?
            """, (guild_id, per_page, offset))
            
            return await cursor.fetchall()
    
    async def get_xp_leaderboard(self, guild_id: int, page: int = 1, per_page: int = 10) -> List[Tuple]:
        """Get XP leaderboard for a guild"""
        offset = (page - 1) * per_page
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT user_id, xp, level
                FROM users 
                WHERE guild_id = ? AND xp > 0
                ORDER BY xp DESC
                LIMIT ? OFFSET ?
            """, (guild_id, per_page, offset))
            
            return await cursor.fetchall()
    
    async def get_user_xp_rank(self, user_id: int, guild_id: int) -> int:
        """Get user's rank in XP leaderboard"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT COUNT(*) + 1 as rank
                FROM users 
                WHERE guild_id = ? 
                AND xp > (SELECT xp FROM users WHERE user_id = ? AND guild_id = ?)
            """, (guild_id, user_id, guild_id))
            
            result = await cursor.fetchone()
            return result[0] if result else 1
    
    async def get_economy_stats(self, guild_id: int) -> Dict[str, Any]:
        """Get economy statistics for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    SUM(cash) as total_cash,
                    SUM(bank) as total_bank,
                    SUM(cash + bank) as total_wealth,
                    MAX(cash + bank) as richest_amount,
                    AVG(cash + bank) as average_wealth
                FROM users 
                WHERE guild_id = ?
            """, (guild_id,))
            
            row = await cursor.fetchone()
            if row:
                return {
                    'total_users': row[0],
                    'total_cash': row[1] or 0,
                    'total_bank': row[2] or 0,
                    'total_wealth': row[3] or 0,
                    'richest_amount': row[4] or 0,
                    'average_wealth': int(row[5]) if row[5] else 0
                }
            return {}
    
    # Item management methods
    
    async def create_item(self, guild_id: int, item_data: Dict[str, Any]):
        """Create a new item"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO items (guild_id, name, description, emoji, price, category, usable, effects)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                guild_id,
                item_data['name'],
                item_data.get('description', ''),
                item_data.get('emoji', '📦'),
                item_data.get('price'),
                item_data.get('category', 'Miscellaneous'),
                item_data.get('usable', False),
                json.dumps(item_data.get('effects', {}))
            ))
            await db.commit()
    
    async def get_item(self, item_name: str, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get item data by name"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM items 
                WHERE guild_id = ? AND LOWER(name) = LOWER(?)
            """, (guild_id, item_name))
            
            row = await cursor.fetchone()
            if row:
                item_data = dict(row)
                item_data['effects'] = json.loads(item_data['effects']) if item_data['effects'] else {}
                return item_data
            return None
    
    async def get_all_items(self, guild_id: int) -> List[Dict[str, Any]]:
        """Get all items for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM items 
                WHERE guild_id = ?
                ORDER BY category, name
            """, (guild_id,))
            
            rows = await cursor.fetchall()
            items = []
            for row in rows:
                item_data = dict(row)
                item_data['effects'] = json.loads(item_data['effects']) if item_data['effects'] else {}
                items.append(item_data)
            return items
    
    async def delete_item(self, item_name: str, guild_id: int):
        """Delete an item and remove from all inventories"""
        async with aiosqlite.connect(self.db_path) as db:
            # Delete from inventories first (foreign key constraint)
            await db.execute("""
                DELETE FROM user_inventory 
                WHERE guild_id = ? AND LOWER(item_name) = LOWER(?)
            """, (guild_id, item_name))
            
            # Delete the item
            await db.execute("""
                DELETE FROM items 
                WHERE guild_id = ? AND LOWER(name) = LOWER(?)
            """, (guild_id, item_name))
            
            await db.commit()
    
    # Inventory management methods
    
    async def get_user_inventory(self, user_id: int, guild_id: int, page: int = 1, per_page: int = 10) -> List[Tuple]:
        """Get user's inventory with pagination"""
        offset = (page - 1) * per_page
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT ui.item_name, ui.quantity, i.description, i.emoji, i.category, i.price, i.usable, i.effects
                FROM user_inventory ui
                JOIN items i ON ui.guild_id = i.guild_id AND ui.item_name = i.name
                WHERE ui.user_id = ? AND ui.guild_id = ? AND ui.quantity > 0
                ORDER BY i.category, ui.item_name
                LIMIT ? OFFSET ?
            """, (user_id, guild_id, per_page, offset))
            
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                item_data = {
                    'description': row[2],
                    'emoji': row[3],
                    'category': row[4],
                    'price': row[5],
                    'usable': row[6],
                    'effects': json.loads(row[7]) if row[7] else {}
                }
                result.append((row[0], row[1], item_data))
            return result
    
    async def get_user_item(self, user_id: int, guild_id: int, item_name: str) -> Optional[Dict[str, Any]]:
        """Get specific item from user's inventory"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT ui.*, i.name as item_name, i.description, i.emoji, i.usable, i.effects
                FROM user_inventory ui
                JOIN items i ON ui.guild_id = i.guild_id AND ui.item_name = i.name
                WHERE ui.user_id = ? AND ui.guild_id = ? AND LOWER(ui.item_name) = LOWER(?)
            """, (user_id, guild_id, item_name))
            
            row = await cursor.fetchone()
            if row:
                item_data = dict(row)
                item_data['effects'] = json.loads(item_data['effects']) if item_data['effects'] else {}
                return item_data
            return None
    
    async def add_user_item(self, user_id: int, guild_id: int, item_name: str, quantity: int):
        """Add items to user's inventory"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO user_inventory (user_id, guild_id, item_name, quantity)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (user_id, guild_id, item_name)
                DO UPDATE SET 
                    quantity = quantity + ?,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, guild_id, item_name, quantity, quantity))
            await db.commit()
    
    async def remove_user_item(self, user_id: int, guild_id: int, item_name: str, quantity: int):
        """Remove items from user's inventory"""
        async with aiosqlite.connect(self.db_path) as db:
            # First, check current quantity
            cursor = await db.execute("""
                SELECT quantity FROM user_inventory 
                WHERE user_id = ? AND guild_id = ? AND item_name = ?
            """, (user_id, guild_id, item_name))
            
            row = await cursor.fetchone()
            if not row:
                return False
            
            current_quantity = row[0]
            new_quantity = max(0, current_quantity - quantity)
            
            if new_quantity == 0:
                # Remove the entry if quantity becomes 0
                await db.execute("""
                    DELETE FROM user_inventory 
                    WHERE user_id = ? AND guild_id = ? AND item_name = ?
                """, (user_id, guild_id, item_name))
            else:
                # Update quantity
                await db.execute("""
                    UPDATE user_inventory 
                    SET quantity = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND guild_id = ? AND item_name = ?
                """, (new_quantity, user_id, guild_id, item_name))
            
            await db.commit()
            return True
    
    # Income roles management
    
    async def add_income_role(self, guild_id: int, role_id: int, income: int):
        """Add or update income role"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO income_roles (guild_id, role_id, income)
                VALUES (?, ?, ?)
                ON CONFLICT (guild_id, role_id)
                DO UPDATE SET income = ?
            """, (guild_id, role_id, income, income))
            await db.commit()
    
    async def remove_income_role(self, guild_id: int, role_id: int):
        """Remove income role"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM income_roles 
                WHERE guild_id = ? AND role_id = ?
            """, (guild_id, role_id))
            await db.commit()
    
    async def get_income_roles(self, guild_id: int) -> List[Tuple[int, int]]:
        """Get all income roles for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT role_id, income FROM income_roles 
                WHERE guild_id = ?
            """, (guild_id,))
            return await cursor.fetchall()
    
    # Level rewards management
    
    async def set_level_rewards(self, guild_id: int, level: int, rewards: Dict[str, Any]):
        """Set rewards for a specific level"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO level_rewards (guild_id, level, money, roles_add, roles_remove, items)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (guild_id, level)
                DO UPDATE SET 
                    money = ?,
                    roles_add = ?,
                    roles_remove = ?,
                    items = ?
            """, (
                guild_id, level,
                rewards.get('money', 0),
                json.dumps(rewards.get('roles_add', [])),
                json.dumps(rewards.get('roles_remove', [])),
                json.dumps(rewards.get('items', {})),
                rewards.get('money', 0),
                json.dumps(rewards.get('roles_add', [])),
                json.dumps(rewards.get('roles_remove', [])),
                json.dumps(rewards.get('items', {}))
            ))
            await db.commit()
    
    async def get_level_rewards(self, guild_id: int, level: int) -> Optional[Dict[str, Any]]:
        """Get rewards for a specific level"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM level_rewards 
                WHERE guild_id = ? AND level = ?
            """, (guild_id, level))
            
            row = await cursor.fetchone()
            if row:
                return {
                    'money': row['money'],
                    'roles_add': json.loads(row['roles_add']) if row['roles_add'] else [],
                    'roles_remove': json.loads(row['roles_remove']) if row['roles_remove'] else [],
                    'items': json.loads(row['items']) if row['items'] else {}
                }
            return None
    
    async def get_all_level_rewards(self, guild_id: int) -> Dict[int, Dict[str, Any]]:
        """Get all level rewards for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM level_rewards 
                WHERE guild_id = ?
                ORDER BY level
            """, (guild_id,))
            
            rows = await cursor.fetchall()
            rewards = {}
            for row in rows:
                rewards[row['level']] = {
                    'money': row['money'],
                    'roles_add': json.loads(row['roles_add']) if row['roles_add'] else [],
                    'roles_remove': json.loads(row['roles_remove']) if row['roles_remove'] else [],
                    'items': json.loads(row['items']) if row['items'] else {}
                }
            return rewards
    
    # Warning system
    
    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        """Add a warning and return warning ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
                VALUES (?, ?, ?, ?)
            """, (guild_id, user_id, moderator_id, reason))
            await db.commit()
            return cursor.lastrowid
    
    async def get_user_warnings(self, guild_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get all warnings for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM warnings 
                WHERE guild_id = ? AND user_id = ?
                ORDER BY timestamp DESC
            """, (guild_id, user_id))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def clear_user_warnings(self, guild_id: int, user_id: int):
        """Clear all warnings for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM warnings 
                WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id))
            await db.commit()
    
    # Cooldown management
    
    async def set_cooldown(self, user_id: int, guild_id: int, command_name: str, duration: int):
        """Set a cooldown for a user"""
        expires_at = datetime.utcnow().timestamp() + duration
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO cooldowns (user_id, guild_id, command_name, expires_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (user_id, guild_id, command_name)
                DO UPDATE SET expires_at = ?
            """, (user_id, guild_id, command_name, expires_at, expires_at))
            await db.commit()
    
    async def check_cooldown(self, user_id: int, guild_id: int, command_name: str) -> Optional[float]:
        """Check if user is on cooldown, return remaining time or None"""
        current_time = datetime.utcnow().timestamp()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT expires_at FROM cooldowns 
                WHERE user_id = ? AND guild_id = ? AND command_name = ?
            """, (user_id, guild_id, command_name))
            
            row = await cursor.fetchone()
            if row and row[0] > current_time:
                return row[0] - current_time
            
            # Clean up expired cooldown
            if row:
                await db.execute("""
                    DELETE FROM cooldowns 
                    WHERE user_id = ? AND guild_id = ? AND command_name = ?
                """, (user_id, guild_id, command_name))
                await db.commit()
            
            return None
    
    async def cleanup_expired_cooldowns(self):
        """Clean up expired cooldowns (should be run periodically)"""
        current_time = datetime.utcnow().timestamp()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM cooldowns WHERE expires_at <= ?
            """, (current_time,))
            await db.commit()
    
    # Utility methods
    
    async def initialize_guild(self, guild_id: int):
        """Initialize guild settings"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO guild_settings (guild_id)
                VALUES (?)
            """, (guild_id,))
            await db.commit()
    
    async def remove_user(self, user_id: int, guild_id: int):
        """Remove all user data from guild"""
        async with aiosqlite.connect(self.db_path) as db:
            # Remove from all tables
            tables = ['users', 'user_inventory', 'warnings', 'cooldowns']
            for table in tables:
                await db.execute(f"""
                    DELETE FROM {table} 
                    WHERE user_id = ? AND guild_id = ?
                """, (user_id, guild_id))
            await db.commit()
    
    async def get_all_user_ids(self, guild_id: int) -> List[int]:
        """Get all user IDs in a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT DISTINCT user_id FROM users WHERE guild_id = ?
            """, (guild_id,))
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
