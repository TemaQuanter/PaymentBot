# This file contains the logic of a telegram bot, that
# accepts USDT payments in tron blockchain.

from typing import List, Tuple, cast

import os

from tronapi import Tron

from random import randint

from string import punctuation

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    InvalidCallbackData,
    PicklePersistence,
    ConversationHandler,
    filters
)

from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

from .helper_functions import build_keyboard, send_message
from ..blockchain.helper_functions import get_unique_amount_usdt
from ..blockchain.transaction import extract_transaction_details

# Ignore some warnings related to conversation continuation
# from various users in various chats.
filterwarnings(action="ignore", message=r".*CallbackQueryHandler",
               category=PTBUserWarning)

# Constants to navigate a conversation.
START_ROUTES, BILLING_PLAN, VERIFY_PAYMENT, END_ROUTES = range(4)

# Billing plans.
BILLING_PLANS = ["$490/month", "$1300/quarter"]


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

    # Get payment address.
    payment_address = os.getenv("TRON_WALLET_ADDRESS")

    await send_message(f"You have <b>1 hour</b> max to make a payment.\n\n"
                       f"Send <b>exactly</b> <code>{amount}</code> USDT to <code>{payment_address}</code> in Tron (TRX)\n\n"
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

    print("Sender address:", transaction_details["sender_address"])
    print("Contract address:", transaction_details["contract_address"])
    print("Receiver address:", transaction_details["receiver_address"])
    print("Value:", transaction_details["value"])
    print("Timestamp UTC:", transaction_details["timestamp_utc"])

    return ConversationHandler.END
