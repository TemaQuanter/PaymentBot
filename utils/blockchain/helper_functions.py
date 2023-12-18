# This file contains some helper functions to work with blockchain.

from random import randint


def get_unique_amount_usdt(amount: str) -> str:
    """This function returns a unique amount USDT to be payed to identify
    the transaction."""

    # 4-digit ending to identify the transaction.
    unique_ending = ".00"

    # Get 4-digit ending to identify the transaction.
    for _ in range(4):
        unique_ending += str(randint(0, 9))

    return amount + unique_ending
