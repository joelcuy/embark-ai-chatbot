import logging
import os
import random
from decouple import config
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=config('SESSION_KEY_PATH')

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def initialize_new_case(update: Update, context: CallbackContext) -> None:
    # TODO Nice to have: save to db
    session_id = random.randint(1000000, 9999999)

    response = detect_intent_texts(config('PROJECT_ID'), session_id, update.message.text, "en-US")
    update.message.reply_text(response)


def main() -> None:
    updater = Updater(config('BOT_TOKEN'))

    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, initialize_new_case))

    updater.start_polling()

    updater.idle()


def detect_intent_texts(project_id, session_id, text, language_code) -> str:
    """Returns the result of detect intent with texts as inputs.

    Using the same `session_id` between requests allows continuation
    of the conversation."""
    from google.cloud import dialogflow

    session_client = dialogflow.SessionsClient()

    session = session_client.session_path(project_id, session_id)
    
    text_input = dialogflow.TextInput(text=text, language_code=language_code)

    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    return response.query_result.fulfillment_text

    # for text in texts:
    #     text_input = dialogflow.TextInput(text=text, language_code=language_code)

    #     query_input = dialogflow.QueryInput(text=text_input)

    #     response = session_client.detect_intent(
    #         request={"session": session, "query_input": query_input}
    #     )

        # print("=" * 20)
        # print("Query text: {}".format(response.query_result.query_text))
        # print(
        #     "Detected intent: {} (confidence: {})\n".format(
        #         response.query_result.intent.display_name,
        #         response.query_result.intent_detection_confidence,
        #     )
        # )
        # print("Fulfillment text: {}\n".format(response.query_result.fulfillment_text))


if __name__ == '__main__':
    main()