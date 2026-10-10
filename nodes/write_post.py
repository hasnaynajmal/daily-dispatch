import logging
from pathlib import Path

from llm_client.gemini import generate_structured
from schemas.draft_post import DraftPost
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

    result = generate_structured(prompt, DraftPost)
    logger.info("Draft post written (hook: %d chars, body: %d chars).", len(result.hook), len(result.body))
    return {"draft_post": result.model_dump()}
