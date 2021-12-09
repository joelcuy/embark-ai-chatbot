from google.cloud import dialogflow

def detect_intent_texts(project_id, session_id, text_to_be_analyzed, language_code) -> dict:
    """Returns the result of detect intent with texts as inputs.

    Using the same `session_id` between requests allows continuation
    of the conversation."""
    session_client = dialogflow.SessionsClient()

    session = session_client.session_path(project_id, session_id)

    text_input = dialogflow.TextInput(text=text_to_be_analyzed, language_code=language_code)

    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    return {
        "message": response.query_result.fulfillment_text,
        "intent": response.query_result.intent.display_name,
        "confidence_level": response.query_result.intent_detection_confidence
    }
    
    