#!/usr/bin/env python3
"""Download one explicitly selected APOD asset into a safe output directory."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download one APOD image, video, or thumbnail URL. This performs "
            "a live network request unless --dry-run is used; existing files "
            "are protected by default."
        )
    )
    parser.add_argument("url", help="explicit http(s) asset URL")
    parser.add_argument(
        "--output-dir", required=True, type=Path, help="directory that will contain the asset"
    )
    parser.add_argument(
        "--filename",
        help="plain filename within --output-dir (default: URL basename or apod-asset)",
    )
    parser.add_argument(
        "--media-type",
        choices=("image", "video", "thumbnail", "unknown"),
        default="unknown",
        help="optional caller-provided media classification for a clear video warning",
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="request timeout in seconds")
    parser.add_argument(
        "--overwrite", action="store_true", help="replace an existing destination explicitly"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="validate the target without making a network request"
    )
    return parser.parse_args()


def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must be an absolute http or https URL")


def safe_filename(url: str, requested: str | None) -> str:
    candidate = requested
    if candidate is None:
        path_name = Path(unquote(urlparse(url).path)).name
        candidate = path_name or "apod-asset"
    if candidate in {"", ".", ".."} or Path(candidate).name != candidate:
        raise ValueError("filename must be a plain filename, not a path")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", candidate):
        raise ValueError("filename may contain only letters, digits, '.', '_' and '-'")
    return candidate


def main() -> int:
    args = parse_args()
    try:
        validate_url(args.url)
        filename = safe_filename(args.url, args.filename)
        output_dir = args.output_dir.expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = (output_dir / filename).resolve()
        output_root = output_dir.resolve()
        if destination.parent != output_root:
            raise ValueError("destination escaped the selected output directory")
        if destination.exists() and not args.overwrite:
            raise FileExistsError(
                f"destination exists: {destination}; choose another filename or pass --overwrite"
            )
        if args.timeout <= 0:
            raise ValueError("--timeout must be greater than zero")
    except (OSError, ValueError, FileExistsError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"target={destination}")
    if args.media_type == "video":
        print("warning: this is marked as video; do not send the downloaded file to Pillow")
    if args.dry_run:
        print("dry-run: no network request made")
        return 0

    print("warning: live network request; verify the URL and destination before continuing")
    temporary = destination.with_name(f".{destination.name}.part-{os.getpid()}")
    try:
        with requests.get(args.url, stream=True, timeout=args.timeout) as response:
            response.raise_for_status()
            with temporary.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        handle.write(chunk)
        temporary.replace(destination)
    except (OSError, requests.RequestException) as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        print(f"error: download failed: {exc}", file=sys.stderr)
        return 1

    print(f"saved={destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
