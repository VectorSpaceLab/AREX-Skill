#!/usr/bin/env python3
"""Call the OpenAI-compatible LightX2V image endpoints."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
from pathlib import Path
from typing import Any

import requests


def _save_bytes(data: bytes, output: str) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _read_file(path_str: str) -> tuple[str, bytes, str]:
    path = Path(path_str)
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return path.name, path.read_bytes(), mime_type


def _write_openai_response(response: requests.Response, output: str) -> Path | None:
    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return _save_bytes(response.content, output)

    body = response.json()
    data = body.get("data") or []
    if not data:
        print(json.dumps(body, ensure_ascii=False, indent=2, default=str))
        return None

    first = data[0]
    if "b64_json" in first:
        return _save_bytes(base64.b64decode(first["b64_json"]), output)
    if "url" in first:
        image = requests.get(first["url"], timeout=120)
        image.raise_for_status()
        return _save_bytes(image.content, output)

    print(json.dumps(body, ensure_ascii=False, indent=2, default=str))
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Call OpenAI-compatible LightX2V image endpoints")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base server URL")
    parser.add_argument("--mode", choices=["generate", "edit"], default="generate", help="Endpoint mode")
    parser.add_argument("--prompt", required=True, help="Prompt text")
    parser.add_argument("--image-path", default="", help="Image file used for edits")
    parser.add_argument("--mask-path", default="", help="Mask file used for edits")
    parser.add_argument("--n", type=int, default=1, help="Number of images; LightX2V currently supports 1")
    parser.add_argument("--size", default="1024x1024", help="Requested size in WxH form")
    parser.add_argument("--response-format", choices=["b64_json", "url"], default="b64_json", help="OpenAI response format")
    parser.add_argument("--seed", type=int, default=None, help="Optional seed")
    parser.add_argument("--negative-prompt", default="", help="Optional negative prompt for edits")
    parser.add_argument("--output", default="save_results/openai_image.png", help="Local output path")
    args = parser.parse_args()

    base = args.url.rstrip("/")

    if args.mode == "generate":
        payload: dict[str, Any] = {
            "prompt": args.prompt,
            "n": args.n,
            "size": args.size,
            "response_format": args.response_format,
        }
        if args.seed is not None:
            payload["seed"] = args.seed
        response = requests.post(f"{base}/v1/images/generations", json=payload, timeout=1200)
        response.raise_for_status()
        path = _write_openai_response(response, args.output)
        if path is not None:
            print(f"Saved image to: {path}")
        return 0

    files: dict[str, Any] = {}
    if args.image_path:
        files["image"] = _read_file(args.image_path)
    if args.mask_path:
        files["mask"] = _read_file(args.mask_path)

    data = {
        "prompt": args.prompt,
        "n": str(args.n),
        "size": args.size,
        "response_format": args.response_format,
        "negative_prompt": args.negative_prompt,
    }
    if args.seed is not None:
        data["seed"] = str(args.seed)

    response = requests.post(f"{base}/v1/images/edits", data=data, files=files or None, timeout=1200)
    response.raise_for_status()
    path = _write_openai_response(response, args.output)
    if path is not None:
        print(f"Saved image to: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
