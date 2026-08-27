#!/usr/bin/env python3
"""Safe LitServe OpenAISpec chat completions example.

Run:
    python openai_chat_server.py --port 8000

OpenAI client:
    from openai import OpenAI
    client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="lit")
    client.chat.completions.create(
        model="lit",
        messages=[{"role": "user", "content": "hello"}],
    )

The server is deterministic and has no model dependency. It demonstrates the
response shapes that real model code should return from LitAPI.predict when
using OpenAISpec.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import litserve as ls
from litserve import OpenAISpec
from litserve.specs.openai import ChatCompletionRequest


def _as_jsonable_dict(value: Any) -> dict[str, Any]:
    """Return a plain dict for Pydantic models, SDK dicts, or unknown objects."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump(mode="json")
        except TypeError:
            return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return {name: getattr(value, name) for name in dir(value) if not name.startswith("_")}


def _first_tool_name(tools: Any) -> str:
    if not tools:
        return "demo_tool"
    first = tools[0]
    first_dict = _as_jsonable_dict(first)
    function = first_dict.get("function")
    if not isinstance(function, dict):
        function = _as_jsonable_dict(function)
    return str(function.get("name") or "demo_tool")


def _summarize_messages(request: ChatCompletionRequest) -> tuple[str, list[str]]:
    """Extract text and media markers from OpenAI-style chat messages."""
    text_parts: list[str] = []
    media_parts: list[str] = []

    for message in request.messages:
        content = message.content
        if content is None:
            continue
        if isinstance(content, str):
            if message.role == "user":
                text_parts.append(content)
            continue
        for part in content:
            part_dict = _as_jsonable_dict(part)
            part_type = part_dict.get("type", "text")
            if part_type == "text":
                text_parts.append(str(part_dict.get("text", "")))
            elif part_type == "image_url":
                image_url = part_dict.get("image_url")
                if isinstance(image_url, dict):
                    detail = image_url.get("detail", "auto")
                    media_parts.append(f"image_url:{detail}")
                else:
                    media_parts.append("image_url")
            elif part_type == "input_audio":
                audio = part_dict.get("input_audio") or {}
                if not isinstance(audio, dict):
                    audio = _as_jsonable_dict(audio)
                media_parts.append(f"input_audio:{audio.get('format', 'unknown')}")
            else:
                media_parts.append(str(part_type))

    latest_text = text_parts[-1] if text_parts else ""
    return latest_text, media_parts


class DemoOpenAIChatAPI(ls.LitAPI):
    """Deterministic chat API for OpenAISpec shape validation."""

    def setup(self, device: str) -> None:
        self.device = device

    def predict(self, request: ChatCompletionRequest, context: dict[str, Any] | None = None):
        # OpenAISpec requires a generator. Yield dicts so roles, tool calls, and
        # usage are explicit in both streaming and non-streaming responses.
        context = context or {}
        latest_text, media_parts = _summarize_messages(request)

        tools = context.get("tools") or request.tools
        if tools:
            tool_name = _first_tool_name(tools)
            yield {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_demo_001",
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps({"location": "Boston, MA"}),
                        },
                    }
                ],
                "prompt_tokens": max(1, len(latest_text.split())),
                "completion_tokens": 1,
                "total_tokens": max(2, len(latest_text.split()) + 1),
            }
            return

        if context.get("response_format") or request.response_format:
            payload = {
                "name": "Science Fair",
                "date": "Friday",
                "participants": ["Alice", "Bob"],
            }
            text = json.dumps(payload, separators=(",", ":"))
            yield {
                "role": "assistant",
                "content": text,
                "prompt_tokens": max(1, len(latest_text.split())),
                "completion_tokens": len(text),
                "total_tokens": max(1, len(latest_text.split())) + len(text),
            }
            return

        if media_parts:
            answer = f"Received {', '.join(media_parts)} with text: {latest_text or 'no text'}"
        elif latest_text:
            answer = f"Echo: {latest_text}"
        else:
            answer = "This is a generated output"

        completion_tokens = 0
        for token in answer.split(" "):
            completion_tokens += 1
            yield {"role": "assistant", "content": token + " "}

        prompt_tokens = max(1, len(latest_text.split()))
        yield {
            "role": "assistant",
            "content": "",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a LitServe OpenAISpec demo chat server.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args()

    api = DemoOpenAIChatAPI(spec=OpenAISpec())
    server = ls.LitServer(api)
    server.run(host=args.host, port=args.port, log_level=args.log_level)


if __name__ == "__main__":
    main()
