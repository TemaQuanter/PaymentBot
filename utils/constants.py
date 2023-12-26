from datetime import timedelta
from dotenv import load_dotenv

import os

# Load environment variables from .env file.
load_dotenv()

# Time limit for payment.
PAYMENT_TIME_LIMIT_DELTA = timedelta(hours=1)

# Transaction expiration timestamp.
TRANSACTION_EXPIRATION_TIMESTAMP = timedelta(hours=2)

# Service address.
SERVICE_ADDRESS = os.getenv("SERVICE_ADDRESS")

# Path to the file with the policy.
POLICY_PATH = "./data/policy.txt"

# URL of trading bot.
SERVICE_URL = os.getenv("SERVICE_URL")

# Support credentials.
SUPPORT_CREDENTIALS = os.getenv("SUPPORT_CREDENTIALS")
