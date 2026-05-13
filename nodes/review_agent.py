import logging
import os
from pathlib import Path

from openai import OpenAI

from schemas.review_result import ReviewResult
from state import PosterState
from llm_client.openai import _get_openai_client

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "review.txt"

def review_agent(state: PosterState) -> dict:
    article = state["ranked_article"]
    draft = state["draft_post"]

    template = _PROMPT_PATH.read_text(encoding="utf-8")
    prompt = (
        template
        .replace("{{ARTICLE_TITLE}}", article.get("title", ""))
        .replace("{{ARTICLE_URL}}", article.get("url", ""))
        .replace("{{ARTICLE_SUMMARY}}", article.get("summary", article.get("snippet", "")))
        .replace("{{DRAFT_POST}}", draft)
    )

    client = _get_openai_client()

    response = client.beta.chat.completions.parse(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        messages=[{"role": "user", "content": prompt}],
        response_format=ReviewResult
    )


    result: ReviewResult = response.choices[0].message.parsed
    logger.info("Review verdict: %s", result.verdict)

    if result.verdict == True:
        return {"review_feedback": "PASS"}
    return {
        "review_feedback": result.feedback,
        "retry_count": state.get("retry_count", 0) + 1,
    }


def route_review(state: PosterState) -> str:
    feedback = state.get("review_feedback", "")
    retry_count = state.get("retry_count", 0)

    if feedback == "PASS":
        return "notify_telegram"
    if retry_count >= MAX_RETRIES:
        logger.warning("Max retries (%d) reached. Exiting pipeline.", MAX_RETRIES)
        return "end"
    return "write_post"
