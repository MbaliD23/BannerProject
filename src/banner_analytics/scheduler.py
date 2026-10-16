from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from .collector import collect_all
from .config import get_settings
from .logging_config import configure_logging

logger = logging.getLogger(__name__)


def run_scheduler() -> None:
    configure_logging()
    settings = get_settings()
    hour, minute = (int(part) for part in settings.schedule_time.split(":", 1))
    scheduler = BlockingScheduler(timezone=settings.timezone)
    scheduler.add_job(
        collect_all,
        CronTrigger(hour=hour, minute=minute, timezone=settings.timezone),
        id="daily-banner-collection",
        name="Daily promotional banner collection",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
        replace_existing=True,
    )
    logger.info("Scheduler started: daily at %s %s", settings.schedule_time, settings.timezone)
    scheduler.start()

