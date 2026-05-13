import logging
import os
from pathlib import Path

from openai import OpenAI

from llm_client.openai import _get_openai_client
from state import PosterState

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "write.txt"

def write_post(state: PosterState) -> dict:
    article = state["ranked_article"]
    feedback = state.get("review_feedback", "")

    template = _PROMPT_PATH.read_text(encoding="utf-8")
    prompt = (
        template
        .replace("{{TITLE}}", article.get("title", ""))
        .replace("{{URL}}", article.get("url", ""))
        .replace("{{SUMMARY}}", article.get("summary", article.get("snippet", "")))
        .replace("{{FEEDBACK}}", feedback or "None")
    )

    client = _get_openai_client()
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        messages=[{"role": "user", "content": prompt}],
    )
    
    draft = response.choices[0].message.content.strip()
    logger.info("Draft post written (%d chars).", len(draft))
    return {"draft_post": draft}
