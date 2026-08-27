#!/usr/bin/env python3
"""Check core STT runtime prerequisites from a source checkout.

Run from the checkout root, or pass --repo-root. This helper avoids hard-coded
checkout paths and performs only lightweight checks by default.
"""

from __future__ import annotations

import argparse
import importlib
from importlib import metadata
import os
import shutil
import sys
from pathlib import Path

REQUIRED_MODULES = [
    "flask",
    "requests",
    "gevent",
    "faster_whisper",
    "fsspec",
    "opencc",
    "torch",
]

DIST_NAMES = {
    "faster_whisper": "faster-whisper",
    "opencc": "opencc-python-reimplemented",
}

REQUIRED_BINARIES = ["ffmpeg", "ffprobe"]


def parse_ini(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith(";") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def check_modules() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_MODULES:
        try:
            importlib.import_module(name)
            dist_name = DIST_NAMES.get(name, name)
            try:
                version = metadata.version(dist_name)
            except metadata.PackageNotFoundError:
                version = "unknown"
            print(f"module ok: {name} ({version})")
        except Exception as exc:  # pragma: no cover - user environment dependent
            errors.append(f"cannot import {name}: {exc}")
    return errors


def check_binaries(repo_root: Path) -> list[str]:
    errors: list[str] = []
    search_path = os.pathsep.join([
        str(repo_root),
        str(repo_root / "ffmpeg"),
        os.environ.get("PATH", ""),
    ])
    for binary in REQUIRED_BINARIES:
        found = shutil.which(binary, path=search_path)
        if found:
            print(f"binary ok: {binary} -> {found}")
        else:
            errors.append(f"missing binary on PATH or under checkout/ffmpeg: {binary}")
    return errors


def maybe_import_app(repo_root: Path) -> list[str]:
    errors: list[str] = []
    sys.path.insert(0, str(repo_root))
    try:
        start = importlib.import_module("start")
        routes = sorted(str(rule) for rule in start.app.url_map.iter_rules())
        print("app import ok; routes:")
        for route in routes:
            print(f"  {route}")
    except Exception as exc:  # pragma: no cover - user environment dependent
        errors.append(f"cannot import app from checkout: {exc}")
    finally:
        try:
            sys.path.remove(str(repo_root))
        except ValueError:
            pass
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check STT app runtime prerequisites.")
    parser.add_argument("--repo-root", default=".", help="Path to an STT source checkout; defaults to the current directory.")
    parser.add_argument("--import-app", action="store_true", help="Also import the Flask app and print its route map. This may create normal runtime directories.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    print(f"repo root: {repo_root}")

    errors: list[str] = []
    if not (repo_root / "start.py").exists():
        errors.append("repo root does not contain start.py")
    if not (repo_root / "set.ini").exists():
        print("warning: set.ini not found; app defaults will be used if the source code allows it")

    values = parse_ini(repo_root / "set.ini")
    if values:
        print(f"config web_address: {values.get('web_address', '(default)')}")
        print(f"config devtype: {values.get('devtype', '(default cpu)')}")
        model_list = values.get("model_list", "")
        if model_list:
            print(f"configured models: {len([x for x in model_list.split(',') if x.strip()])}")

    errors.extend(check_modules())
    errors.extend(check_binaries(repo_root))
    if args.import_app:
        errors.extend(maybe_import_app(repo_root))

    if errors:
        print("\nRuntime check failed:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1

    print("\nRuntime check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
