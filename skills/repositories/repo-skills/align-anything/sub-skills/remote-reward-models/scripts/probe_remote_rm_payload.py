#!/usr/bin/env python3
"""Probe a remote reward-model endpoint and validate its payload contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

DEFAULT_PROMPT = "How many vertical asymptotes does the graph of y=2/(x^2+x-6) have?"
DEFAULT_RESPONSE = "<think>Factor the denominator.</think><answer>2</answer>"
DEFAULT_GOLDEN_RESPONSE = "2"


def load_payload(args: argparse.Namespace) -> dict:
    if args.payload_file:
        return json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
    if args.payload_json:
        return json.loads(args.payload_json)

    prompts = args.prompt if args.prompt is not None else [DEFAULT_PROMPT]
    responses = args.response if args.response is not None else [DEFAULT_RESPONSE]
    payload: dict = {
        "prompts": prompts,
        "responses": responses,
    }
    if args.golden_response is not None:
        payload["golden_responses"] = args.golden_response
    return payload


def validate_payload(payload: dict) -> None:
    if "prompts" not in payload or "responses" not in payload:
        raise ValueError("payload must contain prompts and responses")
    if not isinstance(payload["prompts"], list) or not isinstance(payload["responses"], list):
        raise ValueError("prompts and responses must be lists")
    if not all(isinstance(item, str) for item in payload["prompts"]):
        raise ValueError("all prompts must be strings")
    if not all(isinstance(item, str) for item in payload["responses"]):
        raise ValueError("all responses must be strings")
    if len(payload["prompts"]) != len(payload["responses"]):
        raise ValueError("prompts and responses must have the same length")
    if "golden_responses" in payload:
        if not isinstance(payload["golden_responses"], list):
            raise ValueError("golden_responses must be a list when provided")
        if not all(isinstance(item, str) for item in payload["golden_responses"]):
            raise ValueError("all golden_responses must be strings")
        if len(payload["golden_responses"]) != len(payload["prompts"]):
            raise ValueError("golden_responses must match prompt count when provided")


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe a remote reward endpoint")
    parser.add_argument(
        "--endpoint",
        default="http://127.0.0.1:6000/get_reward",
        help="Remote reward endpoint",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP request timeout in seconds",
    )
    parser.add_argument(
        "--expect-status",
        type=int,
        default=200,
        help="Expected HTTP status code",
    )
    parser.add_argument(
        "--payload-json",
        help="Raw JSON payload string to send instead of building one",
    )
    parser.add_argument(
        "--payload-file",
        help="Path to a JSON payload file to send instead of building one",
    )
    parser.add_argument(
        "--prompt",
        action="append",
        help="Prompt text. Repeat to send multiple rows.",
    )
    parser.add_argument(
        "--response",
        action="append",
        help="Model response text. Repeat to send multiple rows.",
    )
    parser.add_argument(
        "--golden-response",
        action="append",
        dest="golden_response",
        help="Optional gold answer row. Repeat to mirror prompts.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS verification for HTTPS endpoints.",
    )
    parser.add_argument(
        "--show-request",
        action="store_true",
        help="Print the final request body before sending it.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print the payload without sending an HTTP request.",
    )
    args = parser.parse_args()

    try:
        payload = load_payload(args)
        validate_payload(payload)
    except Exception as exc:  # pragma: no cover - validation error path
        print(f"Payload validation failed: {exc}", file=sys.stderr)
        return 2

    if args.show_request or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    if args.dry_run:
        print("Payload validated; HTTP request skipped because --dry-run was set.")
        return 0

    try:
        response = requests.post(
            args.endpoint,
            json=payload,
            timeout=args.timeout,
            verify=not args.insecure,
            headers={"Content-Type": "application/json"},
        )
    except requests.RequestException as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 3

    print(f"HTTP {response.status_code}")
    try:
        body = response.json()
    except ValueError:
        body = {"raw": response.text}
    print(json.dumps(body, indent=2, ensure_ascii=False))

    if response.status_code != args.expect_status:
        print(
            f"Expected HTTP {args.expect_status}, got HTTP {response.status_code}",
            file=sys.stderr,
        )
        return 1

    if response.status_code == 200:
        rewards = body.get("rewards")
        if not isinstance(rewards, list):
            print("Response did not contain a rewards list", file=sys.stderr)
            return 1
        expected = len(payload["prompts"])
        if len(rewards) != expected:
            print(
                f"Reward count {len(rewards)} does not match prompt count {expected}",
                file=sys.stderr,
            )
            return 1
        print("Remote reward payload validated.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
