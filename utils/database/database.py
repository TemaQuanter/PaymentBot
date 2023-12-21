# This file contains utils for working with databases.

import psycopg2
import os

from .models.user import User

from datetime import datetime, timedelta, timezone


class PostgresDB:

    def __init__(self) -> None:
        # Get a database connection.
        self.conn = psycopg2.connect(database=os.getenv("POSTGRES_DB"),
                                     user=os.getenv("POSTGRES_USER"),
                                     password=os.getenv("POSTGRES_PASSWORD"),
                                     host=os.getenv("POSTGRES_HOST"),
                                     port=os.getenv("POSTGRES_PORT"))

        # Create a cursor.
        self.cursor = self.conn.cursor()

    def get_user(self, telegram_id: int) -> User:
        """Return a user from the database."""

        # Execute the command.
        self.cursor.execute(
            f"SELECT * FROM users WHERE telegram_id = {telegram_id}")

        # Get data.
        rows = self.cursor.fetchall()

        # Create a user instance with the data extracted from the database.
        user = User(telegram_id)
        user.subscription_expiration_timestamp = rows[0][1]
        user.amount_due = rows[0][2]
        user.payment_expiration_timestamp = rows[0][3]

        return user

    def insert_user(self, user: User):
        """Insert a new user into the database."""

        try:
            self.cursor.execute(
                "INSERT INTO users (telegram_id) VALUES (%s);", (user.telegram_id,))
            self.conn.commit()
        except psycopg2.DatabaseError as e:
            self.conn.rollback()
            raise e

    def set_amount_due_and_payment_expiration_timestamp(self, user: User):
        """Update amount due and payment expiration timestamp."""

        try:
            self.cursor.execute(
                "UPDATE users SET amount_due = %s, payment_expiration_timestamp = %s WHERE telegram_id = %s;", (user.amount_due, user.payment_expiration_timestamp, user.telegram_id))
            self.conn.commit()
        except psycopg2.DatabaseError as e:
            self.conn.rollback()
            raise e

    def prolong_subscription(self, user: User, period: timedelta):
        """Update subscription expiration timestamp."""

        # Get the current subscription.

        # Retrieve the user from the database.
        user = self.get_user(user.telegram_id)

        # If it is None, then use the current time to calculate the expiration time.
        if user.subscription_expiration_timestamp == None:
            user.subscription_expiration_timestamp = datetime.now(
                timezone.utc) + period
        else:
            # Otherwise - set a new expiration time based on the current subscription
            # expiration time.
            user.subscription_expiration_timestamp += period

        # Save a new subscription expiration time to the database.
        try:
            self.cursor.execute(
                "UPDATE users SET subscription_expiration_timestamp = %s WHERE telegram_id = %s;", (user.subscription_expiration_timestamp, user.telegram_id))
            self.conn.commit()
        except psycopg2.DatabaseError as e:
            self.conn.rollback()
            raise e

    def insert_validated_transaction(self, transaction_id: str, transaction_timestamp: datetime) -> bool:
        """This function inserts a validated transaction into the database.
        If the transaction already exists, the function returns False, true - otherwise."""

        try:
            self.cursor.execute("INSERT INTO validated_transactions (transaction_id, transaction_timestamp) VALUES (%s, %s)", (
                transaction_id, transaction_timestamp))
            self.conn.commit()

            return True
        except psycopg2.errors.UniqueViolation:
            self.conn.rollback()
            return False
        except psycopg2.DatabaseError as e:
            self.conn.rollback()
            raise e
