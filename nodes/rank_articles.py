import logging
from datetime import date
from pathlib import Path

from schemas.ranked_article import RankedArticle
from state import PosterState
from llm_client.gemini import generate_structured
from utils.last_article import load_recent_articles

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "rank.txt"


def rank_articles(state: PosterState) -> dict:
    articles = state["news_results"]
    if not articles:
        logger.warning("No articles to rank.")
        return {"ranked_article": {}}

    today = date.today().strftime("%B %d, %Y")
    template = _PROMPT_PATH.read_text(encoding="utf-8")
    articles_text = "\n\n".join(
        f"[{i + 1}] {a['title']}\n{a['url']}\n{a['snippet']}"
        for i, a in enumerate(articles)
    )

    recent = load_recent_articles()
    if recent:
        previous_text = "\n".join(
            f"{i + 1}. Title: {a.get('title', '')}\n   URL: {a.get('url', '')}"
            for i, a in enumerate(recent)
        )
    else:
        previous_text = "None"

    prompt = (
        template
        .replace("{{DATE}}", today)
        .replace("{{ARTICLES}}", articles_text)
        .replace("{{PREVIOUS_ARTICLE}}", previous_text)
    )

    ranked = generate_structured(prompt, RankedArticle)
    logger.info("Ranked article: %s", ranked.title)
    return {"ranked_article": ranked.model_dump()}
