import logging
import os
from pathlib import Path

from openai import OpenAI

from schemas.ranked_article import RankedArticle
from state import PosterState

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "rank.txt"


def _get_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434") + "/v1",
        api_key=os.environ.get("OLLAMA_API_KEY", "ollama"),
    )


def rank_articles(state: PosterState) -> dict:
    articles = state["news_results"]
    if not articles:
        logger.warning("No articles to rank.")
        return {"ranked_article": {}}

    template = _PROMPT_PATH.read_text(encoding="utf-8")
    articles_text = "\n\n".join(
        f"[{i + 1}] {a['title']}\n{a['url']}\n{a['snippet']}"
        for i, a in enumerate(articles)
    )
    prompt = template.replace("{{ARTICLES}}", articles_text)

    client = _get_client()
    response = client.beta.chat.completions.parse(
        model=os.environ.get("OLLAMA_MODEL", "qwen3:8b"),
        messages=[{"role": "user", "content": prompt}],
        response_format=RankedArticle,
    )
    ranked: RankedArticle = response.choices[0].message.parsed
    logger.info("Ranked article: %s", ranked.title)
    return {"ranked_article": ranked.model_dump()}
