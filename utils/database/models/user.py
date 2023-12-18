# This file contains a class that describes a database model
# of a user.

class User:

    def __init__(self, telegram_id: int) -> None:
        self.telegram_id = telegram_id
