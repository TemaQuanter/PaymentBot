# This file contains the logic of a telegram bot, that
# accepts USDT payments in tron blockchain.

from typing import List, Tuple, cast

from string import punctuation

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InvalidCallbackData,
    PicklePersistence,
    ConversationHandler
)

from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

# Ignore some warnings related to conversation continuation
# from various users in various chats.
filterwarnings(action="ignore", message=r".*CallbackQueryHandler",
               category=PTBUserWarning)

# Constants to navigate a conversation.
START_ROUTES, BILLING_PLAN, END_ROUTES = range(3)

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
                CallbackQueryHandler(choose_billing_plan, pattern="^")
            ]
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


def build_keyboard(option_list: list) -> InlineKeyboardMarkup:
    """Helper function to build an inline keyboard."""
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(option_list[i], callback_data=(
            option_list[i])) for i in range(0, len(option_list))]
    )


async def agree(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """The function that proceeds only if the user agrees to the conditions."""

    query = update.callback_query

    await query.answer()

    await query.edit_message_reply_markup()

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Cool! Let's go!",
                                   parse_mode="HTML")

    # Send a message suggesting various billing plans.
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Choose one of the following billing plans:",
                                   parse_mode="HTML", reply_markup=build_keyboard(BILLING_PLANS))

    # Proceed to choosing a billing plan.
    return BILLING_PLAN


async def decline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """The function that proceeds only if the user declines the conditions and
    a policy."""

    query = update.callback_query

    await query.answer()

    await query.edit_message_reply_markup()

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Perhaps, see you next time:)\n"
                                   "If you change your mind, use <code>/start</code> command",
                                   parse_mode="HTML")

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

    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Congrats! Now you bought a subscription for a {period} for {amount} dollars!",
                                   parse_mode="HTML")

    return ConversationHandler.END
