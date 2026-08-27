#!/usr/bin/env python3
"""Safe EverOS memory HTTP smoke driver.

Default behavior calls only GET /health. Pass --add-flush-search to write one
small memory, flush it, and search it back against a running EverOS server.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any


def request_json(method: str, base_url: str, path: str, payload: dict[str, Any] | None, timeout: float) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
    return {} if not raw else json.loads(raw)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server-url", default="http://127.0.0.1:8000")
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--add-flush-search", action="store_true", help="Actually write and search one tiny memory")
    p.add_argument("--session-id", default="everos-skill-smoke")
    p.add_argument("--user-id", default="everos_skill_user")
    p.add_argument("--memory", default="I keep my Monday design notes in Notion.")
    p.add_argument("--query", default="Where are my Monday design notes?")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    result: dict[str, Any] = {"server_url": args.server_url, "steps": []}
    try:
        health = request_json("GET", args.server_url, "/health", None, args.timeout)
        result["steps"].append({"name": "health", "ok": health.get("status") == "ok", "response": health})
        if args.add_flush_search:
            ts = int(time.time() * 1000)
            add = request_json(
                "POST", args.server_url, "/api/v2/memory/add",
                {"session_id": args.session_id, "messages": [{"sender_id": args.user_id, "role": "user", "timestamp": ts, "content": args.memory}]},
                args.timeout,
            )
            result["steps"].append({"name": "add", "ok": True, "response": add})
            flush = request_json(
                "POST", args.server_url, "/api/v2/memory/flush",
                {"session_id": args.session_id}, args.timeout,
            )
            result["steps"].append({"name": "flush", "ok": True, "response": flush})
            search = request_json(
                "POST", args.server_url, "/api/v2/memory/search",
                {"user_id": args.user_id, "query": args.query, "method": "hybrid", "top_k": 5},
                args.timeout,
            )
            result["steps"].append({"name": "search", "ok": True, "response": search})
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        result["error"] = {"type": "HTTPError", "status": exc.code, "body": body}
    except Exception as exc:
        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for step in result.get("steps", []):
            print(f"{step['name']}: {'OK' if step.get('ok') else 'WARN'}")
        if "error" in result:
            print(json.dumps(result["error"], indent=2), file=sys.stderr)
    return 1 if "error" in result else 0


if __name__ == "__main__":
    raise SystemExit(main())
