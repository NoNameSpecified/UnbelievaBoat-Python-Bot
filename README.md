# UnbelievaBoat-like Discord Bot in Python (aka _Skender_)

### Questions, bug reports or need help with setup ?
Feel free to reach out to me on Discord at **@kendrik2.0**

## Current version Notice:  
#### Currently working on Skender v3, but this will still take some time.
See [v2 release announcement](https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot/releases/tag/v2-legacy-version) for more.  
Development status info (2026-01-03): The v3 update will include a lot of new features and reworked functioning of the bot, sadly this
also means that the release will take more time  until everything is implemented correctly.  
If you have recommendations, feel free to hit me up !

To keep your bot version up to date with released updates, see `version-info.md`.  
#### Please read `command-list.md`. It includes a list of all available commands with explanations and tips.

---

## Official repo:
https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot  
You're free to do anything with the code, but please keep a link to the original repo if you publish yours (see License Section 2).

---

## 🎯 Info and Goal:
Skender emerged from the problem of UB having a balance ceiling and no automated role-income increasing to user's balances, so I rewrote it in python and fixed that.   
The goal was to create an **easily customizable python template** for a Discord bot, so that users can modify the code to fit their needs and build upon it.  

The Bot uses most of UnbelievaBoat's commands for minigames and economy (not moderation tho). After the first basic version,
 I didn't look at UB anymore and added functionalities based on recommendations from users.   
So, I don't know what exactly the "normal" Unbelievaboat includes nowadays, but you can check out `command-list.md` to see what Skender comes with.

---

## 🏁 Install and Use
1. Create a Discord Application for your bot (see https://youtu.be/b61kcgfOm_4, [Discord Developer Portal](https://discord.com/developers/applications))
2. In the "Bot" section of the Discord Developer Portal, **enable Presence Intent**, **Server Members Intent**, and **Message Content Intent**.
3. Download the code and ensure the directory structure is preserved.
4. Open `main.py`, edit lines 40-50 as needed (comments are included).
5. Invite the bot to your server as shown in https://youtu.be/b61kcgfOm_4
6. Create a role for your bot with permission to manage roles (the bot's role must be above the roles it should manage).
7. Install Python 3, if not already installed.
8. Install `pip install discord.py` and `pip install requests`.
9. Create a role in your server called "botmaster" (or whatever you named it in `main.py`) and assign it to the bot admins.
10. Launch `main.py` with **python3**.

You will be guided through the rest of the setup.  
Please take the customizable lines in `main.py` seriously, including the setup channel ID.  
You can browse the database by using a tool like [SQLite Browser](https://sqlitebrowser.org), but be careful when editing
variables directly through a SQLite browser, since it may interfere with the bot usage (especially for JSON strings in the database).


---

## ⚠️ Version 2.0 Notes

A migration script is provided for the switch from the legacy version (json database) to v2.0.  
The migration is **automatic** on first launch, but make sure to follow the console instructions during the process.  
For more, see version-info.md, you can also look at the big comment block at the end of main.py  
If you have any questions, reach out to me via discord (see above).

---

## 🎉 Enjoy customizing and using the bot !
Feel free to share feedback, bug reports, and suggestions !  
Btw: if use this bot for your server, you can let me know if you want (just message me on discord), I'd be happy to see people using it !
