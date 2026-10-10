import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_STORE_PATH = Path(__file__).parent.parent / "last_article.json"
_MAX_HISTORY = 7


def load_recent_articles() -> list[dict]:
    """Return up to the last 7 sent articles, newest first. Empty list on first run."""
    if not _STORE_PATH.exists():
        return []
    try:
        data = json.loads(_STORE_PATH.read_text(encoding="utf-8"))
        # support legacy single-article format
        if isinstance(data, dict):
            return [data]
        return data if isinstance(data, list) else []
    except Exception:
        logger.warning("Could not read last_article.json — ignoring.")
        return []


def save_last_article(article: dict) -> None:
    """Prepend article to the rolling history, keeping at most _MAX_HISTORY entries."""
    try:
        history = load_recent_articles()
        history.insert(0, article)
        history = history[:_MAX_HISTORY]
        _STORE_PATH.write_text(
            json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info("Saved last article: %s", article.get("title", ""))
    except Exception:
        logger.warning("Could not save last_article.json.")
