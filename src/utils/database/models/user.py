# This file contains a class that describes a database model
# of a user.

from datetime import datetime


class User:

    def __init__(self, telegram_id: int, subscription_expiration_timestamp: datetime = None, informed_about_expiration: bool = False) -> None:
        self.telegram_id = telegram_id
        self.subscription_expiration_timestamp = subscription_expiration_timestamp
        self.informed_about_expiration = informed_about_expiration

    def __str__(self) -> str:
        return f"Telegram ID: {self.telegram_id}\n" \
            f"Subscription expiration timestamp: {self.subscription_expiration_timestamp}\n" \
            f"Informed about expiration: {self.informed_about_expiration}"
