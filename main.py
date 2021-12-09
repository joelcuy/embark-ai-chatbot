import os
from decouple import config
from utils import *
from constants import *
from db import *
from detect_intents import detect_intent_texts

from telegram.replymarkup import ReplyMarkup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply
from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
)


# Env Variables Initialization
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config("SESSION_KEY_PATH")

current_session = {}


def main() -> None:
    updater = Updater(config("BOT_TOKEN"))
    dispatcher = updater.dispatcher

    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, initialize_new_case)
    )
    dispatcher.add_handler(CallbackQueryHandler(inline_keyboard_handler))
    updater.start_polling()
    updater.idle()


def initialize_new_case(update: Update, context: CallbackContext) -> None:
    if update.message is not None:
        # Forward message if it is a reply and in the channel

        chat_id = update.message.chat.id
        message_id = update.message.message_id
        date = update.message.date

        global current_session
        current_session = {
            "chat_id": chat_id,
            "message_id": message_id,
            "created_at": date,
        }

        db_data = read_user(chat_id)
        if db_data is None:
            current_session["session_id"] = generate_session_id()
        else:
            last_message_date = db_data["created_at"]
            if get_mins_from(last_message_date) >= SESSION_EXPIRE_MINS:
                current_session["session_id"] = generate_session_id()
            else:
                current_session["session_id"] = db_data["session_id"]

        create_user(chat_id, current_session)

        response = detect_intent_texts(
            config("PROJECT_ID"),
            current_session["session_id"],
            update.message.text,
            config("DIALOGFLOW_LANGUAGE_CODE"),
        )

        """
        Intents Handlers

        To map intents easily based on their needs for reply_markups
        """
        intents_without_reply_markups = [
            "direct:employee_benefits",
            "direct:claim_medical_bills",
            "direct:hr_application_issues",
            "direct:sunway_celcom_pkg",
            "default_welcome_intent",
            "check_remaning_leaves",
        ]

        intents_with_reply_markups = {
            "frequently_asked_questions": faq_keyboard(),
        }

        if response["intent"] in intents_without_reply_markups:
            update.message.reply_text(response["message"], None)
        elif response["intent"] in intents_with_reply_markups:
            update.message.reply_text(
                response["message"],
                reply_markup=intents_with_reply_markups[response["intent"]],
            )

        if response["intent"] == "default_fallback_intent":
            # Send reply to the user
            context.bot.send_message(
                chat_id=update.message.chat_id,
                reply_to_message_id=update.message.message_id,
                text="I'm really sorry for not being able to process your request. I'll forward your request to a live HR staff.",
            )

            # Forward the chat to HR channel
            context.bot.forward_message(
                chat_id="@demoHRchannel",
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id,
            )

        if response["intent"] == "leave_application":
            print(update.message.text)
            update.message.reply_text(response["message"], None)

    else:
        if (
            update.channel_post.reply_to_message is not None
            and update.channel_post.reply_to_message.forward_from is not None
        ):
            context.bot.forward_message(
                chat_id=update.channel_post.reply_to_message.forward_from.id,
                from_chat_id="@demoHRchannel",
                message_id=update.channel_post.message_id,
            )


# Handler input from inline keyboard
def inline_keyboard_handler(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    # Call function from detect_intets.py
    response = detect_intent_texts(
        config("PROJECT_ID"),
        current_session["session_id"],
        query.data,
        config("DIALOGFLOW_LANGUAGE_CODE"),
    )

    query.edit_message_reply_markup(reply_markup=None)
    query.from_user.send_message(response["message"])


def faq_keyboard() -> ReplyMarkup:
    data = {
        "List of Employee Benefits": "direct:employee_benefits",
        "Medical Bill Claim": "direct:claim_medical_bills",
        "HR Application Error": "direct:hr_application_issues",
        "Sunway Celcom Package": "direct:sunway_celcom_pkg",
    }

    inline_keyboard_options = []

    for key, value in data.items():
        inline_keyboard_options.append([InlineKeyboardButton(key, callback_data=value)])

    return InlineKeyboardMarkup(inline_keyboard_options)


# def leave_keyboard() -> ReplyMarkup:
#     data = {
#         "Check Leave Balance": "Check Leave Balance",
#         "Apply for Leave": "Apply Leave",
#         "Withdraw Leave": "Withdraw Leave",
#     }

#     inline_keyboard_options = []

#     for key, value in data.items():
#         inline_keyboard_options.append([InlineKeyboardButton(key, callback_data=value)])

#     return InlineKeyboardMarkup(inline_keyboard_options)


if __name__ == "__main__":
    main()
