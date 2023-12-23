# This file contains some helper functions to work with blockchain.

from random import randint
from ..database.database import PostgresDB
from ..database.models.user import User

import ntplib
from datetime import datetime, timezone

import os

from ..constants import PAYMENT_TIME_LIMIT_DELTA


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


def verify_payment_validity(transaction_details: dict, telegram_id: int) -> (bool, str):
    """This function verifies the payment validity.
    If the payment is valid, the function returns True, False - otherwise."""

    # Return message.
    return_message = (True, "OK")

    # Get a connection to database.
    db = PostgresDB()

    # Get a user from the database.
    user = db.get_user(telegram_id)

    # Check if the amount in transaction is the same as requested.
    # if user.amount_due != transaction_details["value"]:
    #     return_message = (False, "Incorrect value")

    # Check if the transaction was made on time.
    if user.payment_expiration_timestamp.replace(tzinfo=None) < datetime.utcfromtimestamp(transaction_details['timestamp']):
        return_message = (False, "Timestamp expired")

    # Check if the transactions is not an old transaction.
    # The the payment was not made before the request.
    if user.payment_expiration_timestamp.replace(tzinfo=None) - PAYMENT_TIME_LIMIT_DELTA > datetime.utcfromtimestamp(transaction_details['timestamp']):
        return_message = (False, "Timestamp too old")

    # Check that the smart-contract is the required one.
    if transaction_details["contract_address"] != os.getenv("TRON_TOKEN_SMARTCONTRACT"):
        return_message = (False, "Not USDT")

    # Check the the receiver address is the required one.
    if transaction_details["receiver_address"] != os.getenv("TRON_WALLET_ADDRESS"):
        return_message = (False, "Wrong recipient")

    # Close database connection.
    db.close_connection()

    return return_message
