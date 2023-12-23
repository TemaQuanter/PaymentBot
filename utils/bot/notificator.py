# This file contains the code for user notification via telegram bot.

from telegram.ext import Application

from ..database.database import PostgresDB
from ..database.models.user import User

import time

import asyncio
from asyncio import AbstractEventLoop


def notify(application: Application, loop: AbstractEventLoop):
    """This function sends notifications to the users that did not pay for their subscription."""

    # Run endless loop to check what users have their subscriptions next to expiration time
    # and send notifications to them. If they do not pay for their subscription, disconnect them
    # from the service.
    while True:
        # Schedule the coroutine to be run on the event loop
        asyncio.run_coroutine_threadsafe(
            application.bot.send_message(chat_id=1451750898, text="Hello"),
            loop
        )
        time.sleep(5)
