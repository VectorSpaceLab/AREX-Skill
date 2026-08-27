# Copyright 2025 the LlamaFactory team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Smoke-test a running LlamaFactory OpenAI-compatible API server.

This script is intentionally a client-only helper. It does not start a server,
load a model, or require a LlamaFactory checkout. Start the server separately,
for example:

    API_PORT=8000 llamafactory-cli api CONFIG.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def _request(url: str, api_key: str | None, method: str = "GET", payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
        return exc.code, parsed


def _stream_chat(url: str, api_key: str | None, payload: dict) -> tuple[int, str, bool]:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    text_parts: list[str] = []
    saw_done = False
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data:"):
                    continue
                event_data = line.removeprefix("data:").strip()
                if event_data == "[DONE]":
                    saw_done = True
                    break
                chunk = json.loads(event_data)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content")
                if content:
                    text_parts.append(content)
            return response.status, "".join(text_parts), saw_done
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace"), False


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test LlamaFactory OpenAI-compatible API routes.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1", help="Base API URL ending in /v1.")
    parser.add_argument("--api-key", default=None, help="Bearer token when the server was launched with API_KEY.")
    parser.add_argument("--model", default="test", help="Model id to send in request payloads.")
    parser.add_argument("--prompt", default="Say hello in one short sentence.", help="User prompt for chat smoke test.")
    parser.add_argument("--stream", action="store_true", help="Also test streaming SSE chat completion.")
    parser.add_argument("--score", action="store_true", help="Also call /v1/score/evaluation with string messages.")
    parser.add_argument("--expect-model", default=None, help="Optional expected model id from /v1/models.")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    status, models = _request(f"{base_url}/models", args.api_key)
    print(f"GET /v1/models -> HTTP {status}")
    print(json.dumps(models, indent=2, ensure_ascii=False))
    if status != 200:
        return 1

    if args.expect_model:
        actual = models.get("data", [{}])[0].get("id") if isinstance(models, dict) else None
        if actual != args.expect_model:
            print(f"Expected model id {args.expect_model!r}, got {actual!r}", file=sys.stderr)
            return 1

    chat_payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.prompt}],
        "max_tokens": 64,
        "stream": False,
    }
    status, chat = _request(f"{base_url}/chat/completions", args.api_key, method="POST", payload=chat_payload)
    print(f"POST /v1/chat/completions -> HTTP {status}")
    print(json.dumps(chat, indent=2, ensure_ascii=False) if not isinstance(chat, str) else chat)
    if status != 200:
        return 1

    if args.stream:
        stream_payload = dict(chat_payload)
        stream_payload["stream"] = True
        status, streamed_text, saw_done = _stream_chat(f"{base_url}/chat/completions", args.api_key, stream_payload)
        print(f"POST /v1/chat/completions stream -> HTTP {status}, saw_done={saw_done}")
        print(streamed_text)
        if status != 200 or not saw_done:
            return 1

    if args.score:
        score_payload = {"model": args.model, "messages": [args.prompt], "max_length": 1024}
        status, score = _request(f"{base_url}/score/evaluation", args.api_key, method="POST", payload=score_payload)
        print(f"POST /v1/score/evaluation -> HTTP {status}")
        print(json.dumps(score, indent=2, ensure_ascii=False) if not isinstance(score, str) else score)
        if status not in {200, 405}:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
