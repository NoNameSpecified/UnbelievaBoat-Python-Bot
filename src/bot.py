"""
INFO:

	The "bot" part of the Skender discord bot.
		i.e. most of that which was previously packed into main.py
		and has now been split into bot.py, utilities.py and context.py

	Official Repo: https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot

	For more info see main.py

"""

# general imports
import discord
import requests

# --> utilities.py			Import global utility functions.
from utilities import SkenderUtilities
# --> context.py			Import the "context" aka (our own) ctx, but for us to get channel etc. as easy to use objects.
from context import CommandContext
# --> database/__init__.py	Very important: the whole database handling !
import database # includes our SkenderDatabaseHandler.


class SkenderBot:
	def __init__(self, client, admin_role, bot_prefix):
		self.client = client
		self.prefix = bot_prefix
		# now we can use the functions from SkenderUtilities as self.utils.function().
		self.utils = SkenderUtilities(client, admin_role) # also pass the client.
		# init the database handler.
		self.db_handler = database.SkenderDatabaseHandler(client, admin_role)
		# this gets passed to CommandContext, it could also just be set in context.py directly,
		# but this makes it easier for the user to just edit the variables specific to his own bot in main.py
		self.admin_role = admin_role

		# colors
		self.discord_error_rgb_code = discord.Color.from_rgb(239, 83, 80)
		self.discord_blue_rgb_code = discord.Color.from_rgb(3, 169, 244)
		self.discord_success_rgb_code = discord.Color.from_rgb(102, 187, 106)

		# all the usage values in a dictionary.

		self.all_usages = {
			"blackjack_usage": "blackjack <amount or all>",
			"roulette_usage": "roulette <amount or all> <space>",
			"slut_usage": "slut",
			"crime_usage": "crime",
			"work_usage": "work",
			"rob_usage": "rob <user>",
			"balance_usage": "balance [other-user]",
			"deposit_usage": "deposit <amount or all>",
			"withdraw_usage": "withdraw <amount or all>",
			"give_usage": "give <@member> <amount or all>",
			"leaderboard_usage": "leaderboard [page] [-cash | -bank | -total]",
			"help_usage": "help",
			"module_usage": "module [specific module]}\ntipp: use just module first.",
			"add_money_usage": "add-money <@member> <amount>",
			"remove_money_usage": "remove-money <@member> <amount> [cash/bank]",
			"remove_money_role_usage": "remove-money-role <@role> <amount>",
			"add_money_role_usage": "add-money-role <@role> <amount>",
			"change_action_usage": "change-action <action_name> <variable> <new value>",
			"change_variable_usage": "change-variable <variable> <new value>",
			"change_currency_usage": "change-currency <new emoji name>",
			"set_income_reset_usage": "set-income-reset <true/false>",
			"remove_user_item_usage": "remove-user-item <@member> <item short name> <amount>",
			"spawn_item_usage": "spawn-item <@member> <item short name> [amount]",
			"clear_leaderboard_usage": "clear-lb",
			"create_item_usage": "create-item",
			"delete_item_usage": "delete-item <item short name>",
			"buy_item_usage": "buy-item <item short name> <amount>",
			"give_item_usage": "give-item <@member> <item short name> [amount]",
			"use_item_usage": "use <item short name> <amount>",
			"inventory_usage": "inventory [page]",
			"user_inventory_usage": "user-inventory <@member> [page]",
			"catalog_usage": "catalog [item short name]",
			"add_income_role_usage": "add-income-role <@role> <income>",
			"remove_income_role_usage": "remove-income-role <@role>",
			"update_income_role_usage": "update-income-role <@role> <new income>",
			"list_roles_usage": "list-roles",
			"collect_usage": "collect",
			"update_income_usage": "update-income",
			"add_xp_usage": "add-xp <@member> <amount>",
			"remove_xp_usage": "remove-xp <@member> <amount>",
			"check_level_usage": "level [@member]",
			"all_levels_usage": "all-levels",
			"level_leaderboard_usage": "level-lb [page]",
			"change_levels_usage": "change-levels",
			"set_passive_chat_income_usage": "set-passive-chat-income <new amount>"
		}

	"""
	These functions get called through main.py
	"""

	# initialise database (things that cannot be run in __init__(self, client) and get the bot running.
	async def on_ready(self, activity_msg, setup_channel_id):
		print("[Starting bot... please wait until startup complete until you use it...]")
		# this needs to be done here, because it needs to be awaited (and you cannot await in __init__()).
		await self.db_handler.create_database_default_layout(setup_channel_id)
		# get channels loaded in the database handler
		await self.db_handler.get_channel_infos()
		# get xp variables loaded into database handler (xp per msg, passive income, delay for those two things)
		await self.db_handler.get_xp_infos()
		# init the (custom) emoji (only possible here after the bot has started running)
		self.db_handler.get_currency_symbol(first_run=True)
		# show the bot as active !
		activity = discord.Game(name=activity_msg)
		await self.client.change_presence(status=discord.Status.online, activity=activity)

		print("[BOT STARTED UP -- RUNNING]")

	async def handle_message_xp_and_passive_income(self, message):
		ctx = CommandContext(message, None, None)
		# don't add xp for any bot !
		if message.author.bot:
			return
		await self.db_handler.handle_message_xp_and_passive_income(ctx, ctx.user)

	async def handle_message(self, message):
		# check if the message was supposed to be for our bot
		# startswith() also works with a tuple.
		if not ( message.content.startswith(self.prefix) ): return
		# in case you have multiple prefixes, we handle this dynamically.
		used_prefix = message.content[len(self.prefix)]
		# for example, if the message is just "+"
		command_parts = message.content[len(used_prefix):].split()

		if not command_parts: return

		# print("Called with command: ", command_parts)

		# functioning:
		# if the command was: +give money blabla
		# we take the first word the prefix, to just get the command (here: give).
		# that determines which command will be executed (see the long if/elif/elif below).

		param = ["none"] * 4 # we have no use case of more than command + 3 arguments.

		# turn remove-item item_name 3 --> ["remove-item", "item_name", "3"]
		# info: before, i tried to escape out single and double quotes, but that makes little sense.
		# it should be clear that the bot is used without those, also every parameter is always one word.

		# fill our param variable.
		for index, value in enumerate(command_parts):
			# i.e. < 4, meaning we can fill 1, 2, 3 parameters.
			if index < len(param):
				param[index] = value

		print(f"Command called with parameters : {param}")

		# this will always be the command. ["balance", "none", "none", "none"]
		command = param[0]

		# very important ! we get the message channel etc. from this object without needing to always
		# pass the variables through every function (for more see context.py).
		ctx = CommandContext(message, self.admin_role, param)

		# start processing the commands !

		if command in ["blackjack", "bj"]:
			await self.handle_blackjack(ctx)
			return

		elif command in ["roulette"]:
			await self.handle_roulette(ctx)
			return

		elif command in ["slut"]:
			await self.handle_slut(ctx)
			return

		elif command in ["crime"]:
			await self.handle_crime(ctx)
			return

		elif command in ["work"]:
			await self.handle_work(ctx)
			return

		elif command in ["rob", "steal"]:
			await self.handle_rob(ctx)
			return

		elif command in ["balance", "bal"]:
			await self.handle_balance(ctx)
			return

		elif command in ["deposit", "dep"]:
			await self.handle_deposit(ctx)
			return

		elif command in ["withdraw", "with"]:
			await self.handle_withdraw(ctx)
			return

		elif command in ["give", "pay"]:
			await self.handle_give(ctx)
			return

		elif command in ["leaderboard", "lb"]:
			await self.handle_leaderboard(ctx)
			return

		elif command in ["help", "info"]:
			await self.handle_help(ctx)
			return

		elif command in ["module", "module-info", "modules", "modules-info"]:
			await self.handle_module(ctx)
			return

		elif command == "add-money":
			await self.handle_change_money(ctx, mode="add")
			return

		elif command == "remove-money":
			await self.handle_change_money(ctx, mode="remove")
			return

		# splitting change-action and change-variable for front end,
		# but will be one command called back end.
		elif command == "change":
			await ctx.channel.send("Use change-action or change-variable")
			return
		elif command in {"change-action", "edit-action", "action-change"}:
			await self.handle_change_action(ctx)
			return
		elif command in {"change-variable", "edit-variable", "variable-change"}:
			await self.handle_change_variable(ctx)
			return

		elif command in {"change-currency", "edit-currency", "change-currency-symbol", "change-currency-emoji"}:
			await self.handle_change_currency(ctx)
			return

		elif command in ["set-income-reset", "change-income-reset"]:
			await self.handle_set_income_reset(ctx)
			return

		elif command in ["create-item", "new-item", "item-create"]:
			await self.handle_create_item(ctx)
			return

		elif command in ["delete-item", "remove-item"]:
			await self.handle_delete_item(ctx)
			return

		elif command in ["remove-user-item"]:
			await self.handle_remove_user_item(ctx)
			return

		elif command in {"clear-db", "clean-db", "clear-database", "clean-database",
				"clean-leaderboard", "clean-lb", "purge", "remove-gone-users", "remove-users"}:
			await self.handle_clear_database(ctx)
			return

		elif command in ["buy-item", "get-item", "buy"]:
			await self.handle_buy_item(ctx)
			return

		elif command in ["give-item"]:
			await self.handle_give_item(ctx)
			return

		elif command in ["spawn-item"]:
			await self.handle_spawn_item(ctx)
			return

		elif command in ["use", "use-item"]:
			await self.handle_use_item(ctx)
			return

		elif command in ["inventory", "inv"]:
			await self.handle_inventory(ctx)
			return

		elif command in ["user-inventory", "user-inv"]:
			await self.handle_user_inventory(ctx)
			return

		elif command in ["catalog", "items", "item-list", "list-items"]:
			await self.handle_catalog(ctx)
			return

		elif command in ["add-income-role", "add-role-income"]:
			await self.handle_income_role(ctx, mode="add")
			return

		elif command in ["remove-income-role", "delete-income-role", "remove-role-income", "delete-role-income"]:
			await self.handle_income_role(ctx, mode="remove")
			return

		elif command in ["update-income-role", "update-role", "update-role-income"]:
			await self.handle_income_role(ctx, mode="update")
			return

		elif command in ["add-money-role", "add-role-money"]:
			await self.handle_money_role(ctx, mode="add")
			return

		elif command in ["remove-money-role", "remove-role-money"]:
			await self.handle_money_role(ctx, mode="remove")
			return

		elif command in ["list-roles", "list-income-roles", "list-role-income", "list-incomes"]:
			await self.handle_list_income_roles(ctx)
			return

		elif command in ["update-income", "update-incomes"]:
			await self.handle_update_incomes(ctx)
			return

		elif command in ["collect", "get-salary", "update-income-solo"]:
			await self.handle_collect_income(ctx)
			return

		elif command in ["stats", "economy-stats", "statistics"]:
			await self.handle_economy_stats(ctx)
			return

		elif command in {"level", "lvl", "progress", "xp"}:
			await self.handle_check_level(ctx)
			return

		elif command in {"all-levels", "level-info", "levels-info", "levels"}:
			await self.handle_all_levels(ctx)
			return

		elif command in {"level-lb", "lb-level", "level-leaderboard", "leaderboard-levels", "levels-leaderboard", "lvl-lb", "lb-lvl"}:
			await self.handle_level_leaderboard(ctx)
			return

		elif command in {"change-levels", "update-levels", "change-level", "edit-levels"}:
			await self.handle_change_levels(ctx)
			return

		elif command in ["add-xp", "xp-add", "increase-xp"]:
			await self.handle_xp_change(ctx, mode="add")
			return

		elif command in ["remove-xp", "del-xp", "xp-remove", "decrease-xp"]:
			await self.handle_xp_change(ctx, mode="remove")
			return

		elif command in ["set-passive-chat-income", "set-chat-income"]:
			await self.handle_set_passive_chat_income(ctx)
			return

	# ==> now comes the actual part where we define all the functions.

	"""
	
	BOT SECTION (help, module-info, edit, change-currency...).
	
	"""

	# --------------
	#   HELP PAGE
	# --------------

	async def handle_help(self, ctx):
		# default footer text, you can change this.
		help_footer_text = "For more info, contact an admin or <kendrik2.0>."

		color = self.discord_blue_rgb_code

		mode = "(staff version)" if ctx.staff else "(user version)"

		embed = discord.Embed(title=f"Help System {mode}", color=color)

		embed.add_field(name="stats", value="Usage: `stats`", inline=False)
		embed.add_field(
			name="blackjack",
			value=f"Alias: bj  |  Usage: `{self.all_usages['blackjack_usage']}`",
			inline=False
		)
		embed.add_field(
			name="roulette",
			value=f"Usage: `{self.all_usages['roulette_usage']}`",
			inline=False
		)
		embed.add_field(name="slut", value="Usage: `slut`", inline=False)
		embed.add_field(name="crime", value="Usage: `crime`", inline=False)
		embed.add_field(name="work", value="Usage: `work`", inline=False)
		embed.add_field(
			name="rob",
			value=f"Alias: steal  |  Usage: `{self.all_usages['rob_usage']}`",
			inline=False
		)
		embed.add_field(
			name="balance",
			value=f"Alias: bal  |  Usage: `{self.all_usages['balance_usage']}`",
			inline=False
		)
		embed.add_field(
			name="deposit",
			value=f"Alias: dep  |  Usage: `{self.all_usages['deposit_usage']}`",
			inline=False
		)
		embed.add_field(
			name="withdraw",
			value=f"Alias: with  |  Usage: `{self.all_usages['withdraw_usage']}`",
			inline=False
		)
		embed.add_field(
			name="give",
			value=f"Alias: pay  |  Usage: `{self.all_usages['give_usage']}`",
			inline=False
		)
		embed.add_field(
			name="leaderboard",
			value=f"Alias: lb  |  Usage: `{self.all_usages['leaderboard_usage']}`",
			inline=False
		)
		embed.add_field(name="help", value="Alias: info  |  Usage: `help` - shows this", inline=False)
		embed.add_field(name="module", value="Alias: module-info  |  Usage: `module <module, e.g. slut>`", inline=False)
		embed.set_footer(text=help_footer_text)
		await ctx.channel.send(embed=embed)

		# split because embeds have a mex length

		if ctx.staff:
			embed = discord.Embed(title=f"Help System {mode}", color=color)
			embed.add_field(
				name="----------------------\n\nSTAFF ONLY",
				value=f"requires <{self.admin_role}> role",
				inline=False
			)
			embed.add_field(
				name="add-money",
				value=f"Usage: `{self.all_usages['add_money_usage']}`",
				inline=False
			)
			embed.add_field(
				name="add-money-role",
				value=f"Usage: `{self.all_usages['add_money_role_usage']}`",
				inline=False
			)
			embed.add_field(
				name="remove-money",
				value=f"Usage: `{self.all_usages['remove_money_usage']}`",
				inline=False
			)
			embed.add_field(
				name="remove-money-role",
				value=f"Usage: `{self.all_usages['remove_money_role_usage']}`",
				inline=False
			)
			embed.add_field(
				name="change",
				value=f"Usage: `{self.all_usages['change_usage']}`",
				inline=False
			)
			embed.add_field(
				name="change-currency",
				value=f"Usage: `{self.all_usages['change_currency_usage']}`",
				inline=False
			)
			embed.add_field(
				name="set-income-reset",
				value=f"Usage: `{self.all_usages['set_income_reset_usage']}`",
				inline=False
			)
			embed.add_field(
				name="remove-user-item",
				value=f"Usage: `{self.all_usages['remove_user_item_usage']}`",
				inline=False
			)
			embed.add_field(
				name="spawn-item",
				value=f"Usage: `{self.all_usages['spawn_item_usage']}`",
				inline=False
			)
			embed.add_field(
				name="clear-db",
				value=f"Usage: `{self.all_usages['clear_leaderboard_usage']}'` - remove users from database that left the server",
				inline=False
			)
			embed.set_footer(text=help_footer_text)
			await ctx.channel.send(embed=embed)

		# split embed again.

		embed = discord.Embed(title=f"Help System {mode}", color=color)
		embed.add_field(
			name="----------------------\n\nITEM HANDLING",
			value=f"create and delete requires <{self.admin_role}> role" if ctx.staff else "",
			inline=False
		)

		if ctx.staff:
			embed.add_field(name="create-item", value="Usage: `create-item`", inline=False)
			embed.add_field(name="delete-item", value=f"Usage: `{self.all_usages['delete_item_usage']}`", inline=False)

		embed.add_field(name="buy-item", value=f"Usage: `{self.all_usages['buy_item_usage']}`", inline=False)
		embed.add_field(name="give-item", value=f"Usage: `{self.all_usages['give_item_usage']}`", inline=False)
		embed.add_field(name="use", value=f"Usage: `{self.all_usages['use_item_usage']}`", inline=False)
		embed.add_field(name="inventory", value=f"Alias: inv | Usage: `{self.all_usages['inventory_usage']}`", inline=False)
		embed.add_field(name="user-inventory", value=f"Alias: user-inv | Usage: `{self.all_usages['user_inventory_usage']}`", inline=False)
		embed.add_field(name="catalog", value="Usage: `catalog`", inline=False)
		embed.add_field(name="catalog (details about an item)", value="Usage: `catalog <item short name>`", inline=False)
		embed.add_field(name="----------------------\n\nINCOME ROLES",
						value=f"create, delete and update requires <{self.admin_role}> role" if ctx.staff else "", inline=False)
		if ctx.staff:
			embed.add_field(
				name="add-income-role",
				value=f"Usage: `{self.all_usages['add_income_role_usage']}`",
				inline=False
			)
			embed.add_field(
				name="remove-income-role",
				value=f"Usage: `{self.all_usages['remove_income_role_usage']}`",
				inline=False
			)
			embed.add_field(
				name="update-income-role",
				value=f"Usage: `{self.all_usages['update_income_role_usage']}`",
				inline=False
			)
		# commands for everyone again
		embed.add_field(
			name="list-roles",
			value="Usage: `list-roles`",
			inline=False
		)
		embed.add_field(
			name="collect",
			value="Usage: `collect` | get your salary.\nIf you choose to use update-income, please disable this command.",
			inline=False
		)
		if ctx.staff:
			embed.add_field(
				name="update-income",
				value="Usage: `update-income` | Automatically updates ALL INCOMES.",
				inline=False
			)
		embed.set_footer(text=help_footer_text)
		await ctx.channel.send(embed=embed)

		# split embed again

		embed = discord.Embed(title=f"Help System {mode}", color=color)

		embed.add_field(
			name="----------------------\n\nLEVELS",
			value=f"changing levels xp requires <{self.admin_role}> role" if ctx.staff else "",
			inline=False
		)

		embed.add_field(
			name="check level",
			value=f"Alias: lvl | Usage: `{self.all_usages['check_level_usage']}`",
			inline=False
		)
		embed.add_field(
			name="all levels",
			value=f"Alias: levels | Usage: `{self.all_usages['all_levels_usage']}`",
			inline=False
		)
		embed.add_field(
			name="level leaderboard",
			value=f"Alias: lvl-lb | Usage: `{self.all_usages['level_leaderboard_usage']}`",
			inline=False
		)

		if ctx.staff:
			embed.add_field(
				name="set passive chat income",
				value=f"Usage: `{self.all_usages["set_passive_chat_income_usage"]}`",
				inline=False
			)
			embed.add_field(
				name="change-levels",
				value=f"Usage: `{self.all_usages['change_levels_usage']}`",
				inline=False
			)
			embed.add_field(
				name="add-xp",
				value=f"Usage: `{self.all_usages['add_xp_usage']}`",
				inline=False
			)
			embed.add_field(
				name="remove-xp",
				value=f"Usage: `{self.all_usages['remove_xp_usage']}`",
				inline=False
			)

		embed.set_footer(text=help_footer_text)
		await ctx.channel.send(embed=embed)

		return

	# -------------------
	#    MODULE INFO
	# -------------------

	async def handle_module(self, ctx):
		# usage = self.all_usages["module_usage"]

		module = "all" if ctx.param[1] == "none" else ctx.param[1]

		try:
			status, err_msg = await self.db_handler.module(
				ctx, module
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# -------------------------------------------
	#   CHANGE MONEY (ADD MONEY / REMOVE MONEY)
	# -------------------------------------------

	async def handle_change_money(self, ctx, mode="add"):
		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		usage = self.all_usages["add_money_usage"] if mode == "add" else self.all_usages["remove_money_usage"]

		if not await self.utils.check_parameter_count(ctx, usage, parameter_min_amount=2):
			return

		reception_user = await self.utils.get_user_id(ctx.param[1])
		reception_user_obj = self.client.get_user(int(reception_user))
		if not reception_user_obj:
			await self.utils.send_invalid(ctx, "user", usage)
			return
		# reception_user_name = reception_user_obj.name

		amount = await self.utils.check_amount_parameter(ctx, ctx.param[2], usage, mode="strict")
		if amount is None: return

		money_type = ctx.param[3] if ctx.param[3] in ["cash", "bank"] else "bank"

		try:
			if mode == "add":
				status, err_msg = await self.db_handler.add_money(
					ctx, reception_user, amount, reception_user_obj
				)
			else:
				status, err_msg = await self.db_handler.remove_money(
					ctx, reception_user, amount, reception_user_obj, money_type
				)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# -------------------
	# SET INCOME RESET
	# -------------------

	async def handle_set_income_reset(self, ctx):
		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		usage = self.all_usages["set_income_reset_usage"]

		if not await self.utils.check_parameter_count(ctx, usage, parameter_min_amount=1):
			return

		new_value = ctx.param[1]
		if new_value not in ["true", "false"]:
			await self.utils.send_invalid(ctx, "true/false", usage)
			return

		try:
			status, err_msg = await self.db_handler.set_income_reset(
				ctx, new_value
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# ---------------------------------------
	#   EDIT ACTIONS aka CHANGE ACTIONS
	# ---------------------------------------

	async def handle_change_action(self, ctx):
		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		usage = self.all_usages["change_action_usage"]
		if not await self.utils.check_parameter_count(ctx, usage, parameter_min_amount=3):
			return

		mode = "actions"
		action_name = ctx.param[1]
		variable_name = ctx.param[2]
		new_value = ctx.param[3]

		if variable_name == "action_name":
			footer = "variable name for change-action cannot be action_name itself !"
			await self.utils.send_invalid(ctx, "variable_name", usage, mode="strict", footer=footer)
			return

		try:
			status, err_msg = await self.db_handler.change_variables_and_actions(
				ctx, mode, variable_name, str(new_value), action_name=action_name
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(f"Error during handle_change_action, error code: {e}")
			await self.utils.send_error(ctx)

	# ---------------------------------------
	#   EDIT VARIABLES aka CHANGE VARIABLES
	# ---------------------------------------

	async def handle_change_variable(self, ctx):
		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		usage = self.all_usages["change_variable_usage"]
		if not await self.utils.check_parameter_count(ctx, usage, parameter_min_amount=2):
			return

		mode = "variables"
		variable_name = ctx.param[1]
		new_value = ctx.param[2]

		if variable_name == "levels_info_channel" and new_value != "0":
			# this gets the ID of the pinged channel and then checks if it exists.
			new_value = await self.db_handler.get_valid_channels(new_value, ctx.channel)
			if not new_value:
				await self.utils.send_error_report(
					ctx,
					"Channel for levels_info_channel not found.\nIf you want to disable the info channel, "
					"put the new value to 0."
				)
				return
			# returns a list of integers with channel IDs, in this case, only one.
			new_value = new_value[0]
		else:
			is_num, new_value = self.utils.check_formatted_number(new_value)
			if not is_num:
				footer = "For levels_info_channel, ping the channel, for every other variable enter the new value (integer!)"
				await self.utils.send_invalid(ctx, "new value", usage, mode="strict", footer=footer)
				return

		try:
			status, err_msg = await self.db_handler.change_variables_and_actions(
				ctx, mode, variable_name, str(new_value), action_name=None
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(f"Error during handle_change_variable, error code: {e}")
			await self.utils.send_error(ctx)

	# ------------------------------
	# CHANGE CURRENCY SYMBOL (EMOJI)
	# ------------------------------

	async def handle_change_currency(self, ctx):
		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		usage = self.all_usages["change_currency_usage"]

		if not await self.utils.check_parameter_count(ctx, usage, parameter_min_amount=1):
			return

		new_emoji_name = ctx.param[1]

		try:
			status, err_msg = await self.db_handler.change_currency_symbol(
				ctx, new_emoji_name
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	"""
	
	MONEY AND ECONOMY SECTION
	
	"""

	# -------------------
	#     BLACKJACK
	# -------------------

	async def handle_blackjack(self, ctx):
		usage = self.all_usages["blackjack_usage"]
		if not await self.utils.check_parameter_count(ctx, usage=usage, parameter_min_amount=1, parameter_max_amount=1):
			return

		bet = await self.utils.check_amount_parameter(ctx, ctx.param[1], usage=usage, mode="flex")
		if bet == "error": return

		try:
			status, err_msg = await self.db_handler.blackjack(
				ctx, bet
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# -------------------
	#     ROULETTE
	# -------------------

	async def handle_roulette(self, ctx):
		usage = self.all_usages["roulette_usage"]
		if not await self.utils.check_parameter_count(ctx, usage=usage, parameter_min_amount=2):
			return

		bet = await self.utils.check_amount_parameter(ctx, ctx.param[1], usage=usage, mode="flex")
		if bet == "error": return

		space = str(ctx.param[2])
		if space not in ["odd", "even", "black", "red"]:
			try:
				space = int(space)
				if not(0 <= space <= 36):
					raise ValueError
			except:
				await self.utils.send_invalid(ctx, "space", usage)
				return

		space = str(space)
		try:
			status, err_msg = await self.db_handler.roulette(
				ctx, bet, space
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# -------------------
	#       SLUT
	# -------------------

	async def handle_slut(self, ctx):
		try:
			status, err_msg = await self.db_handler.slut(
				ctx
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# -------------------
	#       CRIME
	# -------------------

	async def handle_crime(self, ctx):
		try:
			status, err_msg = await self.db_handler.crime(
				ctx
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# -------------------
	#       WORK
	# -------------------

	async def handle_work(self, ctx):
		try:
			status, err_msg = await self.db_handler.work(
				ctx
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# -------------------
	#       ROB
	# -------------------

	async def handle_rob(self, ctx):
		usage = self.all_usages["rob_usage"]
		if not await self.utils.check_parameter_count(ctx, usage=usage, parameter_min_amount=1, parameter_max_amount=1):
			return

		user_to_rob = await self.utils.get_user_id(ctx.param[1])

		try:
			status, err_msg = await self.db_handler.rob(
				ctx, user_to_rob
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# -------------------
	#      BALANCE
	# -------------------

	async def handle_balance(self, ctx):
		usage = self.all_usages["balance_usage"]

		if "none" in ctx.param[1]:
			userbal_to_check = ctx.user
			username_to_check = ctx.username
			userpfp_to_check = ctx.user_pfp
		elif ctx.param[1] != "none" and ctx.param[2] != "none":
			await self.utils.send_invalid(ctx, "user", usage, mode="optional")
			return
		else:
			userbal_to_check = await self.utils.get_user_id(ctx.param[1])
			user_fetch = self.client.get_user(int(userbal_to_check))
			if not user_fetch:
				await self.utils.send_invalid(ctx, "user", usage, mode="optional")
				return
			username_to_check = user_fetch.name
			userpfp_to_check = user_fetch.display_avatar

		try:
			await self.db_handler.get_balance(
				ctx, userbal_to_check,
				username_to_check, userpfp_to_check
			)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)


	# -------------------
	#     DEPOSIT
	# -------------------

	async def handle_deposit(self, ctx):
		usage = self.all_usages["deposit_usage"]

		if not await self.utils.check_parameter_count(ctx, usage, parameter_min_amount=1, parameter_max_amount=1):
			return

		amount = await self.utils.check_amount_parameter(ctx, ctx.param[1], usage)
		if amount is None: return

		try:
			status, err_msg = await self.db_handler.deposit(
				ctx, amount
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# -------------------
	#     WITHDRAW
	# -------------------

	async def handle_withdraw(self, ctx):
		usage = self.all_usages["withdraw_usage"]

		if not await self.utils.check_parameter_count(ctx, usage, parameter_min_amount=1, parameter_max_amount=1):
			return

		amount = await self.utils.check_amount_parameter(ctx, ctx.param[1], usage)
		if amount is None: return

		try:
			status, err_msg = await self.db_handler.withdraw(
				ctx, amount
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# -------------------
	#       GIVE
	# -------------------

	async def handle_give(self, ctx):
		usage = self.all_usages["give_usage"]
		footer = "Info: for items use give-item !"

		if not await self.utils.check_parameter_count(ctx, usage, parameter_min_amount=2,
													  parameter_max_amount=2, footer=footer):
			return

		reception_user = await self.utils.get_user_id(ctx.param[1])
		reception_user_obj = self.client.get_user(int(reception_user))
		if not reception_user_obj:
			await self.utils.send_invalid(ctx, "user", usage)
			return
		# reception_user_name = reception_user_obj.name

		amount = await self.utils.check_amount_parameter(ctx, ctx.param[2], usage)
		if amount is None: return

		try:
			status, err_msg = await self.db_handler.give(
				ctx, reception_user, amount, reception_user_obj
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	"""
	
	ITEMS SECTIONS
	
	"""

	# ---------------------------
	#   ITEM CREATION / Create item
	# ---------------------------

	async def handle_create_item(self, ctx):
		# initialise, they will all be set during item creation process.
		item_display_name, item_name, cost, description, max_amount_per_transaction = None, None, None, None, None
		stock, max_amount, roles_id_required, roles_id_to_give, trial, duration = None, None, None, None, None, None
		roles_id_to_remove, max_bal, reply_message, item_img_url, roles_id_excluded =  None, None, None, None, None

		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		currently_creating_item = True
		checkpoints = 0
		last_report = ""
		color = self.discord_blue_rgb_code
		# send a first input which we will then edit
		info_text = (":zero: What should the new item be called?\nThis name should be unique and no "
					 "more than 200 characters.\nIt can contain symbols and multiple words.")
		first_embed = discord.Embed(title="Item Info", description="Display Name\n.", color=color)
		first_embed.set_footer(text="Type cancel to quit")

		# send the first embed, which we will edit later
		await ctx.channel.send(info_text, embed=first_embed)

		while currently_creating_item:
			# get input first
			user_input = await self.utils.get_user_input(ctx, default_spell=False)

			# returns none if it timed out.
			if user_input is None:
				await ctx.channel.send(f"{self.utils.emoji_error} Wait for input timed out after 60 seconds.")
				return

			print("at checkpoint ", checkpoints, "\ninput is ", user_input)

			# check if user wants to cancel
			if user_input == "cancel":
				await ctx.channel.send(f"{self.utils.emoji_error}  Cancelled command.")
				return

			if checkpoints == 0:
				# check 0: display name
				if len(user_input) > 200:
					await ctx.channel.send(f"{self.utils.emoji_error} "
										   f"The maximum length for an items name is 200 characters. Please try again.")
					continue
				elif len(user_input) < 3:
					await ctx.channel.send(f"{self.utils.emoji_error}  "
										   f"The minimum length for an items name is 3 characters. Please try again.")
					continue

				# good input
				item_display_name = user_input
				first_embed = discord.Embed(title="Item Info", color=color)
				first_embed.add_field(name="Display Name", value=f"{item_display_name}")
				first_embed.set_footer(text="Type cancel to quit")
				next_info = ("`1` Now we need a short name, which users will use when buying, giving etc. "
							 "Only one word ! (you can use dashes and underscores)")
				last_report = await ctx.channel.send(next_info, embed=first_embed)
				checkpoints += 1
				trial = 0

			if checkpoints == 1:
				trial += 1
				item_name = await self.utils.get_user_input(ctx) if trial == 1 else user_input

				# check 1: name
				if len(item_name) > 10:
					await ctx.channel.send(f"{self.utils.emoji_error} The maximum length for an items short name "
										   f"is 10 characters. Please try again.")
					continue
				elif len(item_name) < 3:
					await ctx.channel.send(f"{self.utils.emoji_error}  The minimum length for an items short name "
										   f"is 3 characters. Please try again.")
					continue
				elif " " in item_name.strip():
					print(f"-{item_name}- -{item_name.strip()}")
					await ctx.channel.send(f"{self.utils.emoji_error}  short name has to be ONE word "
										   f"(dashes or underscores work).")
					continue

				# good input
				first_embed.add_field(name="Short name", value=f"{item_name}")
				first_embed.set_footer(text="Type cancel to quit")
				next_info = "`2` How much should the item cost to purchase?"
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 2:
				# check 2: cost
				is_int, cost = self.utils.check_formatted_number(user_input)
				if not is_int or cost < 1:
					await ctx.channel.send(f"{self.utils.emoji_error}  Invalid price given. Please try again or "
										   f"type cancel to exit.")
					continue

				first_embed.add_field(name="Price", value=f"{cost}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ("`3` Please provide a description of the item.\n"
							 "This should be no more than 200 characters.")
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 3:
				# check 3: description
				if len(user_input) > 200:
					await ctx.channel.send(f"{self.utils.emoji_error} The maximum length for an items description "
										   f"is 200 characters. Please try again.")
					continue
				if user_input.lower() == "skip":
					description = "none"
				else:
					description = user_input

				first_embed.add_field(name="Description", value=f"{description}", inline=False)
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ("`4` How long should this item stay in the store ? (integer, in days)\n"
							 "Minimum duration is 1 day.\nIf no limit, just reply `skip`.")
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 4:
				# check 4: duration
				duration_check = user_input
				if duration_check.lower() == "skip":
					duration = 99999
				else:
					is_int, duration = self.utils.check_formatted_number(duration_check)
					if not is_int:
						await ctx.channel.send(f"{self.utils.emoji_error}  Invalid time duration given. "
											   f"Please try again or type cancel to exit.")
						continue

				duration_str = "unlimited" if duration == 99999 else f"{duration}"
				first_embed.add_field(name="Time remaining", value=f"{duration_str} days left")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ("`5` How much stock of this item will there be?\nIf unlimited, "
							 "just reply `skip` or `infinity`.")
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 5:
				# check 5: stock
				stock = user_input
				if stock.lower() in ["skip", "infinity"]:
					stock = "unlimited"
				else:
					is_int, stock = self.utils.check_formatted_number(stock)
					if not is_int or stock < 1:
						await ctx.channel.send(f"{self.utils.emoji_error}  Invalid stock amount given. "
											   f"Please try again or type cancel to exit.")
						continue

				# stock will be converted into string automatically through SQLite, but usually we should
				# stock = str(stock)

				first_embed.add_field(name="Stock remaining", value=f"{stock}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ("`6` What is the MAX amount of this item per user that should be allowed ?\n"
							 "If none, just reply `skip`.")
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 6:
				# check 6: max amount of item
				max_amount_check = user_input
				if max_amount_check.lower() in ["skip", "infinity"]:
					max_amount = "unlimited"
				else:
					is_int, max_amount = self.utils.check_formatted_number(max_amount_check)
					if not is_int or max_amount < 1:
						await ctx.channel.send(f"{self.utils.emoji_error}  Invalid max amount given. "
											   f"Please try again or type cancel to exit.")
						continue

				first_embed.add_field(name="Max amount", value=f"{max_amount}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ("`7` What is the max amount a user can buy at once ?\nInfo:"
							 "You can add this with automatically giving a role that is also an excluded role, "
							 "and then deleting the role after X days so that users can buy again "
							 "(i.e.: you control how *fast* they can accumulate without setting a hard total).\n"
							 "If none, just reply `skip`.")
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 7:
				# check 7: max you can buy PER transaction.
				# added in v2.0. Goal: limit more precisely than just max amount.
				# e.g.: you give a role that excludes the possibility to buy the item,
				# the max per transaction is set to 1. So the user can only buy one, but
				# after one month you delete the role and ppl can buy again and get a new
				# excluded role when buying the item. So ppl can buy 1 per month but
				# without having a hard limit on how much they can own in total.
				max_amount_per_transaction_check = user_input
				if max_amount_per_transaction_check.lower() in ["skip", "infinity"]:
					max_amount_per_transaction = "unlimited"
				else:
					is_int, max_amount_per_transaction = self.utils.check_formatted_number(max_amount_per_transaction_check)
					if not is_int or max_amount < 1:
						await ctx.channel.send(f"{self.utils.emoji_error}  Invalid max amount per transaction given. "
											   f"Please try again or type cancel to exit.")
						continue

				first_embed.add_field(name="Max per transaction", value=f"{max_amount_per_transaction}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ("`7` What role(s) must the user already have in order to buy this item?\n"
							 "If none, just reply `skip`. For multiple, ping the roles with a space between them.")
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 8:
				# check 8: required role

				req_roles = user_input
				if req_roles.lower() in ["skip", "infinity"]:
					# required roles is for the embed
					required_roles = "none"
					# this is what goes into the database.
					roles_id_required = ["none"]
				else:
					roles_input = self.utils.get_role_id_multiple(user_input)

					if not roles_input:
						await ctx.channel.send(f"{self.utils.emoji_error}  Invalid role given. Please try again.")
						continue

					required_roles = ""
					for role_id in roles_input:
						role = discord.utils.get(ctx.server.roles, id=int(role_id))
						if role is None:
							await ctx.channel.send(f"{self.utils.emoji_error}  Invalid role given. Please try again.")
							continue
						required_roles += f"{role.mention} "
					# above was just for display, this is already our IDs.
					roles_id_required = roles_input

				first_embed.add_field(name="Role required", value=f"{required_roles}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ("`9` What roles should make purchase of this item impossible ? (excluded role(s))?\n"
							 "If none, just reply `skip`. For multiple, ping them with a space between them.")
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 9:
				# check 9: excluded role - meaning you can't buy if possessing it.
				excl_roles = user_input
				if excl_roles.lower() in ["skip", "infinity", "none"]:
					excluded_roles = "none"
					roles_id_excluded = ["none"]
				else:
					roles_input = self.utils.get_role_id_multiple(user_input)

					if not roles_input:
						await ctx.channel.send(f"{self.utils.emoji_error}  Invalid role given. Please try again.")
						continue

					excluded_roles = ""
					for role_id in roles_input:
						role = discord.utils.get(ctx.server.roles, id=int(role_id))
						if role is None:
							await ctx.channel.send(f"{self.utils.emoji_error}  Invalid role given. Please try again.")
							continue
						excluded_roles += f"{role.mention} "
					roles_id_excluded = roles_input

				first_embed.add_field(name="Excluded roles", value=f"{excluded_roles}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ("`10` What role(s) do you want to be given when this item is bought?\n"
							 "If none, just reply `skip`. For multiple, ping them with a space between them.")
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 10:
				# check 10: role to be given when item bought
				give_roles = user_input
				if give_roles.lower() in ["skip", "infinity", "none"]:
					roles_give = "none"
					roles_id_to_give = ["none"]
				else:
					roles_input = self.utils.get_role_id_multiple(user_input)

					if not roles_input:
						await ctx.channel.send(f"{self.utils.emoji_error}  Invalid role given. Please try again.")
						continue

					roles_give = ""
					for role_id in roles_input:

						role = discord.utils.get(ctx.server.roles, id=int(role_id))
						if role is None:
							await ctx.channel.send(f"{self.utils.emoji_error}  Invalid role given. Please try again.")
							continue
						roles_give += f"{role.mention} "
					roles_id_to_give = roles_input

				first_embed.add_field(name="Role given", value=f"{roles_give}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ("`11` What role(s) do you want to be removed from the user when this item is "
							 "bought?\nIf none, just reply `skip`. For multiple, ping with a space between them.")
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 11:
				# check 11: role to be removed when item bought
				remove_roles = user_input
				if remove_roles.lower() in ["skip", "infinity", "none"]:
					roles_remove = "none"
					roles_id_to_remove = ["none"]
				else:
					roles_input = self.utils.get_role_id_multiple(user_input)

					if not roles_input:
						await ctx.channel.send(f"{self.utils.emoji_error}  Invalid role given. Please try again.")
						continue

					roles_remove = ""
					for role_id in roles_input:
						role = discord.utils.get(ctx.server.roles, id=int(role_id))
						if role is None:
							await ctx.channel.send(f"{self.utils.emoji_error}  Invalid role given. Please try again.")
							continue
						roles_remove += f"{role.mention} "
					roles_id_to_remove = roles_input

				first_embed.add_field(name="Role removed", value=f"{roles_remove}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ("`12` What is the maximum balance a user can have in order to buy this item?\n"
							 "If none, just reply `skip`.")
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 12:
				# check 12: max balance
				max_bal_check = user_input
				if max_bal_check.lower() == "skip":
					max_bal = "none"
				else:
					is_int, max_bal = self.utils.check_formatted_number(max_bal_check)
					if not is_int:
						await ctx.channel.send(f"{self.utils.emoji_error}  Invalid max balance given. "
											   f"Please try again or type cancel to exit.")
						continue

				first_embed.add_field(name="Maximum balance", value=f"{max_bal}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ("`13`: What message do you want the bot to reply with, when the item is bought?\n"
							 "For default msg (Congrats on buying the item), just reply `skip`.")
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 13:
				# check 13: reply message
				if len(user_input) > 150:
					await ctx.channel.send(f"{self.utils.emoji_error} The maximum length for a reply message "
										   f"is 150 characters. Please try again.")
					continue
				if user_input.lower() == "skip":
					user_input = "Congrats on buying the item."
				reply_message = user_input

				first_embed.add_field(name="Reply message", value=f"{reply_message}", inline=False)
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = "`14`: What image should the item have? Enter complete url !\nIf none, just reply `skip`."
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 14:
				# check 14: item img
				if user_input.lower() == "skip":
					item_img_url = "EMPTY"
				else:
					try:
						rq = requests.get(user_input)
						if rq.status_code != 200:
							await ctx.channel.send(f"{self.utils.emoji_error} URL not found. Please try again or skip.")
							continue
					except Exception as e:
						print(f"Error at checkpoint 13: {e}")
						await ctx.channel.send(f"{self.utils.emoji_error} URL not found. Please try again or skip.")
						continue
					item_img_url = user_input
					first_embed.set_thumbnail(url=item_img_url)

				next_info = f"{self.utils.emoji_worked}  Item created successfully!"
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints = -1
				currently_creating_item = False

		try:
			status, err_msg = await self.db_handler.create_new_item(
				ctx, item_display_name, item_name, cost, description, duration, stock,
				max_amount, max_amount_per_transaction, roles_id_required, roles_id_to_give, roles_id_to_remove, max_bal,
				reply_message, item_img_url, roles_id_excluded
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
				return
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

		return

	# ---------------------------
	#   DELETE ITEM - REMOVE ITEM
	# ---------------------------

	async def handle_delete_item(self, ctx):
		usage = self.all_usages["delete_item_usage"]

		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		if not await self.utils.check_parameter_count(ctx, usage, parameter_min_amount=1):
			return

		item_name = ctx.param[1]

		confirmation_msg = "This will permanently delete the item, also for every user!\nDo you wish to continue? [y/N]"
		footer = "Info: use remove-user-item to remove an item from a specific user."
		confirmation = await self.utils.confirm_command(ctx, description=confirmation_msg, footer=footer)

		if not confirmation: return

		# handler

		try:
			status, err_msg = await self.db_handler.remove_item(ctx, item_name)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
				return
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

		description=f"{self.utils.emoji_worked}  Item has been removed from the store."\
					f"\nNote: also deleted from everyone's inventory."
		await self.utils.send_embed(ctx, description, color="green")

		return

	# ---------------------------
	#   REMOVE USER ITEM
	# ---------------------------

	async def handle_remove_user_item(self, ctx):
		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		usage = self.all_usages["remove_user_item_usage"]

		# item name and player pinged as parameters.
		if not await self.utils.check_parameter_count(ctx, usage, parameter_min_amount=2):
			return

		player_ping = await self.utils.get_user_id(ctx.param[1])

		exists, reception_user_object = self.utils.check_if_user_exists(ctx, player_ping)
		if not exists:
			await self.utils.send_invalid(ctx, "member", usage)
			return

		item_name = ctx.param[2]

		if "none" in ctx.param[3]:  # we need item amount
			amount = 1
		else:
			amount = ctx.param[3]
			is_int, amount = await self.utils.check_amount_parameter(ctx, amount, usage, mode="strict")
			if not is_int: return

		try:
			status, err_msg = await self.db_handler.remove_user_item(
				ctx, item_name, amount, player_ping, reception_user_object
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
				return
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)
		return

	# ---------------------------
	#   BUY ITEM
	# ---------------------------

	async def handle_buy_item(self, ctx):
		usage = self.all_usages["buy_item_usage"]

		# we need the name, but specific amount is optional.
		if not await self.utils.check_parameter_count(ctx, usage=usage, parameter_min_amount=1):
			return

		item_name = ctx.param[1]

		amount_param = "1" if ctx.param[2] == "none" else ctx.param[2]

		# Strict-Check des Amounts (ganze Zahl, > 0)
		amount = await self.utils.check_amount_parameter(ctx, amount_param, usage, mode="strict")
		if amount is None:
			return

		try:
			status, err_msg = await self.db_handler.buy_item(
				ctx, item_name, amount
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# --------------------
	#      GIVE ITEM
	# --------------------

	async def handle_give_item(self, ctx):
		usage = self.all_usages["give_item_usage"]

		# we need user and item, but amount can be left empty (will be set to 1).
		if not await self.utils.check_parameter_count(ctx, usage=usage, parameter_min_amount=2):
			return

		player_mention = ctx.param[1]
		player_ping = await self.utils.get_user_id(player_mention)

		try:
			user_fetch = self.client.get_user(int(player_ping))
			if not user_fetch:
				raise ValueError("User not found")
			reception_user_object = user_fetch
			if int(player_ping) == ctx.user:
				embed = discord.Embed(description=f"{self.utils.emoji_error}  You cannot trade items with yourself."
												  f" That would be pointless...", color=self.discord_error_rgb_code)
				embed.set_author(name=ctx.username, icon_url=ctx.user_pfp)
				await ctx.channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await self.utils.send_invalid(ctx, "member", usage)
			return

		item_name = ctx.param[2]

		amount_param = "1" if ctx.param[3] == "none" else ctx.param[3]
		amount = await self.utils.check_amount_parameter(ctx, amount_param, usage, mode="strict")
		if amount is None:
			return

		try:
			# false at the end is for "spawn mode".
			status, err_msg = await self.db_handler.give_item(
				ctx, item_name, amount, player_ping, reception_user_object, False
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

		return

	# ---------------------------
	#   SPAWN ITEM
	#      if admins want to "give" someone an item without having to buy and then give it
	# ---------------------------

	async def handle_spawn_item(self, ctx):
		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		usage = self.all_usages["spawn_item_usage"]

		if not await self.utils.check_parameter_count(ctx, usage=usage, parameter_min_amount=2):
			return

		player_mention = ctx.param[1]
		player_ping = await self.utils.get_user_id(player_mention)

		try:
			user_fetch = self.client.get_user(int(player_ping))
			if not user_fetch:
				raise ValueError("User not found")
			reception_user_object = user_fetch
		except Exception:
			await self.utils.send_invalid(ctx, "member", usage)
			return

		if ctx.param[2] == "none":
			await self.utils.send_invalid(ctx, "item", usage)
			return
		item_name = ctx.param[2]

		amount_param = "1" if ctx.param[3] == "none" else ctx.param[3]
		amount = await self.utils.check_amount_parameter(ctx, amount_param, usage, mode="strict")
		if amount is None:
			return

		try:
			# this time, spawn mode set to true.
			status, err_msg = await self.db_handler.give_item(
				ctx, item_name, amount, player_ping, reception_user_object, True
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)


	# --------------
	# 	  USE ITEM     # this will MERELY remove the item from inventory
	# --------------

	async def handle_use_item(self, ctx):
		usage = self.all_usages["use_item_usage"]

		if not await self.utils.check_parameter_count(ctx, usage=usage, parameter_min_amount=1):
			return

		item_used = ctx.param[1]

		amount_param = "1" if ctx.param[2] == "none" else ctx.param[2]
		amount_used = await self.utils.check_amount_parameter(ctx, amount_param, usage, mode="strict")
		if amount_used == "error":
			return

		try:
			status, err_msg = await self.db_handler.use_item(
				ctx, item_used, amount_used
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# ---------------------------------------
	#   CHECK INVENTORY (check own inventory)
	# ---------------------------------------

	async def handle_inventory(self, ctx):
		user_to_check, user_to_check_uname, user_to_check_pfp = "self", "self", "self"
		usage = self.all_usages["inventory_usage"]

		if ctx.param[1] == "none":
			page_number = 1
		else:
			try:
				page_number = int(ctx.param[1])
			except:
				footer = ("info: use it without page once, output will show amount of total pages.\n"
						  "info: use user-inventory to see inventory of another user")
				await self.utils.send_invalid(ctx, "page number", usage, mode="optional", footer=footer)
				return

		try:
			status, err_msg = await self.db_handler.check_inventory(
				ctx, user_to_check, user_to_check_uname, user_to_check_pfp, page_number
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# --------------------------------------------------------
	#   CHECK USER INVENTORY (check inventory of another user)
	# --------------------------------------------------------

	async def handle_user_inventory(self, ctx):
		usage = self.all_usages["user_inventory_usage"]

		if "none" in ctx.param[1]:
			footer = "info: use `inventory` to see your own inventory."
			await self.utils.send_invalid(ctx, "member", usage, mode="strict", footer=footer)
			return

		user_to_check = await self.utils.get_user_id(ctx.param[1])

		try:
			user_obj = self.client.get_user(int(user_to_check))
			user_to_check_uname = user_obj.name
			user_to_check_pfp = user_obj.display_avatar
			if int(user_to_check) == ctx.user:
				user_to_check, user_to_check_uname, user_to_check_pfp = "self", "self", "self"
		except Exception:
			footer = "info: use `inventory` to see your own inventory."
			await self.utils.send_invalid(ctx, "member ping", usage, mode="strict", footer=footer)
			return

		if "none" in ctx.param[2]:
			page_number = 1
		else:
			try:
				page_number = int(ctx.param[2])
			except Exception:
				footer = "info: use it without page once, output will show amount of total pages"
				await self.utils.send_invalid(ctx, "page number", usage, mode="optional", footer=footer)
				return

		try:
			status, err_msg = await self.db_handler.check_inventory(
				ctx, user_to_check, user_to_check_uname, user_to_check_pfp, page_number
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# ---------------------------
	#   ITEMS CATALOG
	# ---------------------------

	async def handle_catalog(self, ctx):
		if "none" in ctx.param[1]:
			item_check = "default_list"
		else:
			item_check = ctx.param[1]

		try:
			status, err_msg = await self.db_handler.catalog(
				ctx, item_check
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	"""
	
	INCOME ROLES SECTION
	
	"""

	# ---------------------------
	#   ADD ROLE, UPDATE ROLE, REMOVE ROLE INCOME ROLE
	# ---------------------------

	async def handle_income_role(self, ctx, mode=None):

		amount = None

		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		if mode not in ["add", "remove", "update"]: raise ValueError("Invalid mode: ")

		usage = self.all_usages[f"{mode}_income_role_usage"]

		if mode == "add":
			await ctx.channel.send("`Info: income is DAILY one. To change a set income_role, use update-income-role`\n")

		# we need at least one role parameter for all of them
		min_parameters = 2 if mode in ["add", "update"] else 1
		if not await self.utils.check_parameter_count(ctx, usage, parameter_min_amount=min_parameters):
			return

		role_parameter = ctx.param[1]

		if mode == "remove":
			# no further checks, since we can also try to delete a role as income role, that was
			# already was deleted on the server and thus this command was called with only the ID.
			income_role = self.utils.get_role_id_single(role_parameter)
		else:
			income_role = await self.utils.check_if_role_exists(ctx, ctx.param[1])
			if income_role is None:
				return

			amount = await self.utils.check_amount_parameter(ctx, ctx.param[2], usage, mode="strict")
			if amount is None: return

		try:
			if mode == "add":
				status, err_msg = await self.db_handler.new_income_role(
					ctx, income_role, amount
				)
			elif mode == "update":
				status, err_msg = await self.db_handler.update_income_role(
					ctx, income_role, amount
				)
			# elif mode == "remove":
			else:
				status, err_msg = await self.db_handler.remove_income_role(
					ctx, income_role
				)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
				return
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)
			return

		# no more info if just adding.
		if mode == "add":
			return

		embed_description = f"{self.utils.emoji_worked}  Role has been"
		embed_description += "disabled as income role." if mode == "remove" else f"updated with new income set to {amount}."

		await self.utils.send_embed(ctx, embed_description, color="green")

		return

	# ---------------------------
	#   LIST INCOME ROLES
	# ---------------------------

	async def handle_list_income_roles(self, ctx):
		try:
			status, err_msg = await self.db_handler.list_income_roles(
				ctx
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# --------------------------------------------
	#   ADD MONEY BY ROLE / REMOVE MONEY BY ROLE
	# --------------------------------------------

	async def handle_money_role(self, ctx, mode=None):
		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		if mode not in ["add", "remove"]:
			raise ValueError("Invalid mode for handle_money_role")

		usage = self.all_usages[f"{mode}_money_role_usage"]

		# we need two parameters: role and amount.
		if not await self.utils.check_parameter_count(ctx, usage, parameter_min_amount=2):
			return

		# get amount and check
		amount = await self.utils.check_amount_parameter(ctx, ctx.param[2], usage, mode="strict")
		if amount is None:
			return

		# check role
		role_id = await self.utils.check_if_role_exists(ctx, ctx.param[1])
		if role_id is None:
			return

		# handler
		try:
			# mode at the end is crucial.
			status, err_msg = await self.db_handler.handle_money_by_role(
				ctx, role_id, amount, mode
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
				return
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# ----------------------------------
	#   UPDATE INCOMES (GLOBAL BY MOD)
	# ----------------------------------

	async def handle_update_incomes(self, ctx):
		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		try:
			status, err_msg = await self.db_handler.update_incomes(
				ctx
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
				return
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)
			return

		# if success:
		embed_description = f"{self.utils.emoji_worked}  Users with registered roles have received their income (into bank account)."
		await self.utils.send_embed(ctx, embed_description, color="green")
		return

	# ---------------------------
	#   UPDATE INCOME FOR YOURSELF ONLY
	# ---------------------------

	async def handle_collect_income(self, ctx):
		try:
			status, err_msg = await self.db_handler.update_incomes_solo(
				ctx
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
				return
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)
			return

	"""
	
	SERVER THINGS
	
	"""

	# ---------------
	#   LEADERBOARD
	# ---------------

	async def handle_leaderboard(self, ctx):
		usage = self.all_usages["leaderboard_usage"]
		modes = ["-cash", "-bank", "-total"]
		options = " | ".join(modes)

		page_number = 1
		mode_type = "-total"
		# start name of embed
		full_name = ctx.server.name

		param1 = ctx.param[1]
		param2 = ctx.param[2]

		if param1 == "none" and param2 == "none":
			full_name += " Leaderboard"

		# because it can be +lb 2 (for page 2 of normal=total leaderboard)
		# or it can be +lb cash 2 (for page 2 in cash mode).
		# but it should not be +lb 2 cash.

		elif param1 != "none" and param2 == "none":
			if param1 in modes:
				mode_type = param1
				full_name += f" {mode_type.strip('-').capitalize()} Leaderboard" if mode_type != "-total" else " Leaderboard"
			else:
				try:
					page_number = int(param1)
					full_name += " Leaderboard"
				except ValueError:
					await self.utils.send_invalid(ctx, options, usage, mode="optional")
					return

		else:
			try:
				page_number = int(param1)
				if param2 not in modes:
					await self.utils.send_invalid(ctx, options, usage, mode="optional")
					return
				mode_type = param2
				full_name += f" {mode_type.strip('-').capitalize()} Leaderboard" if mode_type != "-total" else " Leaderboard"
			except ValueError:
				await self.utils.send_invalid(ctx, options, usage, mode="optional")
				return

		try:
			status, err_msg = await self.db_handler.leaderboard(
				ctx, full_name, page_number, mode_type
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

	# ---------------------------
	#   CLEAN DATABASE / REMOVE GONE USERS / CLEAN LEADERBOARD
	# ---------------------------

	async def handle_clear_database(self, ctx):
		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		# need confirmation, especially in case they want to purge their database
		# right after the update to SkenderBot.
		confirmed = await self.utils.confirm_command(ctx,
					description="This will permanently delete all user instances "
					"that left the server! If you're using version **2.0** of the bot (first release after upgrade "
					"to the new database system), please consider making a **backup** of the database file."
				 	"\nDo you wish to continue? [y/N]")
		if not confirmed:
			return

		try:
			status, err_msg = await self.db_handler.clean_database(ctx)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
				return
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)
			return

		embed = discord.Embed(
			description=f"{self.utils.emoji_worked} {err_msg} user(s) have been removed from database.",
			color=self.discord_success_rgb_code
		)
		embed.set_author(name=ctx.username, icon_url=ctx.user_pfp)
		await ctx.channel.send(embed=embed)

		return

	# ---------------------------
	#   ECONOMY STATISTICS
	# ---------------------------

	async def handle_economy_stats(self, ctx):
		try:
			status, err_msg = await self.db_handler.economy_stats(
				ctx
			)
			if status == "error":
				await self.utils.send_error_report(ctx, err_msg)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)

		return

	# -------------------------------
	#    XP HANDLING (ADD/REMOVE)
	# -------------------------------

	# info: auto xp adding and passive chat income gets handled through main.py on_message --> db_handler directly.
	async def handle_xp_change(self, ctx, mode="add"):
		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		if mode not in ["add", "remove"]:
			raise ValueError("mode for handle_xp_change(self, ...) must be 'add' or 'remove'")

		usage = self.all_usages["add_xp_usage"] if mode == "add" else self.all_usages["remove_xp_usage"]

		# we need a user and an amount
		if not await self.utils.check_parameter_count(ctx, usage, parameter_min_amount=2):
			return

		user_ping = await self.utils.get_user_id(ctx.param[1])
		exists, _ = self.utils.check_if_user_exists(ctx, user_ping)
		if not exists:
			await self.utils.send_invalid(ctx, "member", usage)
			return

		amount = await self.utils.check_amount_parameter(ctx, ctx.param[2], usage, "strict")
		if amount is None: return

		# handle it.
		try:
			status, error = await self.db_handler.change_user_xp(ctx, user_ping, amount, mode)
			if status == "error":
				await self.utils.send_error_report(ctx, error)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)
		return

	# ---------------
	#   CHECK LEVEL
	# ---------------

	async def handle_check_level(self, ctx):
		usage = self.all_usages["check_level_usage"]
		if ctx.param[1] == "none":
			user = ctx.user
		else:
			user = await self.utils.get_user_id(ctx.param[1])
			if not user:
				await self.utils.send_invalid(ctx, "member", usage, mode="optional")
				return

		try:
			status, error = await self.db_handler.check_current_level(ctx, user)
			if status == "error":
				await self.utils.send_error_report(ctx, error)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)
		return

	# --------------
	#   ALL LEVELS
	# --------------

	async def handle_all_levels(self, ctx):
		# usage = self.all_usages["all_levels_usage"]

		try:
			status, error = await self.db_handler.list_all_levels(ctx)
			if status == "error":
				await self.utils.send_error_report(ctx, error)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)
		return

	# -----------------------
	#   LEVELS LEADERBOARD
	# -----------------------

	async def handle_level_leaderboard(self, ctx):
		usage = self.all_usages["level_leaderboard_usage"]

		page = ctx.param[1]

		if page == "none":
			page_number = 1
		else:
			try:
				page_number = int(page)
			except ValueError:
				await self.utils.send_invalid(ctx, "page", usage, mode="optional")
				return

		try:
			status, error = await self.db_handler.level_leaderboard(ctx, page_number)
			if status == "error":
				await self.utils.send_error_report(ctx, error)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)
		return

	# -----------------
	#   CHANGE LEVELS
	# -----------------

	async def handle_change_levels(self, ctx):
		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		# usage = self.all_usages["change_levels_usage"]

		try:
			status, error = await self.db_handler.change_levels(ctx)
			if status == "error":
				await self.utils.send_error_report(ctx, error)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)
		return

	# -----------------------------
	#  CHANGE PASSIVE CHAT INCOME
	# -----------------------------

	async def handle_set_passive_chat_income(self, ctx):
		if not ctx.staff:
			await self.utils.missing_admin(ctx)
			return

		usage = self.all_usages["set_passive_chat_income_usage"]

		if not await self.utils.check_parameter_count(ctx, usage, parameter_min_amount=1):
			await self.utils.send_invalid(ctx, "amount", usage)

		amount = ctx.param[1]

		new_value = await self.utils.check_amount_parameter(ctx, amount_param=amount, usage=usage, mode="strict")
		if new_value is None: return

		try:
			status, error = await self.db_handler.set_passive_chat_income(ctx, new_value)
			if status == "error":
				await self.utils.send_error_report(ctx, error)
		except Exception as e:
			print(e)
			await self.utils.send_error(ctx)
		return

