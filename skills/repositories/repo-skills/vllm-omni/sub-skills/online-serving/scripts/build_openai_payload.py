#!/usr/bin/env python3
"""Build vLLM-Omni OpenAI-compatible payload examples without sending requests.

This helper is intentionally safe: it performs no network I/O, opens no media
files, and imports only Python standard-library modules. It prints a payload and
copyable guidance that a user can review before sending with curl, requests, or
an OpenAI-compatible SDK.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from collections.abc import Mapping
from typing import Any

DEFAULT_PROMPT = "A concise vLLM-Omni test prompt."
DEFAULT_BASE_URL = "http://localhost:8091"


def _json_object(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"--extra-json must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("--extra-json must decode to a JSON object")
    return parsed


def _pretty(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False)


def _quote(value: str) -> str:
    return shlex.quote(value)


def _json_curl(url: str, payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, ensure_ascii=False)
    return " \\\n".join(
        [
            "curl -sS -X POST " + _quote(url),
            "  -H " + _quote("Content-Type: application/json"),
            "  -d " + _quote(body),
        ]
    )


def _multipart_curl(url: str, fields: Mapping[str, Any], *, file_hint: str | None = None) -> str:
    lines = ["curl -sS -X POST " + _quote(url)]
    if file_hint:
        lines.append("  -F " + _quote(file_hint))
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=False)
        else:
            rendered = str(value)
        lines.append("  -F " + _quote(f"{key}={rendered}"))
    return " \\\n".join(lines)


def _split_extra_for_chat(extra: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (curl_nested_extra_body, sdk_extra_body_keyword)."""
    nested = dict(extra)
    keyword = dict(extra)
    return nested, keyword


def build_chat(args: argparse.Namespace) -> tuple[str, str, dict[str, Any], str, str]:
    nested_extra, sdk_extra = _split_extra_for_chat(args.extra_json)
    if args.image_url:
        content: Any = [
            {"type": "text", "text": args.prompt},
            {"type": "image_url", "image_url": {"url": args.image_url}},
        ]
    else:
        content = args.prompt
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": content}],
    }
    if nested_extra:
        payload["extra_body"] = nested_extra
    url = f"{args.base_url.rstrip('/')}/v1/chat/completions"
    sdk = f'''from openai import OpenAI
client = OpenAI(base_url={args.base_url.rstrip('/') + '/v1'!r}, api_key="none")
response = client.chat.completions.create(
    model={args.model!r},
    messages={payload["messages"]!r},
    extra_body={sdk_extra!r},  # SDK keyword; do not nest another extra_body key here.
)'''
    notes = (
        "curl/requests must keep Omni diffusion fields under nested JSON 'extra_body'. "
        "The OpenAI SDK uses the extra_body keyword, which is merged into the final request."
    )
    return "POST", url, payload, _json_curl(url, payload), sdk + "\n\n" + notes


def build_image(args: argparse.Namespace) -> tuple[str, str, dict[str, Any], str, str]:
    payload: dict[str, Any] = {
        "model": args.model,
        "prompt": args.prompt,
        "response_format": args.extra_json.pop("response_format", "b64_json"),
    }
    payload.update(args.extra_json)
    payload.setdefault("size", "1024x1024")
    url = f"{args.base_url.rstrip('/')}/v1/images/generations"
    sdk_standard = {
        "model": args.model,
        "prompt": args.prompt,
        "size": payload.get("size", "1024x1024"),
        "response_format": payload.get("response_format", "b64_json"),
    }
    extension_keys = sorted(k for k in payload if k not in sdk_standard)
    sdk = f'''from openai import OpenAI
client = OpenAI(base_url={args.base_url.rstrip('/') + '/v1'!r}, api_key="none")
response = client.images.generate(**{sdk_standard!r})'''
    if extension_keys:
        sdk += (
            "\n\n# Extension fields present in the curl payload: "
            + ", ".join(extension_keys)
            + "\n# If your OpenAI SDK version does not pass these fields, use direct HTTP instead."
        )
    return "POST", url, payload, _json_curl(url, payload), sdk


def build_image_edit(args: argparse.Namespace) -> tuple[str, str, dict[str, Any], str, str]:
    fields: dict[str, Any] = {
        "model": args.model,
        "prompt": args.prompt,
    }
    if args.image_url:
        fields["url"] = [args.image_url]
    fields.update(args.extra_json)
    fields.setdefault("size", "1024x1024")
    fields.setdefault("output_format", "png")
    url = f"{args.base_url.rstrip('/')}/v1/images/edits"
    file_hint = None if args.image_url else "image=@input.png"
    curl = _multipart_curl(url, fields, file_hint=file_hint)
    sdk_extra = dict(args.extra_json)
    if args.image_url:
        sdk_extra["url"] = [args.image_url]
    sdk = f'''from openai import OpenAI
client = OpenAI(base_url={args.base_url.rstrip('/') + '/v1'!r}, api_key="none")
# For URL/data references:
result = client.images.edit(
    image=[],
    model={args.model!r},
    prompt={args.prompt!r},
    size={fields.get('size')!r},
    output_format={fields.get('output_format')!r},
    extra_body={sdk_extra!r},
)
# For local files, prefer direct multipart HTTP or pass file handles if your SDK version supports them.'''
    return "POST", url, fields, curl, sdk


