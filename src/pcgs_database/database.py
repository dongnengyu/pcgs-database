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
            variety TEXT,
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

    # Add variety column if it doesn't exist (migration for existing databases)
    try:
        cursor.execute("ALTER TABLE coins ADD COLUMN variety TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Create tasks table for task pool
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cert_number TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP
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
                price_guide_value, population, pop_higher, mintage, variety,
                region, holder_type, security, image_url, local_image_path, raw_data, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                coin_data.get("variety"),
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


# Task-related functions

def add_task(cert_number: str) -> int:
    """
    Add a new task to the pool.

    Args:
        cert_number: PCGS certificate number to scrape

    Returns:
        Task ID
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO tasks (cert_number, status) VALUES (?, 'pending')",
        (cert_number,),
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()

    logger.info("Task added: id=%d, cert_number=%s", task_id, cert_number)
    return task_id


def add_tasks_batch(cert_numbers: list[str]) -> list[int]:
    """
    Add multiple tasks to the pool.

    Args:
        cert_numbers: List of PCGS certificate numbers

    Returns:
        List of task IDs
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    task_ids = []
    for cert_number in cert_numbers:
        cursor.execute(
            "INSERT INTO tasks (cert_number, status) VALUES (?, 'pending')",
            (cert_number.strip(),),
        )
        task_ids.append(cursor.lastrowid)

    conn.commit()
    conn.close()

    logger.info("Batch tasks added: %d tasks", len(task_ids))
    return task_ids


def get_pending_task() -> Optional[dict]:
    """
    Get the next pending task and mark it as running.

    Returns:
        Task dictionary if found, None otherwise
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get oldest pending task
    cursor.execute(
        "SELECT * FROM tasks WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1"
    )
    row = cursor.fetchone()

    if row:
        task = dict(row)
        # Mark as running
        cursor.execute(
            "UPDATE tasks SET status = 'running', started_at = ? WHERE id = ?",
            (datetime.now().isoformat(), task["id"]),
        )
        conn.commit()
        conn.close()
        return task

    conn.close()
    return None


def complete_task(task_id: int, success: bool, error_message: str = None) -> None:
    """
    Mark a task as completed or failed.

    Args:
        task_id: Task ID
        success: Whether the task succeeded
        error_message: Error message if failed
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    status = "completed" if success else "failed"
    cursor.execute(
        "UPDATE tasks SET status = ?, error_message = ?, completed_at = ? WHERE id = ?",
        (status, error_message, datetime.now().isoformat(), task_id),
    )
    conn.commit()
    conn.close()

    logger.info("Task %d marked as %s", task_id, status)


def get_all_tasks() -> list[dict]:
    """
    Get all tasks.

    Returns:
        List of task dictionaries
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_task_stats() -> dict:
    """
    Get task statistics.

    Returns:
        Dictionary with task counts by status
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
        FROM tasks
    """)
    row = cursor.fetchone()
    conn.close()

    return {
        "total": row[0] or 0,
        "pending": row[1] or 0,
        "running": row[2] or 0,
        "completed": row[3] or 0,
        "failed": row[4] or 0,
    }


def delete_task(task_id: int) -> bool:
    """
    Delete a task.

    Args:
        task_id: Task ID

    Returns:
        True if deleted, False if not found
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return deleted


def clear_completed_tasks() -> int:
    """
    Delete all completed and failed tasks.

    Returns:
        Number of tasks deleted
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE status IN ('completed', 'failed')")
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    logger.info("Cleared %d completed/failed tasks", deleted)
    return deleted


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
