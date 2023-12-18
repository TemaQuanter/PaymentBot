# This file contains utils for working with databases.

import psycopg2

from .models.user import User


class PostgresDB:

    def __init__(self, DB_NAME: str, DB_USER: str, DB_PASSWORD: str, DB_HOST: str, DB_PORT: str) -> None:
        # Get a database connection.
        self.conn = psycopg2.connect(database=DB_NAME,
                                     user=DB_USER,
                                     password=DB_PASSWORD,
                                     host=DB_HOST,
                                     port=DB_PORT)

        # Create a cursor.
        self.cursor = self.conn.cursor()

    def insert_user(self, user: User):
        # Insert a new user into the database.
        self.cursor.execute(
            f"INSERT INTO users (telegram_id) VALUES (${user.telegram_id})")
        self.conn.commit()
