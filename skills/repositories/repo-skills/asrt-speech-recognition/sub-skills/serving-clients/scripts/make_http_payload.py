#!/usr/bin/env python3
"""Build ASRT HTTP JSON payloads without importing ASRT.

The ASRT HTTP server expects raw WAV sample-frame bytes encoded as URL-safe
base64 text plus WAV metadata. This helper reads user-provided WAV files with
Python's standard wave module only.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import wave
from pathlib import Path
from typing import Any, Dict, Iterable, List

AUDIO_ENDPOINTS = {"/speech", "/all"}
LANGUAGE_ENDPOINTS = {"/language"}
ROOT_ENDPOINTS = {"/"}
ALL_ENDPOINTS = sorted(AUDIO_ENDPOINTS | LANGUAGE_ENDPOINTS | ROOT_ENDPOINTS)


def read_wav_payload(path: Path) -> Dict[str, Any]:
    """Read WAV sample frames and metadata for ASRT's HTTP JSON API."""
    try:
        with wave.open(str(path), "rb") as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            byte_width = wav_file.getsampwidth()
    except wave.Error as exc:
        raise SystemExit(f"error: {path} is not a readable WAV file: {exc}") from exc
    except OSError as exc:
        raise SystemExit(f"error: cannot read {path}: {exc}") from exc

    samples = base64.urlsafe_b64encode(frames).decode("ascii")
    return {
        "samples": samples,
        "sample_rate": sample_rate,
        "channels": channels,
        "byte_width": byte_width,
    }


def normalize_pinyins(values: Iterable[str] | None) -> List[str]:
    """Return non-empty pinyin syllables from repeated args or comma text."""
    if values is None:
        return []
    result: List[str] = []
    for value in values:
        for item in value.split(","):
            item = item.strip()
            if item:
                result.append(item)
    return result


def build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    endpoint = args.endpoint
    if endpoint in AUDIO_ENDPOINTS:
        if args.wav is None:
            raise SystemExit(f"error: --wav is required for endpoint {endpoint}")
        return read_wav_payload(args.wav)
    if endpoint in LANGUAGE_ENDPOINTS:
        pinyins = normalize_pinyins(args.sequence_pinyin)
        if not pinyins:
            raise SystemExit("error: --sequence-pinyin is required for endpoint /language")
        return {"sequence_pinyin": pinyins}
    if endpoint in ROOT_ENDPOINTS:
        return {}
    raise SystemExit(f"error: unsupported endpoint {endpoint!r}")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an ASRT HTTP JSON payload from a WAV file or pinyin sequence.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--endpoint",
        choices=ALL_ENDPOINTS,
        required=True,
        help="ASRT HTTP endpoint whose request body should be constructed.",
    )
    parser.add_argument(
        "--wav",
        type=Path,
        help="WAV file for /speech or /all. Raw sample frames are encoded, not the WAV container.",
    )
    parser.add_argument(
        "--sequence-pinyin",
        nargs="*",
        metavar="PINYIN",
        help="Pinyin syllables for /language. Values may also contain comma-separated syllables.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON with indentation instead of a compact single line.",
    )
    parser.add_argument(
        "--ensure-ascii",
        action="store_true",
        help="Escape non-ASCII characters in JSON output.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    payload = build_payload(args)
    indent = 2 if args.pretty else None
    text = json.dumps(payload, ensure_ascii=args.ensure_ascii, indent=indent)
    sys.stdout.write(text)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
