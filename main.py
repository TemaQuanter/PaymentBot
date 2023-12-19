# This is a bot to accept payments in USDT TRC20 for OpenAiTrader bot.

# Import modules.
from dotenv import load_dotenv
import os

from utils.bot.bot import bot_poll

# Load environment variables from .env file.
load_dotenv()

# Get environmental variables.
telegram_bot_api = os.getenv("TG_BOT_API")

# Start polling the bot.
bot_poll(telegram_bot_api)
