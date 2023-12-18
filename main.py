# This is a bot to accept payments in USDT TRC20 for OpenAiTrader bot.

# Import modules.
from tronapi import Tron
from dotenv import load_dotenv
import os
import json

from utils.blockchain.transaction import extract_transaction_details
from utils.bot.bot import bot_poll
from utils.database.database import PostgresDB

# Load environment variables from .env file.
load_dotenv()

# Get environmental variables.
telegram_bot_api = os.getenv("TG_BOT_API")

DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")

# Initialize a database.
db = PostgresDB(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)

# Start polling the bot.
bot_poll(telegram_bot_api)
