import logging
import os

import requests

from state import PosterState

logger = logging.getLogger(__name__)

LINKEDIN_API = "https://api.linkedin.com/v2/ugcPosts"


def post_linkedin(state: PosterState) -> dict:
    token = os.environ["LINKEDIN_ACCESS_TOKEN"]
    author_urn = os.environ["LINKEDIN_AUTHOR_URN"]
    post = state["draft_post"]

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    body = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": post,
                },
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC",
        },
    }

    try:
        resp = requests.post(LINKEDIN_API, headers=headers, json=body, timeout=15)
        resp.raise_for_status()
        logger.info("LinkedIn post published.")
        return {"linkedin_status": "posted"}
    except requests.RequestException:
        logger.exception("Failed to publish LinkedIn post.")
        return {"linkedin_status": "failed"}
