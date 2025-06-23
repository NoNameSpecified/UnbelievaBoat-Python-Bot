
"""
INFO:

	The migration script for the Skender discord bot.
	Script is currently for Skender VERSION 2.0 (see last released version on official repo).
	See the version you're using through variable BOT_VERSION in main.py.

	TL;DR:
		do you need this ? Only if you still used the legacy bot with a JSON database.

	Official Repo: https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot

	Long version:
		The old version of this bot used JSON for its database. In 2025, I decided to move it to SQLite.
		However, this means that all old databases also have to be migrated to SQLite.
		This script needs to pay close attention to backwards compatibility, since older
		Skender versions did not have all current functionalities and possible customizations.
		But it is all handled here automatically.

		For the different Skender versions:
			This is built for version 2.0, which is the first version to use SQLite instead of JSON.
			I tried to already build everything that might be needed in the future into the current
			SQLite structure. However, if in the future other customizations get added, the database
			will have to be adapted too.
			Current plan: everytime a new SQLite structure is required, the version will increase.
				e.g.: if a new table or column gets added with an update, it will be Skender v3.0, then v4.0.
				for other updates without changes to the database structure, it would be v2.1, v2.2 etc.
			So keep track of the version you currently use (saved as BOT_VERSION in main.py in the original code).

	If you have any questions, feel free to contact me (see information on the repository or my GitHub profile).

"""

# INFO: strings in SQLite have to be single quote, i.e. 'this', NOT "this".

### "variables" (slut, work, rob, crime) will be in the new SQLite tables "actions" and "action_phrases".
# but it will all be set during walkthrough when launching the bot.
# --> nothing to do here ! (for more info, see function start_migration() below).

### Legacy JSON "Symbols" part, now part of the new table "variables".
# 1. Currency emoji: just set it up again when you set up the new bot.
# 2. income reset: is set to true automatically and also something you can choose during setup.
# 3. global collect: gets set automatically.
# 4. last global income update: gets set automatically.
# --> nothing to migrate here !

### items will be moved to table "items_catalog" and to tables "user_items" and "user_used_items".

### income roles will be moved to table "income_roles".

### userdata will be moved to table users.


import os, sys
# no problems with "import database". Else it throws an error if you call it with a wrong PYTHONPATH (happens with "python main.py").
# I didn't notice the bug at first, because I ran the code through PyCharm directly, which seems to handle it automatically.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse, json, sqlite3, shutil, math
from datetime import datetime

# to create database structure
import database


