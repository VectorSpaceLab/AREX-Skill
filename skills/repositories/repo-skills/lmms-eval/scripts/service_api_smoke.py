#!/usr/bin/env python3
"""Inspect server, client, MCP, TUI, and scheduler APIs."""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json

from lmms_eval.entrypoints import AsyncEvalClient, EvalClient, ServerArgs, launch_server
from lmms_eval.entrypoints.job_scheduler import JobScheduler


def _server_args_round_trip() -> dict:
    payload = {"host": "0.0.0.0", "port": 8001, "max_completed_jobs": 3, "temp_dir_prefix": "lmms_eval_smoke_"}
    if hasattr(ServerArgs, "from_dict"):
        args = ServerArgs.from_dict(payload)
    else:
        args = ServerArgs(**payload)
    if hasattr(args, "to_dict"):
        return args.to_dict()
    return {name: getattr(args, name) for name in payload}


async def _scheduler_smoke() -> dict:
    scheduler = JobScheduler(max_completed_jobs=1, temp_dir_prefix="lmms_eval_smoke_")
    await scheduler.start()
    try:
        stats = await scheduler.get_queue_stats()
        return {
            "queue_stats": stats,
            "queue_size": scheduler.queue_size,
            "current_job_id": scheduler.current_job_id,
        }
    finally:
        await scheduler.stop()


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect lmms-eval service APIs.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    args = parser.parse_args()

    report = {
        "imports": {
            "launch_server": launch_server.__name__,
            "EvalClient": EvalClient.__name__,
            "AsyncEvalClient": AsyncEvalClient.__name__,
            "ServerArgs": ServerArgs.__name__,
            "JobScheduler": JobScheduler.__name__,
        },
        "signatures": {
            "EvalClient.evaluate": str(inspect.signature(EvalClient.evaluate)),
            "AsyncEvalClient.evaluate": str(inspect.signature(AsyncEvalClient.evaluate)),
            "ServerArgs": str(inspect.signature(ServerArgs)),
            "JobScheduler": str(inspect.signature(JobScheduler)),
        },
        "server_args_round_trip": _server_args_round_trip(),
        "scheduler": asyncio.run(_scheduler_smoke()),
    }

    try:
        import lmms_eval.mcp.server as mcp_server
        import lmms_eval.tui.server as tui_server
        import lmms_eval.tui.discovery as tui_discovery

        report["imports"].update(
            {
                "mcp.server": mcp_server.__name__,
                "tui.server": tui_server.__name__,
                "tui.discovery": tui_discovery.__name__,
            }
        )
    except Exception as exc:  # pragma: no cover - environment-specific fallback
        report["imports_error"] = str(exc)
        raise

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print("imports: ", ", ".join(sorted(report["imports"].keys())))
        print("signatures: ")
        for name, signature in report["signatures"].items():
            print(f"  {name}: {signature}")
        print(f"scheduler queue_size={report['scheduler']['queue_size']} current_job_id={report['scheduler']['current_job_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
