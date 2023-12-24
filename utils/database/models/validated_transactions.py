# This file contains a class that describes a database model
# of a validated transaction.

class Transaction:

    def __init__(self, transaction_id: str, transaction_timestamp: str) -> None:
        self.transaction_id = transaction_id
        self.transaction_timestamp = transaction_timestamp

    def __str__(self) -> str:
        return f"Transaction hash/id: {self.transaction_id}\n" \
            f"Transaction timestamp: {self.transaction_timestamp}"
