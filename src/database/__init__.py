
"""
INFO:

	The database handler functions of the Skender discord bot.

	Official Repo: https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot

	imported in bot.py and used as self.db_handler.xyz()

	for more info see main.py

"""

"""
IMPORTS
"""

# for calendar stuff
from datetime import datetime, timedelta
# for discord API handling
import discord
# for database handling
import sqlite3, json
# for utility functions
from utilities import SkenderUtilities
# miscellaneous
import os, random, math, asyncio, re, subprocess

# maybe for later:
# from discord.ui import View, Button

# custom blackjack game code (based on https://gist.github.com/StephanieSunshine/d34039857566d957f26cea8277b3ac65).
# --> game_libs/blackjack.py
from game_libs.blackjack import blackjack_discord_implementation
# custom roulette game code (based on https://github.com/ntaliceo/roulette-simulator).
# --> game_libs/roulette.py
from game_libs.roulette import roulette_discord_implementation

"""

    the database handler of the unbelievaboat-python discord bot
    // is imported by ../main.py

    SQLite usage info:
        I often use parameter bindung ("= ?") to avoid issues with certain characters like ' or " etc.
        The other benefit of this method is to prevent SQL injections, which isn't really a risk for this tho,
            since we control the inputs directly in main.py

        I still use = ? a lot of the time as a convention and for the reasons above (or in case you might change
            the behaviour of the bot and would need to prevent SQL injections).
        Note: sometimes in the code values are still inserted directly (= value) for simplicity reasons.
        ("= ?" should be preferred tho)

"""

""" maybe later...
class LeaderboardViewer(View):
    def __init__(self):
        self.bot = bot
        self.user = user
        self.
"""

