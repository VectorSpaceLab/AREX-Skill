#!/usr/bin/env python3
"""Smoke-check a vLLM OpenAI-compatible server with the OpenAI client."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from typing import Any


DEFAULT_PROMPT = "Reply with the single word: pong"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check /v1/models and optionally issue a minimal chat or completion "
            "request to a user-provided vLLM OpenAI-compatible server."
        )
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000/v1",
        help="OpenAI client base URL; include the /v1 suffix",
    )
    parser.add_argument(
        "--api-key",
        default="EMPTY",
        help="API key/token expected by the server, or a placeholder for no-auth servers",
    )
    parser.add_argument(
        "--model",
        help="Model ID to request; defaults to the first ID returned by /v1/models",
    )
    parser.add_argument(
        "--mode",
        choices=("models", "chat", "completion"),
        default="models",
        help="Smoke mode to run",
    )
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Prompt/message text")
    parser.add_argument("--max-tokens", type=int, default=16, help="Small generation cap")
    parser.add_argument("--stream", action="store_true", help="Use streaming output")
    parser.add_argument(
        "--no-request-plan",
        action="store_true",
        help="Print the planned request and exit without contacting the server",
    )
    return parser.parse_args()


def require_openai() -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit(
            "The openai package is required. Install it in the active environment "
            "before running this smoke check."
        ) from exc
    return OpenAI


def print_plan(args: argparse.Namespace) -> None:
    print("Planned vLLM OpenAI smoke check:")
    print(f"  base_url: {args.base_url}")
    print(f"  mode: {args.mode}")
    print(f"  model: {args.model or '<first model from /v1/models>'}")
    print(f"  stream: {args.stream}")
    print("No request was sent because --no-request-plan was provided.")


def first_model_id(models_response: Any) -> str:
    data = getattr(models_response, "data", None)
    if not data:
        raise RuntimeError("/v1/models returned no models")
    model_id = getattr(data[0], "id", None)
    if not model_id:
        raise RuntimeError("first /v1/models entry did not contain an id")
    return model_id


def print_stream_text(chunks: Iterable[Any], mode: str) -> None:
    for chunk in chunks:
        if not getattr(chunk, "choices", None):
            continue
        choice = chunk.choices[0]
        if mode == "chat":
            delta = getattr(choice, "delta", None)
            text = getattr(delta, "content", None) if delta is not None else None
        else:
            text = getattr(choice, "text", None)
        if text:
            print(text, end="", flush=True)
    print()


def main() -> int:
    args = parse_args()
    if args.no_request_plan:
        print_plan(args)
        return 0

    OpenAI = require_openai()
    client = OpenAI(base_url=args.base_url, api_key=args.api_key)

    try:
        models_response = client.models.list()
        model_ids = [item.id for item in models_response.data]
        print("Models:")
        for model_id in model_ids:
            print(f"  {model_id}")
        model = args.model or first_model_id(models_response)

        if args.mode == "models":
            return 0

        if args.mode == "chat":
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": args.prompt}],
                max_tokens=args.max_tokens,
                stream=args.stream,
            )
            if args.stream:
                print_stream_text(response, "chat")
            else:
                print(response.choices[0].message.content)
            return 0

        response = client.completions.create(
            model=model,
            prompt=args.prompt,
            max_tokens=args.max_tokens,
            stream=args.stream,
        )
        if args.stream:
            print_stream_text(response, "completion")
        else:
            print(response.choices[0].text)
        return 0
    except Exception as exc:  # noqa: BLE001 - preserve client/server error text.
        print(f"Smoke check failed: {exc}", file=sys.stderr)
        print(
            "Check that the server is running, base_url includes /v1, the API key "
            "matches --api-key, and the requested model appears in /v1/models.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
