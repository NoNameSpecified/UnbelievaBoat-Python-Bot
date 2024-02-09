# **UnbelievaBoat-like Discord Bot in python**
### For questions about the bot and how to set it up: ask me on Discord at *<kendrik2.0>*

Code is finished, so there won't be any big updates anymore.  
But please report any problems to me via Discord or by opening an issue !

## Official repo:   
https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot  
You're free to do anything with the code, I'd appreciate it if you would keep a link to the official repo tho :)


### - Info
The Bot uses most of UnbelievaBoat's commands for minigames and economy (not moderation tho).  
With time, I have added quite some modifications, couldn't really say which tho, since I dont even use UB anymore lol.

### Please read `src/command_list.txt`.
It not only helps users with how/what commands to use, it also gives tips for admins (using get-salary vs update-income for example).

### - Install & Use
1. Create a Discord Application for your bot (see https://youtu.be/b61kcgfOm_4, https://discord.com/developers/applications)
2. In the Discord Dev Portal, in the "Bot" tab of your application, **enable presence intent, server members intent, message content intent**.
3. Download the code, structured as in this repo.
4. Open the `main.py` file, line 40 and change the **token** to the one of your created bot.
5. Invite the bot to your server as shown in https://youtu.be/b61kcgfOm_4
6. Install python3 if you dont have it
7. Install the Discord Api for python3 using pip (`pip install discord.py`)
8. In your server, create a role named "botmaster" and give it to people who should be bot admins.
9. Launch main.py with **python3**. Beware !! On Windows, please use powershell, else path might not be recognized.
10. [optional]: by default, the currency emoji is set to 💰.  
    You can change it as follows: changing line 75-77 in database/__init__.py. Note: if you uncomment 75, you gotta comment out line 77 ! (by putting a <#> before it, like in line 76. Then use change-currency-symbol (see src/commands.txt) or change "symbol_emoji" `in database/database.json`(needs to be a custom emoji). Contact me if you got issues.

You should be good to go!


### - Goal
It emerged from the problem of UB having a balance ceiling and no automated role-income increasing to user's balances. Obviously it's way bigger now.  
The goal was to make an easily customizable Template of a discord bot, also fixing the issues stated above.  
Another goal is to have the bot written in python so that it's easy to edit for every user. You can adjust the code so it fits exactly what you need.   

### images
On 09.02.24 update I added the option add images for items, that would be shown when calling the single item catalog info ("catalog item_name").
These images are loaded by URL - so they can be anything. I don't encourage however nor do I care if you use licensed images, since i have no way of checking that.
But I definitely don't take any warranty as to what happens if you do use licensed images. Stay safe !

### - json usage
TLDR: json is problematic but I think for small stuff this should still work, contact me if you got any problems / questions tho.  

longer version: So i made this bot a long time ago and I decided to use json, which is honestly a bad idea for a database, as pointed out in https://stackoverflow.com/a/73869286.
However, it would take way too long to change the whole system now, especially since I'm only fixing and adding minor stuff now and don't have the time to do big changes.
But from what I can tell, this works fine aswell and not that slow! If you do face problems concerning speed, please contact me (discord or issue on github) and maybe I can do a little, if it's due to json usage I won't be able to help you tho.
