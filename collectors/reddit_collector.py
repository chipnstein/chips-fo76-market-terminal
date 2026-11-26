import os
from datetime import datetime, timezone
import praw
from dotenv import load_dotenv
from config import SUBREDDIT
from collectors.parser import parse_trade_post
from database.db_manager import DatabaseManager

load_dotenv()


def _build_reddit_client() -> praw.Reddit:
    """Initializes a read-only PRAW client using credentials from .env."""
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    if not all([client_id, client_secret, user_agent]):
        raise RuntimeError(
            "Missing Reddit API credentials in .env "
            "(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT)."
        )

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
    reddit.read_only = True
    return reddit


def collect_latest_trades(db: DatabaseManager, limit: int = 50) -> int:
    """
    Fetches the newest posts from r/Market76, parses them, and inserts
    new records into SQLite. Returns the number of newly added trades.
    """
    reddit = _build_reddit_client()
    subreddit = reddit.subreddit(SUBREDDIT)

    inserted_count = 0
    for post in subreddit.new(limit=limit):
        created_iso = datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat()
        flair = post.link_flair_text or ""

        parsed = parse_trade_post(
            post_id=post.id,
            title=post.title,
            flair=flair,
            created_utc=created_iso,
        )
        if parsed and db.insert_trade(parsed):
            inserted_count += 1

    return inserted_count