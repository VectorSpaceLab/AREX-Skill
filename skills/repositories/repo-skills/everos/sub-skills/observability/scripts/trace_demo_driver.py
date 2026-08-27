#!/usr/bin/env python3
"""Tiny EverOS tracing driver.

By default this only checks /health and prints what to configure. Pass --run-flow
to send one add/flush/search sequence to a running server, useful when tracing is
already enabled and you want a small trace.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from typing import Any


def req(method: str, base: str, path: str, payload: dict[str, Any] | None, timeout: float) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(base.rstrip("/") + path, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
    return {} if not raw else json.loads(raw)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server-url", default="http://127.0.0.1:8000")
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--run-flow", action="store_true", help="Write one tiny memory and search it")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    out: dict[str, Any] = {"steps": [], "note": "Enable everos[otel] and [observability] before expecting exported spans."}
    try:
        out["steps"].append({"name": "health", "response": req("GET", args.server_url, "/health", None, args.timeout)})
        if args.run_flow:
            ts = int(time.time() * 1000)
            session = "everos-trace-demo"
            user = "trace_demo_user"
            out["steps"].append({"name": "add", "response": req("POST", args.server_url, "/api/v2/memory/add", {"session_id": session, "messages": [{"sender_id": user, "role": "user", "timestamp": ts, "content": "I prefer trace demos to use tiny safe fixtures."}]}, args.timeout)})
            out["steps"].append({"name": "flush", "response": req("POST", args.server_url, "/api/v2/memory/flush", {"session_id": session}, args.timeout)})
            out["steps"].append({"name": "search", "response": req("POST", args.server_url, "/api/v2/memory/search", {"user_id": user, "query": "What kind of trace demos do I prefer?", "top_k": 3}, args.timeout)})
    except urllib.error.HTTPError as exc:
        out["error"] = {"type": "HTTPError", "status": exc.code, "body": exc.read().decode("utf-8", errors="replace")}
    except Exception as exc:
        out["error"] = {"type": type(exc).__name__, "message": str(exc)}
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(out["note"])
        for step in out["steps"]:
            print(step["name"])
        if "error" in out:
            print(json.dumps(out["error"], indent=2))
    return 1 if "error" in out else 0


if __name__ == "__main__":
    raise SystemExit(main())
