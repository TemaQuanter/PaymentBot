# This is a bot to accept payments in USDT TRC20 for OpenAiTrader bot.

# Import modules.
from tronapi import Tron
from dotenv import load_dotenv
import os
import json

from utils.transaction import extract_transaction_details

# Load environment variables from .env file.
load_dotenv()

# Recipient address and amount.
to_address = os.getenv("TRON_WALLET_ADDRESS")

# The amount of TRX or token to send.
amount_usdt = 100

# Tron utils.
tron = Tron()

# Get information about the transaction.
result = tron.trx.get_transaction(
    'f7af8fac8c6ffdfd40e06de60ca60c376c9a2c959da44276958967de4a1e3805')

transaction_details = extract_transaction_details(result, tron)

print(transaction_details)
