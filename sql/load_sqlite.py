"""Build data/marketing.db from the raw CSV and sql/schema.sql.

    python sql/load_sqlite.py

The database is a local artifact. It is gitignored and can be rebuilt.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cleaning import clean_marketing, load_raw
from src.formatters import money_amount

RAW_PATH = ROOT / "data" / "raw" / "Marketing.csv"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"
DB_PATH = ROOT / "data" / "marketing.db"

INSERT = """
INSERT INTO campaign_daily (
    id, c_date, campaign_name, campaign_name_raw, category, campaign_id,
    platform, city_tier, targeting, impressions, mark_spent, clicks, leads,
    orders, revenue, gross_profit, weekday, is_weekend
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def build_database(db_path: Path = DB_PATH) -> Path:
    clean = clean_marketing(load_raw(RAW_PATH))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA_PATH.read_text())
        rows = [
            (
                int(row.id),
                row.c_date.strftime("%Y-%m-%d"),
                row.campaign_name,
                row.campaign_name_raw,
                row.category,
                int(row.campaign_id),
                row.platform,
                row.city_tier,
                row.targeting,
                int(row.impressions),
                float(money_amount(row.spend_cents)),
                int(row.clicks),
                int(row.leads),
                int(row.orders),
                float(money_amount(row.revenue_cents)),
                float(money_amount(row.gross_profit_cents)),
                row.weekday,
                int(row.is_weekend),
            )
            for row in clean.itertuples(index=False)
        ]
        connection.executemany(INSERT, rows)
        connection.commit()
        count, spend, revenue = connection.execute(
            "SELECT COUNT(*), ROUND(SUM(mark_spent), 2), ROUND(SUM(revenue), 2) FROM campaign_daily"
        ).fetchone()
    finally:
        connection.close()

    print(f"Loaded {count} rows into {db_path.relative_to(ROOT)}")
    print(f"Spend ${spend:,.2f}   Revenue ${revenue:,.2f}")
    return db_path


if __name__ == "__main__":
    build_database()
