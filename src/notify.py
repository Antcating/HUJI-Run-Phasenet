from datetime import datetime
from pathlib import Path

import telebot

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_detection(
    image_path: Path,
    num_picks: int,
    event_time: datetime,
    chat_id: str = TELEGRAM_CHAT_ID,
) -> bool:
    """
    Send a detection plot with metadata to Telegram.

    Returns True if the message was sent, False if Telegram is not
    configured.
    """
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        print("Telegram not configured; skipping notification")
        return False

    caption = (
        "New detection\n"
        f"Date: {event_time:%Y-%m-%d}\n"
        f"Time: {event_time:%H:%M:%S} {event_time.tzname()}\n"
        f"Picks: {num_picks:,}"
    )

    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

    with open(image_path, "rb") as photo:
        bot.send_photo(chat_id, photo, caption=caption)

    return True
