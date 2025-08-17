"""
INFO:

	The global utilities functions of the Skender discord bot.

	Official Repo: https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot

	imported in bot.py and database/__init__.py and used as self.utils.xyz()

	for more info see main.py

"""

import discord, asyncio, re

class SkenderUtilities:
	def __init__(self, client, admin_role):
		self.client = client

		self.emoji_worked = "✅"
		self.emoji_error = "❌"
		self.emoji_rotating_light = "🚨"
		self.discord_error_rgb_code = discord.Color.from_rgb(239, 83, 80)
		self.discord_blue_rgb_code = discord.Color.from_rgb(3, 169, 244)
		self.discord_success_rgb_code = discord.Color.from_rgb(102, 187, 106)
		self.admin_role = admin_role

	async def setup_get_admin_input(self, channel):
		print("Awaiting admin entry during setup...")
		try:
			answer = await self.client.wait_for(
				"message",
				check=lambda response: response.channel == channel
									   and any( self.admin_role == role.name for role in response.author.roles ),
				timeout=90)
		except asyncio.TimeoutError:
			print("Wait for admin entry timed out after 30 seconds.")
			return None

		print(f"Got: {answer.content}")
		return answer.content.lower().strip()


	async def get_user_input(self, ctx, default_spell=True):
		print("Awaiting User Entry")
		# we want an answer from the guy who wants to give an answer
		try:
			answer = await self.client.wait_for("message",
								check=lambda response: response.author == ctx.message.author
									  and response.channel == ctx.message.channel,
								timeout=60)
		except asyncio.TimeoutError:
			print("Wait for user entry timed out after 60 seconds.")
			return None
		answer = answer.content
		# clean input
		if default_spell:
			answer = answer.lower().strip()
		return answer

	async def ask_for_number(self, ctx, prompt, cancelable=True, min_value=None, max_value=None, err_prompt=None):
		await ctx.channel.send(prompt)

		while 1:
			user_input = await self.get_user_input(ctx)

			if cancelable and user_input == "cancel":
				return None

			is_num, num = self.check_formatted_number(user_input)
			if not is_num:
				await self.send_error_report(ctx, "Needs to be an integer.")
				continue
			if max_value is not None and num > max_value:
				await self.send_error_report(ctx, err_prompt or f"Value must be < {max_value}")
				continue
			if min_value is not None and num <= min_value:
				await self.send_error_report(ctx, err_prompt or f"Value must be > {min_value}")
				continue

			return num

	@staticmethod
	async def get_user_id(user_id):
		# if it's just an id anyway, return it
		if isinstance(user_id, int):
			return user_id

		# else get all digits (not always integers, but should do the trick)
		user_id_digits = "".join(re.findall(r'\d+', str(user_id)))

		# if there was no digit at all (so it was just a string)
		if not user_id_digits: return None
		# else return our id integer
		return int(user_id_digits)

	# get role ids
	@staticmethod
	def get_role_id_multiple(user_input):
		roles = user_input.split(" ")  # so we get a list
		roles_clean = []

		for raw_role in roles:
			digits = "".join(char for char in raw_role if char.isdigit())
			if digits:
				roles_clean.append(digits)

		return roles_clean if roles_clean else None

	# single role
	@staticmethod
	def get_role_id_single(parameter):
		role_beta = str(parameter)  # see another instance where I use this to see why
		role_clean = ""
		for i in range(len(role_beta)):
			try:
				role_clean += str(int(role_beta[i]))
			except:
				pass
		return int(role_clean)

	@staticmethod
	async def get_role_object(ctx, role_id):
		try:
			role_id = int(role_id)
			role_obj = discord.utils.get(ctx.server.roles, id=role_id) or await ctx.server.fetch_role(role_id)
		except:
			# if we try to fetch_role and the role doesn't exist, we return None, and we don't crash.
			role_obj = None

		return role_obj


	async def check_if_role_exists(self, ctx, role):
		role_id = self.get_role_id_single(role)
		role = discord.utils.get(ctx.server.roles, id=int(role_id))
		if role is None:
			await ctx.channel.send(f"{self.emoji_error}  Invalid role given.")
			return None
		return role

	@staticmethod
	async def add_or_remove_roles_user(ctx, user_object, roles, mode="add", verbose=False):
		if not roles:
			return None

		roles_to_mention = []

		for role_id in roles:
			try:
				role = discord.utils.get(ctx.server.roles, id=int(role_id))

				if not role:
					print(f"[role handling] Role {role_id} does not exist.")
					continue
				# else:
				# only if given user object. If not used, we only want to return the mentions.
				if user_object:
					if mode == "add":
						await user_object.add_roles(role, reason="Role added for level reward or item buy")
					elif mode == "remove":
						await user_object.remove_roles(role, reason="Role removed for level reward or item buy")
					else:
						raise ValueError("Invalid mode given for add_or_remove_roles_user.")
				roles_to_mention.append(role)
			except Exception as e:
				print(f"[role handling] Error trying to {mode} {role_id}. Error code {e}")

		return None if not verbose else roles_to_mention

	# send a normal embed with given description
	async def send_embed(self, ctx, description, title=None, color=None, name=None):
		if not color or color != "green": color = self.discord_blue_rgb_code
		else: color = self.discord_success_rgb_code
		# create the embed
		embed = discord.Embed(title=title, description=description, color=color)
		if name: embed.set_author(name=ctx.username, icon_url=ctx.user_pfp)
		await ctx.channel.send(embed=embed)
		return

	# send a general error embed without detailed information
	async def send_error(self, ctx):
		embed = discord.Embed(title="Error.", description="Internal Error, call admin.",
							  color=self.discord_error_rgb_code)
		await ctx.channel.send(embed=embed)
		return

	async def send_error_report(self, ctx, err_msg):
		color = self.discord_error_rgb_code
		embed = discord.Embed(description=f"{err_msg}", color=color)
		embed.set_author(name=ctx.username, icon_url=ctx.user_pfp)
		await ctx.channel.send(embed=embed)
		return

	async def missing_admin(self, ctx):
		embed = discord.Embed(color=self.discord_error_rgb_code)
		embed.set_author(name=ctx.username, icon_url=ctx.user_pfp)
		embed.description = f"🔒 Requires {self.admin_role} role"
		await ctx.channel.send(embed=embed)
		return

	async def check_parameter_count(self, ctx, usage=None,
									 parameter_min_amount=None, parameter_max_amount=None, footer=None):
		all_parameter = ctx.param

		# + 1 because else, counting the first one as command, it would always return 0.
		if parameter_min_amount is not None:
			parameter_min_amount = parameter_min_amount + 1
		if parameter_max_amount is not None:
			parameter_max_amount = parameter_max_amount + 1

		parameter_amount = sum(1 for param in all_parameter if param != "none")
		# default: all fine.
		err_msg = None
		# check if we needed more or less parameters.
		if parameter_min_amount is not None and parameter_amount < parameter_min_amount:
			err_msg = "Too few arguments given."
		elif parameter_max_amount is not None and parameter_amount > parameter_max_amount:
			err_msg = "Too many arguments given."
		# report the correct usage.
		if err_msg:
			embed = discord.Embed(color=self.discord_error_rgb_code)
			embed.set_author(name=ctx.username, icon_url=ctx.user_pfp)
			embed.description = f"{self.emoji_error}  {err_msg}.\n\nUsage:\n`{usage}`"
			# example: "{self.emoji_error}  Too few arguments given.\n\nUsage:\n`deposit <amount or all>`"
			if footer:
				embed.set_footer(text=footer)
			await ctx.channel.send(embed=embed)
			return False
		return True

	# allow users to enter numbers using separators, e.g. 1,000,000.
	@staticmethod
	def check_formatted_number(number):
		number = number.replace(",", "").replace(".", "") # this would also allow '.' as separator.
		# number = number.replace(",", "")
		try:
			number = int(number)
			return True, number
		except (ValueError, TypeError):
			return False, None

	# check values that are supposed to either be "all" or an int (or only an int).
	async def check_amount_parameter(self, ctx, amount_param, usage, mode="flex"):
		if mode not in ["flex", "strict"]:
			raise ValueError("Mode needs to flex or strict for utils.check_amount_parameter.")
		if mode == "flex" and amount_param == "all":
			return amount_param
		# else means we're either in mode strict (only integers allowed) or something else than "all" was entered.
		else:
			is_number, amount = self.check_formatted_number(amount_param)

		if not is_number:
			msg = "<amount or all>" if mode == "flex" else "<amount>"
			embed = discord.Embed(description=f"{self.emoji_error}  Invalid `{msg}` argument given.\n\n"
											  f"Usage:\n`{usage}`", color=self.discord_error_rgb_code)
			embed.set_author(name=ctx.username, icon_url=ctx.user_pfp)
			await ctx.channel.send(embed=embed)
			return None

		return amount

	@staticmethod
	def check_if_user_exists(ctx, user_id):
		user_object = ctx.server.get_member(user_id)
		return (False, None) if not user_object else (True, user_object)

	async def send_invalid(self, ctx, invalid_parameter, usage, mode="strict", footer=None):
		invalid_parameter = f"<{invalid_parameter}>" if mode == "strict" else "[invalid_parameter]"
		embed = discord.Embed(description=f"{self.emoji_error}  Invalid `{invalid_parameter}` argument given."
										  f"\n\nUsage:\n`{usage}`", color=self.discord_error_rgb_code)
		embed.set_author(name=ctx.username, icon_url=ctx.user_pfp)
		if footer: embed.set_footer(text=footer)
		await ctx.channel.send(embed=embed)
		return

	async def check_reception_user(self, ctx, user_parameter, usage):
		reception_user = await self.get_user_id(user_parameter)

		exists, reception_user_name = self.check_if_user_exists(ctx.server, reception_user)

		if not exists:
			await self.send_invalid(ctx,"member", usage)
			return None, None

		return reception_user, reception_user_name


	async def confirm_command(self, ctx, description="Are you sure ? [y/N]", footer=None):
		# for example before completely deleting an item, we want to make sure that
		# the admin really wants to do this.
		sec_embed = discord.Embed(title="Attention", description=f"{self.emoji_rotating_light} {description}",
								  color=self.discord_blue_rgb_code)
		if footer:
			sec_embed.set_footer(text=footer)
		await ctx.channel.send(embed=sec_embed)

		security_check_input = await self.get_user_input(ctx)
		if security_check_input.strip().lower() not in ["yes", "y"]:
			await ctx.channel.send(f"{self.emoji_error}  Cancelled command.")
			return False
		# else he confirmed
		return True

