# This file contains some helper functions to work with blockchain.

from random import randint

from typing import Tuple


from datetime import datetime, timezone

from tronpy import Tron
from tronpy.providers import HTTPProvider

import os
import psycopg2

import time

from src.utils.database.database import PostgresDB
from src.utils.database.models.invoice import Invoice

from ..constants import PAYMENT_TIME_LIMIT_DELTA


# def get_ntp_time(server="pool.ntp.org"):
#     """This function retrieves precise UTC timestamp."""
#     client = ntplib.NTPClient()
#     response = client.request(server)
#     utc_time = datetime.utcfromtimestamp(response.tx_time)
#     # Set the correct timezone
#     utc_time = utc_time.replace(tzinfo=timezone.utc)
#     return utc_time

def get_tron_client() -> Tron:
    """This function returns a tron client."""

    # Get a tron provider.
    provider = HTTPProvider(api_key=os.getenv("TRONGRID_API_KEY"))

    # Return a tron client with API key connection.
    return Tron(provider=provider)


def insert_invoice_with_unique_amount_usdt(telegram_id: int, amount: str, days_valid: int) -> str:
    """This function creates an invoice that is possible
    to uniquely identify in blockchain and returns it."""

    # Get a database connection.
    db = PostgresDB()

    # Remove all expired invoices.
    db.remove_expired_invoices()

    # 4-digit ending to identify the transaction.
    unique_ending = ""

    # Get 4-digit ending to identify the transaction.
    for _ in range(4):
        unique_ending += str(randint(0, 9))

    unique_amount = amount + "." + unique_ending

    # Make sure that the generated amount is completely unique.

    # Get all amounts that are already in use.
    all_unique_amounts = db.get_all_invoice_prices()

    # Traverse all possible values until the unique amount is found.
    for i in range(1, 10001):
        # Check if the value is not already in use.
        # Add '00' in order to make 6-figure decimal part for comparison.
        if (unique_amount + '00') not in all_unique_amounts:
            # Create a new invoice.
            invoice = Invoice(telegram_id, unique_amount,
                              days_valid, datetime.now(timezone.utc) + PAYMENT_TIME_LIMIT_DELTA)

            # Try to insert the invoice into the database.
            try:
                db.insert_invoice(invoice)

                # Insertion was successful, exit the loop.
                break
            except psycopg2.errors.UniqueViolation:
                # An invoice with the same amount due is already in the database.
                pass

        # Increment unique ending by 1 mod 10000.
        unique_amount = f"{amount}.{((int(unique_ending) + i) % 10000):04d}"
    else:
        # All unique values are busy.
        # Close database connection.
        db.close_connection()
        raise Exception("All unique endings are busy")

    # Close database connection.
    db.close_connection()

    return invoice


def verify_payment_validity(transaction_details: dict, telegram_id: int) -> Tuple[bool, str]:
    """This function verifies the payment validity.
    If the payment is valid, the function returns True, False - otherwise."""

    # Establish connection with Tron blockchain.
    tron = get_tron_client()

    # Return message.
    return_message = (True, "OK")

    # Wait for the block to become confirmed.
    while True:
        try:
            # Query transaction info.
            transaction_info = tron.get_transaction_info(
                transaction_details["transaction_id"])

            # Check if the block is confirmed.
            if "id" in transaction_info.keys():
                # Get out of the loop.
                break
        except ValueError:
            return (False, "Transaction not found")
        except:
            return (False, "Internal server error")

        # Wait for some time before performing the check again.
        time.sleep(3)

    # Get a connection to database.
    db = PostgresDB()

    try:
        # Get user invoice
        invoice = db.get_invoice(telegram_id)
    except psycopg2.DatabaseError as e:
        db.close_connection()
        return (False, "Internal server error")

    # Check if transaction status is success.
    if transaction_details["status"] != "SUCCESS":
        return_message = (False, "Transaction failed")

    # Check if the amount in transaction is the same as requested.
    if str(invoice.amount_due).rstrip("0") != str(transaction_details["value"]).rstrip("0"):
        return_message = (False, "Incorrect value")

    # Check if the transaction was made on time.
    if invoice.payment_expiration_timestamp < datetime.utcfromtimestamp(transaction_details['timestamp']).replace(tzinfo=timezone.utc):
        return_message = (False, "Timestamp expired")

    # Check if the transactions is not an old transaction.
    # The the payment was not made before the request.
    if invoice.payment_expiration_timestamp - PAYMENT_TIME_LIMIT_DELTA > datetime.utcfromtimestamp(transaction_details['timestamp']).replace(tzinfo=timezone.utc):
        return_message = (False, "Timestamp too old")

    # Check that the smart-contract is the required one.
    if transaction_details["contract_address"] != os.getenv("TRON_TOKEN_SMARTCONTRACT"):
        return_message = (False, "Not USDT")

    # Check the the receiver address is the required one.
    if transaction_details["receiver_address"] != os.getenv("TRON_WALLET_ADDRESS"):
        return_message = (False, "Wrong recipient")

    # Try to insert transaction into used transactions.
    # Check if transaction is valid (otherwise it may be exploited in a way
    # that decent users will not be able to complete the payment)
    if return_message[0]:
        # The transaction is valid.
        # Now check if it was used for payment.
        try:
            if not db.insert_validated_transaction(
                    transaction_details["transaction_id"], datetime.utcfromtimestamp(transaction_details['timestamp'])):
                # The transaction is already registered.
                return_message = (
                    False, "This transaction has been already used")

        except psycopg2.DatabaseError as e:
            return_message = (False, "Internal server error")

    # Close database connection.
    db.close_connection()

    return return_message
