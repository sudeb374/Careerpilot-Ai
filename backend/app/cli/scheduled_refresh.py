"""
CareerPilot AI — Scheduled Refresh CLI Runner (Phase 6.4)

Command-line entry point for executing scheduled opportunity ingestion and
deadline expiration via external schedulers (cron, Cloud Scheduler, Cloud Run jobs).

Usage:
    python -m app.cli.scheduled_refresh [--force]

Options:
    --force    Execute refresh even if SCHEDULED_REFRESH_ENABLED=false in settings.
"""

import argparse
import asyncio
import sys
import logging

from app.core.database import get_db_session
from app.services.scheduled_refresh import execute_scheduled_refresh

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("careerpilot.cli.scheduled_refresh")


async def run_cli(force: bool = False) -> int:
    """Execute scheduled refresh and return process exit code."""
    logger.info(f"Starting scheduled refresh CLI (force={force})...")
    async with get_db_session() as db:
        summary = await execute_scheduled_refresh(db=db, force=force)

    print("\n" + "=" * 60)
    print("CareerPilot AI — Scheduled Refresh Execution Summary")
    print("=" * 60)
    print(f"Status:             {summary.status.upper()}")
    print(f"Duration:           {summary.duration_seconds}s")
    print(f"Total Inserted:     {summary.total_inserted}")
    print(f"Total Updated:      {summary.total_updated}")
    print(f"Total Duplicates:   {summary.total_duplicates}")
    print(f"Total Expired:      {summary.total_expired}")

    if summary.sources:
        print("\nSources Breakdown:")
        for s in summary.sources:
            print(f"  - [{s.source}] {s.target}")
            print(f"      Status: {s.status}, Found: {s.items_found}, New: {s.items_inserted}, Updated: {s.items_updated}, Dup: {s.items_duplicate}")
            if s.error:
                print(f"      Error: {s.error}")

    if summary.errors:
        print("\nWarnings / Errors:")
        for err in summary.errors:
            print(f"  ! {err}")

    print("=" * 60 + "\n")

    if summary.status in ("success", "partial_failure", "skipped"):
        return 0
    return 1


def main():
    parser = argparse.ArgumentParser(
        description="CareerPilot AI Scheduled Refresh CLI Runner",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force execution even if scheduled refresh is disabled in configuration.",
    )
    args = parser.parse_args()

    exit_code = asyncio.run(run_cli(force=args.force))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
