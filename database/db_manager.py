import sqlite3
from pathlib import Path
from config import DATA_DIR, DB_PATH


class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT NOT NULL,
                    created_utc TEXT NOT NULL,
                    platform TEXT NOT NULL,      -- 'PC', 'PS', 'XB'
                    direction TEXT NOT NULL,     -- 'BUY' (W: item) or 'SELL' (H: item)
                    item_name TEXT NOT NULL,
                    price REAL,                  -- NULL if 'Offer' / no price stated
                    currency TEXT NOT NULL,      -- 'L' (Leaders), 'c' (Caps), or 'OFFER'
                    raw_title TEXT NOT NULL,
                    UNIQUE(post_id, item_name, direction)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_platform_item
                ON trades (platform, item_name, created_utc)
            """)

    def insert_trade(self, trade: dict) -> bool:
        """Inserts a parsed trade record. Returns True if inserted, False if duplicate."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO trades
                    (post_id, created_utc, platform, direction, item_name, price, currency, raw_title)
                VALUES
                    (:post_id, :created_utc, :platform, :direction, :item_name, :price, :currency, :raw_title)
                """,
                trade,
            )
            return cursor.rowcount > 0

    def get_trades_by_platform(self, platform: str, limit: int = 500) -> list[dict]:
        """Fetches recent trades for a specific platform ('PC', 'PS', 'XB')."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT post_id, created_utc, platform, direction, item_name, price, currency, raw_title
                FROM trades
                WHERE platform = ?
                ORDER BY created_utc DESC
                LIMIT ?
                """,
                (platform.upper(), limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_total_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM trades").fetchone()
            return row["cnt"] if row else 0