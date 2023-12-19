# This file contains some helper functions to work with blockchain.

from random import randint
from ..database.database import PostgresDB
from ..database.models.user import User

import ntplib
from time import ctime
from datetime import datetime, timezone


def get_ntp_time(server="pool.ntp.org"):
    """This function retrieves precise UTC timestamp."""
    client = ntplib.NTPClient()
    response = client.request(server)
    utc_time = datetime.utcfromtimestamp(response.tx_time)
    # Set the correct timezone
    utc_time = utc_time.replace(tzinfo=timezone.utc)
    return utc_time


def get_unique_amount_usdt(amount: str) -> str:
    """This function returns a unique amount USDT to be payed to identify
    the transaction."""

    # 4-digit ending to identify the transaction.
    unique_ending = ".00"

    # Get 4-digit ending to identify the transaction.
    for _ in range(4):
        unique_ending += str(randint(0, 9))

    return amount + unique_ending


def verify_payment_validity(transaction_details: dict, telegram_id: int) -> bool:
    """This function verifies the payment validity.
    If the payment is valid, the function returns True, False - otherwise."""
    return True
