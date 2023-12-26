# This file contains the logic of a telegram bot, that
# accepts USDT payments in tron blockchain.

import os

from tronapi import Tron

import psycopg2

from string import punctuation, whitespace, ascii_letters
from datetime import datetime, timedelta, timezone

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    PicklePersistence,
    filters
)

from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

from .helper_functions import build_keyboard, send_message
from ..blockchain.helper_functions import get_unique_amount_usdt, verify_payment_validity
from ..blockchain.transaction import extract_transaction_details

from ..database.models.user import User
from ..database.database import PostgresDB
from ..database.models.invoice import Invoice

from ..constants import PAYMENT_TIME_LIMIT_DELTA, POLICY_PATH, SERVICE_ADDRESS, SERVICE_URL, SUPPORT_CREDENTIALS

import requests

# Ignore some warnings related to conversation continuation
# from various users in various chats.
filterwarnings(action="ignore", message=r".*CallbackQueryHandler",
               category=PTBUserWarning)

# Constants to navigate a conversation.
START_ROUTES, BILLING_PLAN, VERIFY_PAYMENT, END_ROUTES = range(4)


def get_bot(token: str) -> Application:
    """Run the bot."""

    # Get a conversation persistence directory.
    persistence = PicklePersistence(filepath="data/application_persistence")

    # Create the application
    application = Application.builder().token(
        token).persistence(persistence).build()

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
        name="payment",
        persistent=True
    )

    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    return application


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""

    # Get the current user of the bot.
    user = update.effective_user

    keyboard_options = ["Agree", "Decline"]

    # Load policy from a file.
    with open(POLICY_PATH, "r") as fl:
        policy_text = fl.read()

    await update.message.reply_html(
        f"Hi {user.first_name}! Before we continue, please, read our policy\n"
        "Here is our policy👇👇👇\n\n"
        f"{policy_text}\n\n"
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

    # Get database connection.
    db = PostgresDB()

    # Add the user to the database, if they agree.
    try:
        db.insert_user(User(update.effective_user.id))
    except psycopg2.errors.UniqueViolation:
        # If the user already exists, pass.
        pass

    # Create billing plans for a user.
    billing_plans = [
        f"${int(float(sub_plan.amount_due))} / {sub_plan.days_valid} days" for sub_plan in db.get_subscription_plans()]

    # Close database connection.
    db.close_connection()

    # Send a message suggesting various billing plans.
    await send_message("Choose one of the following billing plans:", update, context, reply_markup=build_keyboard(billing_plans))

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
    amount = amount.strip(punctuation + whitespace)

    # Ge a unique ending for the amount to identify blockchain transaction.
    amount = get_unique_amount_usdt(amount)

    # Clear period from symbols.
    period = period.strip(punctuation + whitespace + ascii_letters)

    # Establish database connection.
    db = PostgresDB()

    # Flag that indicates whether or not it is necessary to generate a new invoice.
    generate_new_invoice = False

    # Try to get current invoice for the user.
    try:
        invoice = db.get_invoice(update.effective_user.id)

        # Check if the payment expiration timestamp expired.
        if invoice.payment_expiration_timestamp.replace(tzinfo=None) < datetime.utcnow() or int(float(invoice.amount_due)) != int(float(amount)):
            # The timestamp expired.
            generate_new_invoice = True

            # Remove the invoice.
            db.remove_invoice(invoice.telegram_user_id)
    except psycopg2.errors.NoDataFound:
        # No invoice assigned to the user.
        generate_new_invoice = True

    # Check if it is necessary to generate a new invoice.
    if generate_new_invoice:
        # Create a new invoice.
        invoice = Invoice(update.effective_user.id, amount,
                          period, datetime.utcnow() + PAYMENT_TIME_LIMIT_DELTA)

        # Insert the invoice to the database.
        db.insert_invoice(invoice)

    # Get payment address.
    payment_address = os.getenv("TRON_WALLET_ADDRESS")

    await send_message("You have <b>1 hour</b> max to make a payment.\n\n" +
                       f"Send <b>exactly</b> <code>{invoice.amount_due}</code> USDT to <code>{payment_address}</code> in Tron (TRX)\n\n"
                       f"Afterwards, send me transaction hash/id, so, that I could verify the payment\n\n"
                       f"Send it without any extra symbols, letters or digits, just transaction hash/id", update, context)

    # Close database connection.
    db.close_connection()

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

    # Check if it was possible to extract the data from the transaction.
    if transaction_details == None:
        # It is most likely that that transaction is not a token transfer.
        await send_message("The transaction does not seem to me to be a token transfer...\n"
                           "Please, make sure that you submitted the right transaction hash/id", update, context)

        return VERIFY_PAYMENT

    # Get a verdict on the provided transaction.
    verification_verdict = verify_payment_validity(
        transaction_details, update.effective_user.id)

    # Verify the validity of payment.
    if verification_verdict[0]:
        # Establish database connection.
        db = PostgresDB()

        # Get user invoice.
        invoice = db.get_invoice(update.effective_user.id)

        # Prolong user subscription.
        db.prolong_subscription(
            User(invoice.telegram_user_id), timedelta(days=invoice.days_valid))

        # Get new expiration timestamp.
        user = db.get_user(invoice.telegram_user_id)

        # Remove invoice.
        db.remove_invoice(invoice.telegram_user_id)

        # Close database connection.
        db.close_connection()

        # Calculate access till date.

        # Format the datetime object into the desired string format 'DD/MM/YYYY'
        formatted_date = user.subscription_expiration_timestamp.strftime(
            '%d/%m/%Y')

        # Prolong the user subscription.
        requests.put(f"{SERVICE_ADDRESS}/approve/{update.effective_user.id}")

        # Inform the user that the payment is successful.
        await send_message("Payment is successful! Welcome aboard 🥳\n"
                           "Here is the link to the bot, you can start using it right now!", update, context)

        # Send them the link to the trading bot.
        await send_message(SERVICE_URL, update, context)

        # Inform them about the expiration timestamp.
        await send_message(f"Access till <b>{formatted_date} UTC</b>", update, context)

        # Send a final message.
        await send_message("To renew subscription later, use <code>/start</code>", update, context)
    else:
        # Inform the user that the transaction did not pass verification.
        await send_message("The transaction did not pass verification.\n\n"
                           "Please, try submitting transaction hash/id once again\n\n"
                           "If you are sure, that you did submitted the right transaction hash "
                           f"you can contact support here\n\n{SUPPORT_CREDENTIALS}", update, context)

        await send_message(f"Error message: {verification_verdict[1]}", update, context)

        return VERIFY_PAYMENT

    return ConversationHandler.END
