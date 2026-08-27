#!/usr/bin/env python3
"""Validate a NAVSIM workspace without network, deletion, imports, or workloads.

The validator intentionally uses only environment variables and filesystem
metadata. It does not read project configuration, open pickle/image files, or
create directories. Use --require-files when selected log/sensor roots should
also contain at least one regular file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

REQUIRED_ENV = (
    "NUPLAN_MAP_VERSION",
    "NUPLAN_MAPS_ROOT",
    "NAVSIM_EXP_ROOT",
    "NAVSIM_DEVKIT_ROOT",
    "OPENSCENE_DATA_ROOT",
)

# (original data split, synthetic bundle name or None)
SPLITS: Dict[str, Tuple[str, Optional[str]]] = {
    "mini": ("mini", None),
    "navmini": ("mini", None),
    "trainval": ("trainval", None),
    "navtrain": ("trainval", None),
    "test": ("test", None),
    "navtest": ("test", None),
    "navtest_two_stage": ("test", None),
    "navhard_two_stage": ("test", "navhard_two_stage"),
    # navsafe uses the public two-stage test assets but a narrower filter.
    "navsafe_two_stage": ("test", "navhard_two_stage"),
    "warmup_two_stage": ("test", "warmup_two_stage"),
    "private_test_hard_two_stage": ("private_test_hard", "private_test_hard_two_stage"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check NAVSIM environment variables and split-root layout. "
            "No network, deletion, imports, or benchmark work is performed."
        )
    )
    parser.add_argument("--split", choices=sorted(SPLITS), default="mini")
    parser.add_argument(
        "--require-files",
        action="store_true",
        help="require each selected log/sensor directory to contain a regular file",
    )
    parser.add_argument(
        "--md5",
        action="append",
        metavar="FILE=HEX",
        help="also verify an existing file against an MD5 hex digest; repeatable",
    )
    parser.add_argument("--json", action="store_true", help="emit one JSON result instead of human output")
    return parser.parse_args()


def parse_md5_specs(specs: Optional[Iterable[str]]) -> Tuple[List[Tuple[Path, str]], List[str]]:
    checks: List[Tuple[Path, str]] = []
    errors: List[str] = []
    for spec in specs or []:
        if "=" not in spec:
            errors.append(f"invalid --md5 value {spec!r}; use FILE=HEX")
            continue
        filename, digest = spec.rsplit("=", 1)
        digest = digest.lower()
        if len(digest) != 32 or any(c not in "0123456789abcdef" for c in digest):
            errors.append(f"invalid MD5 digest for {filename!r}")
            continue
        checks.append((Path(filename).expanduser(), digest))
    return checks, errors


def has_regular_file(path: Path) -> bool:
    try:
        return any(item.is_file() for item in path.rglob("*"))
    except OSError:
        return False


def md5sum(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checked_paths(env: Dict[str, str], split: str) -> List[Tuple[str, Path]]:
    data_root = Path(env["OPENSCENE_DATA_ROOT"]).expanduser()
    maps_root = Path(env["NUPLAN_MAPS_ROOT"]).expanduser()
    exp_root = Path(env["NAVSIM_EXP_ROOT"]).expanduser()
    original_split, bundle = SPLITS[split]
    paths: List[Tuple[str, Path]] = [
        ("maps root", maps_root),
        ("experiment root", exp_root),
        (f"original logs ({original_split})", data_root / "navsim_logs" / original_split),
        (f"original sensors ({original_split})", data_root / "sensor_blobs" / original_split),
    ]
    if bundle is not None:
        bundle_root = data_root / bundle
        paths.extend(
            [
                (f"{bundle} synthetic sensors", bundle_root / "sensor_blobs"),
                (f"{bundle} synthetic scene pickles", bundle_root / "synthetic_scene_pickles"),
            ]
        )
    return paths


def main() -> int:
    args = parse_args()
    errors: List[str] = []
    warnings: List[str] = []
    statuses: List[Dict[str, object]] = []

    env: Dict[str, str] = {}
    for name in REQUIRED_ENV:
        value = os.environ.get(name, "").strip()
        if not value:
            errors.append(f"missing required environment variable: {name}")
        else:
            env[name] = value

    if env.get("NUPLAN_MAP_VERSION") and env["NUPLAN_MAP_VERSION"] != "nuplan-maps-v1.0":
        errors.append(
            "NUPLAN_MAP_VERSION must be nuplan-maps-v1.0 for NAVSIM v2.0.0 "
            f"(got {env['NUPLAN_MAP_VERSION']!r})"
        )

    if len(env) == len(REQUIRED_ENV):
        for label, path in checked_paths(env, args.split):
            exists = path.is_dir()
            is_data_root = label.startswith("original ") or "synthetic" in label
            file_ok = (not args.require_files) or not is_data_root or has_regular_file(path)
            ok = exists and file_ok
            reason = "OK" if ok else ("missing directory" if not exists else "no regular files")
            statuses.append({"label": label, "path": str(path), "ok": ok, "detail": reason})
            if not ok:
                errors.append(f"{label}: {path} ({reason})")

    checks, md5_errors = parse_md5_specs(args.md5)
    errors.extend(md5_errors)
    for path, expected in checks:
        if not path.is_file():
            errors.append(f"MD5 file missing: {path}")
            statuses.append({"label": "md5", "path": str(path), "ok": False, "detail": "missing file"})
            continue
        actual = md5sum(path)
        ok = actual == expected
        statuses.append({"label": "md5", "path": str(path), "ok": ok, "detail": actual})
        if not ok:
            errors.append(f"MD5 mismatch: {path} expected {expected}, got {actual}")

    passed = not errors
    result = {
        "split": args.split,
        "environment": {name: env.get(name, "") for name in REQUIRED_ENV},
        "paths": statuses,
        "warnings": warnings,
        "errors": errors,
        "passed": passed,
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"NAVSIM workspace validation: split={args.split}")
        for name in REQUIRED_ENV:
            value = env.get(name)
            print(f"  {'OK' if value else 'ERROR'} env {name}" + (f"={value}" if value else ""))
        for item in statuses:
            print(f"  {'OK' if item['ok'] else 'ERROR'} {item['label']}: {item['path']} ({item['detail']})")
        for warning in warnings:
            print(f"  WARNING {warning}")
        for error in errors:
            print(f"  ERROR {error}")
        print("VALIDATION PASSED" if passed else "VALIDATION FAILED")
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(main())
