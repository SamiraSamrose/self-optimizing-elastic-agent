import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from agent.orchestrator import run_optimization_cycle
from config.settings import LOOP_INTERVAL_SECONDS

logger = logging.getLogger(__name__)


def _cycle_job():
    """
    The job function executed by the scheduler on each interval.
    Runs one full optimization cycle and logs the outcome.
    """
    logger.info("Starting scheduled optimization cycle.")
    try:
        result = run_optimization_cycle(time_range_hours=1)
        logger.info(
            "Optimization cycle completed. Status: %s | Actions taken: %d",
            result.get("status"),
            len(result.get("actions_taken", [])),
        )
        for action in result.get("actions_taken", []):
            logger.info("  Action: %s → %s", action["tool"], action["result_status"])
    except Exception as exc:
        logger.exception("Optimization cycle failed: %s", exc)


def start_scheduler():
    """
    Starts the blocking APScheduler that fires the optimization cycle
    every LOOP_INTERVAL_SECONDS seconds.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    scheduler = BlockingScheduler()
    scheduler.add_job(
        _cycle_job,
        trigger=IntervalTrigger(seconds=LOOP_INTERVAL_SECONDS),
        id="optimization_loop",
        name="Self-Optimizing Elastic SRE Agent",
        replace_existing=True,
    )

    logger.info(
        "Scheduler started. Optimization cycle will run every %d seconds.",
        LOOP_INTERVAL_SECONDS,
    )

    # Run one cycle immediately on startup before waiting for the first interval
    _cycle_job()

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by operator.")
        scheduler.shutdown()
