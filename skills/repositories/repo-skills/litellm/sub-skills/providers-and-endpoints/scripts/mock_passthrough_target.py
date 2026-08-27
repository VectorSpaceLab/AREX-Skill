#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse


class MockPassthroughHandler(BaseHTTPRequestHandler):
    server_version = "LiteLLMMockPassthrough/1.0"

    def do_GET(self) -> None:
        self._respond()

    def do_POST(self) -> None:
        self._respond()

    def do_PUT(self) -> None:
        self._respond()

    def do_PATCH(self) -> None:
        self._respond()

    def do_DELETE(self) -> None:
        self._respond()

    def log_message(self, format: str, *args: Any) -> None:
        print("{} - {}".format(self.client_address[0], format % args))

    def _read_body(self) -> bytes:
        content_length = int(self.headers.get("content-length", "0") or "0")
        return self.rfile.read(content_length) if content_length else b""

    def _headers(self) -> dict[str, str]:
        sensitive = {"authorization", "x-api-key", "api-key", "proxy-authorization"}
        return {
            key: "<redacted>" if key.lower() in sensitive else value
            for key, value in self.headers.items()
        }

    def _body_preview(self, body: bytes) -> Any:
        if not body:
            return None
        content_type = self.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                return json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                return body.decode("utf-8", errors="replace")[:500]
        return body.decode("utf-8", errors="replace")[:500]

    def _response_body(self, body: bytes) -> dict[str, Any]:
        parsed = urlparse(self.path)
        base: dict[str, Any] = {
            "ok": True,
            "method": self.command,
            "path": parsed.path,
            "query": parse_qs(parsed.query),
            "headers": self._headers(),
            "body": self._body_preview(body),
        }
        if parsed.path.endswith("/converse"):
            base["bedrock_converse"] = {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": "mock converse response"}],
                    }
                },
                "stopReason": "end_turn",
                "usage": {"inputTokens": 1, "outputTokens": 2, "totalTokens": 3},
            }
        elif parsed.path.endswith("/invoke"):
            base["bedrock_invoke"] = {
                "id": "msg_mock",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "mock invoke response"}],
                "model": "mock",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 1, "output_tokens": 2},
            }
        return base

    def _respond(self) -> None:
        body = self._read_body()
        response = json.dumps(self._response_body(body), indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Safe local HTTP target for LiteLLM pass-through path, header, and body debugging."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host. Defaults to 127.0.0.1.")
    parser.add_argument("--port", type=int, default=9999, help="Bind port. Defaults to 9999.")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), MockPassthroughHandler)
    print("Mock pass-through target listening on http://{}:{}".format(args.host, args.port))
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping mock pass-through target.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
