#!/usr/bin/env python3
"""Safe EverOS knowledge API probe.

Default behavior calls /health and /api/v2/knowledge/categories. Uploads require
both --allow-write and --file so accidental document writes do not happen.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import uuid
import urllib.error
import urllib.request
from typing import Any


def request(method: str, base: str, path: str, *, json_body: dict[str, Any] | None = None, body: bytes | None = None, headers: dict[str, str] | None = None, timeout: float = 10.0) -> dict[str, Any]:
    data = body if body is not None else (None if json_body is None else json.dumps(json_body).encode())
    req_headers = {"Content-Type": "application/json"} if json_body is not None else {}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(base.rstrip("/") + path, data=data, headers=req_headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
    return {} if not raw else json.loads(raw)


def multipart(fields: dict[str, str], file_path: str) -> tuple[bytes, str]:
    boundary = "----everos-skill-" + uuid.uuid4().hex
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())
    filename = os.path.basename(file_path)
    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    with open(file_path, "rb") as fh:
        content = fh.read()
    chunks.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: {ctype}\r\n\r\n".encode())
    chunks.append(content + b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server-url", default="http://127.0.0.1:8000")
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--allow-write", action="store_true", help="Allow POST /knowledge/documents")
    p.add_argument("--file", help="File to upload when --allow-write is set")
    p.add_argument("--title", default="EverOS skill probe document")
    p.add_argument("--search", help="Optional knowledge search query")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    out: dict[str, Any] = {"steps": []}
    try:
        out["steps"].append({"name": "health", "response": request("GET", args.server_url, "/health", timeout=args.timeout)})
        out["steps"].append({"name": "categories", "response": request("GET", args.server_url, "/api/v2/knowledge/categories", timeout=args.timeout)})
        if args.allow_write and args.file:
            body, ctype = multipart({"title": args.title}, args.file)
            out["steps"].append({"name": "upload", "response": request("POST", args.server_url, "/api/v2/knowledge/documents", body=body, headers={"Content-Type": ctype}, timeout=args.timeout)})
        if args.search:
            out["steps"].append({"name": "search", "response": request("POST", args.server_url, "/api/v2/knowledge/search", json_body={"query": args.search}, timeout=args.timeout)})
    except urllib.error.HTTPError as exc:
        out["error"] = {"type": "HTTPError", "status": exc.code, "body": exc.read().decode("utf-8", errors="replace")}
    except Exception as exc:
        out["error"] = {"type": type(exc).__name__, "message": str(exc)}
    print(json.dumps(out, indent=2, sort_keys=True) if args.json else "\n".join(step["name"] for step in out.get("steps", [])))
    return 1 if "error" in out else 0


if __name__ == "__main__":
    raise SystemExit(main())
