#!/usr/bin/env python3
"""Offline builder and validator for R2R retrieval requests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

def _load_json(value: str | None) -> Any:
    if value is None:
        return None
    if value.startswith("@"):
        return json.loads(Path(value[1:]).read_text())
    return json.loads(value)

def _build_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {"query": args.query}
    if args.search_mode:
        payload["search_mode"] = args.search_mode
    if args.search_settings_json:
        payload["search_settings"] = _load_json(args.search_settings_json)
    if args.kind in {"rag", "agent"}:
        if args.rag_generation_config_json:
            payload["rag_generation_config"] = _load_json(args.rag_generation_config_json)
        if args.task_prompt:
            payload["task_prompt"] = args.task_prompt
        if args.include_web_search:
            payload["include_web_search"] = True
        if args.kind == "agent" and args.message:
            payload["message"] = _load_json(args.message) if args.message.startswith("{") else args.message
    return payload

def main() -> int:
    parser = argparse.ArgumentParser(description="Build and validate R2R search/RAG/agent payloads without contacting a server.")
    parser.add_argument("--kind", choices=("search", "rag", "agent"), default="search")
    parser.add_argument("--query", required=True)
    parser.add_argument("--search-mode")
    parser.add_argument("--search-settings-json")
    parser.add_argument("--rag-generation-config-json")
    parser.add_argument("--task-prompt")
    parser.add_argument("--message", help="Optional agent message string or JSON object string.")
    parser.add_argument("--include-web-search", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--python", action="store_true")
    args = parser.parse_args()

    payload = _build_payload(args)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif args.python:
        print("from r2r import R2RClient")
        print("client = R2RClient(base_url='http://localhost:7272')")
        print(f"print(client.retrieval.{args.kind}(**{payload!r}).results)")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
