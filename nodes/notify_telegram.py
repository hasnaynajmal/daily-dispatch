import logging
import os

import requests

from state import PosterState

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


def notify_telegram(state: PosterState) -> dict:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    post = state["draft_post"]

    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": post,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("Telegram notification sent.")
        return {"telegram_status": "sent"}
    except requests.RequestException:
        logger.exception("Failed to send Telegram notification.")
        return {"telegram_status": "failed"}
