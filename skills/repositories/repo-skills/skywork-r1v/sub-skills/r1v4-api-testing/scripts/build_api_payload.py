#!/usr/bin/env python3
"""Build a no-network OpenAI-compatible payload for Skywork R1V4 batch tests."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_BASE_URL = "https://api.skyworkmodel.ai"
DEFAULT_ENDPOINT = "/api/v1/chat/completions"
DEFAULT_API_KEY_ENV = "SKYWORK_API_KEY"


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean value: {value!r}")


def _infer_mime_type(image_path: Path, explicit: Optional[str] = None) -> str:
    if explicit:
        return explicit
    guessed, _ = mimetypes.guess_type(str(image_path))
    if guessed:
        return guessed
    raise ValueError(
        f"could not infer a MIME type for {image_path}; pass --mime-type explicitly"
    )


def _to_data_url(image: str, mime_type: Optional[str] = None) -> str:
    if not image:
        return ""
    if image.startswith("data:"):
        return image

    image_path = Path(image).expanduser()
    if not image_path.exists():
        raise FileNotFoundError(f"image file not found: {image}")

    mime = _infer_mime_type(image_path, explicit=mime_type)
    raw = image_path.read_bytes()
    encoded = base64.b64encode(raw).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def build_payload(
    image: str,
    question: str,
    model: str,
    stream: bool,
    enable_search: bool,
    base_url: str = DEFAULT_BASE_URL,
    endpoint: str = DEFAULT_ENDPOINT,
    api_key_env: str = DEFAULT_API_KEY_ENV,
    mime_type: Optional[str] = None,
) -> Dict[str, Any]:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string")

    content = []
    encoded_image = ""
    image_source = "none"

    if image:
        encoded_image = _to_data_url(image, mime_type=mime_type)
        image_source = "data-url" if image.startswith("data:") else "file"
        content.append({"type": "image_url", "image_url": {"url": encoded_image}})

    content.append({"type": "text", "text": question})

    payload = {
        "messages": [{"role": "user", "content": content}],
        "model": model,
        "stream": stream,
        "enable_search": enable_search,
    }

    return {
        "request": {
            "base_url": base_url,
            "endpoint": endpoint,
            "url": f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}",
            "method": "POST",
            "headers_template": {
                "Content-Type": "application/json",
                "Authorization": "Bearer <API_KEY_FROM_ENV_OR_CALLER_CONFIG>",
            },
            "auth_env_var": api_key_env,
        },
        "payload": payload,
        "input": {
            "image": image,
            "image_source": image_source,
            "question": question,
            "model": model,
            "stream": stream,
            "enable_search": enable_search,
            "image_encoded": bool(encoded_image),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a Skywork R1V4 OpenAI-compatible payload without sending any network request.",
    )
    parser.add_argument("--image", default="", help="Image file path or already-encoded data URL.")
    parser.add_argument("--question", required=True, help="Question text.")
    parser.add_argument(
        "--model",
        default="skywork/r1v4-lite",
        help="Model name to place in the payload.",
    )
    parser.add_argument(
        "--stream",
        type=parse_bool,
        default=False,
        help="Set the payload stream flag to true or false.",
    )
    parser.add_argument(
        "--enable-search",
        type=parse_bool,
        default=False,
        help="Set the payload enable_search flag to true or false.",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Base API URL.",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help="API endpoint path.",
    )
    parser.add_argument(
        "--api-key-env",
        default=DEFAULT_API_KEY_ENV,
        help="Name of the environment variable that should provide the bearer token.",
    )
    parser.add_argument(
        "--mime-type",
        default=None,
        help="Explicit MIME type when the image extension is not enough.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional file path for the JSON output. Defaults to stdout.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of pretty-printed JSON.",
    )
    args = parser.parse_args()

    result = build_payload(
        image=args.image,
        question=args.question,
        model=args.model,
        stream=args.stream,
        enable_search=args.enable_search,
        base_url=args.base_url,
        endpoint=args.endpoint,
        api_key_env=args.api_key_env,
        mime_type=args.mime_type,
    )

    json_text = json.dumps(
        result,
        ensure_ascii=False,
        indent=None if args.compact else 2,
    )

    if args.output:
        Path(args.output).write_text(json_text + "\n", encoding="utf-8")
    else:
        print(json_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
