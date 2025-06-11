"""
START OF ROOULETTE for https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot.
ROULETTE GAME SLOTS found on https://github.com/ntaliceo/roulette-simulator,
rest is done here
"""

import random, discord, asyncio
# import time


# what will be called to play the game
class roulette_discord_implementation:
	def __init__(self, ctx, bot, currency_emoji):
		self.bot = bot
		self.channel = ctx.channel
		self.currency_symbol = currency_emoji
		# note on 12.10.23: im gonna remove <'00': 'green',> to make it a european roulette game
		self.slots = {'0': 'green', '1': 'red', '2': 'black',
					  '3': 'red', '4': 'black', '5': 'red', '6': 'black', '7': 'red',
					  '8': 'black', '9': 'red', '10': 'black', '11': 'red',
					  '12': 'black', '13': 'red', '14': 'black', '15': 'red',
					  '16': 'black', '17': 'red', '18': 'black', '19': 'red',
					  '20': 'black', '21': 'red', '22': 'black', '23': 'red',
					  '24': 'black', '25': 'red', '26': 'black', '27': 'red',
					  '28': 'black', '29': 'red', '30': 'black', '31': 'red',
					  '32': 'black', '33': 'red', '34': 'black', '35': 'red',
					  '36': 'black'}
	"""
	
	not used but may be, if adding that multiple player can play the same roulette game at once
	
	async def get_user_input(self, message):
		# we want an answer from the guy who wants to give an answer
		answer = await self.bot.wait_for("message", check=lambda response: response.author == message.author)
		answer = answer.content
		# clean input
		answer = answer.lower().strip()
		# we only want hit or stand, nothing else, and still wait after that tho
		if answer not in ["hit", "stand"]:
			return "none"

		return answer
	"""

	async def play(self, ctx, bot, bet, space):
		self.bot = bot

		# get space type
		spaceType = "string"
		try:
			space = int(space)
			spaceType = "int"
		except:
			pass
		space = str(space).lower().strip()

		spin_time = 10

		color = discord.Color.from_rgb(3, 169, 244)
		embed = discord.Embed(description=f"You have placed a bet of {str(self.currency_symbol)} {bet} on `{space}`.", color=color)
		embed.set_author(name=ctx.username, icon_url=ctx.user_pfp)
		embed.set_footer(text=f"Spinning ! ... time remaining: {spin_time} seconds")
		await ctx.channel.send(embed=embed)

		# we're going to use asyncio.sleep() again, after it was put to time.sleep() before
		# i.e. freezing the whole bot. Before the sqlite update, it would create race condition problems with the
		# json database. Now it should be pretty robust with sqlite.
		await asyncio.sleep(spin_time)

		win = lose = multiplicator = None

		if space in ["odd", "even", "black", "red"]:
			multiplicator = 2
		else:
			multiplicator = 35

		result = random.choice(list(self.slots.keys()))
		# print(self.slots[result], result)
		# print(type(result))
		result_prompt = f"The ball landed on: **{self.slots[result]} {result}**!\n\n"

		if space == "black":
			win = 1 if self.slots[result] == "black" else 0

		elif space == "red":
			win = 1 if self.slots[result] == "red" else 0

		elif space == "even":
			result = int(result)
			win = 1 if (result % 2) == 0 else 0

		elif space == "odd":
			result = int(result)
			win = 1 if (result % 2) != 0 else 0

		elif spaceType == "int":
			win = 1 if space == result else 0

		else:
			# shouldnt happen
			print("error")
		# print("here")
		if win:
			result_prompt += f"🎉  **Winner:**  🎉\n{ctx.user_mention} won {str(self.currency_symbol)} {bet*multiplicator}"
		else:
			# TODO when we let multiple users bet on the same roulette
			# result_prompt += "**No Winner :(**"
			result_prompt += f"**No Winner :(**\nYou lost your bet, {ctx.user_mention}"

		# inform user
		await ctx.channel.send(result_prompt)

		return win, multiplicator

