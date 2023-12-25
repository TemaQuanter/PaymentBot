from datetime import timedelta

import os

# Time limit for payment.
PAYMENT_TIME_LIMIT_DELTA = timedelta(hours=1)

# Transaction expiration timestamp.
TRANSACTION_EXPIRATION_TIMESTAMP = timedelta(hours=2)

# Service address.
SERVICE_ADDRESS = os.getenv("SERVICE_ADDRESS")
