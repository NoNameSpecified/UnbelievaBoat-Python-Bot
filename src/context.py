"""
INFO:

	The "context" variables used for the Skender discord bot.

	Official Repo: https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot

	imported as in bot.py and used in on_message(self, message).
		without an extra context class, we would always need to pass the channel, username, user_pfp etc. variables.
		now we can just get it over here and pass it inside the bot with a central variable "ctx".

	for more info see bot.py

"""

class CommandContext:
	def __init__(self, message, admin_role, param):
		# all these "self.variable" will be able to be called as "ctx.variable" in bot.py.
		self.message = message
		self.channel = message.channel
		self.server = message.guild
		self.param = param
		self.user = message.author.id
		self.user_ctx_obj = message.author
		self.user_mention = message.author.mention
		self.user_pfp = message.author.display_avatar.url
		self.username = message.author.name
		self.nickname = str(message.author.display_name)
		self.user_roles = [role.id for role in message.author.roles]

		# some stuff will be only for staff, which will be recognizable by a specific admin-only role
		# for example, admin_role could be "botmaster".
		self.staff = any(role.name == admin_role for role in message.author.roles)
		# print("staff status : ", staff_request)
