#!/usr/bin/env python3
"""Safely validate local multimodal asset paths for InternGPT workflows.

This helper performs only static checks: path presence, file-ness, extension
class, and ImageBind wrapper input grammar. It intentionally imports no model
packages, performs no downloads, and starts no services.

Examples:
  python validate_multimodal_assets.py --audio ./sound.wav --thermal ./thermal.jpg
  python validate_multimodal_assets.py --tool AudioText2Image --tool-input './sound.wav, a rainy street'
  python validate_multimodal_assets.py --tool AudioImage2Image --tool-input './image.jpg,./sound.wav'
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

SUPPORTED_EXTENSIONS = {
    "audio": {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"},
    "image": {".jpg", ".jpeg", ".png", ".bmp", ".webp"},
    "thermal": {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"},
    "video": {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"},
}

IMAGEBIND_TOOLS = {
    "Anything2Image",
    "Audio2Image",
    "Thermal2Image",
    "AudioImage2Image",
    "AudioText2Image",
}


def _looks_remote(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith(("http://", "https://", "s3://", "gs://", "hf://"))


def _validate_path(kind: str, raw_path: str, allow_missing: bool) -> dict:
    item = {
        "kind": kind,
        "path": raw_path,
        "ok": True,
        "errors": [],
        "warnings": [],
    }
    if raw_path is None or not str(raw_path).strip():
        item["ok"] = False
        item["errors"].append("empty path")
        return item

    raw_path = str(raw_path).strip()
    if _looks_remote(raw_path):
        item["ok"] = False
        item["errors"].append("remote URI supplied; expected a local file path")
        return item

    path = Path(raw_path).expanduser()
    suffix = path.suffix.lower()
    supported = SUPPORTED_EXTENSIONS[kind]
    if suffix not in supported:
        item["ok"] = False
        item["errors"].append(
            f"unsupported {kind} extension {suffix or '<none>'}; expected one of {sorted(supported)}"
        )

    if not path.exists():
        message = "path does not exist"
        if allow_missing:
            item["warnings"].append(message)
        else:
            item["ok"] = False
            item["errors"].append(message)
    elif not path.is_file():
        item["ok"] = False
        item["errors"].append("path exists but is not a file")

    return item


def _validate_many(kind: str, paths: Iterable[str], allow_missing: bool) -> list[dict]:
    return [_validate_path(kind, p, allow_missing) for p in paths or []]


def _parse_tool_input(tool: str, tool_input: str, allow_missing: bool) -> list[dict]:
    if tool not in IMAGEBIND_TOOLS:
        return [{"kind": "tool", "path": tool, "ok": False, "errors": ["unknown ImageBind tool"], "warnings": []}]

    if tool == "Anything2Image":
        return [
            {
                "kind": "tool",
                "path": tool,
                "ok": True,
                "errors": [],
                "warnings": ["foundation model only; it has no direct inference input string"],
            }
        ]

    if tool_input is None or not tool_input.strip():
        return [{"kind": "tool_input", "path": "", "ok": False, "errors": ["empty tool input"], "warnings": []}]

    raw = tool_input.strip()
    if tool == "Audio2Image":
        return _validate_many("audio", [raw], allow_missing)

    if tool == "Thermal2Image":
        return _validate_many("thermal", [raw], allow_missing)

    if tool == "AudioImage2Image":
        pieces = [p.strip() for p in raw.split(",")]
        if len(pieces) != 2 or not all(pieces):
            return [
                {
                    "kind": "tool_input",
                    "path": raw,
                    "ok": False,
                    "errors": ["AudioImage2Image expects exactly 'image_path,audio_path'"],
                    "warnings": [],
                }
            ]
        image_path, audio_path = pieces
        return _validate_many("image", [image_path], allow_missing) + _validate_many("audio", [audio_path], allow_missing)

    if tool == "AudioText2Image":
        if "," not in raw:
            return [
                {
                    "kind": "tool_input",
                    "path": raw,
                    "ok": False,
                    "errors": ["AudioText2Image expects 'audio_path,prompt' with at least one comma"],
                    "warnings": [],
                }
            ]
        audio_path, prompt = [p.strip() for p in raw.split(",", 1)]
        results = _validate_many("audio", [audio_path], allow_missing)
        if not prompt:
            results.append(
                {
                    "kind": "prompt",
                    "path": prompt,
                    "ok": False,
                    "errors": ["empty prompt after first comma"],
                    "warnings": [],
                }
            )
        return results

    raise AssertionError(f"unhandled tool {tool}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate local audio/image/thermal/video asset paths and ImageBind wrapper input grammar without model imports."
    )
    parser.add_argument("--audio", nargs="*", default=[], help="Local audio file path(s), e.g. WAV/MP3/FLAC.")
    parser.add_argument("--image", nargs="*", default=[], help="Local ordinary image file path(s), e.g. JPG/PNG.")
    parser.add_argument("--thermal", nargs="*", default=[], help="Local thermal image file path(s), image-like extensions expected.")
    parser.add_argument("--video", nargs="*", default=[], help="Local video file path(s), e.g. MP4/MOV/MKV.")
    parser.add_argument("--tool", choices=sorted(IMAGEBIND_TOOLS), help="Validate the input grammar for one ImageBind generation tool.")
    parser.add_argument("--tool-input", help="Tool input string to validate with --tool.")
    parser.add_argument("--allow-missing", action="store_true", help="Warn instead of failing when a path does not exist.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results: list[dict] = []
    results += _validate_many("audio", args.audio, args.allow_missing)
    results += _validate_many("image", args.image, args.allow_missing)
    results += _validate_many("thermal", args.thermal, args.allow_missing)
    results += _validate_many("video", args.video, args.allow_missing)

    if args.tool:
        results += _parse_tool_input(args.tool, args.tool_input, args.allow_missing)
    elif args.tool_input:
        results.append(
            {
                "kind": "tool_input",
                "path": args.tool_input,
                "ok": False,
                "errors": ["--tool-input requires --tool"],
                "warnings": [],
            }
        )

    if not results:
        results.append(
            {
                "kind": "usage",
                "path": "",
                "ok": False,
                "errors": ["provide at least one asset path or --tool/--tool-input pair"],
                "warnings": [],
            }
        )

    all_ok = all(item["ok"] for item in results)
    payload = {"ok": all_ok, "results": results}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for item in results:
            status = "OK" if item["ok"] else "ERROR"
            subject = item["path"] or item["kind"]
            print(f"[{status}] {item['kind']}: {subject}")
            for warning in item["warnings"]:
                print(f"  warning: {warning}")
            for error in item["errors"]:
                print(f"  error: {error}")
        print(f"Overall: {'ok' if all_ok else 'failed'}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
