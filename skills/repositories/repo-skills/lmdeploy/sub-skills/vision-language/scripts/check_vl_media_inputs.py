#!/usr/bin/env python3
"""Validate LMDeploy multimodal media inputs without model downloads or remote fetches."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from typing import Any
from urllib.parse import urlparse


class CheckError(RuntimeError):
    """Raised when a validation check fails."""


def _record(results: list[dict[str, Any]], name: str, ok: bool, detail: str) -> None:
    results.append({"name": name, "ok": ok, "detail": detail})


_SUPPORTED_MEDIA_TYPES = {
    "image_url": "image_url",
    "image": "image",
    "image_data": "image_data",
    "video_url": "video_url",
    "video": "video",
    "audio_url": "audio_url",
    "audio": "audio",
    "time_series_url": "time_series_url",
    "time_series": "time_series",
}


_ALLOWED_URL_SCHEMES = {"http", "https", "data", "file"}


def _validate_media_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in _ALLOWED_URL_SCHEMES:
        raise CheckError(f"unsupported URL scheme: {parsed.scheme}")
    if parsed.scheme in {"http", "https"} and not parsed.hostname:
        raise CheckError("HTTP(S) URL is missing a hostname")
    if parsed.scheme == "data":
        header, sep, payload = url.partition(",")
        if not sep or ";base64" not in header or not payload:
            raise CheckError("data URL must use data:<mime>;base64,<payload>")
    if not parsed.scheme and not url:
        raise CheckError("media URL/path is empty")


def _validate_content_item(item: dict[str, Any]) -> None:
    item_type = item.get("type")
    if item_type == "text":
        if not isinstance(item.get("text"), str):
            raise CheckError("text item must contain a string 'text' field")
        return
    if item_type not in _SUPPORTED_MEDIA_TYPES:
        raise CheckError(f"unsupported content type: {item_type!r}")

    field_name = _SUPPORTED_MEDIA_TYPES[item_type]
    if field_name not in item:
        raise CheckError(f"{item_type!r} item must contain {field_name!r}")

    value = item[field_name]
    if isinstance(value, str):
        _validate_media_url(value)
        return
    if isinstance(value, dict):
        data_source = value.get("url", value.get("data"))
        if isinstance(data_source, str):
            _validate_media_url(data_source)
            return
        if item_type == "image_data" and data_source is not None:
            return
    raise CheckError(f"{item_type!r} item must be a string or a dict with 'url' or 'data'")


def _validate_messages(messages: list[dict[str, Any]]) -> None:
    if not isinstance(messages, list) or not messages:
        raise CheckError("messages must be a non-empty list")
    for index, message in enumerate(messages):
        if message.get("role") not in {"system", "user", "assistant", "tool"}:
            raise CheckError(f"message {index} has an unexpected role")
        content = message.get("content", "")
        if isinstance(content, str) or content is None:
            continue
        if not isinstance(content, list):
            raise CheckError(f"message {index} content must be a string, null, or list")
        for item in content:
            if not isinstance(item, dict):
                raise CheckError(f"message {index} contains a non-dict content item")
            _validate_content_item(item)


def _build_tiny_image_data_url() -> tuple[str, tuple[int, int], str]:
    from PIL import Image

    from lmdeploy.vl import encode_image_base64, load_image

    image = Image.new("RGB", (2, 2), color=(32, 96, 160))
    encoded = encode_image_base64(image, format="PNG")
    data_url = f"data:image/png;base64,{encoded}"
    decoded = load_image(data_url)
    if decoded.size != (2, 2) or decoded.mode != "RGB":
        raise CheckError(f"unexpected decoded image: size={decoded.size}, mode={decoded.mode}")
    return data_url, decoded.size, decoded.mode


def _check_private_safe_url_helper() -> str:
    try:
        from lmdeploy.vl.media.connection import _is_safe_url
    except Exception as exc:
        return f"skipped private helper import: {exc}"

    blocked_examples = [
        "ftp://example.com/image.jpg",
        "http://127.0.0.1/image.jpg",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]/image.jpg",
    ]
    failures = []
    for url in blocked_examples:
        is_safe, reason = _is_safe_url(url)
        if is_safe:
            failures.append(url)
        elif not reason:
            failures.append(f"{url} returned an empty reason")
    if failures:
        raise CheckError(f"expected unsafe URLs to be blocked: {failures}")
    return f"blocked {len(blocked_examples)} unsafe URL examples"


def _vision_config_summary() -> dict[str, Any]:
    from lmdeploy import VisionConfig

    config = VisionConfig(max_batch_size=2)
    if is_dataclass(config):
        return asdict(config)
    return {"max_batch_size": getattr(config, "max_batch_size", None), "thread_safe": getattr(config, "thread_safe", None)}


def _example_messages(data_url: str) -> list[dict[str, Any]]:
    return [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this generated image."},
            {"type": "image_url", "image_url": {"url": data_url}},
        ],
    }]


def run_checks(print_examples: bool) -> int:
    results: list[dict[str, Any]] = []

    try:
        vision_config = _vision_config_summary()
        _record(results, "imports", True, f"lmdeploy imports; VisionConfig={vision_config}")
    except Exception as exc:
        _record(results, "imports", False, str(exc))

    data_url = ""
    try:
        data_url, size, mode = _build_tiny_image_data_url()
        _record(results, "image-data-url", True, f"decoded generated image size={size}, mode={mode}")
    except Exception as exc:
        _record(results, "image-data-url", False, str(exc))

    try:
        messages = _example_messages(data_url or "data:image/png;base64,AAAA")
        _validate_messages(messages)
        _record(results, "openai-content", True, "validated text + image_url content list")
    except Exception as exc:
        _record(results, "openai-content", False, str(exc))

    try:
        detail = _check_private_safe_url_helper()
        _record(results, "unsafe-url-examples", True, detail)
    except Exception as exc:
        _record(results, "unsafe-url-examples", False, str(exc))

    if print_examples:
        examples = {
            "tuple_prompt": "('Describe this image.', load_image('/path/to/image.jpg'))",
            "messages": _example_messages(data_url or "data:image/png;base64,..."),
            "multi_image_content": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
                    {"type": "image_url", "image_url": {"url": "/path/to/second.jpg"}},
                    {"type": "text", "text": "Compare these images."},
                ],
            }],
        }
        print(json.dumps({"examples": examples}, indent=2))

    print(json.dumps({"checks": results}, indent=2))
    return 0 if all(item["ok"] for item in results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print-examples", action="store_true", help="print representative payload examples")
    args = parser.parse_args()
    return run_checks(print_examples=args.print_examples)


if __name__ == "__main__":
    sys.exit(main())
