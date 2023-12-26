# This is a bot to accept payments in USDT TRC20 for OpenAiTrader bot.

# Import modules.
from dotenv import load_dotenv

import os

from utils.bot.bot import get_bot
from utils.bot.notificator import notify

from telegram import Update

import threading
import asyncio


# Load environment variables from .env file.
load_dotenv()

# Get environmental variables.
telegram_bot_api = os.getenv("TG_BOT_API")

# Get the bot.
application = get_bot(telegram_bot_api)

# Get the current event loop
loop = asyncio.get_event_loop()

# Run a notification cron task that makes subscriptions expire
# and notifies the users.
notify_thread = threading.Thread(target=notify, args=(application, loop))
notify_thread.start()

# Run the bot until the user presses Ctrl-C
application.run_polling(allowed_updates=Update.ALL_TYPES)
