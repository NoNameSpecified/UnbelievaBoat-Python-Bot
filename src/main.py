# --------- Info and general information -----------

"""
INFO for >> SKENDER DISCORD BOT <<

	Official Repo: https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot

    This is a discord bot written in python, designed to copy some of Unbelievaboat's functions,
      but add custom stuff to it (e.g. no balance limit, automatic balance increase etc.)

  	Over time, there have been a lot of added functionalities. The goal is to give everyone
      a template source code of a running bot, that they can download to run their own bot version,
      tweak it and edit it as they wish. If you need help regarding this, feel free
      to message me (see contact information on the GitHub repository or my GitHub profile page).

    For all possibilities, please see command-list.md and version-info.md in the official repository.

    The Discord things are from the discord API (import discord)

    the database (SQLite) is stored in database/ and handled by database/__init__.py
"""

# imports
import discord
from discord.ext.commands import Bot

# the actual "bot" part where everything runs.
from bot import SkenderBot

# maybe don't change the bot version (see version-info.md)
BOT_VERSION = "2.2"			# important for later updates to the bot, in case you need to use a migration script.

"""
	ADD WANTED EDITS HERE (lines 40-50).
"""

# ~~~ specific to each Skender bot ~~~

# Prefix for the bot.
BOT_PREFIX = ("+")			# you can add more prefixes with a comma (tuple).
# this will be shown as a "game" the bot is playing (essentially, this is like the bot's "status").
BOT_ACTIVITY = f"My default prefix is {BOT_PREFIX}"
# set this to whatever role only people who are supposed to be able to use the bot as admins will have.
ADMIN_ROLE = "botmaster" # just the role name.
# --> add your own token here !
token = "putyourtokenhere"
# The discord CHANNEL ID you want set up the bot in. There will be a WALKTHROUGH on the first run.
# if this returns an error, the bot will be set up with all values set to default.
# So please choose one and, if possible, one that only admins can access !
SETUP_CHANNEL_ID = # info: on pc, right-click on a channel and click "Copy channel ID". It's a long number.



# ~~~ init discord and bot ~~~
intents = discord.Intents.all()
client = Bot(command_prefix=BOT_PREFIX, intents=intents)  # init bot
skender = SkenderBot(client, ADMIN_ROLE, BOT_PREFIX)

# ~~~ set custom status ~~~
@client.event
async def on_ready():
	# launch the database handler and check database, get the bot running, load the currency emoji.
	await skender.on_ready(BOT_ACTIVITY, SETUP_CHANNEL_ID)

# ~~~ react if we manage a message ~~~
@client.event
async def on_message(message):
	# for level and passive chat income things
	await skender.handle_message_xp_and_passive_income(message)
	# handle "normal" messages, e.g. '+balance'
	await skender.handle_message(message)

print(f"Starting bot on version {BOT_VERSION}")
client.run(token)


#
#  If you run the bot for the first time, please wait until finishing the walkthrough (if you have a setup_channel set)
#  For any other boot: wait until the bot shows his "activity" message in its profile (takes a few seconds).
#  If you use the bot before that, all variables won't be loaded yet and errors will happen.
#


"""
		>>	INFO ON CODE STRUCTURE AND DATABASE MIGRATION (if you had legacy version with JSON before).

	The rest happens in bot.py, which will use context.py and utilities.py as well as calling the database handler.
		context.py gives us all our variables from the message (like the channel, the user pfp...) so we can pass it
			through the functions as a single object ("ctx", e.g. "ctx.user").
		utilities.py includes a lot of utility functions used both in bot.py and database/__init__.py (database handler)
		bot.py actually handles all the "front end". It handles user inputs and passes the directives on to the database handler.
			Often checks of valid command parameters are done in bot.py directly, other times they're checked in the db handler.
			This is because some variables can only be checked by accessing the database.
		database/__init__.py handles the "back end" and interacts with the database. Every database operation happens there.
			It includes asyncio locks to avoid race conditions. Also, the database is kept open throughout the bot usage.
			To minimize the risk of data loss in cases of abrupt interruptions, every change is directly committed.
		game_libs/ includes roulette and blackjack. It is called through database/__init__.py
		
	The __init__.py are to make the files in the directories importable. They need to stay there, even if they're empty.
	For database/__init__.py, it actually includes code.
		
	If you were using Skender before v2.0 and still have a JSON database, you will need to migrate your database.
	For this, please just launch the bot (without a file that would already be called "database.sqlite" in your database folder...)
		You will then be guided through the rest.
		You can either choose to migrate or choose to convert the database from json to sqlite.
		A backup of the old json file is made. You should delete or rename the database.json after a successfully migration,
		else you will have a warning everytime you boot the bot.
"""

