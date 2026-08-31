"""Offline synthetic check for the inference-and-endpoints sub-skill.

This test deliberately does not use a real token, Hub model mapping, provider,
or network. It checks three composition edges that the repository's narrower
VCR/production tests do not cover together:

* chat tools plus a JSON-schema response format are preserved in the payload;
* an async stream can be cancelled after its first event and the client closes;
* a provider/task preparation mismatch recovers to an explicitly selected
  fallback provider without retrying a request that may have been accepted.

Run from this repository with ``PYTHONPATH=src python .../mock_chat_recovery.py``
when the editable checkout is not installed. It uses only httpx.MockTransport.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from unittest.mock import patch

import httpx

from huggingface_hub import AsyncInferenceClient, InferenceClient
from huggingface_hub.utils import close_session, set_async_client_factory, set_client_factory

MOCK_BASE_URL = "https://mock.invalid/v1"
MODEL_ID = "mock/model"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_weather",
            "description": "Read weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
                "additionalProperties": False,
            },
        },
    }
]

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "weather_answer",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
            "additionalProperties": False,
        },
    },
}


def completion_payload(content: str) -> dict:
    return {
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
        "created": 0,
        "id": "mock-completion",
        "model": MODEL_ID,
        "system_fingerprint": "mock",
        "usage": {"completion_tokens": 1, "prompt_tokens": 1, "total_tokens": 2},
    }


def request_without_auth(request: httpx.Request) -> dict:
    """Decode a request and prove the fixture did not receive credentials."""
    assert request.url.host == "mock.invalid", request.url
    assert "authorization" not in {key.lower() for key in request.headers}
    return json.loads(request.content)


def make_sync_handler(seen: list[dict]) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = request_without_auth(request)
        seen.append(payload)
        assert request.url.path == "/v1/chat/completions"
        assert payload["model"] == MODEL_ID
        assert payload["tools"] == TOOLS
        assert payload["tool_choice"] == "auto"
        # HF Inference translates the OpenAI json_schema request to its
        # grammar-compatible JSON-object wire shape. The call below still
        # supplies RESPONSE_FORMAT as the public input contract.
        assert payload["response_format"] == {
            "type": "json_object",
            "value": RESPONSE_FORMAT["json_schema"]["schema"],
        }
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json=completion_payload('{"answer":"mocked"}'),
            request=request,
        )

    return handler


def sse_chunk(content: str) -> str:
    return "data: " + json.dumps(
        {
            "choices": [
                {
                    "index": 0,
                    "finish_reason": None,
                    "delta": {"role": "assistant", "content": content},
                }
            ],
            "created": 0,
            "id": "mock-stream",
            "model": MODEL_ID,
            "system_fingerprint": "mock",
            "usage": None,
        }
    )


async def exercise_async_cancellation(seen: list[dict]) -> None:
    first_event = asyncio.Event()

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = request_without_auth(request)
        seen.append(payload)
        assert request.url.path == "/v1/chat/completions"
        body = (sse_chunk("first") + "\n\n" + sse_chunk("second") + "\n\n").encode()
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=body,
            request=request,
        )

    # Use the public factory hook rather than replacing a private client field.
    set_async_client_factory(lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    client = AsyncInferenceClient(model=MOCK_BASE_URL, api_key=None)

    async def consume_until_cancelled() -> None:
        stream = await client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": "<PROMPT>"}],
            stream=True,
        )
        async for chunk in stream:
            assert chunk.choices[0].delta.content == "first"
            first_event.set()
            await asyncio.sleep(3600)

    task = asyncio.create_task(consume_until_cancelled())
    try:
        await asyncio.wait_for(first_event.wait(), timeout=2)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        else:  # pragma: no cover - defensive assertion for the synthetic case
            raise AssertionError("async stream consumer was not cancelled")
    finally:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        # close() releases the partially consumed response held by the exit stack.
        await client.close()


def main() -> None:
    sync_requests: list[dict] = []
    async_requests: list[dict] = []
    set_client_factory(lambda: httpx.Client(transport=httpx.MockTransport(make_sync_handler(sync_requests))))

    # Replicate is a valid provider but does not implement conversational/chat
    # in this registry. This preparation mismatch happens before authentication
    # or transport, so no request is attempted and a fallback is safe.
    primary = InferenceClient(model=MODEL_ID, provider="replicate", api_key=None)
    try:
        primary.chat_completion(
            [{"role": "user", "content": "<PROMPT>"}],
            tools=TOOLS,
            response_format=RESPONSE_FORMAT,
        )
    except ValueError as error:
        assert "Task 'conversational' not supported for provider 'replicate'" in str(error)
    else:  # pragma: no cover - defensive assertion for the synthetic case
        raise AssertionError("the intentionally unsupported provider/task pair was accepted")
    assert sync_requests == [], "a preparation mismatch must not make a network request"

    # Explicit fallback provider. The URL target makes this an entirely local
    # hf-inference helper path; MockTransport still intercepts every request.
    fallback = InferenceClient(model=MOCK_BASE_URL, provider="hf-inference", api_key=None)
    with patch("huggingface_hub.inference._providers.hf_inference.get_token", return_value=None):
        output = fallback.chat_completion(
            [{"role": "user", "content": "<PROMPT>"}],
            model=MODEL_ID,
            tools=TOOLS,
            tool_choice="auto",
            response_format=RESPONSE_FORMAT,
        )
    assert output.choices[0].message.content == '{"answer":"mocked"}'
    assert len(sync_requests) == 1

    # The async client uses its own injected MockTransport. Token lookup is
    # patched to None, and request_without_auth rejects authorization headers.
    async def run_async() -> None:
        with patch("huggingface_hub.inference._providers.hf_inference.get_token", return_value=None):
            await exercise_async_cancellation(async_requests)

    asyncio.run(run_async())
    assert len(async_requests) == 1
    close_session()
    print("PASS: mocked tools/schema, async cancellation, and provider fallback; no real network/token used")


if __name__ == "__main__":
    main()
