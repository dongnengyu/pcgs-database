"""SQLite database module with logging and type hints"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Optional

from .config import get_settings

logger = logging.getLogger(__name__)


def get_db_path() -> str:
    """Get database path from settings"""
    return str(get_settings().DB_PATH)


def init_db() -> None:
    """Initialize database tables"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cert_number TEXT UNIQUE NOT NULL,
            pcgs_number TEXT,
            grade TEXT,
            date_mintmark TEXT,
            denomination TEXT,
            price_guide_value TEXT,
            population TEXT,
            pop_higher TEXT,
            mintage TEXT,
            region TEXT,
            holder_type TEXT,
            security TEXT,
            image_url TEXT,
            local_image_path TEXT,
            raw_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", db_path)


def save_coin(coin_data: dict) -> bool:
    """
    Save coin data to database.

    Args:
        coin_data: Dictionary containing coin information

    Returns:
        True if save was successful, False otherwise
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO coins (
                cert_number, pcgs_number, grade, date_mintmark, denomination,
                price_guide_value, population, pop_higher, mintage, region,
                holder_type, security, image_url, local_image_path, raw_data, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                coin_data.get("cert_number"),
                coin_data.get("pcgs_#"),
                coin_data.get("grade"),
                coin_data.get("date,_mintmark"),
                coin_data.get("denomination"),
                coin_data.get("price_guide_value"),
                coin_data.get("population"),
                coin_data.get("pop_higher"),
                coin_data.get("mintage"),
                coin_data.get("region"),
                coin_data.get("holder_type"),
                coin_data.get("security"),
                coin_data.get("image_urls", [None])[0]
                if coin_data.get("image_urls")
                else None,
                coin_data.get("saved_images", [None])[0]
                if coin_data.get("saved_images")
                else None,
                json.dumps(coin_data, ensure_ascii=False),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        logger.info("Data saved: cert_number=%s", coin_data.get("cert_number"))
        return True
    except Exception as e:
        logger.error("Failed to save: %s", e)
        return False
    finally:
        conn.close()


def get_all_coins() -> list[dict]:
    """
    Get all coin records from database.

    Returns:
        List of coin dictionaries ordered by creation date descending
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM coins ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_coin_by_cert(cert_number: str) -> Optional[dict]:
    """
    Get coin by certificate number.

    Args:
        cert_number: PCGS certificate number

    Returns:
        Coin dictionary if found, None otherwise
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM coins WHERE cert_number = ?", (cert_number,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def delete_coin(cert_number: str) -> bool:
    """
    Delete coin by certificate number.

    Args:
        cert_number: PCGS certificate number

    Returns:
        True if coin was deleted, False if not found
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM coins WHERE cert_number = ?", (cert_number,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if deleted:
        logger.info("Deleted coin: cert_number=%s", cert_number)
    else:
        logger.warning("Coin not found for deletion: cert_number=%s", cert_number)

    return deleted


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
