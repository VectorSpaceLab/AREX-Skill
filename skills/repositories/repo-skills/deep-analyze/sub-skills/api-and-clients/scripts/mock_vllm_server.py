#!/usr/bin/env python3
"""CPU-safe mock vLLM server for DeepAnalyze API/client smoke tests."""

from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List

DEFAULT_MODEL_NAME = "DeepAnalyze-8B"
DEFAULT_ANALYZE = "Mock vLLM is preparing a workspace smoke test."
DEFAULT_UNDERSTAND = "The workspace artifact exists and the code executed."
DEFAULT_ANSWER = "Mock generation complete."
DEFAULT_CODE = (
    "from pathlib import Path\n"
    "Path('smoke_artifact.txt').write_text('mock vLLM ok\\n', encoding='utf-8')\n"
    "print('artifact written')\n"
)


class MockVLLMHandler(BaseHTTPRequestHandler):
    server_version = "DeepAnalyzeMockVLLM/1.0"
    model_name = DEFAULT_MODEL_NAME
    analyze_text = DEFAULT_ANALYZE
    understand_text = DEFAULT_UNDERSTAND
    answer_text = DEFAULT_ANSWER
    code_text = DEFAULT_CODE
    stream_delay = 0.0

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _send_json(self, status_code: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_sse(self, payload: Dict[str, Any]) -> None:
        data = f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")
        self.wfile.write(data)
        self.wfile.flush()

    def _models_payload(self, model_name: str) -> Dict[str, Any]:
        created = int(time.time())
        return {
            "object": "list",
            "data": [
                {
                    "id": model_name,
                    "object": "model",
                    "created": created,
                    "owned_by": "deepanalyze",
                }
            ],
        }

    def _select_response_text(self, messages: List[Dict[str, Any]]) -> str:
        for message in messages:
            if not isinstance(message, dict):
                continue
            role = str(message.get("role", "")).lower()
            content = str(message.get("content", "") or "")
            if role == "execute" or "<Execute>" in content or "<Code>" in content:
                return (
                    f"<Understand>\n{self.understand_text}\n</Understand>\n"
                    f"<Answer>\n{self.answer_text}\n</Answer>"
                )
        return (
            f"<Analyze>\n{self.analyze_text}\n</Analyze>\n"
            f"<Code>\n```python\n{self.code_text.rstrip()}\n```\n</Code>"
        )

    def _stream_completion(self, model_name: str, content: str) -> None:
        created = int(time.time())
        chunk_id = f"chatcmpl-{created}{int(time.time_ns() % 1000000):06d}"
        for char in content:
            payload = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model_name,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": char},
                        "finish_reason": None,
                    }
                ],
            }
            self._send_sse(payload)
            if self.stream_delay:
                time.sleep(self.stream_delay)
        final_payload = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }
            ],
        }
        self._send_sse(final_payload)
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(200, {"status": "healthy", "timestamp": int(time.time())})
            return
        if self.path == "/v1/models":
            self._send_json(200, self._models_payload(self.model_name))
            return
        self._send_json(404, {"error": "Endpoint not found"})

    def do_POST(self) -> None:
        if self.path == "/v1/models":
            self._send_json(200, self._models_payload(self.model_name))
            return
        if self.path != "/v1/chat/completions":
            self._send_json(404, {"error": "Endpoint not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            request_data = json.loads(raw_body.decode("utf-8"))
        except Exception as exc:
            self._send_json(400, {"error": f"invalid JSON: {exc}"})
            return

        model_name = str(request_data.get("model") or self.model_name)
        messages = request_data.get("messages") or []
        stream = bool(request_data.get("stream", False))
        response_text = self._select_response_text(messages)

        if stream:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            self._stream_completion(model_name, response_text)
            return

        created = int(time.time())
        chunk_id = f"chatcmpl-{created}{int(time.time_ns() % 1000000):06d}"
        self._send_json(
            200,
            {
                "id": chunk_id,
                "object": "chat.completion",
                "created": created,
                "model": model_name,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_text,
                        },
                        "finish_reason": "stop",
                    }
                ],
            },
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a CPU-safe mock vLLM server for DeepAnalyze smoke tests.",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Bind address for the mock server.")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on.")
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME, help="Model id advertised by /v1/models.")
    parser.add_argument("--analyze-text", default=DEFAULT_ANALYZE, help="Text used inside the initial <Analyze> block.")
    parser.add_argument("--understand-text", default=DEFAULT_UNDERSTAND, help="Text used inside the follow-up <Understand> block.")
    parser.add_argument("--answer-text", default=DEFAULT_ANSWER, help="Text used inside the final <Answer> block.")
    parser.add_argument("--code", default=DEFAULT_CODE, help="Python code returned inside the initial <Code> block.")
    parser.add_argument("--delay", type=float, default=0.0, help="Per-character delay for streamed chunks in seconds.")
    return parser


def run_server(args: argparse.Namespace) -> None:
    MockVLLMHandler.model_name = args.model_name
    MockVLLMHandler.analyze_text = args.analyze_text
    MockVLLMHandler.understand_text = args.understand_text
    MockVLLMHandler.answer_text = args.answer_text
    MockVLLMHandler.code_text = args.code
    MockVLLMHandler.stream_delay = args.delay

    class ReusableThreadingHTTPServer(ThreadingHTTPServer):
        allow_reuse_address = True

    server = ReusableThreadingHTTPServer((args.host, args.port), MockVLLMHandler)
    print(f"Mock vLLM server listening on http://{args.host}:{args.port}")
    print(f"Advertised model: {args.model_name}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping mock vLLM server...")
    finally:
        server.shutdown()
        server.server_close()


def main() -> int:
    args = build_parser().parse_args()
    run_server(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
