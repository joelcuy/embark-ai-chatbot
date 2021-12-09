import os
from decouple import config
from utils import *
from constants import *
from detect_intents import detect_intent_texts

from telegram.replymarkup import ReplyMarkup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply
from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
)

# Env Variables Initialization
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config("SESSION_KEY_PATH")

# Mock MongoDB
hashmap = {}

below_confidence_attempts = 0
fallbackIntentCount = 0


def main() -> None:
    updater = Updater(config("BOT_TOKEN"))
    dispatcher = updater.dispatcher

    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, initialize_new_case)
    )
    # updater.dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()


def initialize_new_case(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat.id
    message_id = update.message.message_id
    date = update.message.date

    ##Dictionary to store Update.message attributes
    current_chat = {
        "chat_id": chat_id,
        "message_id": message_id,
        "created_at": date,
    }

    # the hashmap (aka object) is to store the people’s chat id and mimic like a session once
    # but once the local script restarts, it will be blank again, because it is only stored in runtime
    if chat_id not in hashmap:
        current_chat["session_id"] = generate_session_id()
    else:
        last_message_date = hashmap[chat_id]["created_at"]
        if get_mins_from(last_message_date) >= SESSION_EXPIRE_MINS:
            current_chat["session_id"] = generate_session_id()
        else:
            current_chat["session_id"] = hashmap[chat_id]["session_id"]

    hashmap[chat_id] = current_chat

    # For testing
    print("session", current_chat["session_id"])

    # Call function from detect_intets.py
    response = detect_intent_texts(
        config("PROJECT_ID"),
        current_chat["session_id"],
        update.message.text,
        config("DIALOGFLOW_LANGUAGE_CODE"),
    )

    # For testing
    print(response)

    global below_confidence_attempts
    if response["confidence_level"] < MINIMUM_CONFIDENCE_LEVEL:
        below_confidence_attempts += 1
    else:
        below_confidence_attempts -= 1

    # Default no inline keyboards if doesnt match one of the else if cases
    reply_markup = None
    global fallbackIntentCount
    if response["intent"] == "default_welcome_intent":
        fallbackIntentCount = 0
        reply_markup = welcome_keyboard()
        update.message.reply_text(response["message"], reply_markup=reply_markup)

    elif response["intent"] == "employee_benefits":
        fallbackIntentCount = 0
        update.message.reply_text(response["message"], reply_markup=reply_markup)

    elif response["intent"] == "hr_application_system":
        fallbackIntentCount = 0
        update.message.reply_text(response["message"], reply_markup=reply_markup)

    elif response["intent"] == "leave":
        fallbackIntentCount = 0
        reply_markup = leave_keyboard()
        update.message.reply_text(response["message"], reply_markup=reply_markup)

    elif response["intent"] == "medical":
        fallbackIntentCount = 0
        update.message.reply_text(response["message"], reply_markup=reply_markup)

    elif response["intent"] == "sunway_celcom_pkg":
        fallbackIntentCount = 0
        update.message.reply_text(response["message"], reply_markup=reply_markup)

    elif response["intent"] == "default_fallback_intent":
        # If unable to process user request for 2 times, forward message
        if fallbackIntentCount >= 2:
            # send reply to the user
            context.bot.send_message(
                chat_id=update.message.chat_id,
                reply_to_message_id=update.message.message_id,
                text="I'm really sorry for not being able to process your request. I'll forward your request to a live HR staff, and they'll get back to you in a bit.",
            )

            # Forward the chat to HR channel
            context.bot.forward_message(
                chat_id="@demoHRchannel",
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id,
            )

        else:
            update.message.reply_text(response["message"], reply_markup=reply_markup)

        fallbackIntentCount += 1


# def button(update: Update, context: CallbackContext) -> None:
#     """Parses the CallbackQuery and updates the message text."""
#     query = update.callback_query

#     # CallbackQueries need to be answered, even if no notification to the user is needed
#     # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
#     query.answer()

#     query.edit_message_text(text=f"Selected option: {query.data}")


def welcome_keyboard() -> ReplyMarkup:
    keyboard = [
        [InlineKeyboardButton("Employee Benefits", callback_data="1")],
        [InlineKeyboardButton("Medical", callback_data="2")],
        [InlineKeyboardButton("Leave", callback_data="3")],
        [InlineKeyboardButton("HR Application System", callback_data="4")],
        [InlineKeyboardButton("Sunway Celcom Package", callback_data="5")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup


def leave_keyboard() -> ReplyMarkup:
    keyboard = [
        [InlineKeyboardButton("Check Leave Balance", callback_data="1")],
        [InlineKeyboardButton("Apply for Leave", callback_data="2")],
        [InlineKeyboardButton("Withdraw Leave", callback_data="3")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup


if __name__ == "__main__":
    main()
