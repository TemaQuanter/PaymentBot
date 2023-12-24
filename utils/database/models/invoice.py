# This file contains a class that describes a database model
# of subscription invoice.

from datetime import datetime


class Invoice:

    def __init__(self, telegram_user_id: int, amount_due: str, days_valid: int, payment_expiration_timestamp: datetime) -> None:
        self.telegram_user_id = telegram_user_id
        self.amount_due = amount_due
        self.days_valid = days_valid
        self.payment_expiration_timestamp = payment_expiration_timestamp

    def __str__(self) -> str:
        return f"Telegram user id: {self.telegram_user_id}\n" \
            f"The subscription price: {self.amount_due}\n" \
            f"The number of days the subscription remains valid: {self.days_valid}\n" \
            f"Payment expiration timestamp: {self.payment_expiration_timestamp}\n"
