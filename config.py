from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "market_history.db"

SUBREDDIT = "Market76"
POLL_INTERVAL_SECONDS = 900  # 15 minutes (~96 requests/day)
PLATFORMS = ("PC", "PS", "XB")