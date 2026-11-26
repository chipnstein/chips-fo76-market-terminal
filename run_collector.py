import argparse
import time
from datetime import datetime, timezone
from config import POLL_INTERVAL_SECONDS
from collectors.parser import parse_trade_post
from collectors.reddit_collector import collect_latest_trades
from database.db_manager import DatabaseManager


def seed_sample_data(db: DatabaseManager) -> None:
    """Populates SQLite with sample PC/PS/XB trades for local testing."""
    samples = [
        ("seed_001", "[PC] H: 3500 Leaders W: Clean Pitman Mask", "PC Trade"),
        ("seed_002", "[PC] H: Clean Pitman Mask W: 4000 Leaders", "PC Trade"),
        ("seed_003", "[PC] H: Weenie Wagon Plan W: 20k Caps", "PC Trade"),
        ("seed_004", "[PS] H: 500 Leaders W: Glowing Unicorn Mask", "PS Trade"),
        ("seed_005", "[PS] H: Glowing Unicorn Mask W: 600 Leaders", "PS Trade"),
        ("seed_006", "(Xb1) H: 250 Leaders W: 5x Pin-Pointers", "XB Trade"),
        ("seed_007", "[PC] H: Last Stand W: Offers", "PC Trade"),
    ]

    added = 0
    now_iso = datetime.now(timezone.utc).isoformat()
    for pid, title, flair in samples:
        parsed = parse_trade_post(pid, title, flair, created_utc=now_iso)
        if parsed and db.insert_trade(parsed):
            added += 1

    print(f"[Seed] Added {added} new sample trades (Total in DB: {db.get_total_count()}).")


def run_live_loop(db: DatabaseManager) -> None:
    """Polls r/Market76 on the configured interval until stopped with Ctrl+C."""
    print(f"[Collector] Starting live polling every {POLL_INTERVAL_SECONDS}s. Press Ctrl+C to stop.")
    while True:
        try:
            added = collect_latest_trades(db)
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Added {added} new trades (Total in DB: {db.get_total_count()}).")
        except Exception as e:
            print(f"[Collector] Error during poll: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FO76 Market Terminal Collector")
    parser.add_argument(
        "--seed-test",
        action="store_true",
        help="Insert sample PC/PS/XB trades into SQLite to verify the pipeline without API keys.",
    )
    args = parser.parse_args()

    db = DatabaseManager()
    if args.seed_test:
        seed_sample_data(db)
    else:
        run_live_loop(db)