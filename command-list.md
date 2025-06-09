# 📜 Command List for Skender Bot v2.0

**Last updated:** 09.06.2025 (European date format)  
**Official Repository:** [github.com/NoNameSpecified/UnbelievaBoat-Python-Bot](https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot)  
👉 For setup instructions, see `README.md`.

> Prefix used here: `+`  
> You can change it in `main.py`.
>
> `<this>` means required parameter, `[this]` means optional parameter
>

---

## 0. ℹ️ Information

- Help page: `+help`

---

## 1. 🎲 Mini-Games

- Blackjack: `+blackjack <bet>`
- Roulette: `+roulette <bet> <space>`

---

## 2. 💰 Balance & Money

- Economy Stats: `+stats`
- Check Balance: `+balance`
- Deposit Money: `+deposit <amount or all>`
- Withdraw Money: `+withdraw <amount or all>`
- Give Money: `+give <@member> <amount or all>`
- Server Leaderboard: `+leaderboard [page] [-cash | -bank | -total]`

### 2.1 Admin Commands – Balance & Money

- `+add-money <@member> <amount>`
- `+remove-money <@member> <amount> [cash/bank]`  
  ℹ️ Default: bank
- `+add-money-role <@role> <amount>`
- `+remove-money-role <@role> <amount>`  
  ℹ️ Removes from bank. If amount > user balance, it sets balance to 0.
- `+clear-db`  
  ℹ️ Removes users who left the server from the database (irreversibly).

---

## 3. 💼 Income Commands

- `+slut`
- `+crime`
- `+work`
- `+rob`

---

## 4. 🛠️ Customization (Admin only)

- `+module-info [module]`  
  Get module (income commands) info. You can use this info to later edit the values.
  If you don't know the module names, just use +module without any parameter.
- `+change-variable <variable> <new value>`  
  Change variable settings
  Tip: Use `+module` first and then use change-variable.
- `+change-action <action_name> <variable> <new value>`  
  Example: change delay (cooldown) for blackjack.
- `+change-currency <new emoji name>`  
  Only emojis uploaded to your server are valid, not a discord wide one.
- `+set-income-reset <false/true>`  
  Controls whether income accumulates or if you always only get one-day-income. 
  By default, it is set to true.
- `+set-passive-chat-income <amount>`  
  Passive chat income means that the user receives a certain sum for being active and sending messages.
  The cooldown for this is the same as for gaining xp per message.

---

## 5. 🎁 Items

- `+buy-item <item_name> <amount>`
- `+give-item <@member> <item_name> <amount>`
- `+inventory [page]` – See your own inventory
- `+user-inventory <@member> [page]` – See another user's inventory
- `+use <item_name> <amount>`
- `+catalog [item_name]`  
  Just +catalog shows a list of all items available.
  +catalog name shows detailed information of a specific item.

### 5.1 Admin Commands – Items

- `+create-item`
- `+delete-item <item_name>`  
  ℹ️ Completely removes item for everyone
- `+remove-user-item <@member> <item_name> <amount>`
- `+spawn-item <@member> <item_name> [amount]`  
  ℹ️ Adds an (already created) item to inventory

---

## 6. 👥 Income Roles

Users with a specific role will receive daily income (e.g., 100 = 100/day)

- `+list-roles`
- `+collect`  
  Uses `income_reset` setting to determine payout behavior.
  Can/should be disabled depending on if you want to use update-income

### 6.1 Admin Commands – Income Roles

- `+add-income-role <@role> <income>`
- `+remove-income-role <@role>`
- `+update-income-role <@role> <new_income>`
- `+update-income`  
  Pays all users with income roles.  
  ⚠️ Also affected by `income_reset`.

💡 **Tip:**  
Use `+collect` with `income_reset` set to true (default) and avoid using `update-income`.  
To disable `+collect`, edit `bot.py` and comment out the relevant block (elif command in ["collect" ...).

---

## 7. 🧬 Levels

- `+level [@member]` – View own or mentioned user’s level
- `+all-levels` – Overview of all levels & rewards
- `+level-lb [page]` – Level leaderboard

### 7.1 Admin Commands – Levels

- `+change-levels` – Modify levels and their thresholds, rewards, and XP channels
- `+add-xp <@member> <amount>`
- `+remove-xp <@member> <amount>`

ℹ️ To modify passive chat income, use `+set-passive-chat-income`

---
