import os
from decouple import config
from utils import *
from constants import *
from detect_intents import detect_intent_texts

from telegram import Update, ForceReply
from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    CallbackContext,
)

# Env Variables Initialization
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config("SESSION_KEY_PATH")

# Mock MongoDB
hashmap = {}

below_confidence_attempts = 0

def main() -> None:
    updater = Updater(config("BOT_TOKEN"))
    dispatcher = updater.dispatcher
    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, initialize_new_case)
    )
    updater.start_polling()
    updater.idle()

def initialize_new_case(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat.id
    message_id = update.message.message_id
    date = update.message.date

    current_chat = {
        "chat_id": chat_id,
        "message_id": message_id,
        "created_at": date,
    }

    if chat_id not in hashmap:
        current_chat["session_id"] = generate_session_id()
    else:
        last_message_date = hashmap[chat_id]["created_at"]
        if get_mins_from(last_message_date) >= SESSION_EXPIRE_MINS:
            current_chat["session_id"] = generate_session_id()
        else:
            current_chat["session_id"] = hashmap[chat_id]["session_id"]

    hashmap[chat_id] = current_chat

    # print("session", current_chat["session_id"])

    response = detect_intent_texts(
        config("PROJECT_ID"), current_chat["session_id"], update.message.text, "en-US"
    )

    # print(response)

    global below_confidence_attempts
    if response["confidence_level"] < MINIMUM_CONFIDENCE_LEVEL:
        below_confidence_attempts += 1
    else:
        below_confidence_attempts -= 1

    update.message.reply_text(response["message"])


if __name__ == "__main__":
    main()
