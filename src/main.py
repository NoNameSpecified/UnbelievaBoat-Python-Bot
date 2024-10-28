
# --------- Info and general informations -----------

"""
INFO
  Official Repo: https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot

	This is a discord bot written in python, designed to copy some of Unbelievaboat's functions,
	  but add custom stuff to it (e.g no balance limit, automatic balance increase etc)

	The Discord things are from the discord API (import discord)

	the databses are stored in database/ and handled by database/__init__.py
	  that name is chosen to make it something easily importable

	some of these functions and methods are based on another Bot i made, https://github.com/NoNameSpecified/selenor
"""

# --------- BOT CODE BELOW -----------



"""

// INIT

"""

# imports
import json
import discord
import random
from discord.ext.commands import Bot
# custom database handler
import database
from time import sleep
# check img url
import requests, asyncio


with open('config.json', 'r') as cfg:
  # Deserialize the JSON data (essentially turning it into a Python dictionary object so we can use it in our code) 
  config = json.load(cfg) 
  
# init discord stuff and json handling
BOT_PREFIX = ("+")  # tupple in case we'd need multiple
token = config["token"]
# emojis
emoji_worked = "✅"
emoji_error = "❌"
discord_error_rgb_code = discord.Color.from_rgb(239, 83, 80)
intents = discord.Intents.all()
client = Bot(command_prefix=BOT_PREFIX, intents=intents)  # init bot
db_handler = database.pythonboat_database_handler(client)  # ("database.json")


"""

// GLOBAL FUNCTIONS

"""

async def get_user_input(message, default_spell=True):
	print("Awaiting User Entry")
	# we want an answer from the guy who wants to give an answer
	answer = await client.wait_for("message", check=lambda response: response.author == message.author and response.channel == message.channel)
	answer = answer.content
	# clean input
	if default_spell:
		answer = answer.lower().strip()

	return answer

async def get_user_id(param):
	reception_user_beta = str(param[1])  # the mention in channel gives us <@!USERID> OR <@USERIRD>
	reception_user = ""
	for i in range(len(reception_user_beta)):
		try:
			reception_user += str(int(reception_user_beta[i]))
		except:
			pass
	return reception_user

async def get_role_id_multiple(user_input):
	roles = user_input.split(" ")  # so we get a list
	roles_clean = []

	for i in range(len(roles)):
		current_role = roles[i]
		new_current_role = ""
		for i in range(len(current_role)):
			try:
				new_current_role += str(int(current_role[i]))
			except:
				pass
		roles_clean.append(new_current_role)
	return roles_clean

async def get_role_id_single(parameter):
	role_beta = str(parameter)  # see another instance where i use this to see why
	role_clean = ""
	for i in range(len(role_beta)):
		try:
			role_clean += str(int(role_beta[i]))
		except:
			pass
	return role_clean

async def send_embed(title, description, channel, color="default"):
	# some default colors
	colors = [0xe03ca5, 0xdd7b28, 0x60c842, 0x8ae1c2, 0x008c5a, 0xc5bcc5]
	if color == "default": color = 0xe03ca5
	# create the embed
	embed = discord.Embed(title=title, description=description, color=color)
	await channel.send(embed=embed)
	return


async def send_error(channel):
	embed = discord.Embed(title="Error.", description="Internal Error, call admin.", color=0xff0000)
	await channel.send(embed=embed)
	return


# ~~~ set custom status ~~~
@client.event
async def on_ready():
	activity = discord.Game(name=f"My default prefix is <{BOT_PREFIX}>")
	await client.change_presence(status=discord.Status.online, activity=activity)
	# log_channel = 807057317396217947 # in your server, select a channel you want log info to be sent to
									# rightclick and copy id. put the id here. it should look like this : 807057317396217947
	"""
	NEED LOG CHANNEL ID
	"""
	# channel = client.get_channel(log_channel)
	# await channel.send("running")


	# check json, putting it here because has to be in a async function
	check_status = await db_handler.check_json()

	if check_status == "error":
		# channel = client.get_channel(log_channel)
		color = discord_error_rgb_code
		embed = discord.Embed(description=f"Critical error. JSON file is corrupted or has missing variables.\n\n"
										# f"`Error` code : {error_info}`\n" # -- Possibly to add
										  f" Please contact an admin or delete the JSON database, but do a backup before -\n"
										  f"this will result in re-creating the default config but will also **delete all user data**\n\n", color=color)
		embed.set_author(name="UnbelievaBoat-Python Bot", icon_url="https://blog.learningtree.com/wp-content/uploads/2017/01/error-handling.jpg")
		embed.set_footer(text="tip: default config at https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot")
		# await channel.send(embed=embed)
		quit()

	db_handler.get_currency_symbol()

