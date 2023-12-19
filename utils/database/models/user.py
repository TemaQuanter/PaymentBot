# This file contains a class that describes a database model
# of a user.

class User:

    def __init__(self, telegram_id: int, subscription_expiration_timestamp: int = None, amount_due: int = None, payment_expiration_timestamp: int = None) -> None:
        self.telegram_id = telegram_id
        self.subscription_expiration_timestamp = subscription_expiration_timestamp
        self.amount_due = amount_due
        self.payment_expiration_timestamp = payment_expiration_timestamp

    def __str__(self) -> str:
        return f"Telegram ID: {self.telegram_id}\n" \
            f"Subscription expiration timestamp: {self.subscription_expiration_timestamp}\n" \
            f"Amount due: {self.amount_due}\n" \
            f"Payment expiration timestamp: {self.payment_expiration_timestamp}\n"
