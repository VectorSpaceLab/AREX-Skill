#!/usr/bin/env python3
"""Validate CLaMP inference inputs without importing Muzic or loading models."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

MODEL_NAMES = ("sander-wood/clamp-small-512", "sander-wood/clamp-small-1024")
MODALS = ("music", "text")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def add_error(messages: list[str], text: str) -> None:
    messages.append("ERROR: " + text)


def add_warning(messages: list[str], text: str) -> None:
    messages.append("WARN: " + text)


def check_text_file(path: Path, label: str, messages: list[str]) -> int:
    if not path.exists():
        add_error(messages, f"{label} file is missing: {path}")
        return 0
    if not path.is_file():
        add_error(messages, f"{label} path is not a file: {path}")
        return 0
    text = read_text(path)
    if not text.strip():
        add_error(messages, f"{label} file is empty after stripping whitespace: {path}")
        return 0
    return len([line for line in text.splitlines() if line.strip()]) or 1


def check_mxl(path: Path, messages: list[str], *, allow_nonzip: bool) -> None:
    if not path.exists():
        add_error(messages, f"music file is missing: {path}")
        return
    if not path.is_file():
        add_error(messages, f"music path is not a file: {path}")
        return
    if path.stat().st_size == 0:
        add_error(messages, f"music file is empty: {path}")
        return
    if path.suffix.lower() != ".mxl":
        add_warning(messages, f"music file does not use .mxl extension: {path}")
    if not zipfile.is_zipfile(path):
        msg = f"music file is not a readable compressed .mxl zip container: {path}"
        if allow_nonzip:
            add_warning(messages, msg)
        else:
            add_error(messages, msg)
            return
    else:
        try:
            with zipfile.ZipFile(path) as zf:
                bad = zf.testzip()
                if bad:
                    add_error(messages, f"zip member failed CRC in {path}: {bad}")
        except Exception as exc:  # pragma: no cover - defensive around corrupted files
            add_error(messages, f"could not inspect .mxl zip {path}: {exc}")


def collect_music_keys(music_keys_dir: Path) -> list[Path]:
    if not music_keys_dir.exists() or not music_keys_dir.is_dir():
        return []
    return sorted(p for p in music_keys_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".mxl")


def validate(args: argparse.Namespace) -> dict[str, Any]:
    messages: list[str] = []
    details: dict[str, Any] = {
        "model_name": args.model_name,
        "query_modal": args.query_modal,
        "key_modal": args.key_modal,
        "top_n": args.top_n,
        "inference_dir": str(args.inference_dir),
        "query_count": 1,
        "key_count": 0,
        "cache_files": [],
    }

    if args.top_n < 0:
        add_error(messages, "top_n must be non-negative; source CLaMP uses 0 to mean all results")

    inference_dir = args.inference_dir
    if not inference_dir.exists():
        add_error(messages, f"inference directory is missing: {inference_dir}")
    elif not inference_dir.is_dir():
        add_error(messages, f"inference path is not a directory: {inference_dir}")

    if args.query_modal == "music":
        check_mxl(inference_dir / "music_query.mxl", messages, allow_nonzip=args.allow_nonzip_mxl)
    else:
        check_text_file(inference_dir / "text_query.txt", "text query", messages)

    if args.key_modal == "music":
        music_keys_dir = inference_dir / "music_keys"
        if not music_keys_dir.exists():
            add_error(messages, f"music key directory is missing: {music_keys_dir}")
            music_keys: list[Path] = []
        elif not music_keys_dir.is_dir():
            add_error(messages, f"music key path is not a directory: {music_keys_dir}")
            music_keys = []
        else:
            music_keys = collect_music_keys(music_keys_dir)
            if not music_keys:
                add_error(messages, f"no .mxl files found under music key directory: {music_keys_dir}")
            for path in music_keys:
                check_mxl(path, messages, allow_nonzip=args.allow_nonzip_mxl)
        details["key_count"] = len(music_keys)
        details["music_key_files"] = [str(p) for p in music_keys[: args.list_limit]]
    else:
        text_key_path = inference_dir / "text_keys.txt"
        line_count = check_text_file(text_key_path, "text keys", messages)
        if text_key_path.exists() and text_key_path.is_file():
            keys = [line.strip() for line in read_text(text_key_path).splitlines() if line.strip()]
            details["text_keys_preview"] = keys[: args.list_limit]
            details["key_count"] = len(keys)
            if not keys:
                add_error(messages, f"text key file has no non-empty key lines: {text_key_path}")
        else:
            details["key_count"] = line_count

    if args.top_n > 0 and details["key_count"] and args.top_n > details["key_count"]:
        add_warning(messages, f"top_n={args.top_n} exceeds key_count={details['key_count']}; source script will effectively return all keys")

    cache_dir = inference_dir / "cache"
    if cache_dir.exists() and cache_dir.is_dir():
        details["cache_files"] = sorted(str(p) for p in cache_dir.glob("*_key_cache_*.pth"))
    else:
        add_warning(messages, f"cache directory does not exist yet; source CLaMP will create it when writing key features: {cache_dir}")

    errors = [m for m in messages if m.startswith("ERROR:")]
    warnings = [m for m in messages if m.startswith("WARN:")]
    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "details": details,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate CLaMP inference input layout without loading Torch, Transformers, or Hugging Face assets.",
        epilog=(
            "Example: python scripts/validate_clamp_inputs.py --inference-dir inference "
            "--model-name sander-wood/clamp-small-512 --query-modal text --key-modal music --top-n 5"
        ),
    )
    parser.add_argument("--inference-dir", type=Path, default=Path("inference"), help="Directory containing CLaMP inference files; default: inference")
    parser.add_argument("--model-name", choices=MODEL_NAMES, default=MODEL_NAMES[0], help="CLaMP model name to validate")
    parser.add_argument("--query-modal", choices=MODALS, default="music", help="Query modal expected by clamp.py")
    parser.add_argument("--key-modal", choices=MODALS, default="text", help="Key modal expected by clamp.py")
    parser.add_argument("--top-n", type=int, default=10, help="Requested number of results; 0 means all in the source script")
    parser.add_argument("--allow-nonzip-mxl", action="store_true", help="Warn instead of failing when .mxl files are not readable zip containers")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--list-limit", type=int, default=10, help="Maximum key preview entries in the report")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = validate(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("CLaMP input validation:", "OK" if report["ok"] else "FAILED")
        for key, value in report["details"].items():
            if key.endswith("preview") or key.endswith("files"):
                print(f"- {key}: {len(value)} listed")
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"- {key}: {value}")
        for warning in report["warnings"]:
            print(warning)
        for error in report["errors"]:
            print(error)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