"""

USER-BOT INTERACTION

"""
not_done = False
@client.event
async def on_message(message):
	"""
	start general variable definition
	"""
	global not_done
	# check if message is for our bot
	if not ( message.content.startswith(BOT_PREFIX) ) : return 0;

	# prefix checked, we can continue
	usedPrefix = message.content[0] # in case we would add more prefixes later
	# in selenor bot : check for case sensitive or not c.s. commands, not needed for this bot,
	# make it a clean input
	command = message.content.split(usedPrefix)[1].lower().split(" ")

	# stop if not meant for bot. (like just a "?")
	if command[0] in ["", " "]: return 0;

	"""
	basically, if the command is :
		+give money blabla
		we take what is after the prefix and before everything else, to just get the command
		in this case : "give"
		edit : for now we just splitted it, pure command will be taken with command = command[0]
	this is to redirect the command to further handling
	"""
	# print(command) # for testing purposes

	param_index = 1
	param = ["none", "none", "none", "none"]
	command_updated = []
	# lets say our command says "remove-item <your mom>"

	try:
		for test_cmd in range(len(command)):
			if command[test_cmd].startswith('"') or command[test_cmd].startswith("'"):
				new_slide = ""
				temp_cmd = test_cmd
				while not(command[temp_cmd].endswith('"') or command[temp_cmd].endswith("'")):
					new_slide += command[temp_cmd] + " "
					temp_cmd += 1
				new_slide += command[temp_cmd]
				command_updated.append(new_slide[1:len(new_slide)-1])
				break
			elif command[test_cmd] in [" ", ""]:
				continue
			else:
				command_updated.append(command[test_cmd])
	except:
			await message.channel.send("Error. You maybe opened a single/doublequote or a < and didnt close it")
	command = command_updated
	# print(command)
	for param_index in range(len(command)):
		param[param_index] = command[param_index]
	print(f"Command called with parameters : {param}")
	# for use of parameters later on, will have to start at 0, not 1

	# ~~~~ GET DISCORD VARIABLES for use later on
	# to directly answer in the channel the user called in
	channel = message.channel
	server = message.guild
	user = message.author.id
	user_mention = message.author.mention
	user_pfp = message.author.display_avatar.url
	username = str(message.author)
	nickname = str(message.author.display_name)
	user_roles = [randomvar.id for randomvar in message.author.roles]

	# some stuff will be only for staff, which will be recognizable by the botmaster role
	staff_request = 0
	for role_to_check in message.author.roles:
		if role_to_check.name == "botmaster": staff_request = 1
	print("staff status : ", staff_request)
	command = command[0]

	#

	"""
	START PROCESSING COMMANDS
	"""

	"""

	possible improvements : everything in int, not float
							all displayed numbers with "," as thousands operator
							people can enter amounts with thousands operator
	"""

	"""
		REGULAR COMMANDS (not staff only)
	"""
	# list of commands # their aliases, to make the help section easier
	all_reg_commands_aliases = {
		"blackjack" : "bj",
		"roulette"  : "",
		"slut": "",
		"crime": "",
		"work": "",
		"rob": "steal",
		"balance": "bal",
		"deposit": "dep",
		"withdraw": "with",
		"give": "pay",
		"leaderboard": "lb",
		"help": "info",
		"module": "moduleinfo",
		"use": "use-item"
	}
	all_reg_commands = list(all_reg_commands_aliases.keys())

	# --------------
	# BLACKJACK GAME
	# --------------

	if command in [ "blackjack", all_reg_commands_aliases["blackjack"] ]:
		if "none" in param[1] or param[2] != "none": # only bj <bet> ; nothing more than that 1 parameter
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`blackjack <amount or all>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		bet = param[1]
		# either all or an amount, not some random string
		if bet != "all":
			try:
				# they can use the thousands separator comma
				newAmount = []
				for char in bet:
					if char != ",":
						newAmount.append(char)
				bet = "".join(newAmount)
				bet = int(bet)
				if bet < 100:
					color = discord_error_rgb_code
					embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount or all>` argument given. Bet must be at least 100.\n", color=color)
					embed.set_author(name=username, icon_url=user_pfp)
					await channel.send(embed=embed)
					return
			except:
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount or all>` argument given.\n\nUsage:\n`roulette <amount or all> <space>`", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		bet = str(bet)


		try:
			# gotta check if enough money, if bet enough, etc etc then do the actual game
			status, bj_return = await db_handler.blackjack(user, bet, client, channel, username, user_pfp, message)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{bj_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
		# "success" case where code doesnt fail is answering client directly in handler
		# same for all other games
		return

	# --------------
	# ROULETTE GAME
	# --------------

	# ATTENTION : for now roulette is only playable by ONE person, multiple can't play at once

	elif command in [ "roulette", all_reg_commands_aliases["roulette"] ]: # no alias
		if "none" in param[1] or "none" in param[2]: # we need 2 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`roulette <amount or all> <space>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		bet = param[1]
		# either all or an amount, not some random string
		if bet != "all":
			try:
				# they can use the thousands separator comma
				newAmount = []
				for char in bet:
					if char != ",":
						newAmount.append(char)
				bet = "".join(newAmount)
				bet = int(bet)
				if bet < 100:
					color = discord_error_rgb_code
					embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount or all>` argument given. Bet must be at least 100.\n", color=color)
					embed.set_author(name=username, icon_url=user_pfp)
					await channel.send(embed=embed)
					return
			except:
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount or all>` argument given.\n\nUsage:\n`roulette <amount or all> <space>`", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		bet = str(bet)

		# space must be in second, and a valid space
		space = str(param[2])
		if space not in ["odd", "even", "black", "red"]:
			fail = 0
			try:
				space = int(space)
				if not(space >= 0 and space <= 36):
					fail = 1
			except Exception as e:
				print(e)
				fail = 1
			if fail == 1:
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  Invalid `<space>` argument given.\n\nUsage:\n`roulette <amount or all> <space>`", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		# convert to str, even if number. will be checked in the game itself later
		space = str(space)

		try:
			not_done = True
			# gotta check if enough money, if bet enough, etc etc then do the actual game
			status, roulette_return = await db_handler.roulette(user, bet, space, client, channel, username, user_pfp, user_mention)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{roulette_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
		# print("finished func")
		not_done = False
		return

	# --------------
	# 	  SLUT
	# --------------

	elif command in ["slut", all_reg_commands_aliases["slut"]]:  # no alias
		try:
			status, slut_return = await db_handler.slut(user, channel, username, user_pfp)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{slut_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# --------------
	# 	  CRIME
	# --------------

	elif command in ["crime", all_reg_commands_aliases["crime"]]:  # no alias
		try:
			status, crime_return = await db_handler.crime(user, channel, username, user_pfp)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{crime_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# --------------
	# 	  WORK
	# --------------

	elif command in ["work", all_reg_commands_aliases["work"]]:  # no alias
		try:
			status, work_return = await db_handler.work(user, channel, username, user_pfp)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{work_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		except Exception as e:
			print(e)
			await send_error(channel)



	# --------------
	# 	  ROB
	# --------------

	elif command in ["rob", all_reg_commands_aliases["rob"]]:  # no alias
		# you gotta rob someone
		if "none" in param[1] or param[2] != "none": # we only one param
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`rob <user>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		user_to_rob = await get_user_id(param)

		try:
			status, rob_return = await db_handler.rob(user, channel, username, user_pfp, user_to_rob)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{rob_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# --------------
	#    BALANCE
	# --------------

	elif command in ["balance", all_reg_commands_aliases["balance"]]:
		# you can either check your own balance or someone else's bal
		if "none" in param[1]:
			# tell handler to check bal of this user
			userbal_to_check = user
			username_to_check = username
			userpfp_to_check = user_pfp
		# only one user to check, so only 1 param, if 2 -> error
		elif param[1] != "none" and param[2] != "none":
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `[user]` argument given.\n\nUsage:\n`balance <user>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return
		# else we want the balance of someone else
		else:
			userbal_to_check = await get_user_id(param)
			try:
				user_fetch = client.get_user(int(userbal_to_check))
				print("hello ?")
				username_to_check = user_fetch
				userpfp_to_check = user_fetch.avatar
			except:
				# we didnt find him
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  Invalid `[user]` argument given.\n\nUsage:\n`balance <user>`", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		# go through the handler
		try:
			await db_handler.balance(user, channel, userbal_to_check, username_to_check, userpfp_to_check, not_done)
		except Exception as e:
			print(e)
			await send_error(channel)

	# --------------
	# 	  DEP
	# --------------

	elif command in ["deposit", all_reg_commands_aliases["deposit"]]:
		if "none" in param[1] or param[2] != "none": # we need 1 and only 1 parameter
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`deposit <amount or all>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		amount = param[1]
		# either all or an amount, not some random string
		if amount != "all":
			try:
				# they can use the thousands separator comma
				newAmount = []
				for char in amount:
					if char != ",":
						newAmount.append(char)
				amount = "".join(newAmount)
				amount = int(amount)
				if amount < 1:
					color = discord_error_rgb_code
					embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount or all>` argument given.\n\nUsage:\n`deposit <amount or all>`", color=color)
					embed.set_author(name=username, icon_url=user_pfp)
					await channel.send(embed=embed)
					return
			except:
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount or all>` argument given.\n\nUsage:\n`deposit <amount or all>`", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		try:
			amount = str(amount)
			status, dep_return = await db_handler.deposit(user, channel, username, user_pfp, amount)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{dep_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# --------------
	# 	  WITH
	# --------------

	elif command in ["withdraw", all_reg_commands_aliases["withdraw"]]:
		if "none" in param[1] or param[2] != "none": # we need 1 and only 1 parameter
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`withdraw <amount or all>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		amount = param[1]
		# either all or an amount, not some random string
		if amount != "all":
			try:
				# they can use the thousands separator comma
				newAmount = []
				for char in amount:
					if char != ",":
						newAmount.append(char)
				amount = "".join(newAmount)
				amount = int(amount)
				if amount < 1:
					color = discord_error_rgb_code
					embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount or all>` argument given.\n\nUsage:\n`withdraw <amount or all>`", color=color)
					embed.set_author(name=username, icon_url=user_pfp)
					await channel.send(embed=embed)
					return
			except:
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount or all>` argument given.\n\nUsage:\n`withdraw <amount or all>`", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		try:
			amount = str(amount)
			status, with_return = await db_handler.withdraw(user, channel, username, user_pfp, amount)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{with_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# --------------
	# 	  GIVE
	# --------------

	elif command in ["give", all_reg_commands_aliases["give"]]:
		if "none" in param[1] or "none" in param[2]:  # we need 2 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(
				description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`give <member> <amount or all>`\nInfo: for items use give-item!",
				color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# we need to check validity of both parameters

		# CHECK 1

		reception_user = await get_user_id(param)

		try:
			user_fetch = client.get_user(int(reception_user))
			print(user_fetch)
			reception_user_name = user_fetch

			if int(reception_user) == user:
				# cannot send money to yourself
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  You cannot trade money with yourself. That would be pointless.\n"
												  f"(You may be looking for the `add-money` command.)", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		except:
			# we didnt find him
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<member>` argument given.\n\nUsage:"
											  f"\n`give <member> <amount or all>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# CHECK 2

		amount = param[2]
		# either all or an amount, not some random string
		if amount != "all":
			try:
				# they can use the thousands separator comma
				newAmount = []
				for char in amount:
					if char != ",":
						newAmount.append(char)
				amount = "".join(newAmount)
				amount = int(amount)
				if amount < 1:
					color = discord_error_rgb_code
					embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount or all>` argument given.\n\nUsage:\n`give <member> <amount or all>`", color=color)
					embed.set_author(name=username, icon_url=user_pfp)
					await channel.send(embed=embed)
					return
			except:
				color = discord_error_rgb_code
				embed = discord.Embed(
					description=f"{emoji_error}  Invalid `<amount or all>` argument given.\n\nUsage:\n`give <member> <amount or all>`",
					color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		# handler

		try:
			amount = str(amount)
			status, give_return = await db_handler.give(user, channel, username, user_pfp, reception_user, amount, reception_user_name)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{give_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# --------------
	#  LEADERBOARD
	# --------------

	elif command in ["leaderboard", all_reg_commands_aliases["leaderboard"]]:
		modes = ["-cash", "-bank", "-total"]
		page_number = 1
		mode_type = modes[2]
		server_name = server.name
		full_name = server_name  # + mode_type

		# first, vanilla
		if "none" in param[1] and "none" in param[2]:
			# using default vars
			page_number = 1
			mode_type = modes[2]
			full_name += " Leaderboard"
		# one argument
		elif param[1] != "none" and "none" in param[2]:
			if param[1] in modes:
				mode_type = param[1]
				page_number = 1
				if mode_type == "-total": full_name += " Leaderboard"
				if mode_type == "-cash": full_name += " Cash Leaderboard"
				if mode_type == "-bank": full_name += " Bank Leaderboard"
			else:
				try:
					page_number = int(param[1])
					mode_type = modes[2]
					full_name += " Leaderboard"
				except:
					color = discord_error_rgb_code
					embed = discord.Embed(
						description=f"{emoji_error}  Invalid `[-cash | -bank | -total]` argument given.\n\nUsage:\n"
									f"`leaderboard [page] [-cash | -bank | -total]`", color=color)
					embed.set_author(name=username, icon_url=user_pfp)
					await channel.send(embed=embed)
					return
		# two arguments
		else:
			try:
				page_number = int(param[1])
				mode_type = param[2]
				if mode_type == "-total": full_name += " Leaderboard"
				elif mode_type == "-cash": full_name += " Cash Leaderboard"
				elif mode_type == "-bank": full_name += " Bank Leaderboard"
				else:
					color = discord_error_rgb_code
					embed = discord.Embed(
						description=f"{emoji_error}  Invalid `[-cash | -bank | -total]` argument given.\n\nUsage:\n"
									f"`leaderboard [page] [-cash | -bank | -total]`", color=color)
					embed.set_author(name=username, icon_url=user_pfp)
					await channel.send(embed=embed)
					return
			except:
				color = discord_error_rgb_code
				embed = discord.Embed(
					description=f"{emoji_error}  Invalid `[-cash | -bank | -total]` argument given.\n\nUsage:\n"
								f"`leaderboard [page] [-cash | -bank | -total]`", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		print(f"Looking for {full_name}, at page {page_number}, in mode {mode_type}")

		# handler

		try:
			status, lb_return = await db_handler.leaderboard(user, channel, username, full_name, page_number, mode_type, client)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{lb_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# --------------
	#     HELP
	# --------------

	elif command in ["help", all_reg_commands_aliases["help"]]:
		color = discord.Color.from_rgb(3, 169, 244)
		embed = discord.Embed(title=f"Help System", color=color)
		embed.add_field(name="stats", value=f"Usage: `stats`", inline=False)

		embed.add_field(name=all_reg_commands[0], value=f"Alias: {all_reg_commands_aliases[all_reg_commands[0]]}  |  "
														f"Usage: `blackjack <amount or all>`", inline=False)
		embed.add_field(name=all_reg_commands[1], value=f"Alias: {all_reg_commands_aliases[all_reg_commands[1]]}  |  "
														f"Usage: `roulette <amount or all> <space>`", inline=False)
		embed.add_field(name=all_reg_commands[2], value=f"Alias: {all_reg_commands_aliases[all_reg_commands[2]]}  |  "
												f"Usage: `slut`", inline=False)
		embed.add_field(name=all_reg_commands[3], value=f"Alias: {all_reg_commands_aliases[all_reg_commands[3]]}  |  "
												f"Usage: `crime`", inline=False)
		embed.add_field(name=all_reg_commands[4], value=f"Alias: {all_reg_commands_aliases[all_reg_commands[4]]}  |  "
												f"Usage: `work`", inline=False)
		embed.add_field(name=all_reg_commands[5], value=f"Alias: {all_reg_commands_aliases[all_reg_commands[5]]}  |  "
													f"Usage: `rob`", inline=False)
		embed.add_field(name=all_reg_commands[6], value=f"Alias: {all_reg_commands_aliases[all_reg_commands[6]]}  |  "
													f"Usage: `balance`", inline=False)
		embed.add_field(name=all_reg_commands[7], value=f"Alias: {all_reg_commands_aliases[all_reg_commands[7]]}  |  "
													f"Usage: `deposit <amount>`", inline=False)
		embed.add_field(name=all_reg_commands[8], value=f"Alias: {all_reg_commands_aliases[all_reg_commands[8]]}  |  "
													f"Usage: `withdraw <amount>`", inline=False)
		embed.add_field(name=all_reg_commands[9], value=f"Alias: {all_reg_commands_aliases[all_reg_commands[9]]}  |  "
												f"Usage: `give <member> <amount or all>`", inline=False)
		embed.add_field(name=all_reg_commands[10], value=f"Alias: {all_reg_commands_aliases[all_reg_commands[10]]}  |  "
													f"Usage: `leaderboard [page] [-cash | -bank | -total]`", inline=False)
		embed.add_field(name=all_reg_commands[11], value=f"Alias: {all_reg_commands_aliases[all_reg_commands[11]]}  |  "
													f"Usage: `help` - shows this", inline=False)
		embed.add_field(name=all_reg_commands[12], value=f"Alias: {all_reg_commands_aliases[all_reg_commands[12]]}  |  "
													f"Usage: `module <module, e.g. slut>`", inline=False)
		# edit stuff
		embed.set_footer(text="For more info, contact an admin or <kendrik2.0>")
		await channel.send(embed=embed)

		#### in 2 parts because one was too long

		embed = discord.Embed(title=f"Help System", color=color)
		embed.add_field(name="----------------------\n\nSTAFF ONLY", value=f"requires <botmaster> role", inline=False)
		embed.add_field(name="add-money", value=f"Usage: `add-money <member> <amount>`", inline=False)
		embed.add_field(name="remove-money", value=f"Usage: `remove-money <member> <amount> [cash/bank]`", inline=False)
		embed.add_field(name="remove-money-role", value=f"Usage: `remove-money-role <role> <amount>`", inline=False)
		embed.add_field(name="change", value=f"Usage: `change <module> <variable> <new value>`", inline=False)
		embed.add_field(name="change-currency", value=f"Usage: `change-currency <new emoji name>`", inline=False)
		embed.add_field(name="set-income-reset", value=f"Usage: `set-income-reset <false/true>`", inline=False)
		embed.add_field(name="remove-user-item", value=f"Usage: `remove-user-item <member> <item short name> <amount>`", inline=False)
		embed.add_field(name="spawn-item", value=f"Usage: `spawn-item <player pinged> <item short name> [amount]`", inline=False)
		embed.add_field(name="clean-leaderboard", value=f"Usage: `clean-leaderboard` - remove gone users", inline=False)
		embed.add_field(name="----------------------\n\nITEM HANDLING", value=f"create and delete requires <botmaster> role", inline=False)
		embed.add_field(name="create-item", value=f"Usage: `create-item`", inline=False)
		embed.add_field(name="delete-item", value=f"Usage: `delete-item <item short name>`", inline=False)
		embed.add_field(name="buy-item", value=f"Usage: `buy-item <item short name> <amount>`", inline=False)
		embed.add_field(name="give-item", value=f"Usage: `give-item <member> <item short name> <amount>`", inline=False)
		embed.add_field(name="use", value=f"Usage: `use <item short name> <amount>`", inline=False)
		embed.add_field(name="inventory", value=f"Usage: `inventory [page]`", inline=False)
		embed.add_field(name="user-inventory", value=f"Usage: `user-inventory <member> [page]`", inline=False)
		embed.add_field(name="catalog", value=f"Usage: `catalog [item short name]`", inline=False)
		embed.add_field(name="----------------------\n\nINCOME ROLES", value=f"create, delete and update requires <botmaster> role", inline=False)
		embed.add_field(name="add-income-role", value=f"Usage: `add-income-role <role pinged> <income>`", inline=False)
		embed.add_field(name="remove-income-role", value=f"Usage: `remove-income-role <role pinged>`", inline=False)
		embed.add_field(name="list-roles", value=f"Usage: `list-roles`", inline=False)
		embed.add_field(name="collect", value=f"Usage: `collect` | get your salary. If you choose to use update-income, please disable this command.", inline=False)
		embed.add_field(name="update-income", value=f"Usage: `update-income` | income works DAILY! automatically updates ALL INCOMES time elapsed * income.", inline=False)
		# edit stuff
		embed.set_footer(text="For more info, contact an admin or <kendrik2.0>")

		await channel.send(embed=embed)

	# --------------
	#  MODULE INFO
	# --------------

	elif command in ["module", all_reg_commands_aliases["module"]]:
		if "none" in param[1] or param[2] != "none":  # we need 1 and only 1 parameter
			color = discord_error_rgb_code
			embed = discord.Embed(
				description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`module <module>`",
				color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		module = param[1]

		# handler

		try:
			status, module_return = await db_handler.module(user, channel, module)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{module_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

		"""
			STAFF COMMANDS
		"""

	# --------------
	#   ADD-MONEY
	# --------------

	elif command == "add-money":
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1] or "none" in param[2]:  # we need 2 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`add-money <member> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# we need to check validity of both parameters

		# CHECK 1

		reception_user = await get_user_id(param)
		try:
			user_fetch = client.get_user(int(reception_user))
			print(user_fetch)
			reception_user_name = user_fetch

		except:
			# we didnt find him
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<member>` argument given.\n\nUsage:"
											  f"\n`add-money <member> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# CHECK 2

		amount = param[2]
		try:
			# they can use the thousands separator comma
			newAmount = []
			for char in amount:
				if char != ",":
					newAmount.append(char)
			amount = "".join(newAmount)
			amount = int(amount)
			if amount < 1:
				color = discord_error_rgb_code
				embed = discord.Embed(
					description=f"{emoji_error}  Invalid `<amount>` argument given.\n\nUsage:\n`add-money <member> <amount>`",
					color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount>` argument given.\n\nUsage:\n`add-money <member> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# handler

		try:
			amount = str(amount)
			status, add_money_return = await db_handler.add_money(user, channel, username, user_pfp, reception_user, amount, reception_user_name)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{add_money_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# --------------
	#  REMOVE-MONEY
	# --------------

	elif command == "remove-money":
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1] or "none" in param[2]:  # we need 3 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`remove-money <member> <amount> [cash/bank]`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# we need to check validity of both parameters

		# CHECK 1

		reception_user = await get_user_id(param)

		try:
			user_fetch = client.get_user(int(reception_user))
			print(user_fetch)
			reception_user_name = user_fetch

		except:
			# we didnt find him
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<member>` argument given.\n\nUsage:"
											  f"\n`remove-money <member> <amount> [cash/bank]`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# CHECK 2

		amount = param[2]
		try:
			# they can use the thousands separator comma
			newAmount = []
			for char in amount:
				if char != ",":
					newAmount.append(char)
			amount = "".join(newAmount)
			amount = int(amount)
			if amount < 1:
				color = discord_error_rgb_code
				embed = discord.Embed(
					description=f"{emoji_error}  Invalid `<amount>` argument given.\n\nUsage:\n`remove-money <member> <amount> [cash/bank]`",
					color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount>` argument given.\n\nUsage:\n`remove-money <member> <amount> [cash/bank]`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# CHECK 3
		mode = "bank"
		if param[3] != "none":
			if param[3] in ["cash", "bank"]:
				mode = param[3]
			else:
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  Invalid `[cash/bank]` argument given.\n\nUsage:"
												  f"\n`remove-money <member> <amount> [cash/bank]`", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		# handler

		try:
			amount = str(amount)
			status, rm_money_return = await db_handler.remove_money(user, channel, username, user_pfp, reception_user, amount, reception_user_name, mode)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{rm_money_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# --------------
	#   EDIT VARS
	# --------------

	elif command in ["change", "edit"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1] or "none" in param[2] or "none" in param[3]:  # we need 3 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`change <module> <variable> <new value>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# that would end up messing everything up
		if param[2] == "name":
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  You cannot change module names.", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# we need to check validity of new value parameter
		# other checks will be done in the handler

		# CHECK
		module_name = param[1]
		variable_name = param[2]
		new_value = param[3]
		try:
			new_value = int(new_value)
		except:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<new value>` argument given.\n\nUsage:\n`change <module> <variable> <new value>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# handler

		try:
			new_value = str(new_value)
			status, edit_return = await db_handler.edit_variables(user, channel, username, user_pfp, module_name, variable_name, new_value)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{edit_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# ---------------------------
	#   CHANGE CURRENCY SYMBOL
	# ---------------------------

	elif command in ["change-currency", "edit_currency"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1]:  # we need 1 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`change-currency <new emoji name>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		new_emoji_name = param[1]

		# handler

		try:
			status, emoji_edit_return = await db_handler.change_currency_symbol(user, channel, username, user_pfp, new_emoji_name)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_edit_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# ---------------------------
	#   SET INCOME RESET
	# ---------------------------

	elif command in ["set-income-reset", "change-income-reset"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1]:  # we need 1 parameter
			color = discord_error_rgb_code
			embed = discord.Embed(
				description=f"{emoji_error}  Too few arguments given.\n\nUsage: `set-income-reset <false/true>`",
				color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if param[1] not in ["true", "false"]:  # and that param has to be true/false
			color = discord_error_rgb_code
			embed = discord.Embed(
				description=f"{emoji_error}  Too few arguments given.\n\nUsage: `set-income-reset <false/true>`",
				color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# ok so all checks done
		new_income_reset = param[1]

		# handler
		try:
			status, new_income_reset_return = await db_handler.set_income_reset(user, channel, username, user_pfp,
																				new_income_reset)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{new_income_reset_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)


		"""
			SPECIAL COMMANDS
		"""

	# ---------------------------
	#   ITEM CREATION / Create item
	# ---------------------------

	elif command in ["create-item", "new-item", "item-create"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		currently_creating_item = True
		checkpoints = 0
		last_report = ""
		color = discord.Color.from_rgb(3, 169, 244)
		# send a first input which we will then edit
		info_text = ":zero: What should the new item be called?\nThis name should be unique and no more than 200 characters.\nIt can contain symbols and multiple words."
		first_embed = discord.Embed(title="Item Info", description="Display Name\n.", color=color)
		first_embed.set_footer(text="Type cancel to quit")
		await channel.send(info_text, embed=first_embed)

		while currently_creating_item:
			# get input first
			user_input = await get_user_input(message, default_spell=False)
			print("at checkpoint ", checkpoints, "\ninput is ", user_input)
			# check if user wants cancel
			if user_input == "cancel":
				await channel.send(f"{emoji_error}  Cancelled command.")
				return

			if checkpoints == 0:
				# check 0: display name
				if len(user_input) > 200:
					await channel.send(f"{emoji_error} The maximum length for an items name is 200 characters. Please try again.")
					continue
				elif len(user_input) < 3:
					await channel.send(f"{emoji_error}  The minimum length for an items name is 3 characters. Please try again.")
					continue
				# good input
				item_display_name = user_input
				first_embed = discord.Embed(title="Item Info", color=color)
				first_embed.add_field(name="Display Name", value=f"{item_display_name}")
				first_embed.set_footer(text="Type cancel to quit")
				next_info = ":one: Now we need a short name, which users will use when buying, giving etc. Only one word ! (you can use dashes and underscores)"
				last_report = await channel.send(next_info, embed=first_embed)
				checkpoints += 1
				#item_name = await get_user_input(message)
				#print(item_name)
				trial = 0

			if checkpoints == 1:
				trial +=1
				item_name = await get_user_input(message) if trial == 1 else user_input

				# check 1: name
				if len(item_name) > 10:
					await channel.send(f"{emoji_error} The maximum length for an items short name is 10 characters. Please try again.")
					continue
				elif len(item_name) < 3:
					await channel.send(f"{emoji_error}  The minimum length for an items short name is 3 characters. Please try again.")
					continue
				elif " " in item_name.strip():
					print(f"-{item_name}- -{item_name.strip()}")
					await channel.send(f"{emoji_error}  short name has to be ONE word (dashes or underscores work).")
					continue
				# good input
				first_embed.add_field(name="Short name", value=f"{item_name}")
				first_embed.set_footer(text="Type cancel to quit")
				next_info = ":two: How much should the item cost to purchase?"
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 2:
				# check 2: cost
				try:
					cost = int(user_input)
					if cost < 1:
						await channel.send(f"{emoji_error}  Invalid price given. Please try again or type cancel to exit.")
						continue
				except:
					await channel.send(f"{emoji_error}  Invalid price given. Please try again or type cancel to exit.")
					continue
				first_embed.add_field(name="Price", value=f"{cost}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ":three: Please provide a description of the item.\nThis should be no more than 200 characters."
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 3:
				# check 3: description
				if len(user_input) > 200:
					await channel.send(f"{emoji_error} The maximum length for an items description is 200 characters. Please try again.")
					continue
				if user_input.lower() == "skip":
					description = "none"
				else:
					description = user_input
				first_embed.add_field(name="Description", value=f"{description}", inline=False)
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ":four: How long should this item stay in the store ? (integer, in days)\nMinimum duration is 1 day.\nIf no limit, just reply `skip`."
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 4:
				# check 4: duration
				try:
					duration = int(user_input)
					if duration < 1:
						await channel.send(f"{emoji_error}  Invalid time duration given. Please try again or type cancel to exit.")
						continue
				except:
					if user_input.lower() == "skip":
						#duration = "none"
						duration = 99999 # the problem is that database.py always wants an int to calculate an expiration date.
									   # so ill just put it to 993 days for now, maybe ill add a real fix later
									   # edit: now changed to 99999 which should be enough, will show as "unlimited"
					else:
						await channel.send(f"{emoji_error}  Invalid time duration given. Please try again or type cancel to exit.")
						continue
				if duration == 99999:
					duration_str = "unlimited"
				else:
					duration_str = int(user_input)
				first_embed.add_field(name="Time remaining", value=f"{duration} days left")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ":five: How much stock of this item will there be?\nIf unlimited, just reply `skip` or `infinity`."
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 5:
				# check 5: stock
				try:
					stock = int(user_input)
					if stock < 1:
						await channel.send(f"{emoji_error}  Invalid stock amount given. Please try again or type cancel to exit.")
						continue
				except:
					if user_input.lower() == "skip" or user_input.lower() == "infinity":
						stock = "unlimited"
					else:
						await channel.send(f"{emoji_error}  Invalid stock amount given. Please try again or type cancel to exit.")
						continue

				first_embed.add_field(name="Stock remaining", value=f"{stock}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ":six: What is the MAX amount of this item per user that should be allowed ?\nIf none, just reply `skip`."
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 6:
				# check 6: max amount of item
				try:
					max_amount = int(user_input)
					if max_amount < 1:
						await channel.send(f"{emoji_error}  Invalid max amount given. Please try again or type cancel to exit.")
						continue
				except:
					if user_input.lower() == "skip" or user_input.lower() == "infinity":
						max_amount = "unlimited"
					else:
						await channel.send(f"{emoji_error}  Invalid max amount given. Please try again or type cancel to exit.")
						continue

				first_embed.add_field(name="Max amount", value=f"{max_amount}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ":seven: What role(s) must the user already have in order to buy this item?\nIf none, just reply `skip`. For multiple, ping the roles with a space between them."
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 7:
				# check 7: required role
				try:
					if user_input in ["skip", "none"]:
						raise ValueError

					roles_clean_one = await get_role_id_multiple(user_input)

					required_roles = ""
					for role_id in roles_clean_one:
						try:
							role = discord.utils.get(server.roles, id=int(role_id))
							print(role)
							required_roles += f"{str(role.mention)} "
						except:
							await channel.send(f"{emoji_error}  Invalid role given. Please try again.")
							raise NameError

				except NameError:
					continue

				except ValueError:
					if user_input in ["skip", "none"]:
						required_roles = ["none"]

				except Exception as e:
					await channel.send(f"{emoji_error}  Invalid role given. Please try again.")
					continue
				try:
					roles_id_required = roles_clean_one
					print(roles_id_required)
				except:
					roles_id_required = ["none"]
				first_embed.add_field(name="Role required", value=f"{required_roles}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ":eight: What roles should make purchase of this item impossible ? (excluded role(s))?\nIf none, just reply `skip`. For multiple, ping them with a space between them."
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1
				
			elif checkpoints == 8:
				# check 8: excluded role - meaning you cant buy if possessing it.
				try:
					if user_input in ["skip", "none"]:
						raise ValueError

					roles_clean_two = await get_role_id_multiple(user_input)

					excluded_roles = ""
					for role_id in roles_clean_two:
						try:
							role = discord.utils.get(server.roles, id=int(role_id))
							print(role)
							excluded_roles += f"{str(role.mention)} "
						except:
							await channel.send(f"{emoji_error}  Invalid role given. Please try again.")
							raise NameError

				except NameError:
					continue

				except ValueError:
					if user_input in ["skip", "none"]:
						excluded_roles = ["none"]

				except Exception as e:
					await channel.send(f"{emoji_error}  Invalid role given. Please try again.")
					continue
				try:
					roles_id_excluded = roles_clean_two
					print(roles_id_excluded)
				except:
					roles_id_excluded = ["none"]
				first_embed.add_field(name="Excluded roles", value=f"{excluded_roles}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ":nine: What role(s) do you want to be given when this item is bought?\nIf none, just reply `skip`. For multiple, ping them with a space between them."
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 9:
				# check 9: role to be given when item bought
				try:
					if user_input in ["skip", "none"]:
						raise ValueError

					roles_clean_three = await get_role_id_multiple(user_input)

					roles_give = ""
					for role_id in roles_clean_three:
						try:
							role = discord.utils.get(server.roles, id=int(role_id))
							print(role)
							roles_give += f"{str(role.mention)} "
						except:
							await channel.send(f"{emoji_error}  Invalid role given. Please try again.")
							raise NameError

				except NameError:
					continue

				except ValueError:
					if user_input in ["skip", "none"]:
						roles_give = ["none"]

				except Exception as e:
					await channel.send(f"{emoji_error}  Invalid role given. Please try again.")
					continue

				try:
					roles_id_to_give = roles_clean_three
				except:
					roles_id_to_give = ["none"]
				first_embed.add_field(name="Role given", value=f"{roles_give}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ":keycap_ten: What role(s) do you want to be removed from the user when this item is bought?\nIf none, just reply `skip`. For multiple, ping with a space between them."
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 10:
				# check 10: role to be removed when item bought
				try:
					if user_input in ["skip", "none"]:
						raise ValueError

					roles_clean_four = await get_role_id_multiple(user_input)

					roles_remove = ""
					for role_id in roles_clean_four:
						try:
							role = discord.utils.get(server.roles, id=int(role_id))
							print(role)
							roles_remove += f"{str(role.mention)} "
						except:
							await channel.send(f"{emoji_error}  Invalid role given. Please try again.")
							raise NameError

				except NameError as b:
					print(b)
					continue

				except ValueError:
					if user_input in ["skip", "none"]:
						roles_remove = ["none"]

				except Exception as e:
					await channel.send(f"{emoji_error}  Invalid role given. Please try again.")
					continue

				try:
					roles_id_to_remove = roles_clean_four
				except:
					roles_id_to_remove = ["none"]
				first_embed.add_field(name="Role removed", value=f"{roles_remove}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = "`11` What is the maximum balanace a user can have in order to buy this item?\nIf none, just reply `skip`."
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 11:
				# check 11: max balance
				try:
					max_bal = int(user_input)
					if max_bal < 1:
						await channel.send(f"{emoji_error}  Invalid max balance given. Please try again or type cancel to exit.")
						continue
				except:
					if user_input.lower() == "skip":
						max_bal = "none"
					else:
						await channel.send(f"{emoji_error}  Invalid max balance given. Please try again or type cancel to exit.")
						continue
				first_embed.add_field(name="Maximum balance", value=f"{max_bal}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = "`12`: What message do you want the bot to reply with, when the item is bought?\nIf none, just reply `skip`."
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 12:
				# check 12: reply message
				if len(user_input) > 150:
					await channel.send(f"{emoji_error} The maximum length for a reply message is 150 characters. Please try again.")
					continue
				if user_input.lower() == "skip":
					user_input = f"Congrats on buying the item."
				reply_message = user_input
				first_embed.add_field(name="Reply message", value=f"{reply_message}", inline=False)
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = "`13`: What image should the item have? Enter complete url !\nIf none, just reply `skip`."
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 13:
				# check 13: item img
				if user_input.lower() == "skip":
					user_input = f"EMPTY"
					item_img_url = user_input
				else:
					try:
						rq = requests.get(user_input)
					except:
						await channel.send(f"{emoji_error} URL not found. Please try again or skip.")
						continue
	
					if rq.status_code != 200:
						await channel.send(f"{emoji_error} URL not found. Please try again or skip.")
						continue
					item_img_url = user_input
					first_embed.set_thumbnail(url=item_img_url)
				next_info = f"{emoji_worked}  Item created successfully!"
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints = -1
				# finished with the checks
				currently_creating_item = False

		# handler

		try:
			status, create_item_return = await db_handler.create_new_item(item_display_name, item_name, cost, description, duration, stock, max_amount, roles_id_required, roles_id_to_give, roles_id_to_remove, max_bal, reply_message, item_img_url, roles_id_excluded)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{create_item_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# ---------------------------
	#   DELETE ITEM - REMOVE ITEM
	# ---------------------------

	elif command in ["delete-item", "remove-item"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1]:  # we need 1 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`delete-item <item short name>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		item_name = param[1]

		# since this will completely remove the item
		# we should make sure you rly want to do this (and not remove-user-item).
		security_check = False
		sec_embed = discord.Embed(title="Attention", description="🚨 This will permanently delete the item, also for every user!\nDo you wish to continue? [y/N]", color=discord.Color.from_rgb(3, 169, 244))
		sec_embed.set_footer(text="Info: use remove-user-item to remove an item from a specific user.")
		await channel.send(embed=sec_embed)

		security_check_input = await get_user_input(message)
		if security_check_input.strip().lower() not in ["yes", "y"]:
			await channel.send(f"{emoji_error}  Cancelled command.")
			return

		# handler

		try:
			status, remove_item_return = await db_handler.remove_item(item_name)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{remove_item_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

		color = discord.Color.from_rgb(102, 187, 106) # green
		embed = discord.Embed(description=f"{emoji_worked}  Item has been removed from the store.\nNote: also deletes from everyone's inventory.", color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		return

	# ---------------------------
	#   REMOVE USER ITEM
	# ---------------------------

	elif command in ["remove-user-item"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1]:  # we need player pinged
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`remove-user-item <member> <item short name> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		player_ping = await get_user_id(param)

		try:
			user_fetch = client.get_user(int(player_ping))
			print(user_fetch)
			reception_user_name = user_fetch

		except:
			# we didnt find him
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<member>` argument given.\n\nUsage:"
											  f"\n`remove-user-item <member> <item short name> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[2]:  # we need item name
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`remove-user-item <member> <item short name> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return
		item_name = param[2]

		if "none" in param[3]:  # we need item amount
			amount = 1
		else:
			amount = param[3]

		try:
			amount = int(amount)
			if amount < 1:
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  Invalid `amount` given.\n\nUsage:\n`remove-user-item <member> <item short name> <amount>", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `amount` given.\n\nUsage:\n`remove-user-item <member> <item short name> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# handler

		try:
			status, remove_user_item_return = await db_handler.remove_user_item(user, channel, username, user_pfp, item_name, amount, player_ping, reception_user_name)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{remove_user_item_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
		return
	
	# ---------------------------
	#   REMOVE GONE USERS
	# ---------------------------

	elif command in ["clean-leaderboard", "clean-lb"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# since this will completely remove those users
		# we should make sure you rly want to do this.
		security_check = False
		sec_embed = discord.Embed(title="Attention", description="🚨 This will permanently delete all user instances that left the server!\nDo you wish to continue? [y/N]", color=discord.Color.from_rgb(3, 169, 244))
		await channel.send(embed=sec_embed)

		security_check_input = await get_user_input(message)
		if security_check_input.strip().lower() not in ["yes", "y"]:
			await channel.send(f"{emoji_error}  Cancelled command.")
			return

		# handler

		try:
			status, clean_lb_return = await db_handler.clean_leaderboard(server)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{clean_lb_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
			return

		color = discord.Color.from_rgb(102, 187, 106) # green
		embed = discord.Embed(description=f"{emoji_worked} {clean_lb_return} user(s) have been removed from database.", color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		return


	# ---------------------------
	#   BUY ITEM
	# ---------------------------

	elif command in ["buy-item", "get-item", "buy"]:
		# idk why i said you need botmaster to buy items ?
		"""
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return
		"""

		if "none" in param[1]:  # we need item name
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`buy-item <item short name> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return
		item_name = param[1]

		if "none" in param[2]:  # we need item amount
			amount = 1
		else:
			amount = param[2]

		try:
			amount = int(amount)
			if amount < 1:
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  Invalid `amount` given.\n\nUsage:\n`buy-item <item short name> <amount>`", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `amount` given.\n\nUsage:\n`buy-item <item short name> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# handler
		user_role_ids = [randomvar.id for randomvar in message.author.roles]

		try:
			status, buy_item_return = await db_handler.buy_item(user, channel, username, user_pfp, item_name, amount, user_role_ids, server, message.author)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{buy_item_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
		return

	# ---------------------------
	#   GIVE ITEM -- can also be used to "sell"
	#				but theyll need to not fuck each other and actually pay up
	# ---------------------------

	elif command in ["give-item"]:
		"""
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return
		"""

		if "none" in param[1]:  # we need player pinged
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`give-item <player pinged> <item short name> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		player_ping = await get_user_id(param)

		try:
			user_fetch = client.get_user(int(player_ping))
			print(user_fetch)
			reception_user_name = user_fetch
			print(reception_user_name)

			if int(player_ping) == user:
				# cannot send money to yourself
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  You cannot trade items with yourself. That would be pointless...", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		except:
			# we didnt find him
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<member>` argument given.\n\nUsage:"
											  f"\n`give-item <player pinged> <item> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[2]:  # we need item name
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`give-item <player pinged> <item short name> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return
		item_name = param[2]

		if "none" in param[3]:  # we need item amount
			amount = 1
		else:
			amount = param[3]

		try:
			amount = int(amount)
			if amount < 1:
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  Invalid `amount` given.\n\nUsage:\n`give-item <player pinged> <item short "
												  f"name> <amount>`", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `amount` given.\n\nUsage:\n`give-item <player pinged> <item short name> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# handler

		try:
			status, give_item_return = await db_handler.give_item(user, channel, username, user_pfp, item_name, amount, player_ping, server, message.author, reception_user_name, False) # false is for spawn_mode = False
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{give_item_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
		return

	# ---------------------------
	#   SPAWN ITEM
	#      if admins want to "give" someone an item without having to buy and then give it
	# ---------------------------

	elif command in ["spawn-item"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return


		if "none" in param[1]:  # we need player pinged
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`spawn-item <player pinged> <item short name> [amount]`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		player_ping = await get_user_id(param)

		try:
			user_fetch = client.get_user(int(player_ping))
			print(user_fetch)
			reception_user_name = user_fetch
			print(reception_user_name)

		except:
			# we didnt find him
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<member>` argument given.\n\nUsage:"
											  f"\n`spawn-item <player pinged> <item short name> [amount]`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[2]:  # we need item name
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`spawn-item <player pinged> <item short name> [amount]`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return
		item_name = param[2]

		if "none" in param[3]:  # we need item amount
			amount = 1
		else:
			amount = param[3]

		try:
			amount = int(amount)
			if amount < 1:
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  Invalid `amount` given.\n\nUsage:\n`spawn-item <player pinged> <item short name> [amount]`", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `amount` given.\n\nUsage:\n`spawn-item <player pinged> <item short name> [amount]`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# handler

		try:
			status, give_item_return = await db_handler.give_item(user, channel, username, user_pfp, item_name, amount, player_ping, server, message.author, reception_user_name, True) # True is for spawn_mode = True
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{give_item_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
		return

	# --------------
	# 	  USE ITEM     # this will MERELY remove the item from inventory
	# --------------

	elif command in ["use", all_reg_commands_aliases["use"]]:  # no alias

		if "none" in param[1]:  # we need an item used
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`use-item <item short name> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return
		else:
			item_used = param[1]

		if "none" in param[2]:  # we need item amount
			amount_used = 1     # by default it will be 1
		else:
			amount_used = param[2]
			try:
				amount_used = int(amount_used)
			except:
				color = discord_error_rgb_code
				embed = discord.Embed(
					description=f"{emoji_error}  Amount must be a (whole) integer.\n\nUsage:\n`use-item <item short name> <amount>`",
					color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		try:
			status, use_return = await db_handler.use_item(user, channel, username, user_pfp, item_used, amount_used)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{use_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		except Exception as e:
			print(e)
			await send_error(channel)

	# ---------------------------------------
	#   CHECK INVENTORY (check own inventory)
	# ---------------------------------------

	elif command in ["inventory"]:
		# by default, you look at your own inventory.
		# this is prob useless and its easier to just put user_to_check_uname=none in the func init.py
		# but for now this will do
		user_to_check, user_to_check_uname, user_to_check_pfp = "self", "self", "self"
		# or if for another member
		if param[1] == "none":
			page_number = 1
		else:
			try:
				page_number = int(param[1])
			except:
				color = discord_error_rgb_code
				embed = discord.Embed(
					description=f"{emoji_error}  Invalid page number.\n\nUsage:\n`inventory [page]`", color=color)
				embed.set_footer(text="info: use it without page once, output will show amount of total pages.\ninfo: use user-inventory to see inventory of another user.")
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		# handler

		try:
			status, inventory_return = await db_handler.check_inventory(user, channel, username, user_pfp, user_to_check, user_to_check_uname, user_to_check_pfp, page_number)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{inventory_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
		return

	# --------------------------------------------------------
	#   CHECK USER INVENTORY (check inventory of another user)
	# --------------------------------------------------------

	elif command in ["user-inventory"]:
		# by default, you look at your own inventory.
		# this is prob useless and its easier to just put user_to_check_uname=none in the func init.py
		# but for now this will do
		# or if for another member

		if "none" in param[1]:  # we need a member pinged
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`user-inventory <member> [page]`", color=color)
			embed.set_footer(text="info: use `inventory` to see your own inventory.")
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return
		else:
			# to get his id
			user_to_check = await get_user_id(param)

			try:
				# used for @-mention.

				user_to_check_uname_b = client.get_user(int(user_to_check))
				user_to_check_uname = user_to_check_uname_b.name  # idk why we need this but without it breaks
				user_to_check_pfp = user_to_check_uname_b.display_avatar
				if int(user_to_check) == user:
					user_to_check, user_to_check_uname, user_to_check_pfp = "self", "self", "self"
			except:
				# we didnt find him
				color = discord_error_rgb_code
				embed = discord.Embed(
					description=f"{emoji_error}  Invalid member ping.\n\nUsage:\n`user-inventory <member> [page]`", color=color)
				embed.set_footer(text="info: use `inventory` to see your own inventory.")
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		if param[2] == "none":
			page_number = 1
		else:
			try:
				page_number = int(param[2])
			except Exception as error_code:
				print(error_code)
				color = discord_error_rgb_code
				embed = discord.Embed(
					description=f"{emoji_error}  Invalid page number.\n\nUsage:\n`user-inventory <member> [page]`", color=color)
				embed.set_footer(text="info: use it without page once, output will show amount of total pages")
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return



		# handler

		try:
			status, inventory_return = await db_handler.check_inventory(user, channel, username, user_pfp, user_to_check, user_to_check_uname, user_to_check_pfp, page_number)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{inventory_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
		return

	# ---------------------------
	#   ITEMS CATALOG
	# ---------------------------

	elif command in ["catalog", "items", "item-list", "list-items"]:

		if "none" in param[1]:  # we need item name
			item_check = "default_list"
		else:
			item_check = param[1]

		# handler
		try:
			status, catalog_return = await db_handler.catalog(user, channel, username, user_pfp, item_check, server)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{catalog_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
		return


	# ---------------------------
	#   ADD ROLE INCOME ROLE
	# ---------------------------

	elif command in ["add-income-role", "add-role-income"]:
		await channel.send("Info: the income amount specified is an DAILY one.\nRemember: you need to manually update income.")
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1] or "none" in param[2]:  # we need 3 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`add-income-role <role pinged> <income>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# check role


		income_role = await get_role_id_single(param[1])

		try:
			role = discord.utils.get(server.roles, id=int(income_role))
		except Exception as e:
			print(e)
			await channel.send(f"{emoji_error}  Invalid role given.")
			return

		# check amount
		amount = param[2]
		# they can use the thousands separator comma
		try:
			newAmount = []
			for char in amount:
				if char != ",":
					newAmount.append(char)
			amount = "".join(newAmount)
			amount = int(amount)
			if amount < 1:
				color = discord_error_rgb_code
				embed = discord.Embed(
					description=f"{emoji_error}  Invalid `<amount>` argument given.\n\nUsage:\n`add-income-role <role pinged> <amount>`",
					color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount>` argument given.\n\nUsage:\n`add-income-role <role pinged> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# handler
		try:
			status, create_role_return = await db_handler.new_income_role(user, channel, username, user_pfp, income_role, amount)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{create_role_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
		return

	# ---------------------------
	#   REMOVE ROLE
	# ---------------------------

	elif command in ["remove-income-role", "delete-income-role", "remove-role-income", "delete-role-income"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1]:  # we need 1 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`remove-income-role <role pinged>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# check role

		income_role_beta = str(param[1])  # see another instance where i use this to see why
		income_role = ""
		for i in range(len(income_role_beta)):
			try:
				income_role += str(int(income_role_beta[i]))
			except:
				pass

		try:
			role = discord.utils.get(server.roles, id=int(income_role))
		except Exception as e:
			print(e)
			await channel.send(f"{emoji_error}  Invalid role given. Please try again.")
			return

		# handler
		try:
			status, remove_role_return = await db_handler.remove_income_role(user, channel, username, user_pfp, income_role)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{remove_role_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

		color = discord.Color.from_rgb(102, 187, 106)  # green
		embed = discord.Embed(description=f"{emoji_worked}  Role has been disabled as income role.", color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		return

	# ---------------------------
	#   REMOVE MONEY BY ROLE
	# ---------------------------

	elif command in ["remove-money-role", "remove-role-money"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1] or "none" in param[2]:  # we need 2 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(
				description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`remove-money-role <role pinged> <amount>`",
				color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		amount = param[2]
		try:
			# they can use the thousands separator comma
			newAmount = []
			for char in amount:
				if char != ",":
					newAmount.append(char)
			amount = "".join(newAmount)
			amount = int(amount)
			if amount < 1:
				color = discord_error_rgb_code
				embed = discord.Embed(
					description=f"{emoji_error}  Invalid `<amount>` argument given.\n\nUsage:\n`remove-money-role <role pinged> <amount>`",
					color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except:
			color = discord_error_rgb_code
			embed = discord.Embed(
				description=f"{emoji_error}  Invalid `<amount>` argument given.\n\nUsage:\n`remove-money-role <role pinged> <amount>`",
				color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# check role

		income_role = await get_role_id_single(param[1])

		try:
			role = discord.utils.get(server.roles, id=int(income_role))
		except Exception as e:
			print(e)
			await channel.send(f"{emoji_error}  Invalid role given. Please try again.")
			return

		# handler
		try:
			status, remove_money_role_return = await db_handler.remove_money_role(user, channel, username, user_pfp, server, income_role, amount)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{remove_money_role_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
		return

	# ---------------------------
	#   LIST INCOME ROLES
	# ---------------------------

	elif command in ["list-roles", "list-income-roles", "list-role-income", "list-incomes"]:
		try:
			status, list_roles_return = await db_handler.list_income_roles(user, channel, username, user_pfp, server)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{list_roles_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
		return

	# ---------------------------
	#   UPDATE INCOMES
	# ---------------------------

	elif command in ["update-income"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		try:
			status, update_incomes_return = await db_handler.update_incomes(user, channel, username, user_pfp, server)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{update_incomes_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

		color = discord.Color.from_rgb(102, 187, 106)  # green
		embed = discord.Embed(description=f"{emoji_worked}  Users with registered roles have received their income (into bank account).", color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		return


	# ---------------------------
	#   UPDATE INCOME FOR YOURSELF ONLY
	# ---------------------------

	elif command in ["collect", "get-salary", "update-income-solo"]:

		try:
			status, update_incomes_return = await db_handler.update_incomes_solo(user, channel, username, user_pfp, server, user_roles)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{update_incomes_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

		"""
		color = discord.Color.from_rgb(102, 187, 106)  # green
		embed = discord.Embed(description=f"{emoji_worked}  You have received {update_incomes_return} for your roles {roles_return} (into bank account).", color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)
		"""
		return
	
	
	# ---------------------------
	#   economy stats
	# ---------------------------

	elif command in ["stats", "economy-stats", "statistics"]:

		try:
			status, economy_stats_return = await db_handler.economy_stats(user, channel, username, user_pfp, server)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{economy_stats_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
			
			
		return


"""
END OF CODE.
	-> starting bot
"""

print("Starting bot")
client.run(token)
