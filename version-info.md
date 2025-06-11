# Version Information for the Skender Bot on Discord

**Official Repository:** [github.com/NoNameSpecified/UnbelievaBoat-Python-Bot](https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot)  
**Last Updated:** 11.06.2025 (European date format)  
For **future updates**, keep track of the Skender version you're using.  
For more, see the intro comment in database/database_migration.py.

**Update to v2.0 Notice:**  
I'm very happy to finally announce a big upgrade for this "Unbelievaboat-Python-Bot", which has now been baptized _Skender_.   
There will still be bugs left that I didn't discover yet. Please report these to me to fix.  
After the switch to v2.0, updates will be incrementally again and not with a long pause and then one big update like this time.  
For any questions, suggestions or bug reports, feel free to contact me on discord at <kendrik2.0>.

---

### 🆕 Skender v2.1 (Released: 11.06.2025)

Please update the files mentioned below, main.py doesn't have to be updated.

#### 🔧 Fixed multiple bugs.
- Updated `bot.py`, `database/__init__.py`, `utilities.py`.
- Updated `main.py`, but only to change the bot_version variable to v2.1

#### 💡 Clarification
- Users only gain xp if levels have been created (use `change-levels`) but they will still earn passive chat income.
- Clarification: the excluding / including of specific channels for gaining xp also applies to passive chat income.

---

## 🆕 Skender v2.0 (Released: 11.06.2025)

**To switch from the legacy version to v2.0, a migration script is provided with v2.0.**  
**You will _automatically be guided through the migration_ when launching the new version for the first time and do not need to use it manually. But please read the instructions in the console during the process.**

### 🔧 What's New

- **Switched database** from JSON to SQLite:
    - Improved performance.
    - Fixed race condition issues.
    - Implemented batched and chunked database operations where possible.
- **Completely rebuilt** the bot’s front-end structure, including directory layout.  
  _If you're upgrading from a version below v2.0, please re-download the entire repository!_
- Centralized **customizable edits** (such as token, admin role name...) in main.py lines 40-50.
- **Automatic database setup wizard** on first launch (can be skipped).  
  Includes cooldown configuration, etc.
- **Updated and new commands:**
    - `add-money-by-role`
    - `update-income-role`
    - `module-info`
    - `change-action` and `change-variable` now as two separate commands.
    - Reworked help system: staff commands only visible to staff members
- **New features:**
    - Max amount per transaction for buying items
    - Cooldowns (in minutes) and money limits for gambling (roulette, blackjack)
    - Income reset now applies to both `collect` and `update-income`
- **New: Level system:**
    - Fully customizable:
        - Set XP per message and message delay (e.g. only 1 msg every X min counts)
        - Define level thresholds manually
        - Assign rewards per level (money, items, roles to give, roles to remove)
    - Includes:
        - User `level` info, `add-xp`, `remove-xp`, `level-leaderboard`, overview of `all-levels`
        - Define specific channels as: *include only these* or *exclude these*
- **New: Passive chat income**  
  Uses same delay setting as for XP.
- **Various bug fixes and cosmetic updates.**

---

### ❌ Not added

- **Transaction history**: intentionally omitted because:
    - Transaction data is already public in server channels
    - Would unnecessarily increase database operations and saved data

---

### 🗑️ Removed from Legacy Version

- Nothing has been removed.

---

## 🛣️ Mid-/Long-Term Roadmap

- Allow multiple users to bet on the same roulette game.
- Add slash command support.
- Rework item creation to make it more efficient.
- Add arrows to embeds with multiple pages.

---

## 🪦 Legacy JSON Version

**Developed from:** Early 2021 – May 2025  
**For further info & the source code of this version:**  
[github.com/NoNameSpecified/UnbelievaBoat-Python-Bot/releases/tag/v1-legacy-json](https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot/releases/tag/v1-legacy-json)
