#!/usr/bin/env python3
"""Generate or validate a MOSS FastAPI demo request payload without contacting a server."""

from __future__ import annotations

import argparse
import json
import uuid
from typing import Any, Dict, Optional


def validate_number(name: str, value: float, low: float, high: float) -> None:
    if not (low <= value <= high):
        raise ValueError(f"{name} must be between {low} and {high}, got {value}")


def payload(prompt: str, uid: Optional[str], max_length: int, top_p: float, temperature: float) -> Dict[str, Any]:
    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    if max_length <= 0:
        raise ValueError("max_length must be positive")
    validate_number("top_p", top_p, 0.0, 1.0)
    validate_number("temperature", temperature, 0.0, 1.0)
    return {
        "prompt": prompt,
        "uid": uid or str(uuid.uuid4()),
        "max_length": max_length,
        "top_p": top_p,
        "temperature": temperature,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a JSON payload and optional curl snippet for a MOSS FastAPI demo server.")
    parser.add_argument("--prompt", required=True, help="User prompt sent to the API demo's POST / endpoint.")
    parser.add_argument("--uid", help="Conversation uid. Omit to generate a fresh uid.")
    parser.add_argument("--max-length", type=int, default=2048, help="max_length field passed through to model.generate.")
    parser.add_argument("--top-p", type=float, default=0.8, help="Nucleus sampling top_p value.")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature.")
    parser.add_argument("--url", default="http://127.0.0.1:19324/", help="Server URL for the optional curl snippet.")
    parser.add_argument("--curl", action="store_true", help="Also print a curl command. The command is not executed.")
    args = parser.parse_args()

    try:
        body = payload(args.prompt, args.uid, args.max_length, args.top_p, args.temperature)
    except ValueError as exc:
        print(f"invalid MOSS request: {exc}")
        return 2

    encoded = json.dumps(body, ensure_ascii=False)
    print(json.dumps(body, ensure_ascii=False, indent=2, sort_keys=True))
    if args.curl:
        print("\n# curl snippet (does not run here):")
        print("curl -sS -X POST " + json.dumps(args.url) + " -H 'Content-Type: application/json' -d " + json.dumps(encoded))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
