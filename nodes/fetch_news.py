import asyncio
import logging
import os
from datetime import date

import ollama

from state import PosterState

logger = logging.getLogger(__name__)

_QUERY_TEMPLATES = [
    "new LLM or foundation model release for developers {date}",
    "AI developer tools frameworks APIs released {date}",
    "AI machine learning research paper breakthrough {date}",
    "open source AI model release {date}",
]


def _build_queries() -> list[str]:
    today = date.today().strftime("%B %d, %Y")  # e.g. "May 13, 2026"
    return [t.format(date=today) for t in _QUERY_TEMPLATES]


def _get_client() -> ollama.Client:
    return ollama.Client(
        headers={"Authorization": f"Bearer {os.environ['OLLAMA_API_KEY']}"},
    )


def _search_one(client: ollama.Client, query: str) -> list[dict]:
    try:
        response = client.web_search(query)
        return [
            {
                "title": r.title,
                "url": r.url,
                "snippet": r.content,
            }
            for r in response.results
        ]
    except Exception:
        logger.exception("Search failed for query: %s", query)
        return []


async def _fetch_all() -> list[dict]:
    client = _get_client()
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(None, _search_one, client, q)
        for q in _build_queries()
    ]
    results = await asyncio.gather(*tasks)
    merged: list[dict] = []
    for batch in results:
        merged.extend(batch)
    return merged


def fetch_all_news(state: PosterState) -> dict:
    articles = asyncio.run(_fetch_all())
    logger.info("Fetched %d articles across all search lanes.", len(articles))
    return {"news_results": articles}