def build_speech(args: argparse.Namespace) -> tuple[str, str, dict[str, Any], str, str]:
    payload: dict[str, Any] = {
        "model": args.model,
        "input": args.prompt,
        "voice": args.voice,
        "response_format": args.extra_json.pop("response_format", "wav"),
    }
    payload.update(args.extra_json)
    url = f"{args.base_url.rstrip('/')}/v1/audio/speech"
    sdk_standard = {
        "model": args.model,
        "voice": args.voice,
        "input": args.prompt,
        "response_format": payload.get("response_format", "wav"),
    }
    extra_for_sdk = {k: v for k, v in payload.items() if k not in sdk_standard}
    sdk = f'''from openai import OpenAI
client = OpenAI(base_url={args.base_url.rstrip('/') + '/v1'!r}, api_key="none")
response = client.audio.speech.create(**{sdk_standard!r})
# For vLLM-Omni TTS extensions such as task_type, language, ref_audio,
# ref_text, stream, or stream_format, use direct HTTP or SDK extra_body
# if supported by your OpenAI client version: {extra_for_sdk!r}'''
    return "POST", url, payload, _json_curl(url, payload), sdk


def build_video(args: argparse.Namespace) -> tuple[str, str, dict[str, Any], str, str]:
    fields: dict[str, Any] = {
        "model": args.model,
        "prompt": args.prompt,
    }
    if args.image_url:
        fields["image_reference"] = {"image_url": args.image_url}
    fields.update(args.extra_json)
    fields.setdefault("size", "832x480")
    fields.setdefault("num_frames", 80)
    fields.setdefault("fps", 16)
    url = f"{args.base_url.rstrip('/')}/v1/videos"
    file_hint = None if args.image_url else "input_reference=@input.png  # optional; remove for text-to-video"
    curl = _multipart_curl(url, fields, file_hint=file_hint)
    sdk = '''# vLLM-Omni video generation is a multipart HTTP job API.
# Use direct HTTP (curl or requests/httpx) to create the job, then poll:
#   GET /v1/videos/{video_id}
#   GET /v1/videos/{video_id}/content
# Do not combine input_reference with image_reference/video_reference for the same request.'''
    return "POST", url, fields, curl, sdk


BUILDERS = {
    "chat": build_chat,
    "image": build_image,
    "image-edit": build_image_edit,
    "speech": build_speech,
    "video": build_video,
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build safe no-network vLLM-Omni OpenAI-compatible payload examples.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--endpoint", required=True, choices=sorted(BUILDERS), help="Endpoint family to scaffold")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Text prompt or TTS input")
    parser.add_argument("--model", default="MODEL", help="Served model name; should match the server")
    parser.add_argument("--extra-json", type=_json_object, default={}, help="Extra JSON object merged into the endpoint payload")
    parser.add_argument("--image-url", default=None, help="Optional HTTP(S) or data URL image reference for chat/edit/video examples")
    parser.add_argument("--voice", default="vivian", help="Speech voice for --endpoint speech")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Server base URL used only in printed examples")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output text guidance or machine-readable JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    # Builders may pop defaults from extra_json; isolate the parsed object so
    # repeated use in tests or embeddings cannot mutate caller state.
    args.extra_json = dict(args.extra_json)
    method, url, payload, curl, sdk = BUILDERS[args.endpoint](args)

    if args.format == "json":
        print(_pretty({
            "endpoint_family": args.endpoint,
            "method": method,
            "url": url,
            "payload_or_form_fields": payload,
            "curl_template": curl,
            "python_guidance": sdk,
            "safety": "No HTTP request was sent and no media files were read.",
        }))
        return 0

    print("# vLLM-Omni OpenAI-compatible payload scaffold")
    print("# Safety: this script did not send an HTTP request and did not read media files.")
    print(f"endpoint_family: {args.endpoint}")
    print(f"method: {method}")
    print(f"url: {url}")
    print()
    print("## Payload / form fields")
    print(_pretty(payload))
    print()
    print("## curl template (copy manually after review)")
    print(curl)
    print()
    print("## OpenAI SDK / Python guidance")
    print(sdk)
    print()
    print("# Reminder: start the server with --omni and verify /health before sending live requests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
