#!/usr/bin/env python3
"""Read-only Open-Assistant backend inspection helper.

Example:
  python scripts/check_backend_python.py --repo-root /path/to/Open-Assistant --openapi

The helper imports backend/shared/data modules from an explicit checkout and
prints package, settings, task, label, API-client, and optional route facts. It
never starts a server, connects to Postgres/Redis, or mutates data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect Open-Assistant backend Python imports and protocol facts.")
    parser.add_argument("--repo-root", required=True, type=Path, help="Open-Assistant checkout to inspect.")
    parser.add_argument("--openapi", action="store_true", help="Also import backend main and list registered route paths.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    return parser.parse_args()


def add_repo_paths(repo_root: Path) -> None:
    for rel in ("backend", "oasst-shared", "oasst-data"):
        path = repo_root / rel
        if path.exists():
            sys.path.insert(0, str(path))


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    add_repo_paths(repo_root)

    result: dict[str, object] = {"repo_root_valid": repo_root.is_dir(), "checks": {}}
    if not repo_root.is_dir():
        print(f"error: repo root not found: {repo_root}", file=sys.stderr)
        return 2

    try:
        import oasst_data
        from oasst_backend.config import Settings, TreeManagerConfiguration
        from oasst_shared.api_client import OasstApiClient
        from oasst_shared.exceptions import OasstErrorCode
        from oasst_shared.schemas import protocol
    except Exception as exc:  # pragma: no cover - diagnostic UI
        print(f"error: backend import failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    settings = Settings()
    tree_cfg = TreeManagerConfiguration()
    result["checks"] = {
        "oasst_data_import": getattr(oasst_data, "__name__", "oasst_data"),
        "project_name": settings.PROJECT_NAME,
        "api_prefix": settings.API_V1_STR,
        "message_size_limit": settings.MESSAGE_SIZE_LIMIT,
        "task_validity_minutes": settings.TASK_VALIDITY_MINUTES,
        "rate_limit_enabled_default": settings.RATE_LIMIT,
        "tree_goal_size_default": tree_cfg.goal_tree_size,
        "task_request_types": [x.value for x in protocol.TaskRequestType],
        "interaction_types": ["text_reply_to_message", "message_rating", "message_ranking", "text_labels"],
        "text_labels": [x.value for x in protocol.TextLabel],
        "error_codes_sample": [x.name for x in list(OasstErrorCode)[:20]],
        "api_client_methods": [
            name
            for name in ("fetch_task", "fetch_random_task", "ack_task", "nack_task", "post_interaction", "close")
            if hasattr(OasstApiClient, name)
        ],
    }

    if args.openapi:
        try:
            import main as backend_main

            routes = sorted({getattr(route, "path", None) for route in backend_main.app.routes if getattr(route, "path", None)})
            result["routes"] = routes
        except Exception as exc:  # pragma: no cover - diagnostic UI
            result["openapi_error"] = f"{type(exc).__name__}: {exc}"
            if not args.json:
                print(f"warning: could not import backend main/routes: {result['openapi_error']}", file=sys.stderr)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Open-Assistant backend inspection OK")
        checks = result["checks"]
        assert isinstance(checks, dict)
        for key, value in checks.items():
            print(f"- {key}: {value}")
        if "routes" in result:
            print("- routes:")
            for route in result["routes"]:  # type: ignore[index]
                print(f"  {route}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
