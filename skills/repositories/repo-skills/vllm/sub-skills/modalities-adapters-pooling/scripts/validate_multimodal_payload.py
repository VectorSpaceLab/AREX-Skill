#!/usr/bin/env python3
"""Statically inspect vLLM/OpenAI-style multimodal JSON payloads.

The script does not import vLLM, open media files, or download URLs. It walks a
JSON payload, finds image/audio/video URL references, checks local-file and
remote-domain allowlists, and prints suggested vLLM allowlist flags.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

MEDIA_URL_KEYS = {
    "image_url",
    "audio_url",
    "video_url",
    "url",
}
MEDIA_PART_TYPES = {
    "image_url",
    "audio_url",
    "video_url",
    "input_audio",
    "image",
    "video",
}
SUPPORTED_SCHEMES = {"data", "http", "https", "file"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a JSON payload for vLLM multimodal media URL issues and "
            "suggest --allowed-local-media-path/--allowed-media-domains flags."
        )
    )
    parser.add_argument(
        "payload",
        type=Path,
        help="Path to an OpenAI/vLLM-style JSON request payload.",
    )
    parser.add_argument(
        "--allowed-local-media-path",
        type=Path,
        default=None,
        help="Configured local media root. file:// URLs must resolve under it.",
    )
    parser.add_argument(
        "--allowed-media-domain",
        action="append",
        default=[],
        help="Allowed remote media hostname. Repeat for multiple domains.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser


def load_payload(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as file_obj:
            return json.load(file_obj)
    except FileNotFoundError as exc:
        raise SystemExit(f"payload not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc


def walk(value: Any, path: str = "$"):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def media_url_from_value(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        url = value.get("url")
        if isinstance(url, str):
            return url
    return None


def looks_like_media_string(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith(("data:", "http://", "https://", "file://"))


def collect_media_refs(payload: Any) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    refs: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []

    for path, obj in walk(payload):
        part_type = obj.get("type") if isinstance(obj.get("type"), str) else None
        if "content" in obj and isinstance(obj["content"], str):
            if any(marker in obj["content"] for marker in ("image_url", "file://", "data:")):
                warnings.append(
                    f"{path}.content is a string that appears to contain media; "
                    "OpenAI multimodal content should usually be a list of parts."
                )

        if part_type in MEDIA_PART_TYPES:
            if part_type == "input_audio":
                audio = obj.get("input_audio") or obj.get("audio_url")
                url = media_url_from_value(audio)
            else:
                url = media_url_from_value(obj.get(part_type))
                if url is None and part_type in {"image", "video"}:
                    url = media_url_from_value(obj.get(f"{part_type}_url"))
            if url is None:
                errors.append(f"{path} has media type {part_type!r} but no URL field")
            else:
                refs.append({"path": path, "part_type": part_type, "url": url})

        for key in MEDIA_URL_KEYS:
            if key not in obj:
                continue
            url = media_url_from_value(obj[key])
            if url is None or not looks_like_media_string(url):
                continue
            if any(ref["path"] == f"{path}.{key}" or ref["url"] == url for ref in refs):
                continue
            refs.append({"path": f"{path}.{key}", "part_type": key, "url": url})

    return refs, errors, warnings


def resolved_file_path(parsed_url) -> Path:
    netloc = parsed_url.netloc or ""
    raw_path = unquote((netloc + parsed_url.path) or "")
    return Path(raw_path).expanduser().resolve(strict=False)


def is_subpath(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def analyze_refs(
    refs: list[dict[str, Any]],
    allowed_local_media_path: Path | None,
    allowed_media_domains: set[str],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    local_files: list[str] = []
    remote_domains: list[str] = []
    data_urls = 0
    unsupported: list[str] = []

    local_root = (
        allowed_local_media_path.expanduser().resolve(strict=False)
        if allowed_local_media_path is not None
        else None
    )

    for ref in refs:
        url = ref["url"]
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme not in SUPPORTED_SCHEMES:
            unsupported.append(url)
            errors.append(
                f"{ref['path']} uses unsupported URL scheme {scheme!r}; "
                "vLLM media URLs should be data:, http(s):, or file:."
            )
            continue

        if scheme == "data":
            data_urls += 1
            if ";base64," not in url[:128].lower():
                errors.append(
                    f"{ref['path']} is a data URL but does not advertise base64 data."
                )
            continue

        if scheme in {"http", "https"}:
            hostname = parsed.hostname or ""
            if hostname:
                remote_domains.append(hostname)
            if allowed_media_domains and hostname not in allowed_media_domains:
                errors.append(
                    f"{ref['path']} remote domain {hostname!r} is not in "
                    "--allowed-media-domain."
                )
            elif not allowed_media_domains:
                warnings.append(
                    f"{ref['path']} uses remote media domain {hostname!r}; "
                    "consider --allowed-media-domains for SSRF protection."
                )
            continue

        if scheme == "file":
            file_path = resolved_file_path(parsed)
            local_files.append(str(file_path))
            if local_root is None:
                errors.append(
                    f"{ref['path']} uses local file {file_path}; configure "
                    "--allowed-local-media-path."
                )
            elif not is_subpath(file_path, local_root):
                errors.append(
                    f"{ref['path']} local file {file_path} is outside allowed root "
                    f"{local_root}."
                )

    suggested_domains = sorted(set(remote_domains))
    required_flags: dict[str, Any] = {}
    if local_files:
        required_flags["allowed_local_media_path"] = str(local_root) if local_root else None
    if suggested_domains:
        required_flags["allowed_media_domains"] = suggested_domains

    return {
        "errors": errors,
        "warnings": warnings,
        "local_files": sorted(set(local_files)),
        "remote_domains": suggested_domains,
        "data_url_count": data_urls,
        "unsupported_urls": unsupported,
        "required_flags": required_flags,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = load_payload(args.payload)
    refs, shape_errors, shape_warnings = collect_media_refs(payload)
    analysis = analyze_refs(
        refs,
        args.allowed_local_media_path,
        set(args.allowed_media_domain),
    )

    errors = shape_errors + analysis.pop("errors")
    warnings = shape_warnings + analysis.pop("warnings")
    result = {
        "ok": not errors,
        "media_count": len(refs),
        "media_refs": refs,
        **analysis,
        "errors": errors,
        "warnings": warnings,
    }

    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
