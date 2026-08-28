#!/usr/bin/env python3
"""Deterministic local OpenAI-compatible provider mock for DocsGPT testing.

Implements GET /v1/models and POST /v1/chat/completions, including basic SSE.
It binds to loopback by default, has no authentication, and must not be exposed
as a production service.
"""

from __future__ import annotations

import argparse
import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

MODEL = "docsgpt-mock"


def json_bytes(value: Any) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "DocsGPTMock/1"

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}")

    def send_json(self, status: int, value: Any) -> None:
        body = json_bytes(value)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/v1/models":
            self.send_json(200, {"object": "list", "data": [{"id": MODEL, "object": "model", "owned_by": "local-mock"}]})
        else:
            self.send_json(404, {"error": {"message": "not found", "type": "invalid_request_error"}})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/v1/chat/completions":
            self.send_json(404, {"error": {"message": "not found", "type": "invalid_request_error"}})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
        except Exception as error:
            self.send_json(400, {"error": {"message": f"invalid JSON: {error}", "type": "invalid_request_error"}})
            return
        messages = payload.get("messages")
        if not isinstance(messages, list):
            self.send_json(400, {"error": {"message": "messages must be a list", "type": "invalid_request_error"}})
            return
        last = next((m.get("content") for m in reversed(messages) if isinstance(m, dict) and m.get("role") == "user"), "")
        if isinstance(last, list):
            last = " ".join(str(part.get("text", "")) for part in last if isinstance(part, dict))
        content = f"mock response: {last}".strip()
        completion_id = "chatcmpl-" + uuid.uuid4().hex[:16]
        created = int(time.time())
        if payload.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            for token in content.split(" "):
                chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": payload.get("model") or MODEL,
                    "choices": [{"index": 0, "delta": {"content": token + " "}, "finish_reason": None}],
                }
                self.wfile.write(b"data: " + json_bytes(chunk) + b"\n\n")
                self.wfile.flush()
            final = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": payload.get("model") or MODEL,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            self.wfile.write(b"data: " + json_bytes(final) + b"\n\ndata: [DONE]\n\n")
            self.wfile.flush()
            return
        response = {
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": payload.get("model") or MODEL,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": max(1, len(content.split())), "total_tokens": 1 + max(1, len(content.split()))},
        }
        self.send_json(200, response)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        print("WARNING: mock has no authentication; non-loopback binding is unsafe")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"OpenAI-compatible mock listening on http://{args.host}:{args.port}/v1")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
