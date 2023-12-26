# This file contains utils for working with databases.

import psycopg2
import os

from .models.subscription_plans import SubscriptionPlan
from .models.invoice import Invoice
from .models.user import User
from .models.validated_transactions import Transaction

from datetime import datetime, timedelta, timezone
from typing import List

from ..constants import TRANSACTION_EXPIRATION_TIMESTAMP


class PostgresDB:

    def __init__(self) -> None:
        # Get a database connection.
        self.__conn = psycopg2.connect(database=os.getenv("POSTGRES_DB"),
                                       user=os.getenv("POSTGRES_USER"),
                                       password=os.getenv("POSTGRES_PASSWORD"),
                                       host=os.getenv("POSTGRES_HOST"),
                                       port=os.getenv("POSTGRES_PORT"))

        # Create a __cursor.
        self.__cursor = self.__conn.cursor()

    def get_expired_not_informed_users(self) -> List[User]:
        """This function returns all users from the database, whose subscription
        has expired and they have not been informed about it."""

        # Execute the command.
        self.__cursor.execute(
            "SELECT * FROM users WHERE subscription_expiration_timestamp < (CURRENT_TIMESTAMP AT TIME ZONE 'UTC') AND informed_about_expiration = FALSE;")

        # Get data.
        rows = self.__cursor.fetchall()

        # List of expired users.
        expired_users = list()

        # Traverse each row of the database reply and
        # collect all users with expired subscription.
        for row in rows:
            user = User(row[0])
            user.subscription_expiration_timestamp = row[1]

            expired_users.append(user)

        # Return users with expired subscriptions.
        return expired_users

    def mark_as_informed(self, users: List[User]):
        """This function marks users as informed that their subscription expired."""

        # Traverse each user and mark them as informed about expired subscription.
        for user in users:
            try:
                self.__cursor.execute(
                    "UPDATE users SET informed_about_expiration = TRUE WHERE telegram_id = %s;", (user.telegram_id,))
                self.__conn.commit()
            except psycopg2.DatabaseError as e:
                self.__conn.rollback()
                raise e

    def get_next_to_expire_users(self, before_time: timedelta) -> List[User]:
        """This function returns all users from the database, whose subscription
        will expire is less than "before_time"."""

        # Execute the command.
        self.__cursor.execute(
            "SELECT * FROM users WHERE subscription_expiration_timestamp < (CURRENT_TIMESTAMP AT TIME ZONE 'UTC') + INTERVAL '%s days' AND subscription_expiration_timestamp > (CURRENT_TIMESTAMP AT TIME ZONE 'UTC');", (before_time.days,))

        # Get data.
        rows = self.__cursor.fetchall()

        # List of expired users.
        next_to_expire_users = list()

        # Traverse each row of the database reply and
        # collect all users with expired subscription.
        for row in rows:
            user = User(row[0])
            user.subscription_expiration_timestamp = row[1]

            next_to_expire_users.append(user)

        # Return users with expired subscriptions.
        return next_to_expire_users

    def get_users(self) -> List[User]:
        """This function returns all users from the database."""

        # Execute the command.
        self.__cursor.execute(
            "SELECT * FROM users;")

        # Get data.
        rows = self.__cursor.fetchall()

        # List of expired users.
        users = list()

        # Traverse each row of the database reply and
        # collect all users.
        for row in rows:
            user = User(row[0])
            user.subscription_expiration_timestamp = row[1]

            users.append(user)

        # Return users.
        return users

    def get_user(self, telegram_id: int) -> User:
        """Return a user from the database."""

        # Execute the command.
        self.__cursor.execute(
            "SELECT * FROM users WHERE telegram_id = %s;", (telegram_id,))

        # Get data.
        rows = self.__cursor.fetchall()

        # Check if there is data found.
        if len(rows) == 0:
            # Nothing was found.
            raise psycopg2.errors.NoDataFound

        # Create a user instance with the data extracted from the database.
        user = User(telegram_id)
        user.subscription_expiration_timestamp = rows[0][1]

        return user

    def insert_user(self, user: User):
        """Insert a new user into the database."""

        try:
            self.__cursor.execute(
                "INSERT INTO users (telegram_id, informed_about_expiration) VALUES (%s, FALSE);", (user.telegram_id,))
            self.__conn.commit()
        except psycopg2.DatabaseError as e:
            self.__conn.rollback()
            raise e

    def insert_invoice(self, invoice: Invoice) -> None:
        """This function assigns an invoice to the user."""

        try:
            self.__cursor.execute(
                "INSERT INTO invoice VALUES (%s, %s, %s, %s);", (invoice.telegram_user_id, invoice.amount_due, invoice.days_valid, invoice.payment_expiration_timestamp))
            self.__conn.commit()
        except psycopg2.DatabaseError as e:
            self.__conn.rollback()
            raise e

    def get_invoice(self, telegram_user_id) -> Invoice:
        """This function retrieves current invoice for the user
        from the database."""

        # Execute the command.
        self.__cursor.execute(
            "SELECT * FROM invoice WHERE telegram_user_id = %s;", (telegram_user_id,))

        # Get data.
        rows = self.__cursor.fetchall()

        # Check if there is data found.
        if len(rows) == 0:
            # Nothing was found.
            raise psycopg2.errors.NoDataFound

        # Create invoice form raw data.
        invoice = Invoice(rows[0][0], rows[0][1], rows[0][2], rows[0][3])

        return invoice

    def remove_invoice(self, telegram_user_id: int) -> None:
        """This function removes invoice from the database."""

        try:
            self.__cursor.execute(
                "DELETE FROM invoice WHERE telegram_user_id = %s;", (telegram_user_id,))
            self.__conn.commit()
        except psycopg2.DatabaseError as e:
            self.__conn.rollback()
            raise e

    def get_subscription_plans(self) -> List[SubscriptionPlan]:
        """This function returns subscription plans."""

        # Execute the command.
        self.__cursor.execute(
            "SELECT * FROM subscription_plans;")

        # Get data.
        rows = self.__cursor.fetchall()

        # List of expired users.
        subscription_plans = list()

        # Traverse each row of the database reply and
        # collect all users.
        for row in rows:
            subscription_plan = SubscriptionPlan(int(row[1]), row[2])
            subscription_plans.append(subscription_plan)

        # Return users.
        return subscription_plans

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

        # Reset "user is informed about expired subscription" to false.
        user.informed_about_expiration = False

        # Save a new subscription expiration time to the database.
        try:
            self.__cursor.execute(
                "UPDATE users SET subscription_expiration_timestamp = %s, informed_about_expiration = %s WHERE telegram_id = %s;", (user.subscription_expiration_timestamp, user.informed_about_expiration, user.telegram_id))
            self.__conn.commit()
        except psycopg2.DatabaseError as e:
            self.__conn.rollback()
            raise e

    def insert_validated_transaction(self, transaction_id: str, transaction_timestamp: datetime) -> bool:
        """This function inserts a validated transaction into the database.
        If the transaction already exists, the function returns False, true - otherwise."""

        try:
            self.__cursor.execute("INSERT INTO validated_transactions (transaction_id, transaction_timestamp) VALUES (%s, %s)", (
                transaction_id, transaction_timestamp))
            self.__conn.commit()

            return True
        except psycopg2.errors.UniqueViolation:
            self.__conn.rollback()
            return False
        except psycopg2.DatabaseError as e:
            self.__conn.rollback()
            raise e

    def remove_old_validated_transactions(self) -> None:
        """This function removes transactions that are old enough not to be used again."""

        try:
            self.__cursor.execute(
                "DELETE FROM validated_transactions WHERE transaction_timestamp < (CURRENT_TIMESTAMP AT TIME ZONE 'UTC') - INTERVAL '%s seconds'", (TRANSACTION_EXPIRATION_TIMESTAMP.seconds,))
            self.__conn.commit()
        except psycopg2.DatabaseError as e:
            self.__conn.rollback()
            raise e

    def close_connection(self):
        """This function closes the connection to the database."""

        self.__cursor.close()
        self.__conn.close()
