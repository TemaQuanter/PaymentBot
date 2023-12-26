# This file contains the code for user notification via telegram bot.

from telegram.ext import Application

from utils.constants import SERVICE_ADDRESS

from ..database.database import PostgresDB

import time

from datetime import datetime, timedelta

import asyncio
import requests

from asyncio import AbstractEventLoop

# How frequently to perform the checks.
INTERVAL_DELAY_SECS = 24 * 60 * 60

# Inform the users that their subscription will expire soon, when it expires
# in less than this time.
BEFORE_TIME = timedelta(days=3)


def notify(application: Application, loop: AbstractEventLoop) -> None:
    """This function sends notifications to the users that did not pay for their subscription."""

    # Run endless loop to check what users have their subscriptions next to expiration time
    # and send notifications to them. If they do not pay for their subscription, disconnect them
    # from the service.
    while True:
        # Get a connection to the database.
        db = PostgresDB()

        # Remove old transactions.
        db.remove_old_validated_transactions()

        # Get all users with expired subscriptions from the database.
        expired_users = db.get_expired_not_informed_users()

        # Switch off the bot access for each user whose subscription got expired.
        for expired_user in expired_users:
            # Change the status of a user to expired.
            requests.put(
                f"{SERVICE_ADDRESS}/expired/{expired_user.telegram_id}")

        # Inform all users whose subscription got expired.
        for expired_user in expired_users:
            # Schedule the coroutine to be run on the event loop
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=expired_user.telegram_id, text="Your subscription got expired, to renew it, please use <code>/start</code> command.\n\n"
                    "Your access to the bot is currently restricted and it will not manage your assets from now on until you renew the subscription.", parse_mode="HTML"),
                loop
            )

        # Mark all users as informed that their subscription got expired.
        db.mark_as_informed(expired_users)

        # Get users, whose subscriptions are close to expiration.
        next_to_expire_users = db.get_next_to_expire_users(BEFORE_TIME)

        # Inform all users whose subscription will expire soon.
        for next_to_expire_user in next_to_expire_users:
            # Format the datetime object into the desired string format 'DD/MM/YYYY'
            formatted_date = next_to_expire_user.subscription_expiration_timestamp.strftime(
                '%d/%m/%Y')

            # Schedule the coroutine to be run on the event loop
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=next_to_expire_user.telegram_id, text=f"Your subscription will expire on <b>{formatted_date} UTC</b>, to renew it, please use <code>/start</code> command.\n\n", parse_mode="HTML"),
                loop
            )

        # Disconnect from the database.
        db.close_connection()

        # Make a pause between checks.
        time.sleep(INTERVAL_DELAY_SECS)
