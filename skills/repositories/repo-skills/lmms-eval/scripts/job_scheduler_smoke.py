#!/usr/bin/env python3
"""Smoke the job scheduler lifecycle without submitting real evaluation work."""

from __future__ import annotations

import argparse
import asyncio
import json

from lmms_eval.entrypoints.job_scheduler import JobScheduler


async def _smoke(max_completed_jobs: int) -> dict:
    scheduler = JobScheduler(max_completed_jobs=max_completed_jobs, temp_dir_prefix="lmms_eval_smoke_")
    await scheduler.start()
    try:
        stats = await scheduler.get_queue_stats()
        missing = await scheduler.get_job("missing-job-id")
        cleaned = await scheduler.cleanup_old_jobs()
        return {
            "queue_stats": stats,
            "queue_size": scheduler.queue_size,
            "current_job_id": scheduler.current_job_id,
            "missing_job": missing,
            "cleanup_removed": cleaned,
        }
    finally:
        await scheduler.stop()


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke the lmms-eval job scheduler lifecycle.")
    parser.add_argument("--max-completed-jobs", type=int, default=2, help="Retention limit for finished jobs.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    args = parser.parse_args()

    report = asyncio.run(_smoke(args.max_completed_jobs))
    report["status"] = "ok"

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(f"queue_size={report['queue_size']} current_job_id={report['current_job_id']}")
        print(f"cleanup_removed={report['cleanup_removed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