class SkenderMigration:
	def __init__(self):
		self.db_cursor = None
		self.database = None
		self.json_income_roles = None
		self.json_items = None
		self.json_userdata = None
		self.json_all_data = None
		self.path_to_sqlite = None
		self.path_to_json = None
		self.source_version = None
		self.target_version = None
		self.db_creator = None

	def parse_arguments(self):
		# description gets shown if using python database_migration.py --help.
		parser = argparse.ArgumentParser(description="Migration script from JSON to new SQLite version.")

		parser.add_argument(
			"--source", type=str, required=True, help="Path to old JSON file."
		)
		parser.add_argument(
			"--target", type=str, required=True, help="Path to new JSON file."
		)

		# not required for this first migration script to version v2.0.
		parser.add_argument(
			"--source-version", type=str, required=False, default="legacy", help="Version of old bot (before 2.0 = legacy)."
		)
		parser.add_argument(
			"--target-version", type=str, required=False, default="2.0", help="Version of new bot."
		)

		# parse
		args = parser.parse_args()

		self.path_to_json = args.source
		self.path_to_sqlite = args.target

		if not os.path.exists(self.path_to_json):
			print("Error. Path to JSON file does not exist.")
			quit()

		self.source_version = args.source_version
		self.target_version = args.target_version

	def executemany_by_chunks(self, query, data, chunk=500):
		# index starts at 0, then will be 500, then 1000...
		for index in range(0, len(data), chunk):
			try:
				# execute from 0 to 499, then 500 to 999 etc.
				self.db_cursor.executemany(
					query,
					data[index:index+chunk]
				)
			except Exception as e:
				raise Exception(f"Error updating chunk at {index // chunk}: {e}")
		# commit
		self.database.commit()

	def start_migration(self):
		# create backups
		print("Creating a backup in case anything goes wrong...")
		timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
		directory, original_file = os.path.split(self.path_to_json)
		filename, extension = os.path.splitext(original_file)
		backup_filename = f"{filename}_backup_{timestamp}{extension}"
		backup_path = os.path.join(directory, backup_filename)
		# make copy (in case something goes wrong)
		try:
			shutil.copy(self.path_to_json, backup_path)
		except Exception as e:
			print(f"Error creating backup: {e}. Maybe do a manual backup or rename the original file after finishing this.")
			choice = input("Continue [Y/n] ?")
			choice = choice.lower().strip()
			if choice not in ["n", "no"]:
				print("Exiting... Please also close bot process...")
				quit()

		print(f"Backup complete, saved as {backup_path}.")

		try:
			self.json_all_data = json.load(open(self.path_to_json))
		except json.JSONDecodeError as e:
			print(f"Error while loading JSON: {e}")
			print("Closing migration script. You should probably also stop the bot.")
			quit()

		# "symbols" ! (in new database: variables).
		# --> not done through migration, this will just all be setup at the setup walkthrough
		# also: even tho we will create a database.sqlite, the database handler will still know that it has to
		# go through the set-up walkthrough because there will be no variables set.

		# "variables" (in new database: actions and action_phrases).
		# --> also not backed up.
		#  for the action variables (like the probability to win at crime etc.), the user should set that up during walkthrough.
		#  As for action phrases: I decided against backing those up since the old default phrases were, for some, embarrassing.
		# If you want to back up action_phrases that you created, please do so manually through a sqlite browser
		# or contact me (see repository / my GitHub profile).

		# user data !
		self.json_userdata = self.json_all_data["userdata"]
		# items !
		self.json_items = self.json_all_data["items"]
		# income roles !
		self.json_income_roles = self.json_all_data["income_roles"]

		# create database structure
		self.db_creator = database.SkenderDatabaseCreator(self.path_to_sqlite)
		self.db_creator.create_database()

		# function above closes database, so we need to open it again.
		self.database = sqlite3.connect(self.path_to_sqlite)
		self.db_cursor = self.database.cursor()

	def insert_users(self):
		# Move userdata>>used_items to table "user_used_items".
		# Move userdata>>items to "user_items".

		insert_users_data = []
		insert_user_items_data = []
		insert_user_used_items_data = []

		for user_object in self.json_userdata:
			user_id = user_object["user_id"]
			# could be floats, but need to be integers in new system
			cash = math.ceil(user_object["cash"])
			bank = math.ceil(user_object["bank"])
			# set nickname to user id for now, will be updated for everyone when calling +balance.
			# the other option, fetching all nicknames, would take way too much time
			# and would be complicated to implement since we don't interact with a bot but just database data.
			discord_nick_name = user_id

			# we will not move last_work, last_rob etc., since that has no real impact.
			# everyone will just be able to do it once when the new system is applied.

			# in Legacy Version, there were no levels, so we don't need to move total_xp, current_xp_level.
			# put as tuple directly
			insert_users_data.append( (user_id, discord_nick_name, cash, bank) )

			# now for owned items
			items = user_object["items"]
			if items == "none":
				pass
			else:
				for item in items:
					item_name = item[0]
					item_amount = item[1]
					insert_user_items_data.append( (user_id, item_name, item_amount) )

			# now for used items
			# the problem here is that if there were no used items, it would just be set as "none".
			used_items = user_object["used_items"]
			if used_items == "none":
				pass
			else:
				for item in used_items:
					item_name = item[0]
					item_amount = item[1]
					insert_user_used_items_data.append( (user_id, item_name, item_amount) )

		# put into chunks
		query = "INSERT OR REPLACE INTO users (user_id, user_discord_nick, cash, bank) VALUES (?, ?, ?, ?)"
		self.executemany_by_chunks(query, insert_users_data)

		# put into chunks
		query = "INSERT OR REPLACE INTO user_items (user_id, item_name, amount) VALUES (?, ?, ?)"
		self.executemany_by_chunks(query, insert_user_items_data)

		# put into chunks
		query = "INSERT OR REPLACE INTO user_used_items (user_id, item_name, amount) VALUES (?, ?, ?)"
		self.executemany_by_chunks(query, insert_user_used_items_data)

	def insert_items(self):
		# Compatability problems:
		#	- old items without display name: display name = short name.
		#	- old items without user_pfp.
		#	- old items without excluded roles --> set to "none".
		#	- old items without max_amount --> set to "unlimited".
		#	- old items without max_amount_per_transaction --> set to "unlimited".
		# 	Move: name -> item_name.

		insert_items_data = []

		for item in self.json_items:
			name = item["name"]

			try:
				display_name = item["display_name"]
			except:
				display_name = name

			price = item["price"]
			description = item["description"]
			duration = item["duration"]
			amount_in_stock = item["amount_in_stock"]
			try:
				max_amount = item["max_amount"]
			except:
				max_amount = "unlimited"
			required_roles = item["required_roles"]
			given_roles = item["given_roles"]
			removed_roles = item["removed_roles"]
			try:
				excluded_roles = item["excluded_roles"]
			except:
				excluded_roles = ["none"]
			maximum_balance = item["maximum_balance"]
			reply_message = item["reply_message"]
			expiration_date = item["expiration_date"]
			try:
				item_img_url = item["item_img_url"]
			except:
				item_img_url = "EMPTY"

			# max_amount_per_transaction didn't exist before Skender v2.0
			max_amount_per_transaction = "unlimited"

			insert_items = (
				name, display_name, price, description, duration, amount_in_stock, max_amount,
				max_amount_per_transaction, json.dumps(required_roles), json.dumps(given_roles),
				json.dumps(removed_roles), json.dumps(excluded_roles), maximum_balance, reply_message,
				expiration_date, item_img_url
			)

			insert_items_data.append(insert_items)

		query = """
			INSERT OR IGNORE INTO items_catalog (
				item_name, display_name, price, description, duration,
				amount_in_stock, max_amount, max_amount_per_transaction, required_roles, given_roles,
				removed_roles, excluded_roles, maximum_balance, reply_message,
				expiration_date, item_img_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

		self.executemany_by_chunks(query, insert_items_data)

	def insert_income_roles(self):
		# --> every variable stays the same but last_single_called is removed.
		#	(it was unnecessary and is now saved for every user specifically).
		# we're not moving last_updated --> set to a single last_global_income_update variable
		# instead of having the same last_updated string for every role anyway.

		insert_income_roles_data = []

		for role in self.json_income_roles:
			role_id = role["role_id"]
			role_income = role["role_income"]
			insert_income_roles_data.append( (role_id, role_income) )

		query = f"INSERT OR REPLACE INTO income_roles (role_id, role_income) VALUES (?, ?)"
		self.executemany_by_chunks(query, insert_income_roles_data)

	def close_database(self):
		self.database.commit()
		self.database.close()


if __name__ == "__main__":

	migration_process = SkenderMigration()

	migration_process.parse_arguments()

	print("initiating migration...")
	migration_process.start_migration()
	print("initiation complete")

	print("starting users migration...")
	migration_process.insert_users()
	print("users migration complete")

	print("starting items migration...")
	migration_process.insert_items()
	print("items migration complete")

	print("starting income roles migration...")
	migration_process.insert_income_roles()
	print("income roles migration complete")

	print("closing database...")
	migration_process.close_database()

	print("FINISHED MIGRATING DATABASE.\n\n")
	print("Tip: Delete the database.json file. If anything went wrong, you should still have the backup file.")
	print("If you keep the old database.json file, you will get warning messages everytime you launch the bot.\n")

	input("Enter anything to continue...")

	# either we just stop (if this script was called by itself) or we go back to main process.
	sys.exit()

