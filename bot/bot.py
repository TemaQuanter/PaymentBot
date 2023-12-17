# This file contains the logic of a telegram bot, that
# accepts USDT payments in tron blockchain.

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


class Bot:
    def __init__(self, api_token) -> None:
        self.token = api_token

    def poll(self):
        # Initialize the bot.
        app = Application.builder().token(self.token).build()

        # Register the /start command handler
        app.add_handler(CommandHandler("start", self.start))

        # Start the bot
        app.run_polling()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        await update.message.reply_html(
            f"Hi {user.first_name}!",
        )
