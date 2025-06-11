# UnbelievaBoat-like Discord Bot in Python (aka _Skender_)

### Questions, bug reports or need help with setup ?
Feel free to reach out to me on Discord at **<kendrik2.0>**

## Current version Notice:
- 🔧 Skender v2.1 (bug fixes) released on 11.06.2025 (for changed files, see `version-info.md`)
- 🆕 Skender v2.0 was released on 11.06.2025 (european time format). Please take a look at `version-info.md`, especially if you used the JSON version before !
- 🛠️ Please read `command-list.md`. It includes a list of all available commands with explanations and tips.

---

## Official repo:
https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot  
You're free to do anything with the code, but please keep a link to the original (see License Section 2).

---

## 📣 Info:
The Bot uses most of UnbelievaBoat's commands for minigames and economy (not moderation tho).  
With time, a lot of functionalities were added.  
I don't know what exactly the normal Unbelievaboat includes nowadays, but you can check out `command-list.md`

---

## 🌱 Install & Use
1. Create a Discord Application for your bot (see https://youtu.be/b61kcgfOm_4, [Discord Developer Portal](https://discord.com/developers/applications))
2. In the "Bot" section of the Discord Developer Portal, **enable Presence Intent**, **Server Members Intent**, and **Message Content Intent**.
3. Download the code and ensure the directory structure is preserved.
4. Open `main.py`, edit lines 40-50 as needed (comments are included).
5. Invite the bot to your server as shown in https://youtu.be/b61kcgfOm_4
6. Create a role for your bot with permission to manage roles (the bot's role must be above the roles it should manage).
7. Install Python 3, if not already installed.
8. Install `discord.py` using `pip install discord.py`.
9. Create a role in your server called "botmaster" (or whatever you named it in `main.py`) and assign it to the bot admins.
10. Launch `main.py` with **python3**.

You will be guided through the rest of the setup.  
Please take the customizable lines in `main.py` seriously, including the setup channel ID.

---

## 🎯 Goal
It emerged from the problem of UB having a balance ceiling and no automated role-income increasing to user's balances.  
Obviously it's way bigger now.  
The goal was to create an **easily customizable template** for a Discord bot, also addressing the issues mentioned above.  
Another goal is to have the bot written in Python, so that users can easily modify the code to fit their needs.

---

## ⚠️ Version 2.0 Notes

A migration script is provided for the switch from the legacy version (json database) to v2.0.  
The migration is **automatic** on first launch, but make sure to follow the console instructions during the process.  
For more, see version-info.md, you can also look at the big comment block at the end of main.py  
If you have any questions, reach out to me via discord (see above).

---

## 🎉 Enjoy customizing and using the bot !
Feel free to share feedback, bug reports, and suggestions !

