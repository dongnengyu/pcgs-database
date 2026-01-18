"""Background task scheduler for processing scrape tasks"""

import asyncio
import logging
from typing import Optional

from .database import complete_task, get_pending_task, save_coin
from .scraper import fetch_pcgs_cert

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Background scheduler that processes tasks from the pool"""

    def __init__(self, interval: float = 5.0):
        """
        Initialize the scheduler.

        Args:
            interval: Seconds to wait between checking for new tasks
        """
        self.interval = interval
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the scheduler"""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Task scheduler started (interval: %.1fs)", self.interval)

    async def stop(self) -> None:
        """Stop the scheduler"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Task scheduler stopped")

    async def _run(self) -> None:
        """Main scheduler loop"""
        while self._running:
            try:
                await self._process_next_task()
            except Exception as e:
                logger.error("Scheduler error: %s", e)

            # Wait before checking for next task
            await asyncio.sleep(self.interval)

    async def _process_next_task(self) -> None:
        """Get and process the next pending task"""
        task = get_pending_task()
        if not task:
            return

        task_id = task["id"]
        cert_number = task["cert_number"]

        logger.info("Processing task %d: cert_number=%s", task_id, cert_number)

        try:
            # Fetch coin data
            coin_data = await fetch_pcgs_cert(cert_number)

            # Save to database
            save_coin(coin_data)

            # Mark task as completed
            complete_task(task_id, success=True)
            logger.info("Task %d completed successfully", task_id)

        except Exception as e:
            error_msg = str(e)
            logger.error("Task %d failed: %s", task_id, error_msg)
            complete_task(task_id, success=False, error_message=error_msg)


# Global scheduler instance
scheduler = TaskScheduler()
