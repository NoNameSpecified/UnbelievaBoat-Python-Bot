import json, os, time, random, math, sys, discord, math, asyncio
from datetime import datetime
from datetime import timedelta
import calendar

# custom blackjack game thing
from game_libs.blackjack import blackjack_discord_implementation
# custom roulette game thing
from game_libs.roulette import roulette_discord_implementation

"""

	the database handler of the unbelievaboat-python discord bot
	// is imported by ../main.py

"""


class pythonboat_database_handler:
	# always called when imported in main.py
	def __init__(self, client):
		# we do the path from the main.py file, so we go into the db folder, then select
		self.pathToJson = "database/database.json"
		self.client = client
		# for the json "variables", dont want to make a whole function to find index for variables
		# wont be many anyways. so making it manually
		self.variable_dict = {
			"slut": 0,
			"crime": 1,
			"work": 2,
			"rob": 3
		}

		# for colors
		self.discord_error_rgb_code = discord.Color.from_rgb(239, 83, 80)
		self.discord_blue_rgb_code = discord.Color.from_rgb(3, 169, 244)
		self.discord_success_rgb_code = discord.Color.from_rgb(102, 187, 106)

		# check if file is created, else create it
		if not os.path.exists(self.pathToJson):
			creating_file = open(self.pathToJson, "w")
			# adding default json config into the file if creating new
			# all the users will get created automatically in the function self.find_index_in_db()
			# but for the different jobs etc the program needs configs for variables and symbols
			creating_file.write("""{\n\t"userdata": [],
										"variables":[
											{"name":"slut","delay":15,"min_revenue":50,"max_revenue":400,"proba":50,"win_phrases":["You made","Your dad likes it so much he gives you"],"lose_phrases":["You were fined","Your uncle didn't like the encounter. You pay"],"min_lose_amount_percentage":2,"max_lose_amount_percentage":5},
											{"name":"crime","delay":60,"min_revenue":100,"max_revenue":1200,"proba":30,"win_phrases":["You commited a crime and got","You robbed a bank and got"],"lose_phrases":["You were fined","MacGyver finds you, you pay"],"min_lose_amount_percentage":10,"max_lose_amount_percentage":20},
											{"name":"work","delay":10,"min_revenue":50,"max_revenue":200,"win_phrases":["You worked at SubWay and made","You helped someone do his homework and got"]},
											{"name":"rob","delay":45,"proba":50,"min_gain_amount_percentage":10,"max_gain_amount_percentage":20,"min_lose_amount_percentage":10,"max_lose_amount_percentage":20,"win_phrases":["You robbed and got"],"lose_phrases":["You were caught robbing and have to pay"]}],
										"symbols": [
											{"name":"currency_symbol","symbol_emoji":":dollar:"}
										],
										"items": [
											{}
										],
										"income_roles": [
											{}
										]
										\n}""")
			creating_file.close()

	#

	# check if json file is corrupted
	#  -> in self.check_json()
	# called from main.py

	def get_currency_symbol(self, test=False, value="unset"):
		if not test:
			# get currency symbol to use
			temp_json_opening = open(self.pathToJson, "r")
			temp_json_content = json.load(temp_json_opening)
			# the currency symbol is always at position 0 in the "symbols" part
			currency_symbol = temp_json_content["symbols"][0]["symbol_emoji"]
			#self.currency_symbol = discord.utils.get(self.client.emojis, name=currency_symbol)
			# perhaps currency symbol is too difficult for regular admins to handle, so ill disable it as default.
			self.currency_symbol = "💰"
		else:
			try:
				self.currency_symbol = discord.utils.get(self.client.emojis, name=value)
				print(str(self.currency_symbol))
				if self.currency_symbol == None:
					return "error"
			except:
				return "error"

	# if we handle a already created file, we need certain variables
	async def check_json(self):
		temp_json_opening = open(self.pathToJson, "r")
		temp_json_content = json.load(temp_json_opening)
		"""
		possibly to add :
			improve the error system, raising specific errors with a "error_info"
			for example : "userdata missing", or "slut missing", or even "slut min_revenue missing"
		"""
		try:
			check_content = temp_json_content
			# userdata space
			userdata = check_content["userdata"]
			# variables
			variables = check_content["variables"]
			slut = variables[self.variable_dict["slut"]]
			crime = variables[self.variable_dict["crime"]]
			work = variables[self.variable_dict["work"]]
			rob = variables[self.variable_dict["rob"]]
			# symbol
			currency_symbol = check_content["symbols"][0]
			items = check_content["items"]
			roles = check_content["income_roles"]

			# didnt fail, so we're good
			temp_json_opening.close()
		except Exception as e:
			# something is missing, inform client
			return "error"

	"""
	GLOBAL FUNCTIONS
	"""

	# need to overwrite the whole json when updating, luckily the database won't be enormous
	def overwrite_json(self, content):
		self.json_db = open(self.pathToJson, "w")
		self.clean_json = json.dumps(content, indent=4, separators=(",", ": "))
		self.json_db.write(self.clean_json)
		self.json_db.close()

	# find the user in the database
	def find_index_in_db(self, data_to_search, user_to_find, fail_safe=False):
		user_to_find = int(user_to_find)
		for i in range(len(data_to_search)):
			if data_to_search[i]["user_id"] == user_to_find:
				# print("\nfound user\n")
				return int(i), "none"

		# in this case, this isnt a user which isnt yet registrated
		# but someone who doesnt exist on the server
		# or at least thats what is expected when calling with this parameter
		if fail_safe:
			return 0, "error"

		print("\ncreating user\n")
		# we did NOT find him, which means he doesn't exist yet
		# so we automatically create him
		# edit on 13.02.24: this is fucking useless WTF
		data_to_search.append({
			"user_id": user_to_find,
			"cash": 0,
			"bank": 0,
			# "balance" : cash + bank
			# "roles": "None" ; will be checked when calculating weekly auto-role-income
			"items": "none",
			"used_items": "none",
			"last_slut": "none",
			"last_work": "none",
			"last_crime": "none",
			"last_rob": "none"
		})
		
		"""
			POSSIBLE ISSUE :
				that we need to create user by overwrite, then problem of doing that while another command is
				supposed to have it open etc. hopefully it works just as such
		"""
		# now that the user is created, re-check and return int

		for i in range(len(data_to_search)):
			if data_to_search[i]["user_id"] == user_to_find:
				return int(i), data_to_search

	"""
	CLIENT-DB HANDLING
	"""

	async def blackjack(self, user, bet, bot, channel, username, user_pfp, message):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][user_index]

		# get user stuff
		user_cash = json_user_content["cash"]
		
		if bet == "all":
			bet = user_cash
			if bet < 100:
				return "error", f"❌ Not at least 100 in cash. You currently have {str(self.currency_symbol)} {'{:,}'.format(user_cash)} on hand."
		else:
			bet = int(bet)
		
		if bet > user_cash:
			return "error", f"❌ You don't have that much money in cash. You currently have {str(self.currency_symbol)} {'{:,}'.format(user_cash)} on hand."
		
		# the actual game
		# start it
		startInstance = blackjack_discord_implementation(bot, channel, self.currency_symbol)
		bjPlay = await startInstance.play(bot, channel, username, user_pfp, message, bet)

		if bjPlay == "win":
			json_user_content["cash"] += bet
		elif bjPlay == "blackjack":
			json_user_content["cash"] += bet * 1.5
		elif bjPlay == "loss":
			json_user_content["cash"] -= bet
		elif bjPlay == "bust":
			pass
		else:
			return "error", "❌ error unknown, contact admin"

		# overwrite, end
		json_content["userdata"][user_index] = json_user_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# ROULETTE
	#

	async def roulette(self, user, bet, space, bot, channel, username, user_pfp, mention):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][user_index]

		# get user stuff
		user_cash = json_user_content["cash"]
		
		if bet == "all":
			bet = user_cash
			if bet < 100:
				return "error", f"❌ Not at least 100 in cash. You currently have {str(self.currency_symbol)} {'{:,}'.format(user_cash)} on hand."
		else:
			bet = int(bet)
			
		if bet > user_cash:
			return "error", f"❌ You don't have that much money in cash. You currently have {str(self.currency_symbol)} {'{:,}'.format(user_cash)} on hand."

		# the actual game
		# start it
		startInstance = roulette_discord_implementation(bot, channel, self.currency_symbol)
		roulettePlay, multiplicator = await startInstance.play(bot, channel, username, user_pfp, bet, space, mention)
		# print("done with roulette call")
		# roulettePlay will be 1 for won, 0 for lost
		if roulettePlay:
			json_user_content["cash"] += (bet * multiplicator) - bet
		elif roulettePlay == 0:
			json_user_content["cash"] -= bet
		else:
			return "error", "❌ error unknown, contact admin"

		# overwrite, end
		json_content["userdata"][user_index] = json_user_content
		self.overwrite_json(json_content)
		# print("FINISHED writing")
		return "success", "success"


	
	#
	# SLUT
	#

	async def slut(self, user, channel, username, user_pfp):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][user_index]

		"""
		SPECIFIC TIME ETC
		"""
		# grep values
		slut_data = json_content["variables"][self.variable_dict["slut"]]

		# delay will ALWAYS be in MINUTES
		delay = slut_data["delay"]
		proba = slut_data["proba"]

		time_check = False
		now = datetime.now()
		if json_user_content["last_slut"] == "none":
			# never done it, so go ahead
			time_check = True
		# else, gotta check if enough time passed since last slut
		else:
			last_slut_string = json_user_content["last_slut"]
			# get a timeobject from the string
			last_slut = datetime.strptime(last_slut_string, '%Y-%m-%d %H:%M:%S.%f')
			# calculate difference, see if it works
			passed_time = now - last_slut
			passed_time_minutes = passed_time.total_seconds() // 60.0
			if passed_time_minutes == 0:
				# because of // division it might display 0
				passed_time_minutes = 1
			if passed_time_minutes > delay:
				time_check = True
			else:
				time_check = False
				delay_remaining = delay - passed_time_minutes
		# moving the block here for cleaner code
		if time_check == False:
			color = self.discord_blue_rgb_code
			embed = discord.Embed(description=f"⏱ ️You cannot be a slut for {math.ceil(delay_remaining)} minutes.",
								  color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return "success", "success"
		# else:
			# he can do it

		"""
		ACTUAL FUNCTION
		"""
		# so, explanation :
		# not actually using probabilites or so, just a random number between 1 and 2
		# and if for example probability is 50%, then the random num should be > 1.5 in order to win
		slut_success = random.randint(0, 100)

		if proba < slut_success:
			# LOST

			lose_phrases = random.choice(slut_data["lose_phrases"])
			lose_percentage = random.randint(slut_data["min_lose_amount_percentage"],
											 slut_data["max_lose_amount_percentage"])
			balance = json_user_content["cash"] + json_user_content["bank"]
			loss = balance * (lose_percentage / 100)
			# round up, no floats
			loss = round(loss, 0)
			color = self.discord_error_rgb_code
			embed = discord.Embed(
				description=f"{lose_phrases} {str(self.currency_symbol)} **{'{:,}'.format(int(loss))}**", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			embed.set_footer(text="r.i.p")
			await channel.send(embed=embed)
			json_user_content["cash"] -= loss
			# update last slut time
			json_user_content["last_slut"] = str(now)
			# overwrite, end
			json_content["userdata"][user_index] = json_user_content
			self.overwrite_json(json_content)

			return "success", "success"

		else:
			# SUCCESS
			win_phrases = random.choice(slut_data["win_phrases"])
			gain = random.randint(slut_data["min_revenue"], slut_data["max_revenue"])
			# round up, no floats
			gain = round(gain, 0)
			color = self.discord_success_rgb_code
			embed = discord.Embed(
				description=f"{win_phrases} {str(self.currency_symbol)} **{'{:,}'.format(int(gain))}**", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			embed.set_footer(text="gg")
			await channel.send(embed=embed)
			json_user_content["cash"] += gain
			# update last slut time
			json_user_content["last_slut"] = str(now)
			# overwrite, end
			json_content["userdata"][user_index] = json_user_content
			self.overwrite_json(json_content)

			return "success", "success"

	# we never reach this part of the code

	#
	# CRIME
	#

	async def crime(self, user, channel, username, user_pfp):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][user_index]

		"""
		SPECIFIC TIME ETC
		"""
		# grep values
		crime_data = json_content["variables"][self.variable_dict["crime"]]

		# delay will ALWAYS be in MINUTES
		delay = crime_data["delay"]
		proba = crime_data["proba"]

		time_check = False
		now = datetime.now()
		if json_user_content["last_crime"] == "none":
			# never done it, so go ahead
			time_check = True
		# else, gotta check if enough time passed since last slut
		else:
			last_slut_string = json_user_content["last_crime"]
			# get a timeobject from the string
			last_slut = datetime.strptime(last_slut_string, '%Y-%m-%d %H:%M:%S.%f')
			# calculate difference, see if it works
			passed_time = now - last_slut
			passed_time_minutes = passed_time.total_seconds() // 60.0
			if passed_time_minutes == 0:
				# because of // division it might display 0
				passed_time_minutes = 1
			if passed_time_minutes > delay:
				time_check = True
			else:
				time_check = False
				delay_remaining = delay - passed_time_minutes
		# moving the block here for cleaner code
		if time_check == False:
			color = self.discord_blue_rgb_code
			embed = discord.Embed(description=f"⏱ ️You cannot commit a crime for {math.ceil(delay_remaining)} minutes.",
								  color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return "success", "success"
		# else:
			# print("he can do it")

		"""
		ACTUAL FUNCTION
		"""
		# so, explanation :
		# not actually using probabilites or so, just a random number between 1 and 2
		# and if for example probability is 50%, then the random num should be > 1.5 in order to win
		crime_success = random.randint(0, 100)

		if proba < crime_success:
			# LOST

			lose_phrases = random.choice(crime_data["lose_phrases"])
			lose_percentage = random.randint(crime_data["min_lose_amount_percentage"],
											 crime_data["max_lose_amount_percentage"])
			balance = json_user_content["cash"] + json_user_content["bank"]
			loss = balance * (lose_percentage / 100)
			# round up, no floats
			loss = round(loss, 0)
			color = self.discord_error_rgb_code
			embed = discord.Embed(
				description=f"{lose_phrases} {str(self.currency_symbol)} **{'{:,}'.format(int(loss))}**", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			embed.set_footer(text="r.i.p")
			await channel.send(embed=embed)
			json_user_content["cash"] -= loss
			# update last slut time
			json_user_content["last_crime"] = str(now)
			# overwrite, end
			json_content["userdata"][user_index] = json_user_content
			self.overwrite_json(json_content)

			return "success", "success"

		else:
			# SUCCESS
			win_phrases = random.choice(crime_data["win_phrases"])
			gain = random.randint(crime_data["min_revenue"], crime_data["max_revenue"])
			# round up, no floats
			gain = round(gain, 0)
			color = self.discord_success_rgb_code
			embed = discord.Embed(
				description=f"{win_phrases} {str(self.currency_symbol)} **{'{:,}'.format(int(gain))}**", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			embed.set_footer(text="gg")
			await channel.send(embed=embed)
			json_user_content["cash"] += gain
			# update last slut time
			json_user_content["last_crime"] = str(now)
			# overwrite, end
			json_content["userdata"][user_index] = json_user_content
			self.overwrite_json(json_content)

			return "success", "success"

	# we never reach this part of the code

	#
	# WORK
	#

	async def work(self, user, channel, username, user_pfp):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][user_index]

		"""
		SPECIFIC TIME ETC
		"""
		# grep values
		work_data = json_content["variables"][self.variable_dict["work"]]

		# delay will ALWAYS be in MINUTES
		delay = work_data["delay"]

		time_check = False
		now = datetime.now()
		if json_user_content["last_work"] == "none":
			# never done it, so go ahead
			time_check = True
		# else, gotta check if enough time passed since last slut
		else:
			last_slut_string = json_user_content["last_work"]
			# get a timeobject from the string
			last_slut = datetime.strptime(last_slut_string, '%Y-%m-%d %H:%M:%S.%f')
			# calculate difference, see if it works
			passed_time = now - last_slut
			passed_time_minutes = passed_time.total_seconds() // 60.0
			if passed_time_minutes == 0:
				# because of // division it might display 0
				passed_time_minutes = 1
			if passed_time_minutes > delay:
				time_check = True
			else:
				time_check = False
				delay_remaining = delay - passed_time_minutes
		# moving the block here for cleaner code
		if time_check == False:
			color = self.discord_blue_rgb_code
			embed = discord.Embed(description=f"⏱ ️You cannot work for {math.ceil(delay_remaining)} minutes.",
								  color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return "success", "success"
		# else:
			# print("he can do it")

		"""
		ACTUAL FUNCTION
		"""

		# work is always a success
		win_phrases = random.choice(work_data["win_phrases"])
		gain = random.randint(work_data["min_revenue"], work_data["max_revenue"])
		# round up, no floats
		gain = round(gain, 0)
		color = self.discord_success_rgb_code
		embed = discord.Embed(description=f"{win_phrases} {str(self.currency_symbol)} **{'{:,}'.format(int(gain))}**",
							  color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		embed.set_footer(text="capitalism is great")
		await channel.send(embed=embed)
		json_user_content["cash"] += gain
		# update last slut time
		json_user_content["last_work"] = str(now)
		# overwrite, end
		json_content["userdata"][user_index] = json_user_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# ROB
	#

	async def rob(self, user, channel, username, user_pfp, user_to_rob):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][user_index]

		"""
		SPECIFIC TIME ETC
		"""
		# grep values
		rob_data = json_content["variables"][self.variable_dict["rob"]]

		# delay will ALWAYS be in MINUTES
		delay = rob_data["delay"]
		proba = rob_data["proba"]

		time_check = False
		now = datetime.now()
		if json_user_content["last_rob"] == "none":
			# never done it, so go ahead
			time_check = True
		# else, gotta check if enough time passed since last slut
		else:
			last_slut_string = json_user_content["last_rob"]
			# get a timeobject from the string
			last_slut = datetime.strptime(last_slut_string, '%Y-%m-%d %H:%M:%S.%f')
			# calculate difference, see if it works
			passed_time = now - last_slut
			passed_time_minutes = passed_time.total_seconds() // 60.0
			if passed_time_minutes == 0:
				# because of // division it might display 0
				passed_time_minutes = 1
			if passed_time_minutes > delay:
				time_check = True
			else:
				time_check = False
				delay_remaining = delay - passed_time_minutes
		# moving the block here for cleaner code
		if time_check == False:
			color = self.discord_blue_rgb_code
			embed = discord.Embed(description=f"⏱ ️You cannot rob someone for {math.ceil(delay_remaining)} minutes.",
								  color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return "success", "success"
		# else:
			# print("he can do it")

		"""
		ACTUAL FUNCTION
		"""

		# check if user you want to rob exists
		robbed_user, status = self.find_index_in_db(json_content["userdata"], user_to_rob, fail_safe=True)
		if (robbed_user == 0 and status == "error"):
			# we didnt find him
			color = self.discord_error_rgb_code
			embed = discord.Embed(description=f"❌ Invalid `<user>` argument given.\n\nUsage:\n`rob <user>`",
								  color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return "success", "success"

		if str(user).strip() == str(user_to_rob).strip():
			# you cannot rob yourself
			color = self.discord_error_rgb_code
			embed = discord.Embed(description=f"❌ You cannot rob yourself!", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return "success", "success"

		# you cannot rob from people who have less money than you
		robbed_user_data = json_content["userdata"][robbed_user]
		robbed_balance = robbed_user_data["cash"] + robbed_user_data["bank"]
		user_balance = json_user_content["cash"] + json_user_content["bank"]
		if robbed_balance < user_balance:
			lose_percentage = random.randint(rob_data["min_lose_amount_percentage"],
											 rob_data["max_lose_amount_percentage"])
			balance = json_user_content["cash"] + json_user_content["bank"]
			loss = balance * (lose_percentage / 100)
			# round up, no floats
			loss = round(loss, 0)

			color = self.discord_error_rgb_code
			embed = discord.Embed(
				description=f"❌ You've been fined {str(self.currency_symbol)} **{'{:,}'.format(int(loss))}** for trying to rob a person more poor than you.",
				color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)

			return "success", "success"

		#
		# Normal robbing now
		#

		# so, explanation :
		# not actually using probabilites or so, just a random number between 1 and 2
		# and if for example probability is 50%, then the random num should be > 1.5 in order to win
		crime_success = random.randint(0, 100)

		if proba < crime_success:
			# LOST

			lose_phrases = random.choice(rob_data["lose_phrases"])
			lose_percentage = random.randint(rob_data["min_lose_amount_percentage"],
											 rob_data["max_lose_amount_percentage"])
			balance = json_user_content["cash"] + json_user_content["bank"]
			loss = balance * (lose_percentage / 100)
			# round up, no floats
			loss = round(loss, 0)
			color = self.discord_error_rgb_code
			embed = discord.Embed(
				description=f"❌ {lose_phrases} {str(self.currency_symbol)} **{'{:,}'.format(int(loss))}**", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			embed.set_footer(text="robbing isn't cool")
			await channel.send(embed=embed)
			json_user_content["cash"] -= loss
			# update last slut time
			json_user_content["last_rob"] = str(now)
			# overwrite, end
			json_content["userdata"][user_index] = json_user_content
			self.overwrite_json(json_content)

			return "success", "success"

		else:
			# SUCCESS

			win_phrases = random.choice(rob_data["win_phrases"])
			gain_percentage = random.randint(rob_data["min_gain_amount_percentage"],
											 rob_data["max_gain_amount_percentage"])

			robbed_cash = robbed_user_data["cash"]
			gain = robbed_cash * (gain_percentage / 100)

			# round up, no floats
			gain = round(gain, 0)
			color = self.discord_success_rgb_code
			embed = discord.Embed(
				description=f"✅ {win_phrases} {str(self.currency_symbol)} **{'{:,}'.format(int(gain))}**", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			embed.set_footer(text="lucky")
			await channel.send(embed=embed)
			json_user_content["cash"] += gain
			# update last slut time
			json_user_content["last_rob"] = str(now)
			# overwrite, end
			json_content["userdata"][user_index] = json_user_content
			self.overwrite_json(json_content)

			return "success", "success"

	# this code is never reached

	#
	# BALANCE
	#

	async def balance(self, user, channel, userbal_to_check, username_to_check, userpfp_to_check, not_done):
		# load json
		# print(not_done)
		if not_done: await asyncio.sleep(1)
		json_file = open(self.pathToJson, "r")
		# print("opened json")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
		# check if user exists
		# no need for fail_safe option because that is already checked in main.py before calling this function
		checked_user, status = self.find_index_in_db(json_content["userdata"], userbal_to_check)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][checked_user]
		check_cash = "{:,}".format(int(json_user_content["cash"]))
		check_bank = "{:,}".format(int(json_user_content["bank"]))
		check_bal = "{:,}".format(int(json_user_content["cash"] + json_user_content["bank"]))
		minute_formatted = f"0{datetime.now().minute}" if datetime.now().minute < 10 else datetime.now().minute
		formatted_time = str(f"{datetime.now().hour}:{minute_formatted}")

		color = self.discord_blue_rgb_code
		embed = discord.Embed(color=color)
		embed.add_field(name="**Cash**", value=f"{str(self.currency_symbol)} {check_cash}", inline=True)
		embed.add_field(name="**Bank**", value=f"{str(self.currency_symbol)} {check_bank}", inline=True)
		embed.add_field(name="**Net Worth:**", value=f"{str(self.currency_symbol)} {check_bal}", inline=True)
		embed.set_author(name=username_to_check, icon_url=userpfp_to_check)
		embed.set_footer(text=f"today at {formatted_time}")
		await channel.send(embed=embed)

		self.overwrite_json(json_content)
		return

	#
	# DEPOSIT
	#

	async def deposit(self, user, channel, username, user_pfp, amount):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][user_index]

		user_cash = json_user_content["cash"]

		if amount == "all":
			amount = user_cash
			if amount < 0:
				return "error", "❌ No negative values."
		else:
			amount = int(amount)
			if amount > user_cash:
				return "error", f"❌ You don't have that much money to deposit. You currently have {str(self.currency_symbol)} {'{:,}'.format(user_cash)} on hand."

		json_user_content["cash"] -= amount
		json_user_content["bank"] += amount

		color = self.discord_success_rgb_code
		embed = discord.Embed(
			description=f"✅ Deposited {str(self.currency_symbol)} {'{:,}'.format(int(amount))} to your bank!",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["userdata"][user_index] = json_user_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# WITHDRAW
	#

	async def withdraw(self, user, channel, username, user_pfp, amount):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][user_index]

		user_bank = json_user_content["bank"]

		if amount == "all":
			amount = user_bank
			if amount < 0:
				return "error", "❌ No negative values."
		else:
			amount = int(amount)
			if amount > user_bank:
				return "error", f"❌ You don't have that much money to withdraw. You currently have {str(self.currency_symbol)} {'{:,}'.format(user_bank)} in the bank."

		json_user_content["cash"] += amount
		json_user_content["bank"] -= amount

		color = self.discord_success_rgb_code
		embed = discord.Embed(
			description=f"✅ Withdrew {str(self.currency_symbol)} {'{:,}'.format(int(amount))} from your bank!",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["userdata"][user_index] = json_user_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# GIVE
	#

	async def give(self, user, channel, username, user_pfp, reception_user, amount, recept_uname):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
		reception_user_index, new_data = self.find_index_in_db(json_content["userdata"], reception_user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][user_index]
		json_recept_content = json_content["userdata"][reception_user_index]

		user_cash = json_user_content["cash"]
		recept_cash = json_recept_content["cash"]

		if amount == "all":
			amount = user_cash
			if amount < 0:
				return "error", "❌ No negative values."
		else:
			amount = int(amount)
			if amount > user_cash:
				return "error", f"❌ You don't have that much money to give. You currently have {str(self.currency_symbol)} {'{:,}'.format(int(user_cash))} in the bank."

		json_user_content["cash"] -= amount
		json_recept_content["cash"] += amount

		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(
			description=f"✅ {recept_uname.mention} has received your {str(self.currency_symbol)} {'{:,}'.format(int(amount))}",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["userdata"][user_index] = json_user_content
		json_content["userdata"][reception_user_index] = json_recept_content
		self.overwrite_json(json_content)

		return "success", "success"


	#
	# REMOVE GONE USERS / CLEAN LEADERBOARD
	#
	
	async def clean_leaderboard(self, server):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		
		json_users = json_content["userdata"]
		json_income_roles = json_content["income_roles"]
		amount_removed = 0
		pops = []
		
		# we're gonna remove the user instance and the user params in collect etc.
		for user_index in range(len(json_users)):
			on_server = False
			for on_server_check in range(len(server.members)):
				if json_users[user_index]["user_id"] == server.members[on_server_check].id:
					on_server = True
					break
			
			if not on_server:
				# delete from the user section
				pop_index, b = self.find_index_in_db(json_users, json_users[user_index]["user_id"])
				pops.append(pop_index)
				
				amount_removed += 1
		
		# basically minus because we go reverse, else we change the whole
		# list and then we cant work per index anymore !
		# print(pops)
		pops.reverse()
		# print(pops)
		
		for index in range(len(pops)):
			
			# delete from user income role section
			for i in range(len(json_income_roles)):
				try:
					json_income_roles[i]["last_single_called"].pop(str(json_users[pops[index]]["user_id"]))
				except:
					pass
			
			del json_users[pops[index]]

		# overwrite, end
		json_content["userdata"] = json_users
		json_content["income_roles"] = json_income_roles
		self.overwrite_json(json_content)

		return "success", amount_removed


	#
	# LEADERBOARD
	#

	async def leaderboard(self, user, channel, username, full_name, page_number, mode_type, client):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][user_index]

		"""
		sorting algorithm
		"""
		# yes, i could use a dict
		all_users = []
		all_bal = []
		i = 0
		for i in range(len(json_content["userdata"])):
			all_users.append(json_content["userdata"][i]["user_id"])
			if mode_type == "-cash":
				all_bal.append(int(json_content["userdata"][i]["cash"]))
			elif mode_type == "-bank":
				all_bal.append(int(json_content["userdata"][i]["bank"]))
			else:  # elif mode_type == "-total":
				# print(json_content["userdata"][i]["cash"] + json_content["userdata"][i]["bank"])
				all_bal.append(int(json_content["userdata"][i]["cash"] + json_content["userdata"][i]["bank"]))
		# print(all_bal)
		# so, data is set, now sort

		i = -1
		while i <= len(all_bal):
			i += 1
			try:
				if all_bal[i] < all_bal[i + 1]:
					# save the higher stats one into buffer
					saved = all_bal[i]
					# this one has lower stats, so move him right
					all_bal[i] = all_bal[i + 1]
					# the higher one (saved) takes that position
					all_bal[i + 1] = saved
					# repeat process, but for the player-names
					saved = all_users[i]
					all_users[i] = all_users[i + 1]
					all_users[i + 1] = saved
					i = -1
			except:
				pass

		"""
		this seems to be whats taking the longest time while sorting
		"""

		# use names instead of just ID, except if we cannot find names
		# so for example if someone left the server
		for i in range(len(all_users)):
			try:
				name_object = client.get_user(int(all_users[i])).name
				# print(i, all_users[i], name_object)
				actual_name = str(name_object)
				if all_users[i] == user:
					user_lb_position = i + 1
			except:
				actual_name = str(all_users[i])
			# update
			all_users[i] = actual_name
		try:
			print("user is at position ", user_lb_position)
		except Exception:
			user_lb_position = 10000  # did not find him

		# making nice number formats
		for i in range(len(all_bal)):
			all_bal[i] = '{:,}'.format(all_bal[i])

		# making the formatted output description
		# number of pages which will be needed :
		# we have 10 ranks per page
		"""
		btw before did this (idk why i did this and not just ceil ?)
		if ".0" in str(page_count): page_count = int(page_count)
		if not isinstance(page_count, int):
			page_count += 1
		"""
		ranks_per_page = 10
		page_count = math.ceil(len(all_bal) / ranks_per_page)
		# page_count = (len(all_bal) + ranks_per_page - 1)

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
			leaderboard_formatted += f"\n**{str(i + 1)}.** {user_selection[i_i]} • {str(self.currency_symbol)} {bal_selection[i_i]}"
			i += 1
		# making a nice output
		if page_count == 1:
			page_number = 1
		elif page_number > page_count:
			page_number = 1

		# inform user
		color = self.discord_blue_rgb_code
		embed = discord.Embed(description=f"\n\n{leaderboard_formatted}", color=color)
		# same pfp as unbelievaboat uses
		embed.set_author(name=full_name,
						 icon_url="https://media.discordapp.net/attachments/506838906872922145/506899959816126493/h5D6Ei0.png")
		if user_lb_position == 1:
			pos_name = "st"
		elif user_lb_position == 2:
			pos_name = "nd"
		elif user_lb_position == 3:
			pos_name = "rd"
		else:
			pos_name = ""
		embed.set_footer(
			text=f"Page {page_number}/{page_count}  •  Your leaderboard rank: {user_lb_position}{pos_name}")
		await channel.send(embed=embed)

		return "success", "success"

	#
	# MODULE INFO
	#

	async def module(self, user, channel, module):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		"""
		variable_dict = {
			"slut": 0,
			"crime": 1,
			"work": 2,
			"rob": 3
		}
		"""

		if module not in self.variable_dict.keys() and module not in ["symbols", "currency_symbol"]:
			possible = "slut, crime, work, rob, symbols"
			return "error", f"❌ Module not found. Possibilites : {possible}"

		if module in ["symbols", "currency_symbol"]:
			info_output = f"""Symbol:\nname: {json_content['symbols'][0]['name']}, value: emoji \"{json_content['symbols'][0]['symbol_emoji']}" """
		else:
			module_index = self.variable_dict[module]
			info_output = f"Module: **{module}** info:\nOutput as : <variable name> ; <value>\n```"
			mod = json_content["variables"][module_index]
			module_content = json_content["variables"][module_index]
			for i in range(len(module_content)):
				module_content_vars = list(json_content["variables"][module_index].keys())[i]

				info_output += f'\n"{module_content_vars}" ; {mod[module_content_vars]}'
			info_output += "\n```\n**Note**: Delay is in minutes, proba is x%, percentages are in % too"
		await channel.send(info_output)

		return "success", "success"

	#
	# ADD-MONEY
	#

	async def add_money(self, user, channel, username, user_pfp, reception_user, amount, recept_uname):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		reception_user_index, new_data = self.find_index_in_db(json_content["userdata"], reception_user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_recept_content = json_content["userdata"][reception_user_index]

		json_recept_content["cash"] += int(amount)

		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(
			description=f"✅  Added {str(self.currency_symbol)} {'{:,}'.format(int(amount))} to {recept_uname.mention}'s cash balance",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["userdata"][reception_user_index] = json_recept_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# REMOVE-MONEY
	#

	async def remove_money(self, user, channel, username, user_pfp, reception_user, amount, recept_uname, mode):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		reception_user_index, new_data = self.find_index_in_db(json_content["userdata"], reception_user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_recept_content = json_content["userdata"][reception_user_index]

		json_recept_content[mode] -= int(amount)

		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(
			description=f"✅  Removed {str(self.currency_symbol)} {'{:,}'.format(int(amount))} from {recept_uname.mention}'s {mode} balance",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["userdata"][reception_user_index] = json_recept_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# EDIT VARIABLES
	#

	async def edit_variables(self, user, channel, username, user_pfp, module_name, variable_name, new_value):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		if module_name not in self.variable_dict.keys():
			return "error", "❌ module not found"
		module_index = self.variable_dict[module_name]

		json_module_content = json_content["variables"][module_index]
		try:
			old_value = json_module_content[variable_name]
		except:
			return "error", f"❌ variable name of module {module_name} not found"

		# changing value
		json_module_content[variable_name] = new_value

		# not asking for verification, would just have to reverse by another edit
		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(
			description=f"✅  Changed variable '{variable_name}' of module '{module_name}'\nBefore: '{old_value}'. Now: '{new_value}'",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["variables"][module_index] = json_module_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# EDIT CURRENCY SYMBOL
	#

	async def change_currency_symbol(self, user, channel, username, user_pfp, new_emoji_name):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_emoji = json_content["symbols"][0]

		old_value = json_emoji["symbol_emoji"]

		test_emoji = self.get_currency_symbol(True, new_emoji_name)
		if test_emoji == "error":
			return "error", "❌ Emoji not found."

		# changing value
		json_emoji["symbol_emoji"] = new_emoji_name

		# not asking for verification, would just have to reverse by another edit
		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(description=f"✅  Changed emoji from '{old_value}' to '{new_emoji_name}'", color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["symbols"][0] = json_emoji
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# EDIT CURRENCY SYMBOL
	#

	async def set_income_reset(self, user, channel, username, user_pfp, new_income_reset):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		# info: we dont need to check anything
		# because itll be either true/false
		# if it doesnt exist, we create it. if it does, we change it. simple.

		# changing value
		json_content["symbols"][0]["income_reset"] = new_income_reset

		# not asking for verification, would just have to reverse by another edit
		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(description=f"✅  Changed income-reset to　`{new_income_reset}`", color=color)
		embed.set_footer(text="info: if true (default), daily salary resets every day and does not accumulate.")
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		self.overwrite_json(json_content)

		return "success", "success"

	"""
	ITEM HANDLING
	"""

	#
	# CREATE NEW ITEM / create item
	#

	async def create_new_item(self, item_display_name, item_name, cost, description, duration, stock, max_amount, roles_id_required, roles_id_to_give,
							  roles_id_to_remove, max_bal, reply_message, item_img_url, roles_id_excluded):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_items = json_content["items"]

		for i in range(len(json_items)):
			if json_items[i]["name"] == item_name:
				return "error", "❌ Item with such name already exists."

		# calculate item duration
		today = datetime.today()
		# print(today)
		expiration_date = today + timedelta(days=duration)

		# print("expiration date : ", expiration_date)

		json_items.append({
			"name": item_name,
			"display_name": item_display_name,
			"price": cost,
			"description": description,
			"duration": duration,
			"amount_in_stock": stock,
			"max_amount": max_amount,
			"required_roles": roles_id_required,
			"given_roles": roles_id_to_give,
			"removed_roles": roles_id_to_remove,
			"excluded_roles": roles_id_excluded,
			"maximum_balance": max_bal,
			"reply_message": reply_message,
			"expiration_date": str(expiration_date),
			"item_img_url": item_img_url
		})

		# overwrite, end
		json_content["items"] = json_items
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# REMOVE ITEM AKA DELETE ITEM
	#

	async def remove_item(self, item_name):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_items = json_content["items"]
		item_found = item_index = 0
		for i in range(len(json_items)):
			if json_items[i]["name"] == item_name:
				item_found = 1
				item_index = i
		if not item_found:
			return "error", "❌ Item not found."

		# delete from the "items" section
		json_items.pop(item_index)

		# delete for everyone who had it in their inventory
		user_content = json_content["userdata"]
		for i in range(len(user_content)):
			# tricky
			# i suppose the variable type will either be a string with "none"
			# or a list with lists : ["item_name", amount], so items = [ [], [] ] etc
			"""
			info: on 11.01.24 added a break after pop(ii).
			Only bug should be if user has 2 items with same name, but that shouldnt happen. 
			"""
			if user_content[i]["items"] == "none":
				pass
			else:
				try:
					for ii in range(len(user_content[i]["items"])):
						current_name = user_content[i]["items"][ii][0]
						if current_name == item_name:
							user_content[i]["items"].pop(ii)
							break
				except Exception as e:
					print(e)

		# overwrite, end
		json_content["items"] = json_items
		self.overwrite_json(json_content)

		return "success", "success"
	
	#
	# REMOVE ITEM FROM STORE (STAYS IN USER INVENTORY)
	#

	async def remove_item_from_store(self, item_name):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_items = json_content["items"]
		item_found = item_index = 0
		for i in range(len(json_items)):
			if json_items[i]["name"] == item_name:
				item_found = 1
				item_index = i
		if not item_found:
			return "error", "❌ Item not found."

		# delete from the "items" section
		json_items.pop(item_index)

		# overwrite, end
		json_content["items"] = json_items
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# REMOVE ITEM FROM SPECIFIC USER's INVENTORY
	#

	async def remove_user_item(self, user, channel, username, user_pfp, item_name, amount_removed, reception_user, recept_uname):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		reception_user_index, new_data = self.find_index_in_db(json_content["userdata"], reception_user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_recept_content = json_content["userdata"][reception_user_index]

		# i just copied and adjusted the code snippet from give_item btw.
		try:
			if json_recept_content["items"] == "none":
				return "error", f"❌ User does not have any items."
			else:
				worked = False
				for ii_i in range(len(json_recept_content["items"])):
					if json_recept_content["items"][ii_i][0] == item_name:
						if (json_recept_content["items"][ii_i][1] - amount_removed) < 0:
							return "error", f"❌ User does not have the necessary amount of items.\nInfo: has {json_recept_content['items'][ii_i][1]} items of that item."
						json_recept_content["items"][ii_i][1] -= amount_removed
						worked = True
						break
				if worked == False:
					return "error", f"❌ User does not possess the specified item."

		except:
			return "error", f"❌"

		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(
			description=f"✅ Removed {'{:,}'.format(int(amount_removed))} {item_name} from {recept_uname.mention}.",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["userdata"][reception_user_index] = json_recept_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# BUY ITEM
	#

	async def buy_item(self, user, channel, username, user_pfp, item_name, amount, user_roles, server_object,
					   user_object):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_items = json_content["items"]
		item_found = item_index = 0
		for i in range(len(json_items)):
			if json_items[i]["name"] == item_name:
				item_found = 1
				item_index = i
		if not item_found:
			return "error", "Item not found."
		item = json_items[item_index]
		# get variables
		item_name = item_name
		try: # compatibility
			item_display_name = item["display_name"]
		except:
			item_display_name = item_name
		item_price = item["price"]
		req_roles = item["required_roles"]
		give_roles = item["given_roles"]
		rem_roles = item["removed_roles"]
		try:
			excluded_roles = item["excluded_roles"]
		except:  # compatibility
			excluded_roles = ["none"]
		max_bal = item["maximum_balance"]
		remaining_stock = item["amount_in_stock"]
		try:
			max_amount = item["max_amount"]
		except:
			max_amount = "unlimited"
		expiration_date = item["expiration_date"]
		reply_message = item["reply_message"]

		# calculate expiration
		today = datetime.today()
		expire = datetime.strptime(expiration_date, "%Y-%m-%d %H:%M:%S.%f")
		if today > expire:
			return "error", f"❌ Item has already expired. Expiring date was {expiration_date}"
		# else we're good

		# 1. check req roles
		try:
			if req_roles[0] == "none":
				pass
			else:
				for i in range(len(req_roles)):
					if int(req_roles[i]) not in user_roles:
						return "error", f"❌ User does not seem to have all required roles."
		except Exception as e:
			print("1", e)
			return "error", f"❌ Unexpected error."
		
		# 2. check excluded roles - meaning roles with which you CANT buy
		try:
			if excluded_roles[0] == "none":
				pass
			else:
				for i in range(len(excluded_roles)):
					if int(excluded_roles[i]) in user_roles:
						return "error", f"❌ User possesses excluded role (id: {excluded_roles[i]})."
		except Exception as e:
			print("2", e)
			return "error", f"❌ Unexpected error."

		### BEFORE update, "check rem roles" and "check give roles" was located here. it seems that
		### the intended usage i had back then was to do that stuff once the item is bought.
		### thus this is now located below, after checking balance etc.

		# 4. check if enough money
		sum_price = item_price * amount
		sum_price = round(sum_price, 0)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
		user_content = json_content["userdata"][user_index]
		user_cash = user_content["cash"]
		if user_cash < sum_price:
			return "error", f"❌ Not enough money in cash to purchase.\nto pay: {sum_price} ; in cash: {user_cash}"

		# 5. check if not too much money
		user_bank = user_content["bank"]
		if max_bal != "none":
			if (user_bank + user_cash) > max_bal:
				return "error", f"❌ You have too much money to purchase.\nnet worth: {'{:,}'.format(int(user_bank + user_cash))} ; max bal: {max_bal}"

		# 6. check if enough in stock or not
		if remaining_stock != "unlimited":
			if remaining_stock <= 0:
				return "error", f"❌ Item not in stock."
			elif amount > remaining_stock:
				return "error", f" Not enough remaining in stock ({remaining_stock} remaining)."
		
		# 7. check if not too many items already owned / to be owned
		user_item_amount = 0  # default value in case we have a bug
		if user_content["items"] == "none":
			user_item_amount = 0
		else:
			worked = False
			for ii_i in range(len(user_content["items"])):
				if user_content["items"][ii_i][0] == item_name:
					user_item_amount = user_content["items"][ii_i][1]
					worked = True
					break
			if not worked:  # has items, just not the relevant one
				user_item_amount = 0
		
		if max_amount != "unlimited":
			if int(amount) >= int(max_amount) or int(user_item_amount + amount) >= int(max_amount) + 1:
				available_to_buy = int(max_amount) - int(user_item_amount)
				return "error", f"❌ You have too many items or would own too many.\nYou can buy **{'{:,}'.format(available_to_buy)}** {item_name}(s)"
		
		# 8. rem money, substract stock, add to inventory
		user_content["cash"] -= sum_price
		try:
			item["amount_in_stock"] -= amount
		except:
			# in this case theres no limit so we dont substract anything
			pass
		
		if user_content["items"] == "none":
			user_content["items"] = [[item_name, amount]]
		else:
			needAppend = True
			for i_i in range(len(user_content["items"])):
				if user_content["items"][i_i][0] == item_name:
					user_content["items"][i_i][1] += amount
					needAppend = False
					break
			if needAppend:
				user_content["items"].append([item_name, amount])

		# 9. check remove roles
		try:
			if rem_roles[0] == "none":
				pass
			else:
				for i in range(len(rem_roles)):
					role = discord.utils.get(server_object.roles, id=int(rem_roles[i]))
					try:
						await user_object.remove_roles(role)
					except:
						continue
		except Exception as e:
			return "error", f"❌ Unexpected error."

		# 9. check give roles
		try:
			if give_roles[0] == "none":
				pass
			else:
				for i in range(len(give_roles)):
					role = discord.utils.get(server_object.roles, id=int(give_roles[i]))
					try:
						await user_object.add_roles(role)
					except:
						continue

		except Exception as e:
			print("3", e)
			return "error", f"❌ Unexpected error."
		color = self.discord_blue_rgb_code
		embed = discord.Embed(
			description=f"You have bought {amount} {item_display_name} and paid {str(self.currency_symbol)} **{'{:,}'.format(int(sum_price))}**",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		embed.set_footer(text=reply_message)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["userdata"][user_index] = user_content
		json_content["items"] = json_items
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# GIVE ITEM
	#

	async def give_item(self, user, channel, username, user_pfp, item_name, amount, reception_user, server_object,
						user_object, recept_username, spawn_mode):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
		reception_user_index, new_data = self.find_index_in_db(json_content["userdata"], reception_user)
		recept_uname = recept_username
		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][user_index]
		json_recept_content = json_content["userdata"][reception_user_index]

		try:
			if not spawn_mode:  # not doing this if an admin just spawns an item
				if json_user_content["items"] == "none":
					return "error", f"❌ You do not have any items to give"
				else:
					worked = False
					for ii_i in range(len(json_user_content["items"])):
						if json_user_content["items"][ii_i][0] == item_name:
							if (json_user_content["items"][ii_i][1] - amount) < 0:
								return "error", f"❌ You do not have enough items of that item to give."
							json_user_content["items"][ii_i][1] -= amount
							worked = True
							break
					if worked == False:
						return "error", f"❌ You do not have that item to give"
			else:
				item_found = False
				for i in range(len(json_content["items"])):
					if json_content["items"][i]["name"] == item_name:
						item_found = True
				if not item_found:
					return "error", "Item not found (needs to be created before spawning)."

			# so we should be good, now handling the reception side
			if json_recept_content["items"] == "none":
				json_recept_content["items"] = [[item_name, amount]]
			else:
				needAppend = True
				for i_i in range(len(json_recept_content["items"])):
					if json_recept_content["items"][i_i][0] == item_name:
						json_recept_content["items"][i_i][1] += amount
						needAppend = False
						break
				if needAppend:
					json_recept_content["items"].append([item_name, amount])

		except:
			return "error", f"❌"

		# inform user
		color = self.discord_success_rgb_code
		if not spawn_mode:
			embed = discord.Embed(
				description=f"✅ {recept_uname.mention} has received {'{:,}'.format(int(amount))} {item_name} from you!",
				color=color)
		else:
			embed = discord.Embed(
				description=f"✅ {recept_uname.mention} has received {'{:,}'.format(int(amount))} {item_name} (spawned)!",
				color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["userdata"][user_index] = json_user_content
		json_content["userdata"][reception_user_index] = json_recept_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# USE ITEM
	#

	async def use_item(self, user, channel, username, user_pfp, item_name, amount):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][user_index]

		try:
			if json_user_content["items"] == "none":
				return "error", f"❌ You do not have any items"
			else:
				worked = False
				for ii_i in range(len(json_user_content["items"])):
					if json_user_content["items"][ii_i][0] == item_name:
						if (json_user_content["items"][ii_i][1] - amount) < 0:
							return "error", f"❌ You do not have enough items of that item to use."
						json_user_content["items"][ii_i][1] -= amount

						# we will also add/append to a list for used items
						try:
							if json_user_content["used_items"] == "none":
								json_user_content["used_items"] = [[item_name, amount]]
							else:
								needAppend = True
								for i_i in range(len(json_user_content["used_items"])):
									if json_user_content["used_items"][i_i][0] == item_name:
										json_user_content["used_items"][i_i][1] += amount
										needAppend = False
										break
								if needAppend:
									json_user_content["used_items"].append([item_name, amount])
						except Exception as e:
							# there is no used_items yet
							# not really sure if this will work tho, might have to come back to this
							json_user_content["used_items"] = [[item_name, amount]]


						worked = True
						break
				if not worked:
					return "error", f"❌ You do not have that item to give"
		except Exception as e:
			print(e)
			return "error", f"❌ Unknown error, please contact an admin."


		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(
			description=f"✅ You have used {'{:,}'.format(int(amount))} {item_name}(s) !",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["userdata"][user_index] = json_user_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# CHECK INVENTORY
	#

	async def check_inventory(self, user, channel, username, user_pfp, user_to_check, user_to_check_uname, user_to_check_pfp, page_number):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		if user_to_check == "self":
			user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
			user_content = json_content["userdata"][user_index]
		else: # we re looking for a specific member
			user_index, new_data = self.find_index_in_db(json_content["userdata"], user_to_check)
			user_content = json_content["userdata"][user_index]
			username = user_to_check_uname
			user_pfp = user_to_check_pfp

		"""
		we only care if we have any items owned, not 0
		"""
		items_old = user_content["items"]
		if items_old != "none":
			items = []
			for i in range(len(items_old)):
				if items_old[i][1] > 0:
					items.append(items_old[i])

			# number of pages which will be needed :
			# we have 10 items per page
			items_per_page = 10 

			# our selection !
			index_start = (page_number - 1) * items_per_page
			index_end = index_start + items_per_page
			items_selection = items[index_start: index_end]
			page_count = math.ceil(len(items) / items_per_page)
		else:
			items = "none"
			page_number = 1
			page_count = 1

		if items == "none":
			# inventory_checkup = "**Inventory empty. No items owned.**"
			color = self.discord_blue_rgb_code
			embed = discord.Embed(title="inventory", description="**Inventory empty. No items owned.**", color=color)

		else:
			# inventory_checkup = f""
			color = self.discord_blue_rgb_code
			embed = discord.Embed(title="inventory", color=color)
			current_index = 1 if page_number == 1 else page_number * items_per_page # this is because if we call page 2 we wanna start at 20
			for i in range(len(items_selection)):
				# to get the display name
				json_items = json_content["items"]
				for ii in range(len(json_items)):
					# print("checking item ", json_items[ii]["name"])
					if json_items[ii]["name"] == items_selection[i][0]:
						item_index = ii
						break

				try:
					item_display_name = json_items[ii]["display_name"]
				except:
					item_display_name = items_selection[i][0]  # if there is no display name, we show the normal name
				# btw i use "ideographic space" [　] for tab
				# inventory_checkup += f"[{current_index}]　Item: {item_display_name}\n　　short name: {json_items[ii]['name']}\n　　amount: `{items_selection[i][1]}`\n\n"
				embed.add_field(name=f"[{current_index}]　Item: {item_display_name}",
								value=f"short name: `{items_selection[i][0]}`　"
									  f"amount: `{items_selection[i][1]}`", inline=False)
				current_index += 1

		if page_count == 1:
			page_number = 1
		elif page_number > page_count:
			page_number = 1

		embed.set_author(name=username, icon_url=user_pfp)
		embed.set_footer(text=f"page {page_number} of {page_count}")
		sent_embed = await channel.send(embed=embed)

		# overwrite, end
		# not needed

		return "success", "success"

	#
	# CATALOG
	#

	async def catalog(self, user, channel, username, user_pfp, item_check, server_object):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		items = json_content["items"]
		catalog_final, max_items, current, finished = [], 10, 0, False
		catalog_report = "__Shop Items:__\n```\n"
		if item_check == "default_list":
			for i in range(len(items)):
				current += 1
				try:
					# print(current, max_items)
					catalog_report += f"Item {i}: {items[i]['display_name']}\n      price: {self.currency_symbol} {items[i]['price']};　short name <{items[i]['name']}>\n\n"
					if current >= max_items:
						catalog_report += "\n```"
						catalog_final.append(catalog_report)
						catalog_report = "```"
						current = 0
				except:
					await channel.send("compatbility error, please contact an admin.")
					return "success", "success"

			catalog_report += "\n```\n*For details about an item: use* `shop <item short name>`"
			catalog_final.append(catalog_report)

		else:
			check, img_prob = 0, False
			for i in range(len(items)):
				if items[i]["name"] == item_check:
					check = 1
					item_index = i
			if not check:
				return "error", "❌ Item not found."
			else:  # not needed, but for readability

				if items == "none":
					# inventory_checkup = "**Inventory empty. No items owned.**"
					color = self.discord_blue_rgb_code
					embed = discord.Embed(title="inventory", description="**Inventory empty. No items owned.**",
										  color=color)

				else:
					color = self.discord_blue_rgb_code


				try:
					embed = discord.Embed(title=f"catalog: {items[item_index]['display_name']}", color=color)
				except:
					embed = discord.Embed(title=f"catalog: item {items[item_index]['name']}", color=color)

				req_roles = ""

				for ii in range(len(items[item_index]["required_roles"])):
					if items[item_index]["required_roles"][ii] in ["none", ""]:
						req_roles += "none"
					else:
						role = discord.utils.get(server_object.roles, id=int(items[item_index]["required_roles"][ii]))
						req_roles += f"{str(role.mention)} "
				
				excluded_roles = ""
				try:  # compatibility thingy
					for ii in range(len(items[item_index]["excluded_roles"])):
						if items[item_index]["excluded_roles"][ii] in ["none", ""]:
							excluded_roles += "none"
						else:
							role = discord.utils.get(server_object.roles, id=int(items[item_index]["excluded_roles"][ii]))
							excluded_roles += f"{str(role.mention)} "
				except Exception as e:
					print(f"Error for required roles: {e} - (prob compatibility thingy).")
					excluded_roles += "none"

				give_roles = ""
				for iii in range(len(items[item_index]["given_roles"])):
					if items[item_index]["given_roles"][iii] in ["none", ""]:
						give_roles += "none"
					else:
						role = discord.utils.get(server_object.roles, id=int(items[item_index]["given_roles"][iii]))
						give_roles += f"{str(role.mention)} "

				rem_roles = ""
				for iiii in range(len(items[item_index]["removed_roles"])):
					if items[item_index]["removed_roles"][iiii] in ["none", ""]:
						rem_roles += "none"
					else:
						role = discord.utils.get(server_object.roles, id=int(items[item_index]["removed_roles"][iiii]))
						rem_roles += f"{str(role.mention)} "

				if int(str(datetime.strptime(items[item_index]['expiration_date'], '%Y-%m-%d %H:%M:%S.%f'))[
					   :4]) >= 2100:
					left_time = "never"
				else:
					left_time = str(items[item_index]['expiration_date'])[:10]
				
				# check for old version that dont have a max amount yet
				try:
					max_amount = items[item_index]['max_amount']
				except:
					max_amount = 0

				try:
					embed.add_field(name=f"Item name:", value=f"{items[item_index]['display_name']}", inline=False)
					embed.add_field(name=f"Item short name:", value=f"`{items[item_index]['name']}`", inline=True)
					embed.add_field(name=f"Item price:", value=f"{items[item_index]['price']}", inline=True)
					embed.add_field(name=f"In stock:", value=f"{items[item_index]['amount_in_stock']}", inline=True)
					embed.add_field(name=f"Max amount you can own:", value=f"{max_amount}", inline=False)
					embed.add_field(name=f"Item description:", value=f"{items[item_index]['description']}", inline=False)
					embed.add_field(name=f"Remaining time:", value=f"item expires {left_time}", inline=True)
					embed.add_field(name=f"Max balance to purchase:", value=f"{self.currency_symbol} {items[item_index]['maximum_balance']}", inline=False)
					embed.add_field(name=f"Roles:",
											value=f"Required roles: {req_roles}　"
												  f"Excluded roles: {excluded_roles}　"
												  f"Given roles: {give_roles}　"
												  f"Removed roles: {rem_roles}", inline=False)
					try:
						if items[item_index]['item_img_url'] != "EMPTY":
							embed.set_thumbnail(url=items[item_index]['item_img_url'])
					except:
						# basically we re trying to check if theres an image in the item object
						# but we also try to set it as a thumbnail, and if that fails
						# we wont replace it but warn the user with a specialised footer
						#   yes this is ugly. Itll do for now.
						try:
							if items[item_index]['item_img_url'] != "EMPTY": img_prob = True
						except:
							img_prob = False
				except Exception as error_code:
					print(error_code)
					await channel.send("# warning:\nfallback mode; This should not happen. Try to contact a bot admin (or see github at https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot)")
					catalog_report +=  f"Item short name: <{items[item_index]['name']}>\n" \
									  f"Item price: {items[item_index]['price']}\n" \
									  f"Item description: {items[item_index]['description']}\n" \
									  f"Remaining time: item expires {left_time}\n" \
									  f"Amount remaining: {items[item_index]['amount_in_stock']} in stock\n" \
									  f"Max amount you can own: {items[item_index]['max_amount']}\n" \
									  f"Maximum balance to purchase: {self.currency_symbol} {items[item_index]['maximum_balance']}\n" \
									  f"Required roles: {req_roles}\n" \
									  f"Given roles: {give_roles}\n" \
									  f"Removed roles: {rem_roles}\n"
					await channel.send(catalog_report)
					return "success", "success"

				# embed.set_author(name=username, icon_url=user_pfp)
				embed.set_footer(text="WARNING: URL for img was not found. Could be deprecated\nPlease look into the json file manually or contact an admin.") if img_prob else embed.set_footer(text="Info: always use the short name for commands.")
				sent_embed = await channel.send(embed=embed)
				return "success", "success"
		for i in range(len(catalog_final)):
			await channel.send(catalog_final[i])

		# overwrite, end
		# not needed

		return "success", "success"

	#
	# ROLE INCOMES - NEW ONE
	#

	async def new_income_role(self, user, channel, username, user_pfp, income_role_id, income):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_income_roles = json_content["income_roles"]

		for i in range(len(json_income_roles)):
			if json_income_roles[i]["role_id"] == income_role_id:
				return "error", "❌ Role already exists as income role."

		now = str(datetime.now())
		json_income_roles.append({
			"role_id": income_role_id,
			"role_income": income,
			"last_single_called": {},
			"last_updated": now
		})

		color = self.discord_blue_rgb_code
		embed = discord.Embed(
			description=f"New income role added.\nrole_id : {income_role_id}, income : {str(self.currency_symbol)} **{'{:,}'.format(int(income))}**",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		embed.set_footer(text="smooth")
		await channel.send(embed=embed)

		# overwrite, end
		json_content["income_roles"] = json_income_roles
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# ROLE INCOMES - REMOVE ONE
	#

	async def remove_income_role(self, user, channel, username, user_pfp, income_role_id):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_income_roles = json_content["income_roles"]
		role_found = role_index = 0
		for i in range(len(json_income_roles)):
			if json_income_roles[i]["role_id"] == income_role_id:
				role_found = 1
				role_index = i
		if not role_found:
			return "error", "❌ Role not found."

		# delete from the "items" section
		json_income_roles.pop(role_index)

		# overwrite, end
		json_content["income_roles"] = json_income_roles
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# ROLE INCOMES - LIST
	#

	async def list_income_roles(self, user, channel, username, user_pfp, server_object):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_income_roles = json_content["income_roles"]

		role_list_report = f"__Income Roles List:__\n\n"

		for i in range(len(json_income_roles)):
			role = discord.utils.get(server_object.roles, id=int(json_income_roles[i]["role_id"]))
			ping_role = f"<@&{json_income_roles[i]['role_id']}>"

			role_list_report += f"Role name: {ping_role}\n" \
								f"Role income: {self.currency_symbol} {'{:,}'.format(json_income_roles[i]['role_income'])}\n\n"

		role_list_report += "---------------------------------"

		await channel.send(role_list_report, silent=True)

		# overwrite, end
		# not needed

		return "success", "success"

	#
	# ROLE INCOMES - UPDATE INCOMES
	#
	# okay were gonna change it to an hourly income (10.06.2023)

	async def update_incomes(self, user, channel, username, user_pfp, server_object):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_income_roles = json_content["income_roles"]
		user_content = json_content["userdata"]

		# pretty straight forward i think.
		# first, we go into each role object
		# then we check in everyones roles if they have the role

		role_error = 0  # if a role is deleted or so

		for role_index in range(len(json_income_roles)):
			role_id = json_income_roles[role_index]["role_id"]

			# new edit for hourly income:
			# edit new new edit for daily again..
			now = datetime.now()
			# below could be changed because we need single one for every user now...
			last_income_update_string = json_income_roles[role_index]["last_updated"]
			#

			# get a timeobject from the string
			last_income_update = datetime.strptime(last_income_update_string, '%Y-%m-%d %H:%M:%S.%f')
			# calculate difference, see if it works
			passed_time = now - last_income_update
			# passed_time_final = passed_time.total_seconds() // 3600.0
			passed_time_final = passed_time.days

			try:
				role = discord.utils.get(server_object.roles, id=int(role_id))
			except:
				role_error += 1
				continue

			for member in role.members:
				try:
					# also to create user in case he isnt registered yet
					user_index, new_data = self.find_index_in_db(json_content["userdata"], member.id)

					json_user_content = json_content["userdata"][user_index]
					json_income_roles[role_index]["last_updated"] = str(now)
					income_total = (json_income_roles[role_index]["role_income"] * int(passed_time_final))
					json_user_content["bank"] += income_total
					# overwrite
					json_content["userdata"][user_index] = json_user_content

				except:
					pass
			await channel.send(f"{role.mention}, you have received your income ({self.currency_symbol} {'{:,}'.format(int(income_total))}) !", silent=True)


		# overwrite, end
		json_content["income_roles"] = json_income_roles
		self.overwrite_json(json_content)

		if role_error == 0:
			return "success", "success"
		else:
			return "error", f"error for `{role_error} role(s)`, maybe some got deleted?. Else the command successed."

	#
	# SOLO ROLE INCOME - UPDATE INCOMES SOLO
	#   aka GET SALARY

	async def update_incomes_solo(self, user, channel, username, user_pfp, server_object, user_roles):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)

		json_income_roles = json_content["income_roles"]
		user_content = json_content["userdata"]

		# this is the other way around than the global update income

		role_ping_complete = []
		hours_remaining = "24"
		no_money = True
		income_total = 0
		received_instances = 0
		for role in user_roles:
			for role_index in range(len(json_income_roles)):
				role_id = json_income_roles[role_index]["role_id"]
				if int(role) == int(role_id):
					no_money = False


					# new edit for daily income:
					now = datetime.now()
					# now = datetime.strptime("2024-02-11 00:01:33.884845", '%Y-%m-%d %H:%M:%S.%f')

					# first check if he already got one at all
					try:
						json_user_content = json_content["userdata"][user_index]

						# role_ping_complete.append(discord.utils.get(server_object.roles, id=int(role_id)))

						"""
						30.12.23: new edit. By default now, users will get a daily salary
						and will have to retrieve it daily. You can also change that tho
						by changing "income_reset" to true in the json.
						Because this is an update and we want compatibility with older versions,
						we will need to try and if not write a income_reset.
						"""
						"""
						08.02.24: new new edit. Now, payday resets GLOBALLY (not one day since you specifically did)
						"""
						# true by default
						income_reset, new_day = True, False
						try:
							if json_content["symbols"][0]["income_reset"] == "false": income_reset = False
						except:
							# if not yet updated, we add this to json
							json_content["symbols"][0]["income_reset"] = "true"
						# get the current day
						try:
							last_global_update_string = json_content["symbols"][0]["global_collect"]
							last_global_update = datetime.strptime(last_global_update_string, '%Y-%m-%d %H:%M:%S.%f')

							last_single_called = json_income_roles[role_index]["last_single_called"][str(user)]
							last_single = int(datetime.strptime(last_single_called, '%Y-%m-%d %H:%M:%S.%f').strftime("%d"))

							today_day, last_day = int(now.strftime("%d")), int(last_global_update.strftime("%d"))
							max_days = calendar.monthrange(int(now.strftime("%Y")), int(now.strftime("%m")))[1]
							# print(today_day, last_day, max_days)
							# print(last_single, today_day, last_day)
							if today_day > max_days: last_day = 1
							if last_single < last_day:
								new_day = True

							# for example if i last called on 08th JANUARY and today is 07th FEBRUARY
							# the check above would say nope, so this is to fix that
							if datetime.strptime(last_single_called, '%Y-%m-%d %H:%M:%S.%f') < last_global_update and last_single > last_day:
								new_day = True

							else:
								hour_rem = 24 - int(now.strftime('%H')) - 1
								min_rem_raw = 0 if 60 - int(now.strftime('%M')) == 60 else 60 - int(now.strftime('%M'))
								min_rem = f"0{min_rem_raw}" if min_rem_raw < 10 else min_rem_raw
								hours_remaining = f"{hour_rem}:{min_rem}"
						except Exception as error_code:
							print(error_code)
							await channel.send("setting up")
							json_content["symbols"][0]["global_collect"] = str(now)
							new_day = True


						if income_reset and new_day:
							# you only get it DAILY, other than that it resets !
							income_total += json_income_roles[role_index]["role_income"]
							json_income_roles[role_index]["last_single_called"][str(user)] = str(now)
							received_instances += 1
						json_content["symbols"][0]["global_collect"] = str(now)

					except Exception as error_code:  # he didn't retrieve a salary yet
						print(error_code)
						await channel.send("creating your first entry...")
						json_income_roles[role_index]["last_single_called"][str(user)] = str(now) # removed on 08.02. update
						# also to create user in case he isnt registered yet
						income_total += json_income_roles[role_index]["role_income"]
						received_instances += 1

					# role_ping_complete.append(discord.utils.get(server_object.roles, id=int(role_id)))

		json_user_content = json_content["userdata"][user_index]
		json_user_content["bank"] += income_total
		# overwrite
		json_content["userdata"][user_index] = json_user_content
		json_content["income_roles"] = json_income_roles

		if no_money:
			await channel.send("You have no income roles!")
		else:
			if int(income_total) != 0:
				await channel.send(f"You have received your income ({self.currency_symbol} {'{:,}'.format(int(income_total))}) from a total of {received_instances} different roles!", silent=True)
			else:
				await channel.send(f"`You already collected! Reset in: {hours_remaining} hours.`", silent=True)

		# overwrite, end
		self.overwrite_json(json_content)

		return "success", "success"


	#
	# ADD MONEY BY ROLE
	#

	async def add_money_role(self, user, channel, username, user_pfp, server_object, income_role, amount_added):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_income_roles = json_content["income_roles"]

		# pretty straight forward i think.
		# first, we go into each role object
		# then we check in everyones roles if they have the role

		role = discord.utils.get(server_object.roles, id=int(income_role))
		for member in role.members:
			try:
				# also to create user in case he isnt registered yet
				user_index, new_data = self.find_index_in_db(json_content["userdata"], member.id)

				json_user_content = json_content["userdata"][user_index]
				json_user_content["bank"] += int(amount_added)
				# overwrite
				json_content["userdata"][user_index] = json_user_content

			except:
				pass

		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(
			description=f"✅ You have added {self.currency_symbol} {'{:,}'.format(int(amount_added))} to a total of {'{:,}'.format(int(len(role.members)))} users with that role !",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["income_roles"] = json_income_roles
		self.overwrite_json(json_content)

		return "success", "success"
	
	#
	# REMOVE MONEY BY ROLE
	#

	async def remove_money_role(self, user, channel, username, user_pfp, server_object, income_role, amount_removed):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_income_roles = json_content["income_roles"]

		# pretty straight forward i think.
		# first, we go into each role object
		# then we check in everyones roles if they have the role

		role = discord.utils.get(server_object.roles, id=int(income_role))
		for member in role.members:
			try:
				# also to create user in case he isnt registered yet
				user_index, new_data = self.find_index_in_db(json_content["userdata"], member.id)

				json_user_content = json_content["userdata"][user_index]
				if json_user_content["bank"] - int(amount_removed) < 0:
					json_user_content["bank"] = 0
				else:
					json_user_content["bank"] -= int(amount_removed)
				# overwrite
				json_content["userdata"][user_index] = json_user_content

			except:
				pass

		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(
			description=f"✅ You have removed {self.currency_symbol} {'{:,}'.format(int(amount_removed))} from a total of {'{:,}'.format(int(len(role.members)))} users with that role !",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["income_roles"] = json_income_roles
		self.overwrite_json(json_content)

		return "success", "success"
	
	# 
	# DICE ROLLER
	#

	async def roll(self, user, channel):
		color = self.discord_blue_rgb_code
		embed = discord.Embed(color=color)
		embed.add_field(name=f"**You Rolled:**", value = f"**{random.randint(1, 20)}**", inline=False)
		await channel.send(embed=embed)
		return "success", "success"

	#
	# ECONOMY STATS
	#

	async def economy_stats(self, user, channel, username, user_pfp, server_object):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		
		total_cash, total_bank, total_total = 0, 0, 0
		
		for i in range(len(json_content["userdata"])):
			total_cash += json_content["userdata"][i]["cash"]
			total_bank += json_content["userdata"][i]["bank"]
			
		total_total = total_cash + total_bank

		# inform user
		color = self.discord_blue_rgb_code
		embed = discord.Embed(color=color)
		embed.add_field(name=f"**Total Cash:**", value=f"{self.currency_symbol} {'{:,}'.format(int(total_cash))}", inline=False)
		embed.add_field(name=f"**Total Bank:**", value=f"{self.currency_symbol} {'{:,}'.format(int(total_bank))}", inline=False)
		embed.add_field(name=f"**Total:**", value=f"{self.currency_symbol} {'{:,}'.format(int(total_total))}", inline=False)
		embed.set_author(name="Economy Stats", icon_url="https://upload.wikimedia.org/wikipedia/commons/5/5e/Map_symbol_museum_02.png")
		await channel.send(embed=embed)

		return "success", "success"
