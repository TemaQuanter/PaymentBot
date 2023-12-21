# This file contains the logic of a telegram bot, that
# accepts USDT payments in tron blockchain.

import os

from tronapi import Tron

import psycopg2

from string import punctuation
from datetime import datetime, timedelta, timezone

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters
)

from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

from .helper_functions import build_keyboard, send_message
from ..blockchain.helper_functions import get_unique_amount_usdt, verify_payment_validity
from ..blockchain.transaction import extract_transaction_details

from ..database.models.user import User
from ..database.database import PostgresDB

# Ignore some warnings related to conversation continuation
# from various users in various chats.
filterwarnings(action="ignore", message=r".*CallbackQueryHandler",
               category=PTBUserWarning)

# Constants to navigate a conversation.
START_ROUTES, BILLING_PLAN, VERIFY_PAYMENT, END_ROUTES = range(4)

# Billing plans.
BILLING_PLANS = ["$490/month", "$1300/quarter"]

# Time limit for payment.
PAYMENT_TIME_LIMIT_DELTA = timedelta(hours=1)


def bot_poll(token: str) -> None:
    """Run the bot."""
    # Create the application
    application = Application.builder().token(token).build()

    # Setup conversation handler with the states FIRST and SECOND
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(agree, pattern="^Agree$"),
                CallbackQueryHandler(decline, pattern="^Decline$"),
            ],
            BILLING_PLAN: [
                CallbackQueryHandler(choose_billing_plan)
            ],
            VERIFY_PAYMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND,
                               verify_payment)
            ],
            # END_ROUTES: [
            #     CallbackQueryHandler(
            #         start_over, pattern="^" + str(ONE) + "$"),
            #     CallbackQueryHandler(end, pattern="^" + str(TWO) + "$"),
            # ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""

    # Get the current user of the bot.
    user = update.effective_user

    keyboard_options = ["Agree", "Decline"]

    await update.message.reply_html(
        f"Hi {user.first_name}!\n"
        "Here is our policy\n"
        "bla-bla-bla\n"
        "By agreeing with the policy you confirm,\n"
        "that you accept the conditions written above",
        reply_markup=build_keyboard(keyboard_options)
    )

    return START_ROUTES


async def agree(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """The function that proceeds only if the user agrees to the conditions."""

    query = update.callback_query

    await query.answer()

    await query.edit_message_reply_markup()

    await send_message("Cool! Let's go!", update, context)

    # Send a message suggesting various billing plans.
    await send_message("Choose one of the following billing plans:", update, context, reply_markup=build_keyboard(BILLING_PLANS))

    # Proceed to choosing a billing plan.
    return BILLING_PLAN


async def decline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """The function that proceeds only if the user declines the conditions and
    a policy."""

    query = update.callback_query

    await query.answer()

    await query.edit_message_reply_markup()

    await send_message("Perhaps, see you next time:)\n"
                       "If you change your mind, use <code>/start</code> command", update, context)

    # End a conversation with a user.
    return ConversationHandler.END


async def choose_billing_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """This function gets a billing plan from the user."""

    query = update.callback_query

    await query.answer()

    await query.edit_message_reply_markup()

    # Get amount and the period separately.
    amount, period = query.data.split('/')

    # Clear amount from any symbols.
    amount = amount.strip(punctuation)

    # Ge a unique ending for the amount to identify blockchain transaction.
    amount = get_unique_amount_usdt(amount)

    # Insert a new user to the database.
    user = User(update.effective_user.id)
    db = PostgresDB()

    try:
        # Try to insert a user into the database.
        db.insert_user(user)
    except psycopg2.errors.UniqueViolation:
        # The user already exists, get the user.
        user = db.get_user(update.effective_user.id)

    # Flag that indicates whether or not it is necessary to generate a new invoice.
    generate_new_invoice = False

    # Check if there are both payment expiration timestamp and amount due set.
    if user.amount_due != None and user.payment_expiration_timestamp != None:
        # They are set.
        # Check if the payment expiration timestamp expired.
        if user.payment_expiration_timestamp.replace(tzinfo=None) < datetime.utcnow() or int(float(user.amount_due)) != int(float(amount)):
            # The timestamp expired.
            generate_new_invoice = True
    else:
        generate_new_invoice = True

    # Check if it is necessary to generate a new invoice.
    if generate_new_invoice:
        # Set amount due and payment expiration timestamp.
        user.amount_due = amount
        user.payment_expiration_timestamp = datetime.utcnow() + PAYMENT_TIME_LIMIT_DELTA

        db.set_amount_due_and_payment_expiration_timestamp(user)

    # Get payment address.
    payment_address = os.getenv("TRON_WALLET_ADDRESS")

    # Get payment remaining time.
    payment_remaining_time = (datetime.utcnow()
                              - user.payment_expiration_timestamp.replace(tzinfo=None)).seconds

    payment_remaining_hours = payment_remaining_time // 3600
    payment_remaining_minutes = (payment_remaining_time % 3600) // 60
    payment_remaining_time_seconds = payment_remaining_time % 60

    await send_message("You have <b>1 hour</b> max to make a payment.\n\n".format(payment_remaining_hours, payment_remaining_minutes, payment_remaining_time_seconds) +
                       f"Send <b>exactly</b> <code>{user.amount_due}</code> USDT to <code>{payment_address}</code> in Tron (TRX)\n\n"
                       f"Afterwards, send me transaction hash/id, so, that I could verify the payment\n\n"
                       f"Send it without any extra symbols, letters or digits, just transaction hash/id", update, context)

    # Verify payment
    return VERIFY_PAYMENT


async def verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """This function verifies the payment."""

    # Get the transaction hash/id.
    transaction_hash = update.message.text

    # Inform a user that the transaction is in the process of verification.
    await send_message("Got it, verifying your payment...\n"
                       "It may take several minutes", update, context)

    # Get a connection to a Tron node.
    tron = Tron()

    # Try to get the transaction from tron blockchain.
    try:
        transaction_raw_data = tron.trx.get_transaction(transaction_hash)

    except ValueError:
        # Inform a user that the transaction is not found.
        await send_message("The transaction is not found, please, make sure you sent me a valid transaction hash/id\n\n"
                           "Please, send it again", update, context)

        return VERIFY_PAYMENT

    # Get the transaction details.
    transaction_details = extract_transaction_details(
        transaction_raw_data, tron)

    # Verify the validity of payment.
    if verify_payment_validity(transaction_details, update.effective_user.id):
        # Prolong the user subscription.

        # Inform the user that the payment is successful.
        await send_message("Payment is successful!\n"
                           "Here is the link to the bot, you can start using it right now!", update, context)

        # Send them the link to the trading bot.
        await send_message("https://t.me/open_ai_trader_bot", update, context)

        # Send a final message.
        await send_message("To renew subscription later, use <code>/start</code>", update, context)
    else:
        # Inform the user that the transaction did not pass verification.
        await send_message("The transaction did not pass verification.\n\n"
                           "Please, try submitting transaction hash/id once again\n\n"
                           "If you are sure, that you did submitted the right transaction hash"
                           "you can contact support here\n\n@support", update, context)

        return VERIFY_PAYMENT

    return ConversationHandler.END
