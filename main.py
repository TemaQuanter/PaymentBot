# This is a bot to accept payments in USDT TRC20 for OpenAiTrader bot.

# Import modules.
from tronapi import Tron
from dotenv import load_dotenv
import os
import json

from utils.transaction import extract_transaction_details
from bot.bot import Bot

# Load environment variables from .env file.
load_dotenv()

# Get environmental variables.
telegram_bot_api = os.getenv('TG_BOT_API')

# Initialize telegram bot.
bot = Bot(telegram_bot_api)

# Start polling the bot.
bot.poll()
