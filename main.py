import asyncio
import logging
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

from graph import build_graph
from state import PosterState

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def run_pipeline() -> None:
    logger.info("Daily pipeline starting…")
    graph = build_graph()
    initial_state: PosterState = {
        "news_results": [],
        "ranked_article": {},
        "draft_post": "",
        "review_feedback": "",
        "retry_count": 0,
        "telegram_status": "",
        "linkedin_status": "",
    }
    result = graph.invoke(initial_state)
    logger.info(
        "Pipeline finished. Telegram: %s | LinkedIn: %s",
        result.get("telegram_status"),
        result.get("linkedin_status"),
    )


if __name__ == "__main__":
    if "--once" in sys.argv or "--test" in sys.argv:
        logger.info("Running pipeline once.")
        run_pipeline()
    else:
        scheduler = BlockingScheduler(timezone="UTC")
        scheduler.add_job(run_pipeline, "cron", hour=8, minute=0)
        logger.info("Scheduler started. Pipeline will run daily at 08:00 UTC.")
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")