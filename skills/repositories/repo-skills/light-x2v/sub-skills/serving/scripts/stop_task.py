#!/usr/bin/env python3
"""Stop one LightX2V task or all running tasks."""

from __future__ import annotations

import argparse
import json
from typing import Any

import requests


def _delete_json(url: str) -> dict[str, Any]:
    response = requests.delete(url, timeout=30)
    response.raise_for_status()
    return response.json()


def main() -> int:
    parser = argparse.ArgumentParser(description="Stop a LightX2V task")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base server URL")
    parser.add_argument("--task-id", default="", help="Task id to stop")
    parser.add_argument("--all-running", action="store_true", help="Stop all running tasks instead of one task")
    args = parser.parse_args()

    base = args.url.rstrip("/")
    if args.all_running or not args.task_id:
        result = _delete_json(f"{base}/v1/tasks/all/running")
    else:
        result = _delete_json(f"{base}/v1/tasks/{args.task_id}")

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
