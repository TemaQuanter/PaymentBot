# This file contains the code for user notification via telegram bot.

from telegram.ext import Application

from utils.constants import SERVICE_ADDRESS

from ..database.database import PostgresDB
from ..database.models.user import User

import time

import asyncio
import requests

from asyncio import AbstractEventLoop

INTERVAL_DELAY_SECS = 5


def notify(application: Application, loop: AbstractEventLoop) -> None:
    """This function sends notifications to the users that did not pay for their subscription."""

    # Run endless loop to check what users have their subscriptions next to expiration time
    # and send notifications to them. If they do not pay for their subscription, disconnect them
    # from the service.
    while True:
        # Get a connection to the database.
        db = PostgresDB()

        # Get all users with expired subscriptions from the database.
        expired_users = db.get_expired_users()

        # Switch off the bot access for each user whose subscription got expired.
        for expired_user in expired_users:
            # Change the status of a user to expired.
            # requests.put(
            #     f"{SERVICE_ADDRESS}/expired/{expired_user.telegram_id}")
            pass

        # Inform all users whose subscription got expired.
        for expired_user in expired_users:
            # Schedule the coroutine to be run on the event loop
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=expired_user.telegram_id, text="Your subscription got expired, to renew it, please use <code>/start</code> command.\n"
                    "Your access to the bot is currently restricted and it will not manage your assets from now on, until you renew the subscription.", parse_mode="HTML"),
                loop
            )

        # Disconnect from the database.
        db.close_connection()

        # Make a pause between checks.
        time.sleep(INTERVAL_DELAY_SECS)
