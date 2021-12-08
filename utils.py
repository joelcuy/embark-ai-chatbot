from datetime import datetime, timezone
import logging
import random

def get_mins_from(previous_time):

    current_time = datetime.now(timezone.utc)

    time_diff = current_time - previous_time

    seconds_in_day = 24 * 60 * 60

    return divmod(time_diff.days * seconds_in_day + time_diff.seconds, 60)[0]

def generate_session_id() -> int:
    return random.randint(1000000, 9999999)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)