# This file contains helper function for the bot.

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
)


def build_keyboard(option_list: list) -> InlineKeyboardMarkup:
    """Helper function to build an inline keyboard."""
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(option_list[i], callback_data=(
            option_list[i])) for i in range(0, len(option_list))]
    )


async def send_message(text: str, update: Update, context: ContextTypes.DEFAULT_TYPE, reply_markup: InlineKeyboardMarkup = None):
    """Helper function to send HTML formatted messages."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text,
                                   parse_mode="HTML", reply_markup=reply_markup)
