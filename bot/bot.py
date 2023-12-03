import logging
import asyncio
from datetime import datetime

import telegram
from telegram import (
    Update,
    User,
    BotCommand
)

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    AIORateLimiter,
    MessageHandler,
    filters
)
from telegram.constants import ParseMode

import config
import database
from agent import init_data_agent

class MyFormatter(logging.Formatter):
    def format(self, record):
        formatted = super().format(record)
        formatted = formatted.encode("utf-8").decode("unicode_escape")
        return formatted
    
formatter = MyFormatter('%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s [%(asctime)s] %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.WARNING)

db = database.Database()

user_semaphores = {}
user_tasks = {}

prompt =  """You are Alfa-bank assistant bot. Any question should be related to Alfa-bank. You have to find the answer from the vector index storage, provide answer as it is stated in answers for questions in the database. Keep the answer format. If there links in answer, provide the links. Do not generate explanations that are not in the database without a query."""


model="gpt-3.5-turbo-16k"
agent = init_data_agent(prompt, model)


HELP_MESSAGE = """Commands:
/help – Show help
"""

HELP_GROUP_CHAT_MESSAGE = """
Will create some usefull help message later
"""

def split_text_into_chunks(text, chunk_size):
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]


async def register_user_if_not_exists(update: Update, context: CallbackContext, user: User):
    if not db.check_if_user_exists(user.id):
        db.add_new_user(
            user.id,
            update.message.chat_id,
            username=user.username,
            first_name=user.first_name,
            last_name= user.last_name
        )
        db.start_new_dialog(user.id)

    if db.get_user_attribute(user.id, "current_dialog_id") is None:
        db.start_new_dialog(user.id)

    if user.id not in user_semaphores:
        user_semaphores[user.id] = asyncio.Semaphore(1)
 


async def start_handle(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)
    user_id = update.message.from_user.id

    db.set_user_attribute(user_id, "last_interaction", datetime.now())
    db.start_new_dialog(user_id)

    reply_text =  "Привет! Отвечу н любые вопросы по поводу FAQ от Альфа-Банка\n\n"
    reply_text += HELP_MESSAGE

    await update.message.reply_text(reply_text, parse_mode=ParseMode.HTML)

async def help_handle(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)
    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())
    await update.message.reply_text(HELP_MESSAGE, parse_mode=ParseMode.HTML)

async def message_handle(update: Update, context: CallbackContext):
    _message = update.message.text

    await register_user_if_not_exists(update, context, update.message.from_user)

    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())
    try:
        placeholder_message = await update.message.reply_text("... typing")
        await update.message.chat.send_action(action="typing")

        answer = str(agent.chat(_message))

        try:
            await context.bot.edit_message_text(answer, chat_id=placeholder_message.chat_id, 
                                                message_id=placeholder_message.message_id, 
                                                parse_mode=ParseMode.HTML)
        except telegram.error.BadRequest as e:
            print(e)

            await update.message.reply_text(answer, parse_mode=ParseMode.HTML)

    except Exception as e:
            error_text = f"Something went wrong during completion. Reason: {e}"
            logger.error(error_text)
            await update.message.reply_text(error_text)
            return
    
async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("/help", "Show help message"),
    ])

def run_bot() -> None:
    application = (
        ApplicationBuilder()
        .token(config.telegram_token)
        .concurrent_updates(True)
        .rate_limiter(AIORateLimiter(max_retries=5))
        .http_version("1.1")
        .get_updates_http_version("1.1")
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start_handle))
    application.add_handler(CommandHandler("help", help_handle))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handle))

    # start the bot
    application.run_polling()


if __name__ == "__main__":
    run_bot()