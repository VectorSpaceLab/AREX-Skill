#!/usr/bin/env python3
"""Inspect InvokeAI OpenAPI routes safely, with bundled fallback route families."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from typing import Any

FALLBACK_ROUTERS = [
    {
        "tag": "authentication",
        "prefix": "/api/v1/auth",
        "role": "login, logout, setup status/admin setup, current user, admin user CRUD",
        "route_to": "operations-config",
    },
    {
        "tag": "app",
        "prefix": "/api/v1/app",
        "role": "version, dependency report, patchmatch, runtime config, external provider config, log level, invocation cache",
        "route_to": "operations-config",
    },
    {
        "tag": "model_manager",
        "prefix": "/api/v2/models",
        "role": "model records, install/delete, scanning, Hugging Face login, starter models",
        "route_to": "../model-management/SKILL.md",
    },
    {
        "tag": "download_queue",
        "prefix": "/api/v1/download_queue",
        "role": "model/download jobs",
        "route_to": "../model-management/SKILL.md",
    },
    {
        "tag": "queue",
        "prefix": "/api/v1/queue",
        "role": "session queue enqueue/control/status/history",
        "route_to": "../workflows-queues/SKILL.md",
    },
    {
        "tag": "workflows",
        "prefix": "/api/v1/workflows",
        "role": "workflow records, tags, thumbnails, categories",
        "route_to": "../workflows-queues/SKILL.md",
    },
    {
        "tag": "custom_nodes",
        "prefix": "/api/v2/custom_nodes",
        "role": "custom node packs and reload",
        "route_to": "../workflow-nodes/SKILL.md",
    },
    {"tag": "images", "prefix": "/api/v1/images", "role": "image upload/metadata/files", "route_to": "feature/API docs"},
    {"tag": "boards", "prefix": "/api/v1/boards", "role": "board CRUD", "route_to": "feature/API docs"},
    {"tag": "boards", "prefix": "/api/v1/board_images", "role": "board-image membership", "route_to": "feature/API docs"},
    {"tag": "virtual_boards", "prefix": "/api/v1/virtual_boards", "role": "date virtual boards", "route_to": "feature/API docs"},
    {"tag": "style_presets", "prefix": "/api/v1/style_presets", "role": "style preset CRUD/import/export", "route_to": "feature/API docs"},
    {"tag": "utilities", "prefix": "/api/v1/utilities", "role": "dynamic prompts, prompt expansion, image-to-prompt", "route_to": "feature/API docs"},
    {"tag": "client_state", "prefix": "/api/v1/client_state", "role": "client state per queue", "route_to": "../workflows-queues/SKILL.md"},
    {"tag": "recall", "prefix": "/api/v1/recall", "role": "recall parameters by queue", "route_to": "../workflows-queues/SKILL.md"},
    {"tag": "model_relationships", "prefix": "/api/v1/model_relationships", "role": "related model relationships", "route_to": "../model-management/SKILL.md"},
]


def load_live_schema() -> tuple[dict[str, Any] | None, str | None]:
    try:
        from invokeai.app.api_app import app  # type: ignore
    except Exception as exc:
        return None, f"Could not import invokeai.app.api_app: {type(exc).__name__}: {exc}"
    try:
        schema = app.openapi()
    except Exception as exc:
        return None, f"Could not generate OpenAPI schema: {type(exc).__name__}: {exc}"
    if not isinstance(schema, dict):
        return None, "OpenAPI generation returned an unexpected non-dict payload."
    return schema, None


def summarize_schema(schema: dict[str, Any]) -> dict[str, Any]:
    paths = schema.get("paths", {})
    by_tag: dict[str, list[dict[str, str]]] = defaultdict(list)
    if isinstance(paths, dict):
        for path, methods in sorted(paths.items()):
            if not isinstance(methods, dict):
                continue
            for method, operation in sorted(methods.items()):
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue
                if not isinstance(operation, dict):
                    continue
                tags = operation.get("tags") or ["untagged"]
                tag = str(tags[0]) if tags else "untagged"
                by_tag[tag].append(
                    {
                        "method": method.upper(),
                        "path": str(path),
                        "operation_id": str(operation.get("operationId") or ""),
                        "summary": str(operation.get("summary") or ""),
                    }
                )
    return {
        "title": schema.get("info", {}).get("title") if isinstance(schema.get("info"), dict) else None,
        "version": schema.get("info", {}).get("version") if isinstance(schema.get("info"), dict) else None,
        "route_count": sum(len(items) for items in by_tag.values()),
        "tags": {tag: items for tag, items in sorted(by_tag.items())},
    }


def print_live_summary(summary: dict[str, Any], limit: int) -> None:
    print(f"OpenAPI title: {summary.get('title') or '-'}")
    print(f"OpenAPI version: {summary.get('version') or '-'}")
    print(f"Route operations: {summary.get('route_count', 0)}")
    print()
    tags = summary.get("tags", {})
    for tag, operations in tags.items():
        print(f"## {tag} ({len(operations)})")
        for operation in operations[:limit]:
            op_id = f" [{operation['operation_id']}]" if operation.get("operation_id") else ""
            print(f"- {operation['method']} {operation['path']}{op_id}")
        if len(operations) > limit:
            print(f"- ... {len(operations) - limit} more")
        print()


def fallback_payload() -> dict[str, Any]:
    return {"fallback": True, "routers": FALLBACK_ROUTERS}


def print_fallback(reason: str | None = None) -> None:
    if reason:
        print(f"Live OpenAPI unavailable: {reason}")
        print("Using bundled route-family fallback. Exact schemas require a full InvokeAI runtime environment.")
        print()
    for item in FALLBACK_ROUTERS:
        print(f"- {item['prefix']} ({item['tag']}): {item['role']} -> {item['route_to']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect InvokeAI OpenAPI route families safely.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    parser.add_argument("--fallback", action="store_true", help="Do not import InvokeAI; print bundled route-family fallback.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if live OpenAPI import/generation fails.")
    parser.add_argument("--limit", type=int, default=12, help="Max operations to print per tag in text mode.")
    args = parser.parse_args()

    if args.fallback:
        payload = fallback_payload()
        if args.json:
            json.dump(payload, sys.stdout, indent=2, sort_keys=True)
            print()
        else:
            print_fallback()
        return 0

    schema, error = load_live_schema()
    if schema is None:
        if args.strict:
            print(error or "Live OpenAPI unavailable", file=sys.stderr)
            return 2
        payload = fallback_payload()
        payload["live_error"] = error
        if args.json:
            json.dump(payload, sys.stdout, indent=2, sort_keys=True)
            print()
        else:
            print_fallback(error)
        return 0

    summary = summarize_schema(schema)
    if args.json:
        json.dump(summary, sys.stdout, indent=2, sort_keys=True)
        print()
    else:
        print_live_summary(summary, max(1, args.limit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
