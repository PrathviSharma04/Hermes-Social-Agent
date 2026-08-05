# Telegram Command Center Setup

The Hermes Social Agent is designed to be fully remote-controlled via Telegram (Phase 10). This means you don't need to SSH into your server to check status, approve posts, or change strategies.

## 1. Create a Bot on Telegram
1. Open Telegram and search for `@BotFather`.
2. Send the command `/newbot`.
3. Follow the instructions to choose a name and username for your bot.
4. BotFather will give you an **HTTP API Token**. Keep this secret.

## 2. Get Your Chat ID
1. Search for `@userinfobot` on Telegram and send it a message.
2. It will reply with your `Id` (a number like `123456789`). This is your personal Chat ID.

## 3. Configure the Agent
Open your `.env` file and set the credentials:

```env
TELEGRAM_BOT_TOKEN=your:bot_token_from_botfather
TELEGRAM_CHAT_ID=your_chat_id
```
*(Setting `TELEGRAM_CHAT_ID` ensures the bot will only respond to you and ignore commands from strangers.)*

## 4. Run the Bot
Start the bot in long-polling mode directly from the CLI:

```bash
hermes-social telegram start
```
*(On an EC2 instance, you should run this using `screen`, `tmux`, or as a `systemd` service so it stays alive).*

To quickly verify your connection without starting the full bot, run:
```bash
hermes-social telegram test
```

## Example Commands
You can speak to the bot naturally. Try:
- *"What are you posting tomorrow?"*
- *"Show me this week's performance."*
- *"Approve tomorrow's post."*
- *"Pause publishing."*
- *"Emergency stop!"*