# only as a separate class so that we can call it through database_migration.py
# explanations for the things we do here are in the actual class SkenderDatabaseHandler below.
# this is just for the create_database function !
class SkenderDatabaseCreator:
	def __init__(self, path):
		self.path_to_db = path
		self.database, self.db_cursor = None, None

	# create or check database
	def create_database(self):
		self.database = sqlite3.connect(self.path_to_db)
		self.db_cursor = self.database.cursor()

		# adding default sqlite config into the file if creating new
		# all the users will get created automatically in the function self.get_user_object()
		# but for the different jobs etc. the program needs configs for variables and symbols

		# we will create more tables than were in the old json version.
		# this will make handling the db easier, like looking for balance will be less to compute
		# if it just contains a fixed amount of variables vs when it also needs to read an unknown amount of user items.

		# important: since we need multiple tables for things that were before in one json item
		# (i.e. users, user_items, user_used_items and actions and action_phrases) and we use FOREIGN KEYS for that
		# we can simply set ON DELETE CASCADE at the FOREIGN KEYS. This enables us to just delete the user entry
		# in table users, and it will automatically delete the user_items and user_used_items saved with his user_id.

		# table users (was called "userdata" before)
		# user_id means discord id
		# user_number will track all users that ever existed, even if they get deleted later on with clean_database.
		# last_single_called moved here, was scattered around each role before (only relevant if you use +collect).
		# new: now also adding columns for level handling.
		self.db_cursor.execute('''
			CREATE TABLE IF NOT EXISTS users (
				user_number INTEGER PRIMARY KEY AUTOINCREMENT,
				user_id INTEGER UNIQUE,
				user_discord_nick TEXT,
				cash INTEGER DEFAULT 0,
				bank INTEGER DEFAULT 0,
				last_slut TEXT DEFAULT 'none',
				last_work TEXT DEFAULT 'none',
				last_crime TEXT DEFAULT 'none',
				last_rob TEXT DEFAULT 'none',
				last_blackjack TEXT DEFAULT 'none',
				last_roulette TEXT DEFAULT 'none',
				last_single_collect TEXT DEFAULT 'none',
				total_xp INTEGER DEFAULT 0,
				current_xp_level INTEGER DEFAULT 0,
				last_xp_collect TEXT DEFAULT 'none'
		)
		''')

		# table user_items (was in userdata before)
		self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_items (
				user_id INTEGER NOT NULL,
				item_name TEXT NOT NULL,
				amount INTEGER DEFAULT 0,
				PRIMARY KEY (user_id, item_name),
				FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
		)
		''')
		# for this we will also create an index so searching will be faster
		# when only looking for user_id and not user_id & item_name
		self.db_cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_items_user_id ON user_items(user_id)")

		# table user_used_items (was in userdata before)
		self.db_cursor.execute('''
			CREATE TABLE IF NOT EXISTS user_used_items (
				user_id INTEGER NOT NULL,
				item_name TEXT NOT NULL,
				amount INTEGER DEFAULT 0,
				PRIMARY KEY (user_id, item_name),
				FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
		)
		''')

		# table actions (was called "variables" before, the phrases are in a separate table now)
		self.db_cursor.execute('''
			CREATE TABLE IF NOT EXISTS actions (
				action_name TEXT PRIMARY KEY,
				delay INTEGER DEFAULT 10,
				proba INTEGER DEFAULT 50,
				min_revenue INTEGER DEFAULT 50,
				max_revenue INTEGER DEFAULT 500,
				min_lose_amount_percentage INTEGER DEFAULT 10,
				max_lose_amount_percentage INTEGER DEFAULT 20,
				min_gain_amount_percentage INTEGER DEFAULT 10,
				max_gain_amount_percentage INTEGER DEFAULT 20
		)
		''')

		# table action_phrases (was stored directly in the "variables" (so in the actions) in json before)
		# action info is not a primary key because else you could only have 1 phrase per action.
		# phrase id is not really useful but for logging info I chose to add it.
		# CHECK makes sure that the value is either "win" or "lose" (was "win_phrases" / "lose_phrases" before)
		self.db_cursor.execute('''
			CREATE TABLE IF NOT EXISTS action_phrases (
			phrase_id INTEGER PRIMARY KEY AUTOINCREMENT,
			action_name TEXT,
			type TEXT CHECK(type in ('win', 'lose')),
			phrase TEXT,
			FOREIGN KEY (action_name) REFERENCES actions(action_name)
		)
		''')

		# table items_catalog ("items" before)
		self.db_cursor.execute('''
			CREATE TABLE IF NOT EXISTS items_catalog (
				item_name TEXT PRIMARY KEY,
				display_name TEXT,
				price INTEGER,
				description TEXT,
				duration INTEGER,
				amount_in_stock TEXT,
				max_amount TEXT,
				max_amount_per_transaction TEXT,
				required_roles TEXT,
				given_roles TEXT,
				removed_roles TEXT,
				excluded_roles TEXT,
				maximum_balance TEXT,
				reply_message TEXT,
				expiration_date TEXT,
				item_img_url TEXT
		)
		''')

		# table income_roles (includes what was "last_called" in the old json)
		self.db_cursor.execute('''
			CREATE TABLE IF NOT EXISTS income_roles (
				role_id INTEGER,
				role_income INTEGER
		)
		''')

		# table "variables" (was supposed to be named table "SYMBOLS" but other stuff got thrown in this table too).

		"""
		What the table should look like at the end, but it's too painful and unintended SQLite behaviour
		to just put it all into columns (which, however, has the advantage of being able to set
		the right type directly). So we're going "normal" but with an extra column for type:
				currency_emoji_name TEXT DEFAULT 'unset',
				income_reset TEXT DEFAULT 'true',
				common_reset_time TEXT DEFAULT NULL,
				last_global_income_update TEXT DEFAULT NULL,
				min_amount_to_blackjack INTEGER DEFAULT 100,
				max_amount_to_blackjack INTEGER DEFAULT 0,
				min_amount_to_roulette INTEGER DEFAULT 100,
				max_amount_to_roulette INTEGER DEFAULT 0,
				delay_blackjack INTEGER DEFAULT 0,
				delay_roulette INTEGER DEFAULT 0,
				levels_info_channel INTEGER DEFAULT 0,
				xp_per_msg INTEGER DEFAULT 10,
				passive_income_per_msg INTEGER DEFAULT 0,
				xp_and_passive_income_delay INTEGER DEFAULT 5
		"""

		self.db_cursor.execute('''
			CREATE TABLE IF NOT EXISTS variables (
				var_name TEXT PRIMARY KEY,
				var_type TEXT,
				var_value TEXT,
				var_default_value TEXT,
				var_description TEXT
		)
		''')

		self.db_cursor.execute('''
			CREATE TABLE IF NOT EXISTS level_channels(
				mode TEXT DEFAULT 'exclude',
				channels TEXT DEFAULT 'none'
		)
		''')

		# new: table for levels ! every user has his individual xp, but we also need a table for variables etc.
		self.db_cursor.execute('''
             CREATE TABLE IF NOT EXISTS levels (
             	level_number INTEGER PRIMARY KEY,
             	level_xp INTEGER
        )
        ''')

		# extra table for rewards !
		# rewards can (currently) be: money, items (text --> json: names, amounts), roles (text --> json: role_ids).
		#			json.loads() / json.dumps().

		# Decision: level_number as PRIMARY KEY in this table instead of adding a table for role_rewards,
		# 			where each role reward would have had to be another row.
		# Reasons:
		#   - rewards types are limited through the column variables in this table (money, items, roles).
		#	- roles get added into a JSON string. If someone wants to edit it manually, it would be as tough
		#	  to manually edit SQLite as to edit the json string, maybe the latter would even be easier.
		#	- Performance issues with loading + rewriting json should not be relevant compared to having one more table.
		# Possible issues:
		# 	- trying to give items or roles that don't exist anymore.
		# Proposed solution:
		# 	- each time the function wants to give a role, if it is not found through discord.utils.get,
		#	  then delete it from the json string. Same thing for items
		#	- This method is more efficient than doing it in the function remove_item/remove_income_role function,
		#	  then you would have to loop through every level reward row, check the json etc.

		self.db_cursor.execute('''
			CREATE TABLE IF NOT EXISTS level_rewards (
				level_number INTEGER PRIMARY KEY,
				reward_money INTEGER,
				reward_items TEXT,
				reward_roles_given TEXT,
				reward_roles_removed TEXT,
				FOREIGN KEY (level_number) REFERENCES levels(level_number) ON DELETE CASCADE
		)
		''')

		# commit and close database file
		self.database.commit()
		self.database.close()

		return

# this comment is just automatically added for code checks in PyCharm IDE btw. Else it goes nuts on SQLite code.
# noinspection SqlNoDataSourceInspection

class SkenderDatabaseHandler:
	# always called when imported in main.py
	def __init__(self, client, admin_role):
		# important to avoid race conditions: lock database !
		# --> only one process can write to the database at the same time.
		# but since we also activated WAL (see below), we don't prevent the bot from reading data.
		# so it can continue to work smoothly.
		self.db_lock = asyncio.Lock()
		# ==> for the implementation, see def execute_commit(self, ...) and def executemany(self, ...)
		# we can simply set up the lock there and have it working for the entire code.
		# splitting execute (no lock) and execute_commit (with lock) to avoid unnecessary coroutines.

		# INFO: I'm going to just keep the database open, not put it as an option to close at the end of each function.
		# Reasons: makes the code and handling all returns way more complex, doesn't suit the "bot" characteristics
		# to always open and close, when multiple users are supposed to be able to access it simultaneously.
		# And: the risk of data loss should be very low because we always commit directly, so even if the database
		# gets closed abruptly, we should be safe.

		# init these variables as None which means that no database is opened and no cursor is set
		self.database, self.db_cursor = None, None
		# --> self.get_currency_symbol()
		self.currency_symbol = None
		# --> self.get_channel_infos()
		self.default_variable_info, self.level_channels_info = None, None
		# --> self.get_xp_infos()
		self.xp_per_msg, self.passive_income_per_msg, self.xp_and_passive_income_delay = None, None, None
		self.level_channel_objects = []
		# we do the path from the main.py file, so we go into the db folder, then select
		base_directory = os.path.dirname(os.path.abspath(__file__))
		self.path_to_db = os.path.join(base_directory, "database.sqlite")
		old_json_path = os.path.join(base_directory, "database.json")
		self.client = client

		# initiate utils (../utilities.py)
		self.utils = SkenderUtilities(client, admin_role)
		# info channel, will be set later (when opening / when creating).
		self.channel_level_info = None
		# the channels that are either included or excluded. Will be set later.
		self.channels_level_mode, self.channels_level_handling = None, None

		# for colors
		self.discord_error_rgb_code = discord.Color.from_rgb(239, 83, 80)
		self.discord_blue_rgb_code = discord.Color.from_rgb(3, 169, 244)
		self.discord_success_rgb_code = discord.Color.from_rgb(102, 187, 106)
		self.error_emoji = "❌"
		self.worked_emoji = "✅"

		# to create the database
		db_creator = SkenderDatabaseCreator(self.path_to_db)

		# check for old JSON.
		offer_migration = False

		if os.path.exists(old_json_path) and not os.path.exists(self.path_to_db):
			print("\n\nOLD JSON DATABASE FOUND.")
			offer_migration = True
		elif os.path.exists(old_json_path):
			print("\nOld JSON Database found, but also new SQLite version.\n"
				  "If you already migrated, you can ignore this (maybe rename database.json"
				  " to old_db.json to avoid this message.\nIf you did not migrate yet, please DELETE the SQLite file "
				  "and then run the bot again (A SQLite file will be created and added automatically during migration.")

			while 1:
				user_input = input("Do you want to [1] continue or [2] migrate ? ")
				user_input = user_input.lower().strip()
				if user_input not in ["1", "2", "[1]", "[2]"]:
					continue
				if user_input in ["1", "[1]"]:
					offer_migration = False
					break
				else:
					offer_migration = True
					break

		if offer_migration:
			while 1:
				user_input = input("Do you wish to [1] CONTINUE (creates an empty database) or"
								   " [2] MIGRATE (creates a new database with data from json) ?: ")

				user_input = user_input.lower().strip()

				if user_input in {"1", "[1]", "continue"}:
					confirm = input("Are you sure you wish to lose all data from the old database ? [y/N]: ")
					if confirm.lower().strip() in ["y", "yes"]:
						break
					else:
						print("Aborting startup...")
						quit()
				elif user_input in {"2", "[2]", "migrate"}:
					# print("For MIGRATION: Please run database/database_migration.py")
					# quit()

					print("Starting migration process...")

					try:
						arguments = ["--source", old_json_path, "--target",
									 self.path_to_db, "--source-version", "legacy", "--target-version", "2.0"]

						subprocess.run([
							"python",
							os.path.join(base_directory, "database_migration.py")
						] + arguments)

						# finished migrating.

						break

					except Exception as e:
						print(f"Unexpected error occurred. Error code: {e}.\nPlease contact the developer.")

				else:
					print("Please enter either [1] or [2]. This step is very important and can not be skipped.")
					continue


		# check if database is created, else create it

		# right now we create everytime.
		if not os.path.exists(self.path_to_db):
			print(f"\n\nLOG: creating new database at {self.path_to_db}\n\n")
			# close in case database was opened
			self.close_database()
			# create
			db_creator.create_database()
			# open again
			self.open_database()
			# when we create a new db, we add tables and also the "actions", "actions_phrases" and "income_reset"
			# the rest of the tables / columns get initialised empty.
			self.db_set_up = False
		else:
			# check if exists but is empty
			self.open_database()
			default_var = self.db_cursor.execute(
				"SELECT var_value FROM variables WHERE var_name = ?",
				("income_reset",)
			).fetchone()

			if default_var is None:
				self.db_set_up = False
				print(f"\n\nLOG: found empty database at {self.path_to_db}\n\n")
			else:
				print(f"\n\nLOG: checking database at {self.path_to_db} and adding missing tables.\n")
				# only check if all tables exist / create tables if they don't.
				# close database again (because create database needs to open and close himself)
				self.close_database()
				# create
				db_creator.create_database()
				# open again
				self.open_database()
				self.db_set_up = True

		# get CURRENCY SYMBOL ==> done through ../main.py in @on_ready, because the bot needs to actually run first,
		# else we can't fetch any emojis from servers.
		# if you want to change the currency symbol, edit it in the database or by change_currency_emoji().

		# if we are going to keep a database session running,
		# we might as well open it here, when starting the bot
		self.open_database()

	#
	# CREATE DEFAULT DATABASE INSERTS WITH USER WALKTHROUGH
	#

	# called in main.py in on_ready()
	async def create_database_default_layout(self, setup_channel_id):
		# this function needs to be called from main.py.
		# this is easier than checking in main.py if a database already exists.
		if self.db_set_up:
			return

		# else: go on and fill database.
		self.open_database()

		# create default values and information for variables. Will be useful later,
		# the goal is to make the user set up the database and set values directly on first set up.
		# dictionary with:
		# 	value[0] is the default var_value,
		# 	value[1] is info,
		#	value[2] is var_type,
		#	the dictionary key is var_name
		self.default_variable_info = {
			"currency_emoji_name": [
				"unset",
				"This variable allows you to use a custom emoji as currency emoji. The emoji must be "
					"a custom emoji uploaded to the server, e.g. 'shiny_coin', not a default emoji. "
					"Enter only the name (without ':'-sign etc) or leave default value "
					"(will set emoji to dollar bag).",
				"str"
			],
			"income_reset": [
				"true",
				"Setting this to false will enable users to accumulate income. e.g.: "
					"someone did not collect his income for 10 days, he will get 10 x Collect at once. "
					"If set to true, he will only get 1 Collect, no matter what.\nInfo: it makes sense "
					"to set it to 'true' for individual income collection, and to 'false' for server "
					"wide update income by moderators (see command_list.txt for more).",
				"str"
			],
			"common_reset_time": [
				None,
				"skip",
				"str"
			],
			"last_global_income_update": [
				None,
				"skip",
				"str"
			],
			"min_amount_to_blackjack": [
				100,
				"This sets the minimum amount to be able to play blackjack.",
				"int"
			],
			"max_amount_to_blackjack": [
				0,
				"This sets the minimum amount to be able to play blackjack.",
				"int"
			],
			"min_amount_to_roulette": [
				100,
				"This sets the minimum amount to be able to play roulette.",
				"int"
			],
			"max_amount_to_roulette": [
				0,
				"This sets the maximum amount to be able to play roulette.",
				"int"
			],
			"delay_blackjack": [
				0,
				"This sets the cooldown (in minutes !) between 2 blackjack games a user can play. "
					"\nFor no cooldown / usage limit, leave at 0.",
				"int"
			],
			"delay_roulette": [
				0,
				"This sets the cooldown (in minutes !) between 2 roulette games a user can play. "
					"\nFor no cooldown / usage limit, leave at 0.",
				"int"
			],
			"levels_info_channel": [
				0,
				"Enter the discord ID of or 'ping' the (one!) channel you want level-up "
					"messages to be sent to. If set to 0 or set channel cannot be found, "
					"the info messages will be sent in the channel the user last sent a message.",
				"int"
			],
			"xp_per_msg": [
				10,
				"The xp a user will gain each time he sends a message (and cooldown finished, see "
					"later variables. It's recommended not to play with it too much. It's simpler "
					"to adjust the xp-step for every level instead of playing with huge xp numbers per msg.",
				"int"
			],
			"passive_income_per_msg": [
				0,
				"This is not the same as level rewards ! You can set money rewards for both, "
					"or only level-money-rewards (i.e. gaining a certain sum when when reaching "
					"a certain level, or only passive income per message.\n**Passive income per message** "
					"- aka passive chat income - is the money amount a user will receive for each message "
					"(see cooldown in the next step).",
				"int"
			],
			"xp_and_passive_income_delay": [
				5,
				"This is the cooldown aka delay (in minutes !) for a message to count for "
					"passive chat income and/or gaining xp for a message. Goal: avoid spam.",
				"int"
			]
		}
		# common_reset_time gets set to NULL at the end when writing changes.

		# structure see above for default_variable_info
		self.level_channels_info = {
			"mode": [
				"exclude",
				"Mode can be set to **include** or **exclude**. When set to include, only the given channels "
					"will count for xp. When set to exclude, all channels except given channels will count for xp.\n"
					"Please choose include/exclude wisely according to the number of channels you will enter."
			],
			# will be one single json string in the end,
			# but to always get a "list" we can access in json, we initialize this as a list that we will dump.
			"channels": [
				["none"],
				"The channels. Enter channel id(s) or ping the channels (all in one message)."
			]
		}

		setup_channel = None
		# everything in a big try/except, so we don't create a corrupted database.
		try:

			# WALKTHROUGH : get our info from the user !

			# try to get the channel:
			# btw: fetch_channel because else get_channel grabs from cache and cache may be empty,
			# since we're just setting up the bot.
			setup_channel = await self.client.fetch_channel(setup_channel_id)

			if not setup_channel:
				print("\n\n\nSETUP CHANNEL NOT FOUND. USING DEFAULT VALUES.\n\n\n")
				skip = True
			else:

				await setup_channel.send("**Setting up the bot.**\nYou will be guided through setting "
										 "variables and level channel infos for your bot.\n"
										 "You can enter **skip**, this will set all values to default.\n"
										 "If you wish to continue, enter anything."
										 "\n\nInfo: only admins can use this.")

				answer = await self.utils.setup_get_admin_input(setup_channel)

				if not answer or answer in ["none", "skip", "<skip>"]:
					skip = True
				else:
					skip = False

			# common for skip and no skip:

			# Reminder: structure is this
			# 	var_name TEXT PRIMARY KEY,
			# 	var_type TEXT,
			# 	var_value TEXT,
			# 	var_default_value TEXT

			var_names = []
			var_types = []
			# will be set to default or filled below.
			var_values = []
			var_default_values = []
			var_descriptions = []

			# for levels:
			level_mode = self.level_channels_info["mode"][0]
			level_channels = self.level_channels_info["channels"][0]

			for key, value in self.default_variable_info.items():
				# value[1] is the information we display in the conversation below.
				var_names.append(key)
				var_types.append(value[2])
				# must be set as string !
				# for common_reset_time we want a SQLite NULL value (set through None in python).
				var_default_values.append(str(value[0]) if value[0] is not None else None)
				var_descriptions.append(value[1])

			if skip:
				var_values = var_default_values[:]
				setup_info = f"{self.worked_emoji} Database set up with default values."
			else:
				# first: insert variables into var_values

				for key, value in self.default_variable_info.items():
					await setup_channel.send(f"Variable **{key}**.\nInfo: {value[1]}.\n"
											 f"Default value: {value[0]}, type: {value[2]}.\n")
					while 1:
						entered_value = None
						await setup_channel.send("Enter **value** or **default** to set default value")

						# set_get_admin_input already strips and lowers the string.
						user_input = await self.utils.setup_get_admin_input(setup_channel)

						if user_input is None or user_input in ["skip", "default"]:
							# "common_reset_time" as SQLite NULL per default.
							if key not in ["common_reset_time", "last_global_income_update"]:
								entered_value = str(value[0])
							else:
								entered_value = None
							break

						if key == "common_reset_time":
							entered_value = None
							break
						if key == "last_global_income_update":
							entered_value = None
							break

						if key == "currency_emoji_name":
							try_emoji, info = self.get_currency_symbol(test=True, new_emoji=user_input, first_run=False)
							if try_emoji == "error":
								await setup_channel.send(info)
								continue
							entered_value = user_input

						elif key == "income_reset" and user_input not in ["true", "false"]:
							await setup_channel.send("Error. Must be true or false.")
							continue
						elif key == "income_reset":
							entered_value = user_input

						else:
							is_int, number = self.utils.check_formatted_number(user_input)
							if not is_int:
								await setup_channel.send("Error. Must be an integer.")
								continue

							if key == "levels_info_channel":
								channel_exists = self.client.get_channel(user_input)
								if not channel_exists:
									await setup_channel.send("Channel not found.")
									continue

							entered_value = number

						break
					var_values.append(entered_value)

				# now for channels

				# reset the channels list
				level_channels = []

				for key, value in self.level_channels_info.items():
					await setup_channel.send(
						f"**Variable {key}**.\nInfo: {value[1]}.\n"
						f"Default value: {value[0]}.\n"
					)
					while 1:
						await setup_channel.send("Enter **value** or **default** to set default value")

						user_input = await self.utils.setup_get_admin_input(setup_channel)

						# default values if wanted
						if user_input is None or user_input in ["skip", "default"]:
							if key == "mode":
								level_mode = value[0]
							else:
								level_channels = value[0]
							# not breaking yet, because he can want to set mode to default but set specific channels
							continue

						if key == "mode":
							if user_input not in ["exclude", "include"]:
								await setup_channel.send("Error. Must be 'exclude', 'include'")
								continue
							level_mode = user_input

						elif key == "channels":

							level_channels = await self.get_valid_channels(level_channels, setup_channel)

						break

				setup_info = f"{self.worked_emoji} Database set up with set values."

			# now actually execute and then inform:

			# for the variables
			insert_data = list(zip(var_names, var_types, var_values, var_default_values, var_descriptions))
			await self.executemany(
				"INSERT OR REPLACE INTO variables "
				"(var_name, var_type, var_value, var_default_value, var_description)"
				"VALUES (?, ?, ?, ?, ?) ",
				insert_data,
				commit=True
			)

			# for the levels.
			insert_levels = (level_mode, json.dumps(level_channels))
			await self.execute_commit(
				"INSERT OR REPLACE INTO level_channels (mode, channels) VALUES (?, ?)",
				insert_levels
			)

			# inform
			await setup_channel.send(setup_info)
		except Exception as e:
			print(f"ERROR CODE setting up database: {e}")
			if setup_channel:
				await setup_channel.send(f"{self.error_emoji} ERROR: {e}. Stopping code, database closed. "
									 	 f"Please inform an admin.\nShutting down the bot.")
			self.close_database()
			# quit, don't miss-setup the database !
			quit()


		# ACTIONS - this will just be put to this, will still be editable later.

		# action_name, delay, proba, min_revenue, max_revenue, min_lose_amount_percentage, max_lose_amount_percentage,
		# ... min_gain_amount_percentage, max_gain_amount_percentage.
		actions = [
			("slut", 10, 50, 50, 400, 2, 5, None, None),
			("crime", 60, 30, 100, 1200, 10, 20, None, None),
			("work", 10, None, 50, 200, None, None, None, None),
			("rob", 45, 50, None, None, 10, 20, 10, 20)
		]
		# insert all actions
		await self.executemany('''
	   		INSERT OR IGNORE INTO actions (
                action_name, delay, proba, min_revenue, max_revenue,
                min_lose_amount_percentage, max_lose_amount_percentage,
                min_gain_amount_percentage, max_gain_amount_percentage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
			''', actions, commit=True)

		# ACTION PHRASES
		action_phrases = [
			# slut actions
			("slut", "win", "With a wink 💋, you made"),
			("slut", "win", "You made a client very happy 😏 and earned"),
			("slut", "win", "Your performance was unforgettable 🎀. You received"),
			("slut", "win", "Your client liked it so much 😍, he gave you"),
			("slut", "win", "Your skills were unmatched tonight 💃. You received"),
			("slut", "win", "You rocked their world 🌪️. A generous tip brought you"),
			("slut", "lose", "You were fined 🚨"),
			("slut", "lose", "Your client didn't like the encounter 😒. You pay"),
			("slut", "lose", "The client refused to pay 🙅. You lost"),
			("slut", "lose", "A scandal went viral 📸... You were fined"),
			("slut", "lose", "The police 🚓 arrested you. You were fined"),
			("slut", "lose", "Your client ghosted you 👻. You lost"),
			("slut", "lose", "Your performance flopped 💔. You had to pay"),
			("slut", "lose", "A scandal leaked online 📰... You were fined"),
			("slut", "lose", "You were caught in the act 😳. The police fined you"),

			# crime actions
			("crime", "win", "You pulled off a heist 🕵️ and got"),
			("crime", "win", "You cracked the vault 🔓 and walked away with"),
			("crime", "win", "You committed a crime 🧨 and got"),
			("crime", "win", "You robbed a bank 🏦 and got"),
			("crime", "win", "You tricked the guards 🧠 and escaped with"),
			("crime", "win", "You pulled off the heist of the year 🎬 and got"),
			("crime", "lose", "You were arrested mid-crime 🚓. You paid"),
			("crime", "lose", "You were fined 🧾 and had to pay"),
			("crime", "lose", "MacGyver finds you 🚨. You pay"),
			("crime", "lose", "You were caught red-handed ⛓️. You paid"),
			("crime", "lose", "Interpol 👮 tracked you down. You lost"),
			("crime", "lose", "You slipped up 🤦 and were fined"),

			# work actions
			("work", "win", "Your shift went smoothly 💼. You made"),
			("work", "win", "Your shift went great 👍. You earned"),
			("work", "win", "You worked at SubWay 🥪 and made"),
			("work", "win", "You helped someone do his homework 📚 and got"),
			("work", "win", "You freelanced 👨‍💻 and got"),
			("work", "win", "Hard work pays off 💪 ! This time, you got"),

			# rob actions
			("rob", "win", "You robbed 🕵️ and got"),
			("rob", "win", "You picked the right target 🎯 and grabbed"),
			("rob", "win", "A clean robbery 🧤! You got away with"),
			("rob", "win", "You disappeared into the shadows 🌒 with"),
			("rob", "win", "No alarms, no witnesses 🕶️. You escaped with"),
			("rob", "lose", "You were caught robbing 🚨 and have to pay"),
			("rob", "lose", "You tripped on your way out 🤕. Embarrassing... You lost"),
			("rob", "lose", "Someone called the cops 🚔. You paid"),
			("rob", "lose", "Someone saw you 👀 and asked for hush money. You had to pay")
		]

		await self.executemany('''
                INSERT OR IGNORE INTO action_phrases (
                action_name, type, phrase
            ) VALUES (?, ?, ?)
			''', action_phrases, commit=True)

		await setup_channel.send("If you want to use levels, please consider calling `change-levels`."
								 "\nYou can set rewards like money, roles and items !")

		self.close_database()

		# update:
		self.db_set_up = True

	# very important.
	def get_currency_symbol(self, test=False, new_emoji="default", first_run=False):

		# when first starting the self.client, just try to get the emoji set in the database.
		if first_run: # called through ../main.py
			try:
				currency_symbol = self.execute(
					"SELECT var_value FROM variables WHERE var_name = ?",
					("currency_emoji_name", )
				).fetchone()["var_value"]
			except Exception as e:
				print(f"ERROR. Database may have problems. Error code: {e}")
				currency_symbol = "unset"

			# by default, it's just the moneybag emoji
			if currency_symbol == "unset":
				# if currency emoji is unset, we just put it to 💰, but that's done when calling this function.
				print("No custom emoji set, using 💰")
				self.currency_symbol = "💰"
				return None, None
			# else: try to set new emoji
			emoji = discord.utils.get(self.client.emojis, name=currency_symbol)
			if emoji is None:
				self.currency_symbol = "💰"
				print(f"{self.error_emoji} Emoji not found (first run).")
				return None, None
			# else it worked, set the emoji
			self.currency_symbol = emoji
			print(f"Emoji found and set to {self.currency_symbol}")

		# else it means we're trying to change the emoji-name in the database (called from here, not on_ready in main.py)
		emoji = discord.utils.get(self.client.emojis, name=new_emoji)
		if emoji is None:
			return "error", f"{self.error_emoji} Emoji not found."

		if not test: self.currency_symbol = emoji
		return "success", None

	# channel can be set to None if we just do a background check.
	async def check_valid_channels(self, all_channel_ids, channel=None):
		error = 0
		valid_channel_ids = []

		for channel_id in all_channel_ids:
			if channel_id == "none": continue
			print(all_channel_ids, channel_id)
			# fetch because get_channel just grabs from cache and if we have a new
			# bot being set up, cache is prob empty.
			try:
				channel_obj = await self.client.fetch_channel(int(channel_id))
				if channel_obj is None:
					if channel: await channel.send(f"Channel with id {channel_id} not found. Skipping it.")
					error += 1
				else:
					valid_channel_ids.append(channel_id)
					self.level_channel_objects.append(channel_obj)
			except Exception as e:
				print(f"Error : {e}")

		return valid_channel_ids, error

	# actually get the channels
	async def get_valid_channels(self, user_input, channel):
		# find all channel pings
		# something starting with <# and ending with >. () gives us just the numbers.
		ping_ids = re.findall(r"<#(\d+)>", user_input)
		# something (\b limits it, kind of like .strip()), with 17 to 19 integers (channel IDs).
		# edit: 17 to 19 should be the usual discord channel id length, but I'd rather take no risks.
		# + we're checking for valid IDs later anyway.
		raw_ids = re.findall(r"\b\d{10,20}\b", user_input)

		# all our ids
		all_channel_ids = set(ping_ids + raw_ids)

		# check if valid
		valid_channel_ids, err_count = await self.check_valid_channels(all_channel_ids, channel)
		# is supposed to be a json string.
		return valid_channel_ids

	# run this separately, called in main.py.
	# ran after creation etc. so we only need to do it once.
	async def get_channel_infos(self):
		row = self.execute("SELECT mode FROM level_channels LIMIT 1").fetchone()

		self.channels_level_mode = row["mode"] if row else None

		levels_json = self.execute("SELECT channels FROM level_channels LIMIT 1").fetchone()
		if levels_json is None:
			self.channels_level_handling = []
		else:
			try:
				self.channels_level_handling = json.loads(levels_json["channels"])

				# do a check in case (so it doesn't have to be done everytime when using the variable:
				valid_channels, err_count = await self.check_valid_channels(self.channels_level_handling)
				self.channels_level_handling = [int(channel) for channel in valid_channels]
				print(f"Checking channels... result: {err_count} errors found. "
					  f"{len(self.channels_level_handling)} running.")

			except json.JSONDecodeError as e:
				self.channels_level_handling = []
				print(f"ERR (not critical): could not load included/excluded channels. Error code: {e}")

		result = self.execute(
			"SELECT var_value FROM variables WHERE var_name = ?",
			("levels_info_channel",)
		).fetchone()

		self.channel_level_info = None
		if result:
			level_id = result["var_value"]
			self.channel_level_info = self.client.get_channel(int(level_id))
			if self.channel_level_info is None:
				try:
					self.channel_level_info = await self.client.fetch_channel(int(level_id))
				except Exception as e: pass


		print(f"Channels: info channel is {self.channel_level_info}, "
			  f"level handling channel is {self.channels_level_handling}")

		return

	# get infos from variables that we won't need to fetch every time
	async def get_xp_infos(self):
		# we should be able to easily fetchone()[0] directly, should not be NULL.
		self.xp_per_msg = self.execute(
			"SELECT var_value FROM variables WHERE var_name = ?",
			("xp_per_msg",)
		).fetchone()

		self.xp_per_msg = self.xp_per_msg["var_value"] if self.xp_per_msg else 0

		self.passive_income_per_msg = self.execute(
			"SELECT var_value FROM variables WHERE var_name = ?",
			("passive_income_per_msg",)
		).fetchone()

		self.passive_income_per_msg = self.passive_income_per_msg["var_value"] if self.passive_income_per_msg else 0

		self.xp_and_passive_income_delay = self.execute(
			"SELECT var_value FROM variables WHERE var_name = ?",
			("xp_and_passive_income_delay",)
		).fetchone()

		if self.xp_and_passive_income_delay:
			self.xp_and_passive_income_delay = self.xp_and_passive_income_delay["var_value"]
		else:
			self.xp_and_passive_income_delay = 0

		# set to integers
		self.xp_per_msg = int(self.xp_per_msg)
		self.passive_income_per_msg = int(self.passive_income_per_msg)
		self.xp_and_passive_income_delay = int(self.xp_and_passive_income_delay)


	"""
	GLOBAL FUNCTIONS
	"""

	def open_database(self):
		if self.database is None:
			# print(f"[LOG]: Opening database !")
			# this also creates the file automatically, if it does not exist !
			self.database = sqlite3.connect(self.path_to_db)
			# WAL means Write-Ahead Logging. Useful for multiple simultaneous accesses.
			# this is VERY IMPORTANT, KEEP IT THIS WAY IF YOU DON'T KNOW WHAT YOU'RE DOING.
			self.database.execute("PRAGMA journal_mode=WAL")

			# row allows us to get the data from sql as python dict. Probably very useful.
			# beware: it is readonly !
			# also VERY IMPORTANT, KEEP IT THIS WAY (except if you want to re-write the whole bot).
			self.database.row_factory = sqlite3.Row
			self.db_cursor = self.database.cursor()

	def commit(self):
		# if it is None, then we didn't open the database so there is nothing to commit,
		# but it means that we wanted to access the database, so we can open it as a safe result
		if self.database is None:
			self.open_database()
			return
		# else db is open, commit.
		# print(f"[LOG]: Committing to database !")
		self.database.commit()

	def close_database(self):
		if self.database is not None:
			# print("[LOG]: Closing database !")
			self.database.commit()
			self.database.close()
		self.database = None
		self.db_cursor = None

	async def execute_commit(self, query, parameters=(), commit=True):
		if not commit: raise ValueError("Are you trying to use self.execute() ?")
		if self.database is None or self.db_cursor is None:
			self.open_database()
		# avoid race conditions
		async with self.db_lock:
			result = self.db_cursor.execute(query, parameters)
			# commit should be set to True when calling this function in the following contexts:
			# INSERT, UPDATE, DELETE, CREATE, DROP, ALTER etc.
			self.commit()
			return result

	# separate execute and execute with commit, since else we would need to await every SELECT,
	# which may reduce performance.
	def execute(self, query, parameters=()):
		if self.database is None or self.db_cursor is None:
			self.open_database()
		result = self.db_cursor.execute(query, parameters)
		return result

	# executemany is always with commit
	async def executemany(self, query, parameters=(), commit=True):
		if not commit: raise ValueError("error, need to commit !!")
		if self.database is None or self.db_cursor is None:
			self.open_database()
		async with self.db_lock:
			result = self.db_cursor.executemany(query, parameters)
			self.commit()
			return result

	# this is to split the execute in chunks in case there is a lot to do
	async def executemany_by_chunks(self, query, data, chunk=1000):
		# in case there are a huge bunch of people, split it a bit.
		# but: chunk should not be too small in case between our edits another process wants to also edit
		# the database values we want to change. So this should be kept relatively high to avoid race conditions.
		# default chunk is 1000, but it can be changed when calling this function.

		# index starts at 0, then will be 1000, then 2000...
		for index in range(0, len(data), chunk):
			try:
				# execute from 0 to 1000, then 1000 to 2000 etc.
				await self.executemany(
					query,
					data[index:index+chunk], commit=True
				)
			except Exception as e:
				raise Exception(f"Error updating chunk at {index // chunk}: {e}")

	# I don't know how useful these will be, but it's good to have them
	def fetchone(self):
		if self.database is None:
			self.open_database()
		# will fetch wherever the cursor is at. So it depends on what was executed before calling this function.
		return self.db_cursor.fetchone()
	def fetchall(self):
		if self.database is None:
			self.open_database()
		return self.db_cursor.fetchall()

	async def change_balance(self, user_id, amount, balance_obj="cash", mode="replace"):
		# update (not insert, since we already have our user), commit and close
		# safe execute does all that automatically.

		if balance_obj not in ["cash", "bank"]:
			raise ValueError("for self.change_balance(self, ...), balance_obj must be 'cash' or 'bank'")

		if mode == "replace":
			await self.execute_commit(
				f"UPDATE users SET {balance_obj} = ? WHERE user_id = ?",
				(amount, user_id)
			)
		elif mode == "add":
			await self.execute_commit(
				f"UPDATE users SET {balance_obj} = {balance_obj} + ? WHERE user_id = ?",
				(amount, user_id)
			)
		elif mode == "subtract":
			await self.execute_commit(
				f"UPDATE users SET {balance_obj} = {balance_obj} - ? WHERE user_id = ?",
				(amount, user_id)
			)
		elif mode == "pass":
			# in this case we don't change the balance (e.g. blackjack returned "bust") but only update last used.
			pass
		else:
			raise ValueError("mode for change_balance(self, ...) must be either "
							 "'replace', 'add',  'subtract' or 'pass'.")


	@staticmethod
	def format_number_separator(number):
		# returns a nice 2,123,123,242 instead of just 2123123242
		return '{:,}'.format(int(number))

	#
	# GET USER OBJECT: find the user in the database // create user (automatically) !
	#

	async def get_user_object(self, user_id_searched, fail_safe=False):
		user_id_searched = int(user_id_searched)
		self.open_database()
		# info: the ? and tuple is to prevent sql injections, apparently. Which is not necessary here but still cool.
		# we need fetchone() because else we just set the cursor without actually fetching data
		# no need for fetchall() because user_id is unique.
		# we fetch select into a tuple (user_to_find, ...) because the ... will be all the data.
		# we could also select specific data, like: SELECT user_id, user_discord_nick ... (user_to_find, user_nick) etc.
		user_object = self.execute(
			f"SELECT * FROM users WHERE user_id = ?", (user_id_searched, )
		).fetchone()

		# info: we get a tuple but because of sqlite.Row above, we can also access like a python dict.
		# fetchone() returns "None" if nothing is found.
		# if it is not none, just return the user (and None, because we return "error" if we're in fail_safe mode)
		if user_object is not None:
			return user_object

		# info: fail_safe just means that we don't create the user if we didn't find them.
		# else: if fail_safe, just return that the user was not found:
		if fail_safe:
			# in this case, this isn't a user which isn't yet registered, but someone who doesn't exist on the server
			# or at least that's what is expected when calling with this parameter "Fail safe"
			return None

		# else: CREATE NEW USER !
		print("\n[LOG]: creating user\n")
		# get current discord nickname:
		try:
			user_nickname_obj = self.client.get_user(user_id_searched).name
			user_nickname = str(user_nickname_obj)
			user_nickname = self.escape_nickname(user_nickname)
		except Exception as e:
			print(f"\n[LOG]: failed to fetch user nickname for {user_id_searched} when creating user\n Error: {e}")
			# error -> id will be used as nickname.
			user_nickname = str(user_id_searched)
		# values: user_id, user_discord_nick, cash, bank, last_slut, last_work,
		#         last_rob, last_crime, last_blackjack, last_roulette
		# info: user_number auto-increments, goal: see total amount of users ever, even those who left.
		# we set all except user_id and user_discord_nick to the DEFAULT VALUES, so we don't edit them here
		new_user_object = (user_id_searched, user_nickname)
		# commit set to True, because we need to commit after INSERT / UPDATE ...
		await self.execute_commit(
			"INSERT INTO users (user_id, user_discord_nick) VALUES (?, ?)",
			new_user_object
		)
		# now get user object and return it
		user_object = self.execute(
			f"SELECT * FROM users WHERE user_id = ?", (user_id_searched, )
		).fetchone()
		return user_object

	@staticmethod
	def escape_nickname(nickname):
		discord_escape_chars = "\\*_~|`>"
		# result string, how we will save the nickname.
		escaped = ""
		for letter in nickname:
			if letter in discord_escape_chars:
				escaped += "\\"
			escaped += letter
		return escaped

	async def update_nickname(self, user, nickname=None):
		# create user if he doesn't exist
		await self.get_user_object(user)

		# if we already know the nickname, no need for an api check.
		if nickname is not None:
			user_nickname = self.escape_nickname(nickname)
		else:
			try:
				user_nickname = str(self.client.get_user(user).name)
				user_nickname = self.escape_nickname(user_nickname)
			except Exception as e:
				print(f"Error updating nickname at {user}, problem: {e}")
				# error -> id will be used as nickname.
				user_nickname = str(user)

		# info: directly UPDATE and not first SELECT, check if not the same, then UPDATE,
		# because SQLite checks itself and doesn't do the UPDATE if the value didn't change.
		await self.execute_commit(
			"UPDATE users SET user_discord_nick = ? WHERE user_id = ?",
			(user_nickname, user)
		)
		return None

	async def send_confirmation(self, ctx, msg, color="green", footer=None, title=None):
		if color == "green": color = self.discord_success_rgb_code
		elif color == "blue": color = self.discord_blue_rgb_code
		elif color == "red": color = self.discord_error_rgb_code
		if not title:
			embed = discord.Embed(description=f"{msg}", color=color)
		else:
			embed = discord.Embed(title=title, description=f"{msg}", color=color)
		embed.set_author(name=ctx.username, icon_url=ctx.user_pfp)

		# could be added for all embeds in general, unsure as of now.
		# if footer is None:
		if footer == "CURR_TIME":
			formatted_time = str(f"{datetime.now().hour:02}:{datetime.now().minute:02}")
			embed.set_footer(text=f"today at {formatted_time}")

		if footer is not None and footer != "CURR_TIME":
			embed.set_footer(text=footer)
		await ctx.channel.send(embed=embed)


	"""
	COMMON FUNCTIONS FOR GAMBLE AND ACTIONS
	"""


	# this function checks gamble limits. Limits can be amounts of money (min / max possible bet)
	# or a time limit (i.e. a cooldown before being able to bet again)
	#	for the time limit see function --> check_action_delay(self, ...) below this one.
	def check_gamble_amount_limits(self, game, user_cash, bet):
		# check amount limits !
		if game not in ["roulette", "blackjack"]:
			raise ValueError("function parameter <game> must be either 'roulette' or 'blackjack'.")

		min_amount = self.execute(f"SELECT * FROM variables WHERE var_name = 'min_amount_to_{game}' ").fetchone()
		max_amount = self.execute(f"SELECT * FROM variables WHERE var_name = 'max_amount_to_{game}' ").fetchone()

		if min_amount is None or max_amount is None:
			raise ValueError("Error while fetching from database. Please contact an admin.")
		elif min_amount["var_type"] == "int" and max_amount["var_type"] == "int":
			min_amount = int(min_amount["var_value"])
			max_amount = int(max_amount["var_value"])
		else:
			raise ValueError("Error while fetching from database. Please contact an admin.")

		if bet == "all": bet = user_cash
		else: bet = int(bet)

		if bet > user_cash:
			return ("error", (f"{self.error_emoji} You don't have that much money in cash."
				f"\nYou currently have {str(self.currency_symbol)} {self.format_number_separator(user_cash)} on hand."),
					None)
		if bet < min_amount:
			return ("error", (f"{self.error_emoji} You need to place a bet of at least {min_amount}."
				f"\nYou are trying to play with {str(self.currency_symbol)} {self.format_number_separator(bet)}."),
					None)
		# if max_amount == 0 it means there is no max amount.
		if max_amount != 0 and bet > max_amount:
			return ("error", (f"{self.error_emoji} The maximum possible bet for this is {max_amount}.\n"
				f"You are trying to play with {str(self.currency_symbol)} {self.format_number_separator(user_cash)}."),
					None)

		return "success", "success", bet

	# check delay (cooldown) for an action or gambling.
	def check_action_delay(self, action_name, user_object, mode="action"):
		# returns "run" --> cooldown passed or "delay" --> not enough time passed.
		# delay will ALWAYS be in MINUTES

		# technically, "action_name" is unprecise, because it can also be gamble_name.
		if mode == "action":
			# get from table "actions" where every action has a delay set.

			delay = self.execute(
				"SELECT delay FROM actions WHERE action_name = ?",
				(action_name,)
			).fetchone()["delay"]
		elif mode == "gamble":
			# for gambling, the bigger variables are in the table "variables".
			# btw: no risk for SQL injections since only our code calls this and checks everything.
			delay = self.execute(f"SELECT var_value FROM variables WHERE var_name = 'delay_{action_name}' ").fetchone()
			if not delay: return "error", "unknown error"
			delay = int(delay["var_value"])
		else:
			raise ValueError("mode must be either 'action' or 'gamble'.")

		# if it is the user's first time using the action/gamble, we can skip the whole check.
		last_run_string = user_object[f"last_{action_name}"] # always the same layout: last_slut, last_roulette ...
		if last_run_string == "none":
			return "run", None

		# else: not the first run, so check the time passed and if that is enough for delay.
		now = datetime.now()
		# get a time object from the string
		last_run = datetime.strptime(last_run_string, '%Y-%m-%d %H:%M:%S.%f')
		# calculate difference, see if it works
		passed_time = now - last_run
		passed_time_minutes = passed_time.total_seconds() // 60.0 # floor division to get a clean integer, not float.
		if passed_time_minutes == 0:
			# because of floor division it might display 0
			passed_time_minutes = 1
		if passed_time_minutes > delay:
			# enough time passed !
			return "run", None
		# else: still need to wait.
		# get the delay remaining, ceil (aka round up to above) to get a more readable answer (2.1  --> 2 min left).
		delay_remaining = math.ceil(delay - passed_time_minutes)

		# return our data
		return "delay", delay_remaining

	async def send_cooldown_embed(self, ctx, action, cooldown_left):
		embed_text = f"⏱ ️You need to wait {cooldown_left} minutes before using {action} again."
		embed = discord.Embed(description=f"{embed_text}", color=self.discord_blue_rgb_code)
		embed.set_author(name=ctx.username, icon_url=ctx.user_pfp)
		await ctx.channel.send(embed=embed)

	# write changes for gamble (blackjack, roulette) and actions (work, slut, crime, rob)
	async def actions_write_changes(self, ctx, new_cash, action, mode="replace"):
		# update balance
		await self.change_balance(ctx.user, new_cash, "cash", mode)

		# update last used values (last_slut, last_roulette ...)
		# update last slut time
		current_time = str(datetime.now())
		await self.execute_commit(
			f"UPDATE users SET last_{action} =  ? WHERE user_id = ?",
			(current_time, ctx.user)
		)
		# print(f"WRITTEN {current_time} TO {ctx.user} AS <last_{action}>")

	"""
	GAMBLING (blackjack, roulette)
	"""

	#
	# COMMON GAMBLE CHECK
	#

	async def gamble_check(self, ctx, game, bet):
		# get data
		user_object = await self.get_user_object(ctx.user)

		# check amount limits
		user_cash = user_object["cash"]
		status, msg, bet = self.check_gamble_amount_limits(game, user_cash, bet)
		# "error" = amount not correct. we keep "error" because that is the central way we interact with ../main.py
		if status == "error":
			# the error messages are formatted in the check function directly.
			return status, msg, None, None, None

		# check time limit
		status, delay_remaining = self.check_action_delay(game, user_object, mode="gamble")
		if status == "delay":
			await self.send_cooldown_embed(ctx, game, delay_remaining)
			# return success, because we have done everything back end (that ../main.py needed us to do)
			return "success", None, None, None, None
		# everything is fine.
		else: return "run", None, user_object, user_cash, int(bet)

	#
	# BLACKJACK
	#

	async def blackjack(self, ctx, bet):

		"""
			INFO for ALL FURTHER FUNCTIONS AS WELL
			in the old bot version, we used
				self.find_index_in_db(data_to_search, user),
				now -> await self.get_user_object()
			the good thing is: with sqlite3.Row we also get a python dict so we can easily access values !
			Beware tho: sqlite3.Row is READONLY !
		"""

		status, msg, user_object, user_cash, bet = await self.gamble_check(ctx, "blackjack", bet)
		if status != "run": return status, msg

		# else: run the actual game
		# start it
		start_instance = blackjack_discord_implementation(ctx, self.client, self.currency_symbol)
		blackjack_result = await start_instance.play(ctx, self.client, bet)

		# updates are done through common function above

		if blackjack_result == "win":
			await self.actions_write_changes(ctx, bet, "blackjack", mode="add")
		elif blackjack_result == "blackjack":
			await self.actions_write_changes(ctx, bet * 1.5, "blackjack", mode="add")
		elif blackjack_result == "loss":
			await self.actions_write_changes(ctx, bet, "blackjack", mode="subtract")
		elif blackjack_result == "bust":
			# could just say 0 and add / subtract, but it is cleaner with pass.
			# we use this function so that we can still update the "last used"
			await self.actions_write_changes(ctx, 0, "blackjack", mode="pass")
		else:
			return "error", f"{self.error_emoji} error unknown, contact admin"

		return "success", "success"

	#
	# ROULETTE
	#

	async def roulette(self, ctx, bet, space):

		# global checks for amounts and time limits
		status, msg, user_object, user_cash, bet = await self.gamble_check(ctx, "roulette", bet)

		if status != "run": return status, msg

		# the actual game
		# start it
		start_instance = roulette_discord_implementation(ctx, self.client, self.currency_symbol)
		roulette_win, multiplicator = await start_instance.play(ctx, self.client, bet, space)

		# roulettePlay will return 1 for won, 0 for lost
		if roulette_win:
			await self.actions_write_changes(ctx, bet*multiplicator - bet, "roulette", mode="add")
		elif roulette_win == 0:
			await self.actions_write_changes(ctx, bet, "roulette", mode="subtract")
		else:
			return "error", f"{self.error_emoji} error unknown, contact admin"

		return "success", "success"


	"""
	ACTIONS (work, slut, crime, rob).
	"""

	#
	# COMMON ACTIONS FUNCTIONS - CHECK and EXECUTE
	#

	async def actions_check(self, ctx, action):
		# get data
		user_object = await self.get_user_object(ctx.user)

		# check time limit
		status, delay_remaining = self.check_action_delay(action, user_object)
		if status == "delay":
			await self.send_cooldown_embed(ctx, action, delay_remaining)
			return "success", None
		# everything is fine.
		else: return "run", user_object

	def get_random_action_phrase(self, action, type_):
		phrase = self.execute(
			"SELECT phrase FROM action_phrases where action_name = ? AND type = ? ORDER BY RANDOM() LIMIT 1",
			(action, type_)
		).fetchone()["phrase"]
		return phrase

	def calculate_action_loss(self, action, user_object):
		min_loss_percentage, max_loss_percentage = self.execute(
			"SELECT min_lose_amount_percentage, max_lose_amount_percentage FROM actions WHERE action_name = ?",
			(action,)
		).fetchone()
		loss_percentage = random.randint(min_loss_percentage, max_loss_percentage)
		# we lose a certain amount of the total net worth, even if that brings us in a deficit in cash.
		balance = user_object["cash"] + user_object["bank"]
		loss = balance * (loss_percentage / 100)
		# round up, no floats
		return round(loss, 0)

	async def actions_run(self, ctx, action, user_object, user_to_rob=None):
		if action == "work":
			# there is no probability for work, it always works.
			success = True
		else:
			# will always return an INT between 0 and 100. Only other case is for work (see above).
			proba = self.execute(
				"SELECT proba FROM actions WHERE action_name = ?",
				(action,)
			).fetchone()["proba"]
			# random.random() gives float between 0.0 and 1.0 (1.0 being excluded).
			# our probability value is between 0 and 100, so we divide it by 100.
			# if our probability to win is greater than the "dice roll", then it returns True.
			# example: 30% (0.3) chance to win. random.random() returns 0.5: lost.
			success = (proba / 100) > random.random()

		if not success:
			# get a loss phrase, directly only choosing one random from the table through sql.
			lose_phrase = self.get_random_action_phrase(action, "lose")

			# for losing, slut, crime and rob have the same functioning ; work will never not success.
			# --> if action in ["slut", "crime", "rob"]:
			loss = self.calculate_action_loss(action, user_object)

			# write changes to database and update "last_..."
			await self.actions_write_changes(ctx, loss, action, mode="subtract")

			# inform user
			msg =f"{lose_phrase} {str(self.currency_symbol)} **{self.format_number_separator(loss)}**"
			await self.send_confirmation(ctx, msg, color="red", footer="r.i.p")

			return None

		# else: we won. with "rob" you gain a percentage from someone else, all other work with a min- and max-revenue.

		# get a phrase, works same for all.
		win_phrase = self.get_random_action_phrase(action, "win")
		# init win as 0, calculate below.
		win = 0

		# handle "normal" actions
		if action in ["slut", "crime", "work"]:
			# range values (absolute amounts)
			min_win, max_win = self.execute(
				"SELECT min_revenue, max_revenue FROM actions WHERE action_name = ?", (action,)
			).fetchone()
			# how much we made
			win = random.randint(min_win, max_win)
		# handle robbing specifically.
		elif action in ["rob"]:
			# range values for rob are a certain percentage from what someone else has on hand, not an absolute amount.
			min_win_percentage, max_win_percentage = self.execute(
				"SELECT min_gain_amount_percentage, max_gain_amount_percentage FROM actions WHERE action_name = ?",
				(action,)
			).fetchone()
			# actual percentage
			win_percentage = random.randint(min_win_percentage, max_win_percentage)

			# check if user to rob exists. "fail_safe" because this will not create the user if he doesn't exist.
			robbed_user_object = await self.get_user_object(user_to_rob, fail_safe=True)

			if robbed_user_object is None:
				# no such user exists.

				msg = f"{self.error_emoji} Invalid `<user>` argument given.\n\nUsage:\n`rob <user>`"
				await self.send_confirmation(ctx, msg, color="red")
				return None

			if str(ctx.user).strip() == str(user_to_rob).strip():
				# you cannot rob yourself
				msg = f"{self.error_emoji} You cannot rob yourself!"
				await self.send_confirmation(ctx, msg, color="red")
				return None

			# you cannot rob from people who have less money than you
			robbed_balance = robbed_user_object["cash"] + robbed_user_object["bank"]
			user_balance = user_object["cash"] + user_object["bank"]

			if robbed_balance < user_balance:
				loss = self.calculate_action_loss(action, user_object)

				msg = (f"{self.error_emoji} You've been fined {str(self.currency_symbol)} "
					   f"**{self.format_number_separator(loss)}** for trying to rob a person poorer than you."),
				await self.send_confirmation(ctx, msg, color="red")

				return None

			# all checks passed, now we actually rob.
			robbed_user_cash = robbed_user_object["cash"]
			win = robbed_user_cash * (win_percentage / 100)

		# -> final handling for successful action.

		# round up, no floats
		win = round(win, 0)
		# write changes to database and update "last_..."
		await self.actions_write_changes(ctx, win, action, mode="add")
		# inform user
		msg = f"{win_phrase} {str(self.currency_symbol)} **{self.format_number_separator(win)}**"
		await self.send_confirmation(ctx, msg, color="green", footer="gg")

		return None

	#
	# SLUT
	#

	async def slut(self, ctx):

		# global checks for actions
		status, user_object = await self.actions_check(ctx, "slut")
		if status != "run": return status, None

		await self.actions_run(ctx, "slut", user_object)

		return "success", "success"

	#
	# CRIME
	#

	async def crime(self, ctx):

		# global checks for actions
		status, user_object = await self.actions_check(ctx, "crime")
		if status != "run": return status, None

		await self.actions_run(ctx, "crime", user_object)

		return "success", "success"

	#
	# WORK
	#

	async def work(self, ctx):

		# global checks for actions
		status, user_object = await self.actions_check(ctx, "work")
		if status != "run": return status, None

		await self.actions_run(ctx, "work", user_object)

		return "success", "success"

	#
	# ROB
	#

	async def rob(self, ctx, user_to_rob):

		# global checks for actions
		status, user_object = await self.actions_check(ctx, "rob")
		if status != "run": return status, None

		await self.actions_run(ctx, "rob", user_object, user_to_rob)

		return "success", "success"


	"""
	BALANCE HANDLING (balance, deposit, withdraw, give...)
	"""

	#
	# BALANCE
	#

	async def get_balance(self, ctx, user_to_check, username_to_check, userpfp_to_check):
		# check if user exists (-> main.py: if we check ourselves, user_to_check = user, else it's from the other user.)
		# no need for fail_safe option because that is already checked in main.py before calling this function
		user_object = await self.get_user_object(user_to_check)

		check_cash = self.format_number_separator(user_object["cash"])
		check_bank = self.format_number_separator(user_object["bank"])
		check_bal = self.format_number_separator(user_object["cash"] + user_object["bank"])
		# :02 means "always at least 2 numbers after comma" and gives us 10:04 and not 10:4.
		formatted_time = str(f"{datetime.now().hour:02}:{datetime.now().minute:02}")

		color = self.discord_blue_rgb_code
		embed = discord.Embed(color=color)
		embed.add_field(name="**Cash**", value=f"{str(self.currency_symbol)} {check_cash}", inline=True)
		embed.add_field(name="**Bank**", value=f"{str(self.currency_symbol)} {check_bank}", inline=True)
		embed.add_field(name="**Net Worth:**", value=f"{str(self.currency_symbol)} {check_bal}", inline=True)
		embed.set_author(name=username_to_check, icon_url=userpfp_to_check)
		# set a footer with time info to make it look clean
		embed.set_footer(text=f"today at {formatted_time}")
		await ctx.channel.send(embed=embed)

		# we also use this to update the nickname.
		await self.update_nickname(ctx.user, ctx.nickname)

		return "success", "success"

	#
	# COMMON FUNCTION FOR DEPOSIT AND GIVE
	#

	async def check_and_change_funds(self, ctx, user_object, amount, mode="cash"):
		if mode not in ["cash", "bank"]: raise ValueError("Only cash or bank at check_and_change_funds(self, ...)")

		user_cash = user_object["cash"]
		user_bank = user_object["bank"]

		if amount == "all":
			amount = user_cash if mode == "cash" else user_bank
			if amount < 0:
				return "error", f"{self.error_emoji} You have debts in {mode} !"
		else:
			amount = int(amount)
			if amount > user_cash and mode == "cash":
				return "error", (f"{self.error_emoji} You don't have that much money on hand.\n"
					f"You currently have {str(self.currency_symbol)} {self.format_number_separator(user_cash)}.")
			elif amount > user_bank and mode == "bank":
				return "error", (f"{self.error_emoji} You don't have that much money to withdraw.\n"
								 f"You currently have {str(self.currency_symbol)} "
								 f"{self.format_number_separator(user_bank)} in the bank.")

		# write changes
		# subtract from bank if mode is bank (withdraw) or from cash if we're at deposit or give.
		await self.change_balance(ctx.user, amount, balance_obj=mode, mode="subtract")
		return "success", amount

	#
	# DEPOSIT
	#

	async def deposit(self, ctx, amount):
		# get user
		user_object = await self.get_user_object(ctx.user)

		# also removes money from cash
		status, msg = await self.check_and_change_funds(ctx, user_object, amount)
		if status == "error":
			return status, msg
		# so we know the amount if we said "all"
		if status == "success": amount = int(msg)

		await self.change_balance(ctx.user, amount, balance_obj="bank", mode="add")

		# inform user
		msg = (f"{self.worked_emoji} Deposited {str(self.currency_symbol)} "
			   f"{self.format_number_separator(amount)} to your bank!")
		await self.send_confirmation(ctx, msg)

		return "success", "success"

	#
	# WITHDRAW
	#

	async def withdraw(self, ctx, amount):
		# get user
		user_object = await self.get_user_object(ctx.user)

		# also adds money to cash
		status, msg = await self.check_and_change_funds(ctx, user_object, amount, mode="bank")
		if status == "error":
			return status, msg
		# so we know the amount if we said "all"
		if status == "success": amount = int(msg)

		await self.change_balance(ctx.user, amount, balance_obj="bank", mode="subtract")

		# inform user
		msg = (f"{self.worked_emoji} Withdrew {str(self.currency_symbol)} "
			   f"{self.format_number_separator(amount)} from your bank!")
		await self.send_confirmation(ctx, msg)

		return "success", "success"

	#
	# GIVE
	#

	async def give(self, ctx, reception_user, amount, recept_user_obj):

		if str(ctx.user).strip() == str(reception_user).strip():
			msg = (f"{self.error_emoji} You're trying to give yourself money ?"
				   f"\ninfo: You may be looking for the `add-money` command")
			await self.send_confirmation(ctx, msg, color="red")
			return None

		# get user
		user_object = await self.get_user_object(ctx.user)

		status, msg = await self.check_and_change_funds(ctx, user_object, amount)
		if status == "error":
			return status, msg
		# so we know the amount if we said "all"
		if status == "success": amount = int(msg)

		await self.change_balance(reception_user, amount, balance_obj="cash", mode="add")

		# inform user
		msg = (f"{self.worked_emoji} {recept_user_obj.mention} has received your "
			   f"{str(self.currency_symbol)} {self.format_number_separator(amount)}")
		await self.send_confirmation(ctx, msg)

		return "success", "success"

	#
	# ADD-MONEY
	#

	async def add_money(self, ctx, reception_user, amount, recept_user_obj):
		# get data
		reception_user_object = await self.get_user_object(reception_user)

		await self.change_balance(reception_user_object["user_id"], amount, balance_obj="cash", mode="add")

		# inform user
		msg = (f"{self.worked_emoji}  Added {str(self.currency_symbol)} {self.format_number_separator(amount)} "
			   f"to {recept_user_obj.mention}'s cash balance")
		await self.send_confirmation(ctx, msg)

		return "success", "success"

	#
	# REMOVE-MONEY
	#

	async def remove_money(self, ctx, reception_user, amount, recept_user_obj, mode):
		# get data
		reception_user_object = await self.get_user_object(reception_user)

		await self.change_balance(reception_user_object["user_id"], amount, balance_obj=mode, mode="subtract")

		# inform user
		msg = (f"{self.worked_emoji}  Removed {str(self.currency_symbol)} {self.format_number_separator(amount)} "
			   f"from {recept_user_obj.mention}'s {mode} balance")
		await self.send_confirmation(ctx, msg)

		return "success", "success"

	"""
	EDITING DATABASE VARIABLES THROUGH COMMAND
	"""

	#
	# MODULE INFO
	#

	async def module(self, ctx, module):

		# module can be "all" or a specific module.

		if module != "all":

			# OPTION 1 : first look if he meant a variable.

			row_info = self.execute(
				"SELECT * FROM variables WHERE var_name = ?",
				(module,)
			).fetchone()

			if row_info:

				embed = discord.Embed(color=self.discord_blue_rgb_code)
				name = f"🔧 Name: `{row_info['var_name']}`"
				value = (
					f"💡 Value: `{row_info['var_value']}`\n"
					f"🛠️ Default: `{row_info['var_default_value']}`\n"
					f"📦 Type: `{row_info['var_type']}`\n"
					f"📝 Description: {row_info['var_description']}"
				)

				embed.add_field(name=name, value=value, inline=False)

				await ctx.channel.send(embed=embed)
				return "success", "success"

			# OPTION 2: module seems to either action or wrong input
			fetch = self.execute(
				"SELECT * FROM actions WHERE action_name = ?", (module,)
			).fetchone()
			if not fetch:
				return "error", "Module with that name was not found (use module all)."

			# else make the embed.
			action = fetch
			embed = discord.Embed(color=self.discord_blue_rgb_code)
			embed.title = f"⚙️ Action: {action['action_name']}"

			embed.description = ("The actual variable names are put in **fat**.\n"
								 "Use those those for change-action !")

			embed.add_field(
				name=f"⏳ Delay",
				value=f"- **delay**: {action['delay']} minutes.",
				inline=False
			)
			embed.add_field(
				name=f"🎲 Probability",
				value=f"- **proba**: {action['proba'] if action['proba'] else 100} %.",
				inline=False
			)

			if action['min_revenue']:
				embed.add_field(
					name=f"💰 Revenue",
					value=f"- **min_revenue** {action['min_revenue']}\n"
						  f"- **max_revenue** {action['max_revenue']} {self.currency_symbol}\n",
					inline=False
				)

			if action['min_lose_amount_percentage']:
				embed.add_field(
					name=f"📉 Lose %",
					value=f"- **min_lose_amount_percentage**: {action['min_lose_amount_percentage']} %\n"
						  f"- **max_lose_amount_percentage**: {action['max_lose_amount_percentage']} %\n",
					inline=False
				)
			if action['min_gain_amount_percentage']:
				embed.add_field(
					name=f"📈 Gain %",
					value=f"- **min_gain_amount_percentage**: {action['min_gain_amount_percentage']} %\n"
						  f"- **max_gain_amount_percentage**: {action['max_gain_amount_percentage']} %\n",
					inline=False
				)

			# inform
			await ctx.channel.send(embed=embed)
			return "success", "success"

		# else: module = "all"

		# INFO: this will return a list of tuples with following content (number = index in tuple)
		#	0: column index in table, starting at 0.
		#	1: column name
		#	2: column type
		#	3: if column can be NULL (1) or not (0).
		#	4: default value.
		#	5: 1 if primary key, else 0.

		all_variables_info = self.execute(
			"SELECT * FROM variables"
		).fetchall()

		# for the variables. We only have 1 row per variable.

		embed = discord.Embed(color=self.discord_blue_rgb_code)
		embed.title = "TABLE 'VARIABLES'"

		for row in all_variables_info:
			embed.add_field(
				name=f"🔧 Name: {row['var_name']}\n",
				value=f"Value: {row['var_value']}\n"
					  f"️Default value: {row['var_default_value']}\n"
					  f"Type: {row['var_type']}",
				inline=False)

		footer = (f"Example: use module levels_info_channel **for more information**\n on that variable.\n"
				  f"e.g. use: change-variable xp_per_msg value 10")
		embed.set_footer(text=footer)
		# flush
		await ctx.channel.send(embed=embed)

		extra_info = ("info: to edit currency_emoji_name, use the change-currency command.\n"
					  "info: to edit income_reset, use set-income-reset.\n"
					  "info: you cannot (and should not) edit common_reset_time or last_global_income_update through the bot.")

		await ctx.channel.send(extra_info)

		# now for the actions. There, we actually deal with rows.

		actions_columns = self.execute(
			"SELECT * FROM actions"
		).fetchall()

		embed = discord.Embed(color=self.discord_blue_rgb_code)
		embed.title = "TABLE 'ACTIONS'"

		# here we can use the dict from sqlite3.Row again. PRAGMA always returns tuples.
		for row in actions_columns:
			value = (f"⏳ Delay: {row['delay']} minutes,\n"
					 f"🎲 Probability: {row['proba'] if row['proba'] else 100} %,\n")
			if row["min_revenue"]:
				value += f"💰 Revenue: min {row['min_revenue']}, max {row['max_revenue']} {self.currency_symbol}\n"
			if row['min_lose_amount_percentage']:
				value += (f"📉 min. loss (%): {row['min_lose_amount_percentage']},\n"
						  f" max. loss (%): {row['max_lose_amount_percentage']}\n")
			if row["min_gain_amount_percentage"]:
				value += (f"📈 min. gain (%): {row['min_gain_amount_percentage']},\n"
						  f" max. gain (%): {row['max_gain_amount_percentage']}")

			embed.add_field(
				name=f"Action: {row['action_name']}",
				value=value,
				inline=False
			)

		# flush.
		footer = (f"Example: use module rob for info only on that action.\n"
				  f"e.g. use: change-action crime proba 30")
		embed.set_footer(text=footer)
		await ctx.channel.send(embed=embed)

		# send info
		await ctx.channel.send("Info: This includes all changeable modules except levels.\n"
							   "For income-reset, please use set-income-reset.\n"
							   "For passive-chat-income, please use set-passive-chat-income")

		return "success", "success"

	#
	# EDIT VARIABLES AKA CHANGE VARIABLES AKA CHANGE ACTIONS.
	#

	async def change_variables_and_actions(
			self, ctx, mode, variable_name, new_value, action_name=None
	): # why does he look sad lol

		if mode not in ["actions", "variables"]:
			raise ValueError("mode for change_variables_and_actions must be 'actions' or 'variables'")

		if mode == "actions":
			# check if action exists
			result = self.execute(
				"SELECT * FROM actions WHERE action_name = ?",
				(action_name,)
			).fetchone()

			if not result:
				return "error", "action not found."

			# also, we cannot change action_name itself. But that check is done in bot.py before calling this function.

			try:
				current_value = result[variable_name]
				# not current value means that it is set to NULL in the database.
				# that means that it is not editable ! e.g. there is no min_revenue for rob, but a percentage, etc.
				# is None and not "if not current_value" since that would also be True if the value is 0.
				if current_value is None:
					return "error", "the variable name you chose cannot be edited for this action"
			except:
				return "error", "the given variable name does not exist"

			# SQL injection risk is handled through the try/except above.
			print(f"UPDATE actions SET {variable_name} = {new_value} WHERE action_name = {action_name}")
			await self.execute_commit(
				f"UPDATE actions SET {variable_name} = ? WHERE action_name = ?",
				(new_value, action_name)
			)

			# inform
			await ctx.channel.send(f"{self.worked_emoji} {variable_name} for {action_name} set to {new_value}")

		else:

			if variable_name == "currency_emoji_name":
				return "error", "Use the specific command to change currency emoji."
			if variable_name == "income_reset":
				return "error", "Use the specific command to change income reset."
			if variable_name in ["common_reset_time", "last_global_income_update"]:
				return "error", "You cannot change common_reset_time or last_global_income_update."

			# check if variable exists
			result = self.execute(
				"SELECT * FROM variables WHERE var_name = ?",
				(variable_name,)
			).fetchone()

			if not result:
				return "error", "Variable not found."

			# btw: we don't have to check if for level_channels_info the channel is correct format and exists,
			# since we already did that in bot.py before calling this function.

			# check if integer (all variables that can be changed here need to be integers) is also done in bot.py

			await self.execute_commit(
				"UPDATE variables SET var_value = ? WHERE var_name = ?",
				(new_value, variable_name)
			)

			# inform
			msg = f"{self.worked_emoji} {variable_name} set to {new_value}"
			if variable_name == "levels_info_channel":
				msg += "\n## Reboot the bot for changes to apply."

			await ctx.channel.send(msg)

		return "success", "success"

	#
	# EDIT CURRENCY SYMBOL
	#

	async def change_currency_symbol(self, ctx, new_emoji_name):
		# old emoji
		old_value = self.execute(
			"SELECT var_value FROM variables WHERE var_name = ?",
			("currency_emoji_name",)
		).fetchone()["var_value"]

		status, msg = self.get_currency_symbol(True, new_emoji_name)
		if status == "error":
			return status, msg

		# changing value
		await self.execute_commit(
			"UPDATE variables SET var_value = ? WHERE var_name = ?",
			(new_emoji_name, "currency_emoji_name")
		)

		# no verification btw.
		# inform user
		msg = (f"{self.worked_emoji}  Changed emoji from '{old_value}' to '{new_emoji_name}'"
			   f"\n\n**Please REBOOT the bot for emoji to update.**")
		await self.send_confirmation(ctx, msg)

		return "success", "success"

	#
	# SET INCOME RESET
	#

	async def set_income_reset(self, ctx, new_income_reset):

		# changing value
		await self.execute_commit(
			"UPDATE variables SET var_value = ? WHERE var_name = ?",
			(new_income_reset, "income_reset")
		)

		# inform user
		msg = f"{self.worked_emoji}  Changed income-reset to　`{new_income_reset}`"
		footer = "info: if true (default), daily salary resets every day and does not accumulate."
		await self.send_confirmation(ctx, msg, color="green", footer=footer)

		return "success", "success"

	#
	# SET PASSIVE CHAT INCOME
	#

	async def set_passive_chat_income(self, ctx, new_value):

		# changing value
		await self.execute_commit(
			"UPDATE variables SET var_value = ? WHERE var_name = ?",
			(new_value, "passive_income_per_msg")
		)

		# inform user
		msg = f"{self.worked_emoji}  Changed passive chat income to　`{new_value}`\n**Please REBOOT Bot to apply.**"
		footer = "info: income is per message, with the same cooldown as for gaining xp."
		await self.send_confirmation(ctx, msg, color="green", footer=footer)

		return "success", "success"

	"""
	ITEM HANDLING
	"""

	#
	# CREATE NEW ITEM / create item
	#

	async def create_new_item(
			self, ctx, item_display_name, item_name, price, description, duration, stock,
			max_amount, max_amount_per_transaction, roles_id_required, roles_id_to_give, roles_id_to_remove,
			max_bal, reply_message, item_img_url, roles_id_excluded
	):

		result = self.execute(
			"SELECT 1 FROM items_catalog WHERE item_name = ?",
			(item_name, )
		).fetchone()

		if result: return "error", f"{self.error_emoji} Item with such name already exists."

		# calculate item duration
		today = datetime.today()
		expiration_date = today + timedelta(days=duration)

		# INFO: we need to set the role(s) as JSON, because SQL cannot handle a list otherwise
		# and since multiple roles have to be able to be added, we go through json.
		await self.execute_commit("""
			INSERT OR IGNORE INTO items_catalog (
				item_name, display_name, price, description, duration,
				amount_in_stock, max_amount, max_amount_per_transaction, required_roles, given_roles,
				removed_roles, excluded_roles, maximum_balance, reply_message,
				expiration_date, item_img_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
  	(item_name, item_display_name, price, description, duration,
   				stock, max_amount, max_amount_per_transaction, json.dumps(roles_id_required),
				json.dumps(roles_id_to_give), json.dumps(roles_id_to_remove),
 				json.dumps(roles_id_excluded), max_bal, reply_message, expiration_date, item_img_url)
		)

		return "success", "success"

	#
	# REMOVE ITEM AKA DELETE ITEM
	#

	async def remove_item(self, ctx, item_name):

		# try to delete item
		result = await self.execute_commit(
			"DELETE FROM items_catalog WHERE item_name = ?",
			(item_name,)
		)

		if result.rowcount == 0: return "error", f"{self.error_emoji} Item not found."

		# also delete from inventories
		await self.execute_commit(
			"DELETE FROM user_items WHERE item_name = ?",
			(item_name,)
		)

		return "success", "success"

	#
	# REMOVE ITEM FROM SPECIFIC USER's INVENTORY
	#

	async def remove_user_item(self, ctx, item_name, amount_removed, reception_user, recept_user_obj):

		result = self.execute("SELECT * FROM user_items WHERE user_id = ?", (ctx.user,)).fetchone()
		if not result:
			return "error", f"{self.error_emoji} User does not have any items."

		possessed_items = self.check_user_item_amount(ctx.user, amount_removed)

		if result.rowcount == 0:
			return "error", f"{self.error_emoji} User does not possess the specified item."
		if possessed_items - amount_removed < 0:
			return "error", (f"{self.error_emoji} User does not have the necessary amount of items.\n"
							 f"Info: has {possessed_items} items of that item.")

		await self.execute_commit(
			"UPDATE user_items SET amount = ? WHERE user_id = ? AND item_name = ?",
			(amount_removed, reception_user, item_name)
		)

		# inform user
		msg = (f"{self.worked_emoji} Removed {self.format_number_separator(amount_removed)} "
			   f"{item_name} from {recept_user_obj.mention}.")
		await self.send_confirmation(ctx, msg)

		return "success", "success"


	"""
	COMMON ITEM HANDLING FUNCTIONS
	"""

	def check_user_item_amount(self, user, item_name, mode="specific"):
		# if called with mode="any", we check if the user has any items at all.
		if mode == "any":
			# print(user, type(user))
			# with limit to have a fast check if someone has a lot of items
			any_items_owned = self.execute("SELECT 1 FROM user_items WHERE user_id = ? LIMIT 1",
										   (user,)).fetchall()

			# print(any_items_owned)

			return True if any_items_owned else False

		already_owned = self.execute("SELECT amount FROM user_items WHERE user_id = ? AND item_name = ?",
									 (user, item_name)).fetchone()
		# set to 0 if already_owned is None.
		already_owned_amount = already_owned["amount"] if already_owned else 0
		return already_owned_amount

	# we can merge updating user_items and user_used_items with the same function,
	# since they both have the same columns (user_id, item_name, amount).
	async def safe_items_update(self, table, user, item_name, new_amount, mode="replace"):
		await self.get_user_object(user)
		# check if table exists. We know that these two tables definitely exist,
		#	so we don't need an extra "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)"
		# btw: I just learned that for "in/not in" checks, {} is faster than [] and ()
		# 	but you should use [] if you need duplicates or a certain order.
		# 	I won't change the [] everywhere I used "not in" tho.
		if table not in {"user_items", "user_used_items"}:
			return "error", "only user_items and user_used_items table able to modify."
		if mode not in {"replace", "add"}:
			return "error", "only 'replace' or 'add' mode can be used (FUNC: safe_items_update)."

		# check if row already exists
		row_exists = self.execute(f"SELECT 1 FROM {table} WHERE user_id = ? AND item_name = ?",
								  (user, item_name)).fetchone()

		# now create a new row or update the existing one
		set_mode = "amount = amount + ?" if mode == "add" else "amount = ?"

		if not row_exists:
			await self.execute_commit(
				f"INSERT INTO {table} VALUES (?, ?, ?)",
				(user, item_name, new_amount)
			)
		else:
			await self.execute_commit(
				f"UPDATE {table} SET {set_mode} WHERE user_id = ? AND item_name = ?",
				(new_amount, user, item_name)
			)
		# worked.
		return "success", "success"


	"""
	SPECIFIC ITEM FUNCTIONS
	"""

	#
	# BUY ITEM
	#

	async def buy_item(self, ctx, item_name, amount):

		try:
			amount = int(amount)
		except:
			return "error", "amount not integer"

		# get variables
		item = self.execute(
			"SELECT * FROM items_catalog WHERE item_name = ?",
			(item_name,)).fetchone()
		if not item:
			return "error", "Item not found."

		# get the display name
		# this automatically checks, if such a key exists (else: none), else it takes the item_name.
		# before it was checked through another SQLite query.
		item_display_name = item["display_name"] or item_name

		item_price = item["price"]
		# since roles are saved as json lists, we need to load it too.
		req_roles = json.loads(item["required_roles"])
		give_roles = json.loads(item["given_roles"])
		rem_roles = json.loads(item["removed_roles"])
		excluded_roles = json.loads(item["excluded_roles"])
		max_bal = item["maximum_balance"]
		remaining_stock = item["amount_in_stock"]
		max_amount = item["max_amount"]
		max_amount_per_transaction = item["max_amount_per_transaction"]
		expiration_date = item["expiration_date"]
		reply_message = item["reply_message"]

		# calculate expiration
		today = datetime.today()
		expire = datetime.strptime(expiration_date, "%Y-%m-%d %H:%M:%S.%f")
		if today > expire:
			return "error", f"{self.error_emoji} Item has already expired. Expiring date was {expiration_date}"
		# else we're good

		# 1. check req roles. Using all() because he needs ALL of those roles.
		# info: [int(role) in user_roles for role in req_roles]
		# 	will check if role is in user_roles for every role in req_roles. So it loops automatically.
		if req_roles != ["none"] and not all(int(role) in ctx.user_roles for role in req_roles):
			return "error", f"{self.error_emoji} User does not seem to have all required roles."

		# 2. check excluded roles. Using any() because even ONE excluded role is enough to block.
		if excluded_roles != ["none"]:
			has_excluded = [int(role) in ctx.user_roles for role in excluded_roles] # example: [False, False, False, True]
			# has_excluded is automatically True if there is one True in the list.
			if any(has_excluded):
				return "error", f"{self.error_emoji} User possesses excluded role (id: {has_excluded[0]})."

		# 3. check if enough money
		sum_price = round(item_price * amount, 0)
		user_object = await self.get_user_object(ctx.user)
		user_cash = user_object["cash"]
		if user_cash < sum_price:
			return "error", (f"{self.error_emoji} Not enough money in cash to purchase.\n"
							 f"to pay: {sum_price} ; in cash: {user_cash}")

		# 4. check if not too much money
		user_bal = user_object["bank"] + user_cash
		if max_bal != "none" and user_bal > max_bal:
			return "error", (f"{self.error_emoji} You have too much money to purchase.\n"
							 f"net worth: {self.format_number_separator(user_bal)} ; max bal: {max_bal}")

		# 5. check if not too many items already owned / to be owned
		already_owned_amount = self.check_user_item_amount(ctx.user, item_name)
		if max_amount != "unlimited":
			max_amount = int(max_amount)
			if already_owned_amount + amount > max_amount:
				return "error", (f"{self.error_emoji} You have too many items or would own too many.\n"
					f"You can buy **{self.format_number_separator(max_amount - already_owned_amount)}** {item_name}(s)")

		# 5.1: check if not too many at once
		if max_amount_per_transaction != "unlimited":
			max_amount_per_transaction = int(max_amount_per_transaction)
			if amount > max_amount_per_transaction:
				return "error", (f"{self.error_emoji} You cannot buy so many items at once.\n"
				f"You can buy **{self.format_number_separator(max_amount_per_transaction)}** {item_name}(s) at once")


		# --> those were the checks, now we execute.

		# 6. remove money
		await self.change_balance(ctx.user, sum_price, mode="subtract")

		# 7. check if enough in stock or not, subtract stock
		# this is a bit tricky because remaining_stock can be either unlimited or a number (as string).
		if remaining_stock != "unlimited":
			remaining_stock = int(remaining_stock)
			if remaining_stock - amount < 0:
					return "error", f"{self.error_emoji} Not enough remaining in stock ({remaining_stock} remaining)."
			await self.execute_commit(
				"UPDATE items_catalog SET amount_in_stock = amount_in_stock - ? WHERE item_name = ?",
				( int(remaining_stock) - amount, item_name),
			)
		# else if unlimited: skip.

		# 8. add to inventory (create a new row if he did not have that item yet, else - on conflict - update).
		new_amount = already_owned_amount + amount
		await self.safe_items_update("user_items", ctx.user, item_name, new_amount)

		# 9. check remove roles
		if rem_roles != ["none"]:
			await self.utils.add_or_remove_roles_user(ctx, ctx.user_ctx_obj, rem_roles, mode="remove")

		# 10. check give roles
		if give_roles != ["none"]:
			await self.utils.add_or_remove_roles_user(ctx, ctx.user_ctx_obj, give_roles, mode="add")

		# done ! -> inform user
		msg = (f"You have bought {amount} {item_display_name} and paid {str(self.currency_symbol)} "
			   f"**{self.format_number_separator(sum_price)}**")
		await self.send_confirmation(ctx, msg, color="blue", footer=reply_message)

		return "success", "success"

	#
	# GIVE ITEM
	#

	async def give_item(self, ctx, item_name, amount, reception_user, recept_user_object, spawn_mode):

		item_exists = self.execute("SELECT * FROM items_catalog WHERE item_name = ?",
								   (item_name,)).fetchone()
		if not item_exists:
			return "error", f"{self.error_emoji} Item not found (needs to be created before spawning)."

		user_items_amount = self.execute(
			"SELECT amount FROM user_items WHERE item_name = ? AND user_id = ?",
			(item_name, ctx.user)
		).fetchone()
		user_items_amount = user_items_amount["amount"] if user_items_amount else 0

		try:
			# if it's not just an admin spawning an item
			# then we remove the given items from the giving user.
			if not spawn_mode:  # not doing this if an admin just spawns an item
				if user_items_amount < amount:
					return "error", f"{self.error_emoji} You do not have enough items of that item to give."

				# else: goes through
				new_amount = user_items_amount - amount
				await self.safe_items_update("user_items", ctx.user, item_name, new_amount)
			# now handling the reception side
			reception_user_items_amount = self.check_user_item_amount(reception_user, item_name)
			reception_new_amount = reception_user_items_amount + amount
			await self.safe_items_update("user_items", reception_user, item_name, reception_new_amount)

		except Exception as e:
			print("Error while giving/spawning item:", e)
			return "error", f"{self.error_emoji} Unknown error."

		# inform user
		if not spawn_mode:
			msg = (f"{self.worked_emoji} {recept_user_object.mention} has received "
				   f"{self.format_number_separator(amount)} {item_name} from you!")
		else:
			msg =(f"{self.worked_emoji} {recept_user_object.mention} has received "
				  f"{self.format_number_separator(amount)} {item_name} (spawned)!")
		await self.send_confirmation(ctx, msg)

		return "success", "success"

	#
	# USE ITEM
	#

	async def use_item(self, ctx, item_name, amount):

		user_items = self.execute("SELECT * FROM user_items WHERE user_id = ? AND item_name = ?",
								  (ctx.user, item_name)).fetchone()
		if not user_items:
			return "error", f"{self.error_emoji} You do not have the specified item."
		else: user_item_amount = user_items["amount"]

		# use items
		if user_item_amount < amount:
			return "error", f"{self.error_emoji} You do not have enough items of that item to use."

		# else proceed
		# increase the user_used_items table. Default mode is to just replace, but
		# since we work with two different tables, the easiest way is just to say "increase" in the other function
		# and not double-check here, if he already used those items etc.
		await self.safe_items_update("user_used_items", ctx.user, item_name, amount, mode="add")

		# remove items the user has
		new_owned_amount = user_item_amount - amount
		await self.safe_items_update("user_items", ctx.user, item_name, new_owned_amount, mode="replace")

		# inform user
		plural = "s" if amount > 1 else ""
		msg = f"{self.worked_emoji} You have used {self.format_number_separator(amount)} {item_name}{plural} !"
		await self.send_confirmation(ctx, msg)

		return "success", "success"

	#
	# CHECK INVENTORY
	#

	async def check_inventory(self, ctx, user_to_check,
							  user_to_check_uname, user_to_check_pfp, page_number):

		# you can check your own inventory or someone else's.
		# btw: right now, all the "user_to_check..." variables have no use, they could just be put in the normal
		# user, username, ctx.user_pfp variables, since we don't use both but only one anyway
		# (see below: only one name and pfp used). But I'll keep it, in case it may be of use later
		# e.g.: showing on the embed that the inventory belongs to X, but the check has been called by Y.
		if user_to_check != "self":
			user = user_to_check
			local_username = user_to_check_uname
			local_user_pfp = user_to_check_pfp
		else:
			user = ctx.user
			local_username = ctx.username
			local_user_pfp = ctx.user_pfp

		# first check: any items ?
		any_items = self.check_user_item_amount(user, None, mode="any")
		if not any_items:
			title = "inventory"
			msg = "**Inventory empty. No items owned.**"
			footer = f"page 1 of 1"
			await self.send_confirmation(ctx, msg, color="blue", footer=footer, title=title)
			return "success", "success"

		# else: make inventory checkup.
		# get all the items he still has (skip those with amount at 0)
		user_items = self.execute("SELECT * FROM user_items WHERE user_id = ? AND amount > 0",
								  (user,)).fetchall()
		# example return:
		#	[
		#		{"user_id": ..., "item_name": ..., "amount": ...}
		#				without sqlite3.Row it would just be the values (uid, name, amount)
		#		... as many as there are items
		#	]

		total_items = math.ceil(len(user_items))

		# how many pages will be needed
		items_per_page = 10
		page_count = math.ceil(total_items / items_per_page)
		# set actual page count:
		# min() returns smallest number, i.e. makes sure we only go as far as there are pages
		# max() gives the bigger number, i.e. makes sure we don't drop below one.
		page_number = max(1, min(page_number, page_count))

		# create embed:

		# init embed (not using send_confirmation(self, ...) since we tweak the fields here.
		color = self.discord_blue_rgb_code
		embed = discord.Embed(title="inventory", color=color)

		# this is because if we call page 2 we want to start at 20
		current_index = (page_number - 1) * items_per_page + 1 # +1 to start at 1 and not 0

		# get the item infos that we are going to need
		all_names = [obj["item_name"] for obj in user_items]
		if not all_names:
			all_item_infos = []
			all_amounts = {}
		else:
			# this gives us (?, ?, ?) with ? being the amount of names we're fetching.
			fetch_all_query = f"({','.join(['?'] * len(all_names))})"
			# now fetch
			all_item_infos = self.execute(
				f"SELECT * FROM items_catalog WHERE item_name IN {fetch_all_query}",
				all_names
			).fetchall()

			# create all_amounts dictionary, since we need to be able to easily access it below.
			all_amounts = {obj["item_name"]: obj["amount"] for obj in user_items}

		# fill with content

		# previously without embeds: inventory_checkup = f""
		# for new embed version:
		for item_info in all_item_infos:
			display_name = item_info["display_name"]
			item_name = item_info["item_name"]
			amount = all_amounts[item_name]

			# += f"[{current_index}]　Item: {display_name}\n　　short name: {item_name}\n　　amount: `{amount}`\n\n"
			embed.add_field(
				name=f"[{current_index}] 📦 Item: {display_name}",
				value=f"Short name: `{item_name}`　" # [　] this is ideographic space and not normal space
					  f"Amount: `{amount}`",
				inline=False
			)
			current_index += 1

		# finish up embed and send
		footer = f"page {page_number} of {page_count}. Total: {total_items} different item{'s' if total_items > 1 else ''}!"
		embed.set_author(name=local_username, icon_url=local_user_pfp)
		embed.set_footer(text=footer)
		await ctx.channel.send(embed=embed)

		return "success", "success"

	#
	# CATALOG
	#

	async def catalog(self, ctx, item_check):

		all_items_raw = self.execute("SELECT * FROM items_catalog").fetchall()
		all_items = {item["item_name"]: item for item in all_items_raw}

		if not all_items:
			return "error", "There are no items available currently !"

		catalog_final = []
		items_per_page = 10
		current = 0

		# init the report.
		# report is using normal text and not embeds, to be able to show more on less space, since catalog can be huge.
		catalog_report = "__Items catalog:__\n```\n"

		# default list means we just want a list of all available items.
		if item_check == "default_list":
			# we need .values() because, all_items now being a dict, else item would just be the key.
			for index, item in enumerate(all_items.values(), start=1):
				current += 1
				catalog_report += (f"Item {index}: {item['display_name']}\n      price: {item['price']};"
								   f"　short name <{item['item_name']}>\n\n")
				if current >= items_per_page:
					catalog_report += "\n```"
					catalog_final.append(catalog_report)
					catalog_report = "```"
					current = 0

			catalog_report += "\n```\n*For details about an item: use* `catalog <item short name>`"
			catalog_final.append(catalog_report)

			for page in catalog_final:
				await ctx.channel.send(page)

			return "success", "success"

		# else: the user wants detailed information about a specific item.

		if item_check not in all_items:
			return "error", f"{self.error_emoji} Item not found."

		display_name = all_items[item_check]['display_name']
		item_name = all_items[item_check]['item_name']
		price = all_items[item_check]['price']
		amount_in_stock = all_items[item_check]['amount_in_stock']
		max_amount = all_items[item_check]['max_amount']
		description = all_items[item_check]['description']
		maximum_balance = all_items[item_check]['maximum_balance']
		item_img_url = all_items[item_check]['item_img_url']

		color = self.discord_blue_rgb_code
		embed = discord.Embed(title=f"catalog: {display_name}", color=color)

		# required roles
		req_roles = ""
		req_roles_raw = json.loads(all_items[item_check]["required_roles"])
		for role in req_roles_raw:
			role = discord.utils.get(ctx.server.roles, id=int(role))
			req_roles += f"{str(role.mention)} "

		# excluded roles
		excluded_roles = ""
		excluded_roles_raw = json.loads(all_items[item_check]["excluded_roles"] or [])
		for role in excluded_roles_raw:
			role = discord.utils.get(ctx.server.roles, id=int(role))
			excluded_roles += f"{str(role.mention)} "

		# given roles when buying item
		give_roles = ""
		give_roles_raw = json.loads(all_items[item_check]["given_roles"] or [])
		for role in give_roles_raw:
			role = discord.utils.get(ctx.server.roles, id=int(role))
			give_roles += f"{str(role.mention)} "

		# roles removed when buying item
		rem_roles = ""
		rem_roles_raw = json.loads(all_items[item_check]["removed_roles"] or [])
		for role in rem_roles_raw:
			role = discord.utils.get(ctx.server.roles, id=int(role))
			rem_roles += f"{str(role.mention)} "

		# expiration date
		exp_date = datetime.strptime(all_items[item_check]['expiration_date'], '%Y-%m-%d %H:%M:%S.%f')
		if exp_date.year >= 100:
			left_time = "never"
		else:
			left_time = exp_date.strftime('%d/%m/%Y')

		# now configure the embed
		embed.add_field(
			name="📦 Item name:",
			value=f"{display_name}",
			inline=False
		)
		embed.add_field(
			name="🏷️ Short name:",
			value=f"`{item_name}`",
			inline=True
		)
		embed.add_field(
			name="💰 Price:",
			value=f"{price}",
			inline=True
		)
		embed.add_field(
			name="📦 In stock:",
			value=f"{amount_in_stock}",
			inline=True
		)
		embed.add_field(
			name="🔢 Max ownership:",
			value=f"{max_amount}",
			inline=False
		)
		embed.add_field(
			name="📝 Description:",
			value=f"{description}",
			inline=False
		)
		embed.add_field(
			name="⏳ Remaining time:",
			value=f"🕒 Expires {left_time}",
			inline=True
		)
		embed.add_field(
			name="💸 Max balance to buy:",
			value=f"{self.currency_symbol} {maximum_balance}",
			inline=False
		)
		embed.add_field(
			name="🧩 Roles:",
			value=(
				f"✅ Required: {req_roles}　"
				f"🚫 Excluded: {excluded_roles}　"
				f"🎁 Given: {give_roles}　"
				f"❌ Removed: {rem_roles}"
			),
			inline=False
		)

		if item_img_url != "EMPTY":
			embed.set_image(url=item_img_url)
			embed.set_footer(text="info: item should have an img set. "
								  "If it doesn't appear, the url is probably broken.")
		else:
			embed.set_footer(text="Info: always use the short name for commands.")
		await ctx.channel.send(embed=embed)

		return "success", "success"


	"""
	ROLE HANDLING (--> income)
	"""

	"""
	COMMON ROLE HANDLING FUNCTIONS
	"""

	def get_all_income_roles(self, mode="default"):
		roles = self.execute("SELECT * FROM income_roles").fetchall()
		return roles

	def role_exists(self, role_id):
		exists = self.execute("SELECT 1 FROM income_roles WHERE role_id = ?",
							  (role_id, )).fetchone()
		return exists is not None

	async def update_income_roles(self, role_id, mode="none", role_income=None):

		if mode not in ["insert", "remove", "update"]:
			raise ValueError("update_roles(self, ...) needs a mode parameter.")

		if mode == "remove":
			result = await self.execute_commit(
				"DELETE FROM income_roles WHERE role_id = ?",
				(role_id, )
			)
			if result.rowcount == 0: return "error", f"{self.error_emoji} Role not found."
			return None, None

		# checks to see if it is able to be updated / inserted.
		if mode == "insert" and self.role_exists(role_id):
			return "error", f"{self.error_emoji} Role already exists as income role."
		if mode == "update" and not self.role_exists(role_id):
			return "error", f"{self.error_emoji} Role to update was not found as registered income role."

		if mode == "insert":
			await self.execute_commit(
				f"INSERT INTO income_roles (role_id, role_income) VALUES (?, ?)",
				(role_id, role_income)
			)

		if mode == "update":
			await self.execute_commit(
				f"UPDATE income_roles SET role_income = ? WHERE role_id = ?",
				(role_income, role_id)
			)

		return None, None

	"""
	SPECIFIC ROLE FUNCTIONS
	"""

	#
	# ROLE INCOMES - NEW INCOME ROLE - ADD INCOME ROLE
	#

	async def new_income_role(self, ctx, income_role_id, income):

		now = str(datetime.now())

		insert, err_msg = await self.update_income_roles(
			income_role_id, mode="insert", role_income=income
		)

		if insert == "error": return insert, err_msg

		# inform user
		msg = (f"New income role added.\nrole_id : {income_role_id}, income : {str(self.currency_symbol)} "
			   f"**{self.format_number_separator(income)}**")
		await self.send_confirmation(ctx, msg, color="blue", footer="smooth")

		return "success", "success"

	#
	# ROLE INCOMES - REMOVE ROLE
	#

	async def remove_income_role(self, ctx, income_role_id):

		insert, err_msg = await self.update_income_roles(income_role_id, mode="remove")
		if insert == "error": return insert, err_msg

		return "success", "success"

	#
	# ROLE INCOMES - UPDATE ROLE
	#

	async def update_income_role(self, ctx, income_role_id, new_income):

		insert, err_msg = await self.update_income_roles(income_role_id, mode="update", role_income=new_income)
		if insert == "error": return insert, err_msg

		return "success", "success"

	#
	# ROLE INCOMES - LIST ROLES
	#

	async def list_income_roles(self, ctx):

		color = self.discord_blue_rgb_code

		roles_per_page = 15 ; page = 1
		description = ""
		current = 0

		all_income_roles = self.get_all_income_roles()

		if not all_income_roles:
			return "error", "There are no income roles set currently !"

		for index, role in enumerate(all_income_roles, start=1):
			current += 1
			# discord.utils.get is slower than this, but safer to work with and ping is controllable.
			# ping_role = f"<@&{role['role_id']}>"
			ping_role = discord.utils.get(ctx.server.roles, id=int(role["role_id"]))

			# skip if there is an error with the role
			if not ping_role:
				print(f"Error with role {role}, {role['role_id']}")
				continue

			description += (f"`{index}` - Role {ping_role.mention} | "
							f"{self.currency_symbol} {self.format_number_separator(role['role_income'])}\n")

			if current >= roles_per_page:
				embed = discord.Embed(title=f"**Income Roles List [{page}]:**", description=description, color=color)
				await ctx.channel.send(embed=embed)
				description = ""
				current = 0
				page += 1

		# if there's a leftover, send anyway.
		if description != "":
			embed = discord.Embed(title=f"**Income Roles List [{page}]:**", description=description, color=color)
			await ctx.channel.send(embed=embed)

		return "success", "success"

	#
	# ROLE INCOMES - UPDATE INCOMES - globally (daily income)
	#

	async def update_incomes(self, ctx):
		# we check each role object and then look, what role everyone has and update accordingly.

		# moderator can choose to also set accumulation (i.e.: called 2 days ago, now again = 2 payments) to false.
		# if its value is true, everyone just gets 1 income payment per role
		reset_status = self.execute(
			"SELECT var_value FROM variables WHERE var_name = ?",
			("income_reset", )
		).fetchone()["var_value"]

		# inform that we're starting
		await ctx.channel.send(f"```\nStarting global income update with income_reset set to {reset_status}...\n"
						   f"This may take some time to complete.\n```")

		# get all roles
		all_income_roles = self.get_all_income_roles()
		# log errors when trying to fetch roles through discord API
		role_error = 0
		# init a grouped msg
		block = ""
		# init a grouped sqlite update
		grouped_update = []

		# calculate time
		last_global_income_update_row = self.execute(
			"SELECT var_value FROM variables WHERE var_name = ?",
			("last_global_income_update", )
		).fetchone()
		reset_time = datetime.min.time()
		now = datetime.now()

		if last_global_income_update_row is None or last_global_income_update_row[0] is None:
			# emergency ! we never updated all incomes. Set date to yesterday, so that everyone can collect.
			last_global_income_update = datetime.combine(now.date() - timedelta(days=1), reset_time)
		else:
			last_global_income_update_str = last_global_income_update_row[0]
			last_global_income_update = datetime.strptime(last_global_income_update_str, "%Y-%m-%d %H:%M:%S.%f")

		days_passed = (now - last_global_income_update).days

		# go through the roles
		for index, role in enumerate(all_income_roles, start=1):
			role_id = role["role_id"]
			role_income = role["role_income"]

			# see info for the .execute(SELECT income_reset) above
			income_total = role_income * days_passed if reset_status.lower() == "false" else role_income

			# now get the role object and then update each member who has the role
			role_obj = discord.utils.get(ctx.server.roles, id=int(role_id))
			if not role_obj:
				role_error += 1
				continue

			# go through all the server members who have that role
			for member in role_obj.members:
				# used to create the user in case he wasn't registered yet
				uid_obj = await self.get_user_object(member.id)
				uid = uid_obj["user_id"]

				# append our grouped sqlite update
				grouped_update.append((income_total, uid))

			block += (f"`[{index}/{len(all_income_roles)}]` @{role_obj.name}, "
					  f"you have received your income ({self.currency_symbol} "
					  f"{self.format_number_separator(income_total)}) !\n")

			# avoid "too many requests" errors in case we have a lot of roles and API requests.
			# small pause every 5 runs
			if index % 5 == 0:
				# send te block
				await ctx.channel.send(block)
				# reset block
				block = ""
				# little timeout
				await asyncio.sleep(0.3)

		# flush block.
		if block:
			await ctx.channel.send(block)

		# update last_global_income_update
		new_midnight = datetime.combine( now.date(), reset_time )
		# format to string with microseconds, else there is inconsistency in the way we save time strings.
		new_midnight_formatted = str(new_midnight.strftime("%Y-%m-%d %H:%M:%S.%f"))
		await self.execute_commit(
			"UPDATE variables SET var_value = ? WHERE var_name = ?",
			(new_midnight_formatted, "last_global_income_update")
		)

		# actually make the update of each balance in the database
		command = "UPDATE users SET bank = bank + ? WHERE user_id = ?"
		await self.executemany_by_chunks(command, grouped_update)


		if role_error == 0:
			return "success", "success"
		else:
			return "error", (f"error for `{role_error} role(s)` (maybe the role was deleted on the server"
							 f"but not in the database)\n Else the command ran through "
							 f"({len(all_income_roles)-role_error} successes).")

	#
	# SOLO ROLE INCOME - UPDATE INCOMES SOLO - GET SALARY - COLLECT
	#

	async def update_incomes_solo(self, ctx):

		# create role in case he isn't registered yet
		await self.get_user_object(ctx.user)

		# GLOBAL RESET TIME.	Examples: midnight, 8am, 7pm...
		# reset_time = time(hour=8)
		reset_time = datetime.min.time()


		# in contrary to update_incomes, where one admin updates all incomes,
		# this function will let each user collect his own income by himself.
		# if income_reset (in table variables) is set to true, he can only get 1 full payment (1 income per role).
		# if set to false, he can collect all the income he "missed" since the last time he collected.

		# important notice: for income_reset = true, we don't simply let each user wait 24h and then collect again.
		# rather, we set a global reset time. So if the reset time is at 23h (whatever timezone the bot is in),
		# then every can collect at 22h59 and at 23h01. It makes the checks easier on our side
		# and is more user-friendly and aesthetic. In the end, every user still has 24h to collect his income.
		# the "global collect time" is stored in table variables as "common_reset_time"

		# functioning: get all roles the user has, check for matching roles in income_roles table, update income.
		# also make a nice embedded message.

		# edit: there was a huge unseen bug before. I set a "global_collect" date, but it wasn't actually global.
		# it just reset, everytime someone was able to collect his income. So if someone collected at 22h00
		# everyone had to wait until the next day at 22h00. But if the first guy on this "new day" only collected at
		# say 23h, well the collect time for next day was now 23h next day. Meaning we lost an hour of money lol.
		# fix --> check and eventually set a global collect date everytime this function is called.

		now = datetime.now()
		# date turns year-month-day hours-minutes-seconds to just year-month-day.
		today = now.date()
		# global collect date
		lgc_str = self.execute(
			"SELECT var_value FROM variables WHERE var_name = ?",
			("common_reset_time", )
		).fetchone()
		if lgc_str is None or lgc_str["var_value"] is None:
			# emergency ! we never collected. Set date to yesterday, so that everyone can collect.
			last_global_collect = datetime.combine(now.date() - timedelta(days=1), reset_time)
		else:
			lgc_str = lgc_str["var_value"]
			last_global_collect = datetime.strptime(lgc_str, "%Y-%m-%d %H:%M:%S.%f")
		last_global_collect_day = last_global_collect.date()

		# if new day since last time
		if today > last_global_collect_day:
			# reset to midnight (.min.time() sets to midnight)
			new_midnight = datetime.combine( now.date(), reset_time )
			# format to string with microseconds, else there is inconsistency in the way we save time strings.
			new_midnight_formatted = str(new_midnight.strftime("%Y-%m-%d %H:%M:%S.%f"))
			await self.execute_commit(
				"UPDATE variables SET var_value = ? WHERE var_name = ?",
				(new_midnight_formatted, "common_reset_time")
			)

		# when the user last collected
		lsc_str = self.execute(
			"SELECT last_single_collect FROM users WHERE user_id = ?",
			(ctx.user, )
		).fetchone()["last_single_collect"]
		# returns None if we never collected before, so we can safely go ahead and let them collect.
		if not lsc_str or lsc_str.lower() == "none":
			last_single_collected = datetime.combine(now.date() - timedelta(days=1), reset_time)
			new_day = True
		# only else we check time.
		else:
			last_single_collected = datetime.strptime(lsc_str, "%Y-%m-%d %H:%M:%S.%f")
			# calculate difference. If he last collected BEFORE today, then he can collect.
			new_day = last_single_collected.date() < last_global_collect.date()

		# return and inform if not new_day (i.e. payout date not yet reset)
		# else: payout date has not yet reset.
		if not new_day:
			# until midnight (datetime.combine) until next day (timedelta(days=1)).
			next_reset_time = datetime.combine(now.date(), reset_time) + timedelta(days=1)
			time_remaining = next_reset_time - now
			# need to work with seconds because timedelta only gives days, seconds, microseconds, not hours and minutes.
			formatted_time_remaining = f"{time_remaining.seconds // 3600 :02}:{(time_remaining.seconds % 3600) // 60 :02}"
			await ctx.channel.send(f"`⌛ You already collected! Reset in: {formatted_time_remaining} hours.`")
			return "success", "success"

		# else we can start collecting income !

		# get an "all roles" dict directly to make less database requests.
		all_income_roles = self.get_all_income_roles()

		# check for matches
		matching_roles = [ role for role in all_income_roles if role["role_id"] in ctx.user_roles ]

		# inform if there are no matching roles return.
		if not matching_roles:
			await self.send_confirmation(ctx, "`You have no income role !`", color="blue",
										 footer="You can try again with an income role.")
			return "success", "success"

		# get income reset value
		income_reset = self.execute(
			"SELECT var_value FROM variables WHERE var_name = ?",
			("income_reset",)
		).fetchone()["var_value"]
		if income_reset.lower().strip() == "true":
			# only get 1 times your income.
			payment_multiplier = 1
		else:
			days_passed = ( last_global_collect - last_single_collected ).days
			if days_passed < 0: days_passed = 0
			# every income multiplied by the amount of days you didn't collect.
			payment_multiplier = days_passed

		# get the role objects for the matching roles (for a role.mention in the embed)
		role_objects = {}
		for role in matching_roles:
			obj = discord.utils.get(ctx.server.roles, id=role["role_id"])
			role_objects[ role["role_id"] ] = obj

		# now get the new income and format an embed.
		total_new_income = 0

		# init embed
		embed = discord.Embed(title="payday!", color=self.discord_blue_rgb_code)
		embed.set_author(name=ctx.username, icon_url=ctx.user_pfp)

		final_report = ""

		for index, role in enumerate(matching_roles, start=1):
			amount = role["role_income"]
			final_report += (f"`{index}` - "
							 f"{role_objects[role['role_id']].mention}\t"
							 f"{self.currency_symbol} {amount} x {payment_multiplier} = {amount * payment_multiplier}\n")
			total_new_income += amount * payment_multiplier

		# update balance in database
		await self.execute_commit(
			"UPDATE users SET bank = bank + ? WHERE user_id = ?",
			(total_new_income, ctx.user)
		)
		# update the collect time in database
		await self.execute_commit(
			"UPDATE users SET last_single_collect = ? WHERE user_id = ?",
			(str(now), ctx.user)
		)

		# add a total income info to the embed.
		# adjust description for income_reset = False
		if income_reset:
			description = (f"{self.worked_emoji} Received {payment_multiplier} days' income: "
						   f"{self.currency_symbol} {self.format_number_separator(total_new_income)}\n\n")
		else:
			description = (f"{self.worked_emoji} Received income: {self.currency_symbol} "
						   f"{self.format_number_separator(total_new_income)}\n\n")
		# add the actual report.
		full_report = description + final_report

		await self.send_confirmation(ctx, full_report, color="blue", footer="CURR_TIME")

		return "success", "success"

	#
	# COMMON ROLE BALANCE FUNCTION
	#

	async def change_balance_by_role(self, ctx, income_role, amount, mode):

		if mode not in {"add", "remove"}:
			raise ValueError("Mode needs to be add or remove [at function change_balance_by_role(self, ...)].")

		# we get the role object, then we check each member who has the role and remove them the amount.

		role_obj = discord.utils.get(ctx.server.roles, id=income_role)

		if not role_obj:
			return "error", f"{self.error_emoji} Role not found."

		all_income_roles = self.get_all_income_roles()

		role = [ r[income_role] for r in all_income_roles if r["role_id"] == income_role]

		if not role:
			return "error", f"{self.error_emoji} Role exists, but not registered as income role in database."

		all_role_members = [ member.id for member in role_obj.members ]

		# because we use executemany below and executemany requires a list of tuples.
		all_changes = []

		# for better performance, we use asyncio.gather. It executes the SQLite queries parallely
		# and does not require to await self.get_user_object for every user (also: no need for an extra await here !)
		all_user_data = await asyncio.gather( *(self.get_user_object(user) for user in all_role_members) )

		for user_id, user_object in zip(all_role_members, all_user_data):

			user_bank = user_object["bank"]
			user_cash = user_object["cash"]
			user_balance = user_bank + user_cash

			if mode == "remove":
				if user_balance - amount < 0:
					# set bank to negative of what user has in cash.
					# allows us to still just edit bank variable and not bank and cash.
					user_bank = -user_cash
				else:
					user_bank -= amount
			elif mode == "add":
				user_bank += amount

			# add the tuple
			all_changes.append( (user_bank, user_id) )

		# execute in batches
		query = "UPDATE users SET bank = ? WHERE user_id = ?"
		await self.executemany_by_chunks(query, all_changes)

		return len(all_role_members)


	#
	# REMOVE MONEY BY ROLE / ADD MONEY BY ROLE (remove/add money from all users with the role)
	#

	async def handle_money_by_role(self, ctx, income_role, amount, mode):

		if mode not in ["add", "remove"]:
			raise ValueError("Mode for handling_money_role needs to be add or remove.")

		executed_instances = await self.change_balance_by_role(ctx, income_role, amount, mode=mode)

		# inform user
		done = "removed" if mode == "remove" else "added"
		msg = (f"{self.worked_emoji} You have {done} {self.currency_symbol} {self.format_number_separator(amount)} "
			   f"from a total of {self.format_number_separator(len(executed_instances))} users with that role !")
		await self.send_confirmation(ctx, msg)

		return "success", "success"


	"""
	STATISTICS AND SERVER WIDE USER FUNCTION (Purge, leaderboard)
	"""

	#
	# REMOVE USERS / REMOVE GONE USERS / CLEAN LEADERBOARD / CLEAN DATABASE
	#

	async def clean_database(self, server):
		# we will remove all users from the users table but also from the income roles table.
		amount_removed = 0

		# all members who are currently on the server
		# using a set comprehension (only adds each ID once; could also use list comprehension tho, since ID is unique)
		current_member_id = {str(member.id) for member in server.members}
		# all users who are registered in the bot.
		# fetchall() returns a tuple, so we will only use (id, ) later.
		all_users_id = self.execute("SELECT user_id FROM users").fetchall()
		# will be a list of tuples for executemany at the end.
		users_to_remove = []
		# run through the list
		for (user_id, ) in all_users_id:
			if user_id not in current_member_id:
				# pass as tuple executemany awaits a list of tuples and not just a list.
				users_to_remove.append( (user_id, ))
				amount_removed +=1

		# update database.
		# Thanks to ON DELETE CASCADE, this will also remove their entries in user_items and user_used_items
		query = "DELETE FROM users WHERE user_id = ?"
		await self.executemany_by_chunks(query, users_to_remove)

		# close, return the amount of users removed
		return "success", amount_removed

	#
	# LEADERBOARD
	#

	async def leaderboard(self, ctx, full_name, page_number, mode):
		# get data from all users:
		# get the money data
		if mode == "-cash":
			raw_balances = self.execute("SELECT cash FROM users").fetchall()
		elif mode == "-bank":
			raw_balances = self.execute("SELECT bank FROM users").fetchall()
		else: # elif mode == "-total":
			raw_balances = self.execute("SELECT cash + bank FROM users").fetchall()

		if not raw_balances:
			return "error", "no user created to show leaderboard !"

		# unpack values since fetchall() returns tuples (like this: ((a, ...), (b, ...) ...)
		all_bal = [bal[0] for bal in raw_balances]

		# get the user data and unpack the id's
		raw_users = self.execute("SELECT user_id FROM users").fetchall()
		all_users = [row[0] for row in raw_users]

		# --> data is set, now sort

		# zip gives us a list of [ (user1_id, user1_bal) ... ] so we can grab bal for each user by x[1]
		combined_list = list(zip(all_users, all_bal))


		# now sort(key, ...) will sort it as such:
		#  - reverse = True to show the highest values (highest bal) first for leaderboard.
		#  - lambda x: x[1] is an inline function for def returnX(x): return x[1]
		#    in this case: x[1] will be the balance, which is what we want to sort our values as.

		combined_list.sort(key=lambda x: x[1], reverse=True)

		# unpack list with zip unpack operator, gives us 2 lists again, but now in the right order.
		all_users, all_bal = zip(*combined_list)
		# back to list so we can edit the info later.
		all_users = list(all_users) ; all_bal = list(all_bal)

		# info: in old json version, we fetched the user nickname everytime we built the leaderboard.
		# now we save it in the users table. It gets added the first time, when a user is created.
		# and then it updates everytime the user calls "balance"
		# btw: I decided against making it automatically when a user changes his nickname,
		# which can be caught through main.py.
		# but if a lot of users are inactive anyway, it would be lost resources to change nicknames of these people.
		# so the bot does check more often if the nickname changed, but less database operations to change the nickname.
		# someone who does not call his balance often will probably not care about leaderboard as well.

		# default user lb position. Will be kept, if we don't find him (unlikely).
		user_lb_position = 10000

		# use names instead of just ID, except if we cannot find names
		# so for example if someone left the server
		for i, user_id in enumerate(all_users):
			result = self.execute(
				"SELECT user_discord_nick FROM users WHERE user_id = ?",
				(user_id,)).fetchone()
			if result:
				cached_nickname = result["user_discord_nick"]
			# else: if none found in the database, fetchone returns None
			else:
				cached_nickname = str(user_id)

			if user_id == ctx.user:
				# the position our user is at in the leaderboard
				user_lb_position = i + 1

			# update
			all_users[i] = cached_nickname

		# making nice number formats
		for i in range(len(all_bal)):
			all_bal[i] = self.format_number_separator(all_bal[i])

		# 10 ranks per page
		ranks_per_page = 10
		# ceil gives us next number (29.02 = 30 pages)
		page_count = math.ceil(len(all_bal) / ranks_per_page)

		# getting page number
		if page_count == 1:
			page_number = 1
		# if he wants page 2000 but there is only 1 page
		if page_number > page_count or page_number < 1:
			page_number = 1

		# our selection !
		index_start = (page_number - 1) * ranks_per_page
		index_end = index_start + ranks_per_page
		user_selection = all_users[index_start: index_end]
		bal_selection = all_bal[index_start: index_end]

		# making the formatted !
		if page_number == 1:
			i = 0
		else:
			"""
			this is because if we call page 2 we wanna start at 20
			edit (26.04.24): page 2 should be starting at 10 obviously lol, 3 starts at 2.
			without this we would have 1-10 on page 1 and then 21-30 on page 2.
			"""
			i = (page_number - 1) * ranks_per_page

		leaderboard_formatted = f""
		for i_i in range(len(user_selection)):
			leaderboard_formatted += (f"\n**{str(i + 1)}.** {user_selection[i_i]}"
									  f" • {str(self.currency_symbol)} {bal_selection[i_i]}")
			i += 1

		# inform user
		color = self.discord_blue_rgb_code
		embed = discord.Embed(description=f"\n\n{leaderboard_formatted}", color=color)

		embed.set_author(name=full_name,
						 icon_url=ctx.server.icon.url if ctx.server.icon else None)
		if user_lb_position == 1:
			pos_name = "st"
		elif user_lb_position == 2:
			pos_name = "nd"
		elif user_lb_position == 3:
			pos_name = "rd"
		else:
			pos_name = ""
		# position - 1 because if we are at position 1, and we do 1 // 0, we would get 0 instead of page 1.
		# and + 1 page at the end because in our calculation, we omit that lb starts at page 1 and not 0.
		user_page = (user_lb_position - 1) // ranks_per_page + 1

		embed.set_footer(
			text=f"Page {page_number}/{page_count}  •  Your leaderboard rank: {user_lb_position}{pos_name}."
				 f"\nUse +lb {user_page}")

		# TODO - add arrows to move through pages
		# lb_object = LeaderboardViewer(  )

		await ctx.channel.send(embed=embed) # (embed=embed, view=lb_object)

		return "success", "success"

	#
	# ECONOMY STATS
	#

	async def economy_stats(self, ctx):
		# load json

		# before, we did SELECT * FROM users,
		# then we looped through users and added their cash and bank and third for total_total we added all.
		# with SQLite, it is now easier.
		stats = self.execute("SELECT SUM(cash) AS total_cash, SUM(bank) AS total_bank FROM users").fetchone()

		total_cash = stats["total_cash"] or 0
		total_bank = stats["total_bank"] or 0
		total_total = total_cash + total_bank

		# inform user
		color = self.discord_blue_rgb_code
		embed = discord.Embed(color=color)
		embed.add_field(
			name=f"🪙 **Total:**  {self.format_number_separator(total_total)}",
			value=f"",
			inline=False
		)
		embed.add_field(
			name=f"🏦 **Total Bank:**  {self.format_number_separator(total_bank)}",
			value=f"",
			inline=False
		)
		embed.add_field(
			name=f"💵 **Total Cash:**  {self.format_number_separator(total_cash)}",
			value=f"",
			inline=False
		)
		embed.set_author(
			name="Economy Stats",
			icon_url="https://upload.wikimedia.org/wikipedia/commons/5/5e/Map_symbol_museum_02.png"
		)
		await ctx.channel.send(embed=embed)

		return "success", "success"


	"""
	LEVELS
	"""


	"""
	Gaining XP.
	"""

	#
	# CHECK IF DELAY RAN OUT
	#

	def check_xp_delay(self, last):
		try:
			now = datetime.now()
			# get a time object from the string
			last_run = datetime.strptime(last, '%Y-%m-%d %H:%M:%S.%f')
			# calculate (this is more precise than seconds // 60 > delay)
			return (now - last_run).total_seconds() > self.xp_and_passive_income_delay * 60
		except Exception as e:
			print(f"Error when checking xp delay (skipping & trying fix), error code: {e}")
			# in any case, just return True.
			# it will set the time variable again anyway, which will fix it.
			return True

	#
	# LEVELER - HANDLE XP / GAIN XP AND PASSIVE CHAT INCOME PER MESSAGE
	#

	async def handle_message_xp_and_passive_income(self, ctx, user):
		# don't do troubles during database setup.
		if not self.db_set_up: return None, None

		# don't gain xp if there are no levels set up.
		# but still gain passive chat income.
		any_levels = self.execute(
			"SELECT * FROM levels"
		).fetchone()

		# check if right channel first
		if self.channels_level_mode == "include" and ctx.channel.id not in self.channels_level_handling:
			return "success", "success"
		elif self.channels_level_mode == "exclude" and ctx.channel.id in self.channels_level_handling:
			return "success", "success"

		last_counted_message = self.execute(
			"SELECT last_xp_collect FROM users WHERE user_id = ?",
			(user, )
		).fetchone()

		if not last_counted_message:
			await self.get_user_object(user)
			last_counted_message = self.execute(
				"SELECT last_xp_collect FROM users WHERE user_id = ?",
				(user, )
			).fetchone()

		last_counted_message_string = last_counted_message["last_xp_collect"]

		if last_counted_message_string != "none":
			delay_passed = self.check_xp_delay(last_counted_message_string)
		else:
			delay_passed = True

		# delay is both for xp and passive chat income.

		if not delay_passed:
			return "success", "success"

		# else: delay passed.

		# only gain xp if there are any levels
		if any_levels:
			# add the xp (also automatically calculates if new level)
			await self.change_user_xp(ctx, user, self.xp_per_msg, "add")

		# also PASSIVE INCOME !
		if self.passive_income_per_msg > 0:
			await self.change_balance(user, self.passive_income_per_msg, "bank", mode="add")

		# update last xp / passive chat income collect date.
		await self.execute_commit(
			"UPDATE users SET last_xp_collect = ? WHERE user_id = ?",
			(datetime.now(), user)
		)

		await self.calculate_current_level_simple(ctx, user)

		return "success", "success"


	"""
	Level calculations (current level, level rewards...)
	"""

	#
	# CALCULATE CURRENT LEVEL (and update his new level in the database)
	# (simple means it is calculated through SQLite directly)

	async def calculate_current_level_simple(self, ctx, user, auto_update=True):
		# create if not exist
		await self.get_user_object(user)
		# get xp
		row = self.execute(
			"SELECT current_xp_level, total_xp FROM users WHERE user_id = ?",
			(user,)
		).fetchone()

		if row is not None:
			user_level, user_xp = row
		else:
			user_xp = 0 ; user_level = 0

		# we should change this if working with multiple users at once, but for one user this will do.
		# order by descending so that we catch the first ("LIMIT 1") level we actually reached the xp for.
		row = self.execute(
			"SELECT level_number FROM levels WHERE level_xp <= ? ORDER BY level_xp DESC LIMIT 1",
			(user_xp, )
		).fetchone()
		current_level = row["level_number"] if row else 0

		# we set user_lvl in each user row instead of calculating it everytime.
		if not auto_update:
			return None, None

		# if the user was removed XP through the remove-xp command,
		# then we also want to decrease his level again.
		if current_level > user_level or current_level < user_level:
			await self.execute_commit(
				"UPDATE users SET current_xp_level = ? WHERE user_id = ?",
				(current_level, user)
			)
			await self.level_up(ctx, current_level)

		next_level_xp = self.execute(
			"SELECT level_xp FROM levels WHERE level_number = ?",
			(current_level+1,)
		).fetchone()

		if not next_level_xp:
			return current_level, "highest level reached."

		next_level_xp = next_level_xp["level_xp"] if next_level_xp else 0
		# if we're already at the top, it may return a negative value. So put to 0 at least.
		xp_remaining = max(0, next_level_xp - user_xp)

		return current_level, xp_remaining

	#
	# GET LEVEL REWARD
	#

	def get_level_reward(self, level_number):
		# get the rewards.
		rewards_row = self.execute(
			"SELECT * FROM level_rewards WHERE level_number = ?",
			(level_number,)
		).fetchone()

		rewards_row = rewards_row if rewards_row else None

		if not rewards_row:
			return None, None, None, None

		# money: amount or 0
		reward_money = rewards_row["reward_money"]

		# items: list of item names or list with "none"
		reward_items = json.loads(rewards_row["reward_items"])
		if reward_items == ["none"]:
			reward_items = None
		else:
			items_dictionary = {}
			for item in reward_items:
				name = item["item_name"]
				amount = item["amount"]
				items_dictionary[name] = amount
			reward_items = items_dictionary

		# roles: list of roles that are going to be added or removed
		reward_roles_given = json.loads(rewards_row["reward_roles_given"])
		if reward_roles_given == ["none"]:
			reward_roles_given = None
		# you can choose to remove certain roles at certain levels (for example, add "pro" and remove role "rookie").
		reward_roles_removed = json.loads(rewards_row["reward_roles_removed"])
		if reward_roles_removed == ["none"]:
			reward_roles_removed = None

		return reward_money, reward_items, reward_roles_given, reward_roles_removed

	#
	# LEVEL UP MESSAGE
	#

	async def level_up(self, ctx, new_level):
		user_obj = ctx.user_ctx_obj

		# get the rewards
		money, items, add_roles, remove_roles = self.get_level_reward(new_level)

		# add money
		await self.change_balance(ctx.user, money, "bank", "add")

		# add the items

		if items:
			item_msg = "\n".join(f"• {item_name}: {amount}" for item_name, amount in items.items())
			for item_name, amount in items.items():
				await self.safe_items_update("user_items", ctx.user, item_name, amount, mode="add")
		else:
			item_msg = None

		# add the roles
		added_roles_mention = await self.utils.add_or_remove_roles_user(
			ctx, user_obj, add_roles, mode="add", verbose=True
		) if add_roles else None

		# remove the roles
		removed_roles_mention = await self.utils.add_or_remove_roles_user(
			ctx, user_obj, remove_roles, mode="remove", verbose=True
		) if remove_roles else None

		embed = None
		if money or items or added_roles_mention or removed_roles_mention:
			embed = discord.Embed(color=self.discord_blue_rgb_code)

			embed.title = "You received:"

			if money > 0:
				embed.add_field(name= "💰 Money", value=f"{self.currency_symbol} {money}.", inline=False)
			if items:
				embed.add_field(name="📦 Items", value=f"{item_msg}", inline=False)
			if added_roles_mention:
				role_mentions = " ".join(role.mention for role in added_roles_mention)
				embed.add_field(name="🎁 Given roles", value=role_mentions, inline=False)
			if removed_roles_mention:
				role_mentions = " ".join(role.mention for role in removed_roles_mention)
				embed.add_field(name="❌ Removed roles", value=role_mentions, inline=False)

		# send congratulation
		msg = f"GG {ctx.user_mention}, you just levelled up to **level {new_level}** !"

		if self.channel_level_info:
			await self.channel_level_info.send(msg)
			if embed: await self.channel_level_info.send(embed=embed)
		else:
			await ctx.channel.send(msg)
			if embed: await ctx.channel.send(embed=embed)

		return

	"""
	Commands the user calls
	"""

	#
	# CHECK CURRENT LEVEL - CHECK LEVEL
	#

	# show own current level.
	async def check_current_level(self, ctx, user):
		current_level, remaining_xp = await self.calculate_current_level_simple(ctx, user)

		total_xp = self.execute(
			"SELECT total_xp FROM users WHERE user_id = ?",
			(user,)
		).fetchone()

		total_xp = total_xp["total_xp"] if total_xp else "error"

		description = (f"🎯 **Current Level:** `Level {current_level}`.\n"
					   f"✨ **Total XP:** `{total_xp}`\n"
					   f"📈 **XP left to level {current_level + 1}:** `{remaining_xp}`")

		await self.utils.send_embed(ctx, description, None, "blue", name=True)

		return "success", "success"

	#
	# ADD XP / REMOVE XP
	#

	async def change_user_xp(self, ctx, user, amount, mode):
		if mode not in ["add", "remove"]: raise ValueError("mode for change_user_xp(self, ...) must be add or remove")

		# create user if not created.
		await self.get_user_object(user)

		operator = "+" if mode == "add" else "-"
		# COALESCE means that it sets to 0 if it was NULL. But we default total_xp to 0 at user creation anyway,
		# so it shouldn't be a big problem.
		await self.execute_commit(
			f"UPDATE users SET total_xp = COALESCE(total_xp, 0) {operator} ? WHERE user_id = ?",
			(amount, user)
		)

		await self.calculate_current_level_simple(ctx, user, auto_update=True)

		await self.send_confirmation(ctx, f"{'Added' if mode == 'add' else 'Removed'} {amount} xp {'to' if mode == 'add' else 'from'} user.")

		return "success", "success"

	#
	#    LIST ALL LEVELS
	#

	async def list_all_levels(self, ctx, mode="levels"):

		# all levels
		levels_row = self.execute("SELECT * FROM levels").fetchall()

		levels_and_xp = None

		if levels_row:
			levels_and_xp = {}
			for level in levels_row:
				level_number = level["level_number"]
				levels_and_xp[level_number] = level["level_xp"]

		if mode == "all":
			embed = discord.Embed(title="Level channels:", color=self.discord_blue_rgb_code)
			embed.description = (f"Mode: {self.channels_level_mode}.\n"
								 f"Channels: {' '.join(r.mention for r in self.level_channel_objects)}")
			await ctx.channel.send(embed=embed)

		if not levels_and_xp:
			await ctx.channel.send(f"{self.error_emoji} You don't have any levels set up yet !")
			return "success", None

		# sort levels (x[0] is the level number)
		sorted_levels = sorted(levels_and_xp.items(), key=lambda x: int(x[0]))

		# calculate how many pages we will need
		number_of_levels = len(sorted_levels)
		max_per_embed = 10
		# we could also do lvls // max and then if lvls % max total +=1, but this seems cleaner
		total_pages = math.ceil(number_of_levels / max_per_embed)

		for page in range(total_pages):
			embed = discord.Embed(
				title=f"Levels (page {page+1}/{total_pages})",
				color=self.discord_blue_rgb_code
			)

			# get only the levels for this page
			start_index = page * max_per_embed
			end_index = start_index + max_per_embed
			current_level = sorted_levels[start_index:end_index]

			for level_number, xp in current_level:

				# get the rewards
				money, items, add_roles, remove_roles = self.get_level_reward(level_number)

				# items
				item_msg = "\n".join(f"• {item_name}: {amount}" for item_name, amount in items.items()) if items else "—"

				# given roles
				added_roles_mention = await self.utils.add_or_remove_roles_user(
					ctx, user_object=None, roles=add_roles, mode="add", verbose=True
				) if add_roles else None
				if added_roles_mention:
					added_roles_mention_str = ", ".join(role.mention for role in added_roles_mention)
				else:
					added_roles_mention_str = "—"

				# remove roles
				removed_roles_mention = await self.utils.add_or_remove_roles_user(
					ctx, user_object=None, roles=remove_roles, mode="remove", verbose=True
				) if remove_roles else None
				if removed_roles_mention:
					removed_roles_mention_str = ", ".join(role.mention for role in removed_roles_mention)
				else:
					removed_roles_mention_str = "—"

				reward_info = f"✨ xp for level: {xp}.\n"
				# also say if the money to receive is 0
				reward_info += f"Money: {self.currency_symbol} {money}.\n"
				reward_info += f"Items: {item_msg}.\n"
				reward_info += f"Given roles: {added_roles_mention_str}\n"
				reward_info += f"Removed roles: {removed_roles_mention_str}\n"

				embed.add_field(
					name=f"⏫ Level {level_number}",
					value=reward_info,
					inline=False
				)
				# buffer
				embed.add_field(name="", value="", inline=False)

			# flush
			await ctx.channel.send(embed=embed)

		return "success", "success"

	#
	#    LEVEL LEADERBOARD
	#

	async def level_leaderboard(self, ctx, page_number):

		# info: this is a mashed up and revisited version of the normal leaderboard(self, ...) function here.

		all_rows = self.execute(
			"SELECT current_xp_level, total_xp FROM users"
		).fetchall()

		if not all_rows:
			return "error", "no users created yet !"

		# unpack values since fetchall() returns tuples
		all_levels = [row[0] for row in all_rows]
		all_total_xp = [row[1] for row in all_rows]

		# get the user data and unpack the id's
		raw_users = self.execute("SELECT user_id FROM users").fetchall()
		all_users = [row[0] for row in raw_users]

		# zip gives us a list of [ (user1_id, user1_bal) ... ] so we can grab bal for each user by x[1]
		combined_list = list(zip(all_users, all_total_xp, all_levels))

		combined_list.sort(key=lambda x: x[1], reverse=True)

		# unpack list with zip unpack operator, gives us 2 lists again, but now in the right order.
		all_users, all_total_xp, all_levels = zip(*combined_list)
		# back to list so we can edit the info later.
		all_users = list(all_users) ; all_levels = list(all_levels) ; all_total_xp = list(all_total_xp)

		# default user lb position. Will be kept, if we don't find him (unlikely).
		user_lb_position = 10000

		for i, user_id in enumerate(all_users):
			result = self.execute(
				"SELECT user_discord_nick FROM users WHERE user_id = ?",
				(user_id,)).fetchone()

			cached_nickname = result["user_discord_nick"] if result else str(user_id)

			if user_id == ctx.user:
				# the position our user is at in the leaderboard
				user_lb_position = i + 1

			# update
			all_users[i] = cached_nickname

		# 10 ranks per page
		ranks_per_page = 10
		# ceil gives us next number (29.02 = 30 pages)
		page_count = math.ceil(len(all_levels) / ranks_per_page)

		# getting page number
		if page_count == 1:
			page_number = 1
		# in case he wants page 20 but there are only 10.
		if page_number > page_count or page_number < 1:
			page_number = 1

		# our selection !
		index_start = (page_number - 1) * ranks_per_page
		index_end = index_start + ranks_per_page
		user_selection = all_users[index_start: index_end]
		level_selection = all_levels[index_start: index_end]
		total_xp_selection = all_total_xp[index_start: index_end]

		# making the formatted !
		if page_number == 1:
			i = 0
		else:
			i = (page_number - 1) * ranks_per_page

		leaderboard_formatted = f""
		for i_i in range(len(user_selection)):
			leaderboard_formatted += (f"\n**{str(i + 1)}.** {user_selection[i_i]}"
									  f" • level `{level_selection[i_i]}` • total xp `{total_xp_selection[i_i]}`")
			i += 1

		# inform user
		color = self.discord_blue_rgb_code
		embed = discord.Embed(
			description=f"\n\n{leaderboard_formatted}",
			color=color
		)
		name = f"{ctx.server.name} Level Leaderboard"


		embed.set_author(
			name=name,
			icon_url=ctx.server.icon.url if ctx.server.icon else None
		)
		if user_lb_position == 1:
			pos_name = "st"
		elif user_lb_position == 2:
			pos_name = "nd"
		elif user_lb_position == 3:
			pos_name = "rd"
		else:
			pos_name = ""
		# position - 1 because if we are at position 1, and we do 1 // 0, we would get 0 instead of page 1.
		# and + 1 page at the end because in our calculation, we omit that lb starts at page 1 and not 0.
		user_page = (user_lb_position - 1) // ranks_per_page + 1

		embed.set_footer(
			text=f"Page {page_number}/{page_count}  •  Your leaderboard rank: {user_lb_position}{pos_name}."
				 f"\nUse +lb {user_page}")

		# TODO - add arrows to move through pages
		# lb_object = LeaderboardViewer(  )

		await ctx.channel.send(embed=embed) # (embed=embed, view=lb_object)

		return "success", "success"

	# ------------------------------------
	#    CHANGE LEVELS / UPDATE LEVELS
	# ------------------------------------

	async def change_levels(self, ctx):
		await ctx.channel.send("### Info on current data.")

		# first send current levels, mode set to all to also show channels.
		_, set_levels = await self.list_all_levels(ctx, mode="all")

		# either change level channels or levels or level rewards.

		# modes = ["channels", "levels xp and rewards", "change level xp thresholds only", "change level rewards only"]
		# await ctx.channel.send(
		# 	f"Do you want to change\n[1]: {modes[0]},\n [2]: {modes[1]},\n[3]: {modes[2]},\n[4]: {modes[3]} ? (or cancel)"
		# )
		modes = ["channels", "levels xp and rewards"]

		await ctx.channel.send(
			f"## Starting setup.\nDo you want to change [1]: {modes[0]} or [2]: {modes[1]} ? (or cancel)"
		)

		# first get the info
		mode = None
		while 1:
			user_input = await self.utils.get_user_input(ctx)
			if user_input is None:
				continue

			if user_input == "1":
				mode = "channels"
				break
			elif user_input == "2":
				mode = "levels"
				break
			#elif user_input == "3":
			#	mode = "levels_xp"
			#	break
			#elif user_input == "4":
			#	mode = "reward"
			#	break
			elif user_input in ["cancel", "skip"]:
				return "success", "success"
			else:
				# await self.utils.send_error_report(ctx, "Enter 1, 2, 3, 4 or cancel to cancel.")
				await self.utils.send_error_report(ctx, "Enter 1 or 2 or cancel to cancel.")

		# to change level channels
		if mode == "channels":
			await ctx.channel.send(f"Do you want to change [1]: mode or [2]: channels ? (or cancel)")

			while 1:
				sub_mode = None
				user_input = await self.utils.get_user_input(ctx)
				if user_input is None: continue

				if user_input == "1":
					sub_mode = "mode"
					break
				elif user_input == "2":
					sub_mode = "channels"
					break
				elif user_input in ["cancel", "skip"]:
					return "success", "success"
				else:
					await self.utils.send_error_report(ctx, "Enter 1, 2, or cancel to cancel.")

			if sub_mode == "mode":
				await ctx.channel.send(f"Set mode to include or exclude ? (or cancel)")
				user_input = await self.utils.get_user_input(ctx)

				if user_input not in ["exclude", "include"]:
					await self.utils.send_error_report(ctx, "Wrong input. Command cancelled.")
					return "success", "success"

				# we only have one row there so it's okay
				await self.execute_commit(
					"UPDATE level_channels SET mode = ?",
					(user_input,)
				)

				return "success", "success"

			elif sub_mode == "channels":
				await ctx.channel.send("Ping all channels you want to set.")
				user_input = await self.utils.get_user_input(ctx)

				if user_input is None:
					await self.utils.send_error_report(ctx, "Response time timed out. Cancelling.")
					return "success", "success"

				channels = await self.get_valid_channels(user_input, ctx.channel)
				channels = channels if channels else ["none"]
				new_channels = json.dumps(channels)

				if channels == ["none"]:
					await ctx.channel.send("Info: no valid channels found. Setting channels to none.")

				await self.execute_commit(
					"UPDATE level_channels SET channels = ?",
					(new_channels,)
				)

				await ctx.send(f"{self.worked_emoji} Data has been set up.")

				return "success", "success"

			else:
				return "error", "unknown error."

		# to change the levels completely
		# for this, we always go through every level and set up everything.
		# so everytime is like a complete setup
		if mode == "levels":

			await ctx.channel.send("Do you want to start at level 1 and rewrite/create everything or start at a "
								   "**specific level** ?\nIf yes, just enter **level number**, "
								   "else enter **anything else**.")

			user_input = await self.utils.get_user_input(ctx)

			try:
				user_input = int(user_input)

				# see if we have all items below
				check_level = self.execute(
					"SELECT * FROM levels WHERE level_number = ?",
					(user_input - 1,)
				).fetchone()

				if not check_level:
					await ctx.channel.send("Level does not exist. Moving into new setup.")
					raise ValueError

				level_number = user_input
				last_xp = check_level["level_xp"]

			except Exception as e:
				await ctx.channel.send(
					"```\nWe will now create all levels anew.\n"
					"Enter stop to save created levels cancel to cancel changes completely.\n"
					"You can only enter stop after having finished the current level.\n```")

				level_number = 1
				# to avoid a higher level having lower xp than a lower level.
				last_xp = 0

			# fill first value so that we can loop through it later and start at the level 1 directly.
			# dict will look like this: number : [xp, money, items, roles], [xp, money, items, roles], ...
			final_level_infos = {}

			cancel = False
			stop = False

			to_enter = {
				"level_xp": 0,
				"reward_money": 0,
				"reward_items": ["none"],
				"reward_roles_given": ["none"],
				"reward_roles_removed": ["none"]
			}

			while not cancel:

				await ctx.channel.send(f"`LEVEL {level_number}`.")

				# new level values list, we will write into it with
				final_level_infos[level_number] = []

				# get into it for every level
				while 1:
					if cancel: break

					for key, value in to_enter.items():
						if cancel: break

						while 1:

							if key == "level_xp":

								xp = await self.utils.ask_for_number(
									ctx,
									prompt="Enter xp threshold to reach for this level...",
									min_value=last_xp,
									max_value=None,
									err_prompt="Needs to be higher than xp of levels before."
								)
								# None means cancelled
								if xp is None:
									cancel = True
									break

								# append our final levels list
								final_level_infos[level_number].append(xp)
								last_xp = xp

								break

							elif key == "reward_money":
								money = await self.utils.ask_for_number(
									ctx,
									prompt="Enter money reward for this level (can be 0)."
								)
								# None means cancelled
								if money is None:
									cancel = True
									break

								# append our final levels list
								final_level_infos[level_number].append(money)
								break

							elif key == "reward_items":
								await ctx.channel.send(
									"Enter all item short names and amounts, separated by dashes and spaces, "
									"that you want as reward for this level.\n**Example:** sword-10 fish-3"
									"\nIf you don't want to reward items for this level, enter **none**.")

								user_input = await self.utils.get_user_input(ctx)

								if user_input is None:
									continue

								if user_input == "cancel":
									cancel = True
									break
								if user_input == "none":
									# will be json.dumps() later.
									final_level_infos[level_number].append(["none"])
									break

								items = []
								invalid = False

								for item_str in user_input.split(" "):

									try:
										item_name, item_amount = item_str.split("-")
									except ValueError:
										await self.utils.send_error_report(
											ctx,
											"Invalid item format. Use format like: `sword-10 pistol-3`"
											" (with dash between name and amount)."
										)
										invalid = True
										break

									check = self.execute(
										"SELECT * FROM items_catalog WHERE item_name = ?",
										(item_name,)
									).fetchone()
									if not check:
										await self.utils.send_error_report(
											ctx,
											f"Invalid item name: {item_name}.\n"
											"Enter all names and amounts again, separated by dashes and spaces."
										)
										invalid = True
										# breaks our for loop
										break

									is_num, check_amount = self.utils.check_formatted_number(item_amount)

									if not is_num:
										await self.utils.send_error_report(
											ctx,
											f"Invalid amount for item: {item_name}..\n"
											"Enter all names and amounts again, separated by dashes and spaces."
										)
										invalid = True
										# breaks our for loop
										break

									items.append({"item_name": item_name, "amount": check_amount})

								if invalid:
									continue

								final_level_infos[level_number].append(items)
								break

							elif key in ["reward_roles_given", "reward_roles_removed"]:
								x = "given" if key == "reward_roles_given" else "removed"
								await ctx.channel.send(
									f"Ping all roles that will be {x} when reaching this level.\n"
									f"If you don't want to reward {x} roles for this level, enter **none**.")

								user_input = await self.utils.get_user_input(ctx)

								if user_input is None:
									continue

								if user_input == "cancel":
									cancel = True
									break

								if user_input == "none":
									# will be json.dumps() later.
									final_level_infos[level_number].append(["none"])
									break

								role_ids = self.utils.get_role_id_multiple(user_input)

								if not role_ids:
									await self.utils.send_error_report(
										ctx, "No valid roles found. Setting to none."
									)
									continue

								valid_role_ids = []

								for role_id in role_ids:
									exists = await self.utils.check_if_role_exists(ctx, role_id)
									if exists:
										valid_role_ids.append(role_id)

								if not valid_role_ids:
									await self.utils.send_error_report(
										ctx, "No valid roles found. Setting to none."
									)
									continue
								else:
									final_level_infos[level_number].append(valid_role_ids)
								break

							else:
								break

					if cancel:
						return "error", "cancelled command."

					await ctx.channel.send(
						f"\n{self.worked_emoji} Level {level_number} saved into buffer.\n"
						f"Enter anything to **continue**, **stop** to save entered levels and quit, **cancel** to cancel.")

					user_input = await self.utils.get_user_input(ctx)
					if user_input is None: continue

					if user_input == "cancel":
						cancel = True
						break

					if user_input in ["stop", "save"]:
						stop = True
						break

					break
				level_number += 1

				if cancel:
					return "error", "cancelled command."
				if stop:
					break

			# just as backup
			if cancel:
				return "error", "cancelled command."

			# save set up levels.
			level_numbers = sorted(final_level_infos.keys())
			insert_level_xp = []
			insert_level_reward_money = []
			insert_level_reward_items = []
			insert_level_reward_roles_given = []
			insert_level_reward_roles_removed = []
			for level_num in level_numbers:
				level_data = final_level_infos[level_num]
				# index 0 was the xp
				insert_level_xp.append(level_data[0])
				insert_level_reward_money.append(level_data[1])
				insert_level_reward_items.append( json.dumps(level_data[2]) )
				insert_level_reward_roles_given.append( json.dumps(level_data[3]) )
				insert_level_reward_roles_removed.append( json.dumps(level_data[4]) )

			# execute levels
			await self.executemany_by_chunks(
				"INSERT OR REPLACE INTO levels (level_number, level_xp) VALUES (?, ?)",
				list(zip(level_numbers, insert_level_xp)),
				chunk=500
			)

			insert_rewards = list(zip(
				level_numbers,
				insert_level_reward_money,
				insert_level_reward_items,
				insert_level_reward_roles_given,
				insert_level_reward_roles_removed,
			))

			# execute rewards
			await self.executemany_by_chunks(
				"INSERT OR REPLACE INTO level_rewards "
				"(level_number, reward_money, reward_items, reward_roles_given, reward_roles_removed) "
				"VALUES (?, ?, ?, ?, ?)",
				insert_rewards,
				chunk=500
			)

		await ctx.channel.send("\n## Please reboot the bot for changes to come into effect !")

		return "success", "success"
