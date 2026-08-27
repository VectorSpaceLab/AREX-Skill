#!/usr/bin/env python3
"""Inspect LightX2V service and task status."""

from __future__ import annotations

import argparse
import json
from typing import Any

import requests


def _get_json(url: str) -> dict[str, Any]:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect LightX2V service or task status")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base server URL")
    parser.add_argument("--task-id", default="", help="Optional task id to inspect")
    parser.add_argument("--show-tasks", action="store_true", help="Also print the full task list")
    args = parser.parse_args()

    report: dict[str, Any] = {"service_status": _get_json(f"{args.url.rstrip('/')}/v1/service/status")}
    if args.task_id:
        report["task_status"] = _get_json(f"{args.url.rstrip('/')}/v1/tasks/{args.task_id}/status")
    if args.show_tasks or not args.task_id:
        report["tasks"] = _get_json(f"{args.url.rstrip('/')}/v1/tasks/")

    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
