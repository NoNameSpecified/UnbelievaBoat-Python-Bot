# **UnbelievaBoat-like Discord Bot in python**
### For questions about the bot and how to set it up: ask me on Discord at *<kendrik2.0>*

Code is finished, so there won't be any big updates anymore.
But please report any problems to me via Discord or by opening an issue !

## Official repo:   
https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot

You're free to do anything with the code, I'd appreciate it if you would keep a link to the official repo tho :)


### - Info
The Bot uses most of UnbelievaBoat's commands for minigames and economy (not moderation tho).
I have actually tweaked it a bit and added things that people suggested. 
#### For a full list, see `src/command_list.txt`.
It emerged from the problem of UB having a balance ceiling and no automated role-income increasing to user's balances.
Obviously it's way bigger now.

### - Goal
The goal was to make an easily customizable Template of a discord bot, also fixing the issues stated above.
Another goal is to have the bot written in python so that it's easy to edit for every user. You can adjust the code so it fits exactly what you need.

### - Install & Use
1. Create a Discord Application for your bot (see https://youtu.be/b61kcgfOm_4, https://discord.com/developers/applications)
2. In the Discord Dev Portal, in the "Bot" tab of your application, **enable presence intent, server members intent, message content intent**.
3. Download the code, structured as in this repo.
4. Open the `main.py` file, line 40 and change the **token** to the one of your created bot.
5. [optional] In the `database/database.json` file: scroll down to the symbols part and put a *custom emoji name* in the "symbol_emoji" variable. - for example if you have a bitcoin emoji called "btc". It must be an emoji you uploaded to the server, not a discord-wide one.
    --> info to step 6: it is set to 💰 as default. you can still change that by following step 6 and changing line 75-77 in database/__init__.py. Note: if you uncomment 75, you gotta comment out line 77 ! (by putting a <#> before it, like in line 76
6. Invite the bot to your server as shown in https://youtu.be/b61kcgfOm_4
7. Install python3 if you dont have it
8. Install the Discord Api for python3 using pip (`pip install discord.py`)
9. In your server, create a role named "botmaster" and give it to people who should be bot admins.
10. Launch main.py with **python3**. Beware !! On Windows, please use powershell, else path might not be recognized.

You should be good to go!


### json usage
tldr: json is problematic but I think for small stuff this should still work, contact me if you got any problems / questions tho.
longer version:
So i made this bot a long time ago and I decided to use json, which is honestly a bad idea for a database, as pointed out in https://stackoverflow.com/a/73869286.
However, it would take way too long to change the whole system now, especially since I'm only fixing and adding minor stuff now and don't have the time to do big changes.
But from what I can tell, this works fine aswell and not that slow! If you do face problems concerning speed, please contact me (discord or issue on github) and maybe I can do a little, if it's due to json usage I won't be able to help you tho.
