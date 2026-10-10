from typing import TypedDict


class PosterState(TypedDict):
    # Search
    news_results: list[dict]      # all articles from all 4 lanes

    # Ranking
    ranked_article: dict           # {title, url, summary}

    # Writing
    draft_post: dict               # {hook, body, url}
    review_feedback: str           # reviewer's notes on last draft
    retry_count: int               # number of rewrite attempts

    # Publishing
    telegram_status: str           # "sent" | "failed"
    linkedin_status: str           # "posted" | "failed"
