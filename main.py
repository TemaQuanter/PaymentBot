# This is a bot to accept payments in USDT TRC20 for OpenAiTrader bot.

# Import modules.
from dotenv import load_dotenv

import os


from telegram import Update

import threading
import asyncio

from src.bot.bot import get_bot
from src.bot.notificator import notify


# Load environment variables from .env file.
load_dotenv()

# Get environmental variables.
telegram_bot_api = os.getenv("TG_BOT_API")

# Get the bot.
application = get_bot(telegram_bot_api)

# Create a new event loop and set it.
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Run a notification cron task that makes subscriptions expire
# and notifies the users.
notify_thread = threading.Thread(target=notify, args=(application, loop))
notify_thread.start()

# Run the bot until the user presses Ctrl-C
application.run_polling(allowed_updates=Update.ALL_TYPES)
