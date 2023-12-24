# This file contains a class that describes a database model
# of a subscription plan.

class SubscriptionPlan:

    def __init__(self, days_valid: int, amount_due: str) -> None:
        self.id = None
        self.days_valid = days_valid
        self.amount_due = amount_due

    def __str__(self) -> str:
        return f"The number of days the subscription remains valid: {self.days_valid}\n" \
            f"The subscription price: {self.amount_due}\n"
