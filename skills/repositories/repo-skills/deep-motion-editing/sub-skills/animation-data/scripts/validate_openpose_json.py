#!/usr/bin/env python3
"""Validate the OpenPose JSON directory contract used by style transfer.

This helper never rewrites files, fills missing detections, smooths points, or
runs the model. It reports the effective multiple-of-four prefix used by the
legacy loader and flags ordering/data-quality hazards before inference.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REQUIRED = {
    "pose_keypoints_2d": 25,
    "hand_left_keypoints_2d": 21,
    "hand_right_keypoints_2d": 21,
}
_FRAME_TOKEN = re.compile(r"(\d+)")


class Validation:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.files: List[Dict[str, Any]] = []

    def run(self) -> None:
        if not self.directory.is_dir():
            self.errors.append(f"not a directory: {self.directory}")
            return
        entries = sorted(self.directory.iterdir(), key=lambda item: item.name)
        json_files = [entry for entry in entries if entry.is_file() and entry.suffix.lower() == ".json"]
        other_files = [entry.name for entry in entries if entry.is_file() and entry.suffix.lower() != ".json"]
        if other_files:
            self.warnings.append(
                "non-JSON files are present and will be ignored by this validator: "
                + ", ".join(other_files[:8])
                + (" ..." if len(other_files) > 8 else "")
            )
        if not json_files:
            self.errors.append("directory contains no .json files")
            return

        frame_tokens: List[Tuple[str, Optional[int]]] = []
        for path in json_files:
            token_match = _FRAME_TOKEN.findall(path.stem)
            token = int(token_match[-1]) if token_match else None
            frame_tokens.append((path.name, token))
            self._validate_file(path, token)

        numeric = [(name, token) for name, token in frame_tokens if token is not None]
        if len(numeric) != len(frame_tokens):
            missing = [name for name, token in frame_tokens if token is None]
            self.errors.append(
                "cannot establish numeric frame order for: " + ", ".join(missing[:8])
                + (" ..." if len(missing) > 8 else "")
            )
        else:
            tokens = [token for _, token in numeric]
            duplicates = sorted({token for token in tokens if tokens.count(token) > 1})
            if duplicates:
                self.errors.append(f"duplicate numeric frame names: {duplicates[:8]}")
            gaps = [expected for expected in range(tokens[0], tokens[-1] + 1) if expected not in set(tokens)]
            if gaps:
                self.errors.append(
                    f"non-contiguous numeric frame names: missing {gaps[:8]}"
                    + (" ..." if len(gaps) > 8 else "")
                )
            if tokens != sorted(tokens):
                self.warnings.append(
                    "lexical filename order differs from numeric frame order; rename with zero-padded frame tokens"
                )

        effective = len(json_files) // 4 * 4
        if len(json_files) % 4:
            self.warnings.append(
                f"{len(json_files)} JSON files found; the legacy loader silently uses only the first {effective} files"
            )

        empty = sum(1 for item in self.files if item.get("people_count") == 0)
        if empty:
            self.warnings.append(
                f"{empty} frame(s) have no detected people; source code carries forward/backward values rather than rejecting them"
            )

    def _validate_file(self, path: Path, token: Optional[int]) -> None:
        item: Dict[str, Any] = {"file": path.name, "frame_token": token}
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.errors.append(f"{path.name}: invalid JSON or unreadable file: {exc}")
            item["error"] = str(exc)
            self.files.append(item)
            return

        if not isinstance(payload, dict):
            self.errors.append(f"{path.name}: top-level JSON value must be an object")
            self.files.append(item)
            return
        people = payload.get("people")
        if not isinstance(people, list):
            self.errors.append(f"{path.name}: missing people list")
            self.files.append(item)
            return
        item["people_count"] = len(people)
        self.files.append(item)
        if not people:
            return
        person = people[0]
        if not isinstance(person, dict):
            self.errors.append(f"{path.name}: people[0] must be an object")
            return
        for key, minimum_joints in REQUIRED.items():
            values = person.get(key)
            if not isinstance(values, list):
                self.errors.append(f"{path.name}: people[0] missing list {key}")
                continue
            required_values = minimum_joints * 3
            if len(values) < required_values:
                self.errors.append(
                    f"{path.name}: {key} has {len(values)} values; need at least {required_values} "
                    f"({minimum_joints} x [x,y,confidence])"
                )
                continue
            if len(values) % 3:
                self.warnings.append(f"{path.name}: {key} length {len(values)} is not divisible by 3")
            try:
                numeric_values = [float(value) for value in values]
            except (TypeError, ValueError):
                self.errors.append(f"{path.name}: {key} contains a non-numeric value")
                continue
            if not all(math.isfinite(value) for value in numeric_values):
                self.errors.append(f"{path.name}: {key} contains NaN or infinity")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate OpenPose body/hand JSON frames without changing files or invoking style transfer."
    )
    parser.add_argument("json_dir", type=Path, help="directory containing OpenPose .json frames")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable report")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    report = Validation(args.json_dir.expanduser())
    report.run()
    effective = len(report.files) // 4 * 4
    result = {
        "directory": str(args.json_dir.expanduser()),
        "valid": not report.errors and (not args.strict or not report.warnings),
        "errors": report.errors,
        "warnings": report.warnings,
        "json_files_checked": len(report.files),
        "effective_multiple_of_four_prefix": effective,
        "files": report.files,
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=False))
    else:
        print(f"OpenPose directory: {report.directory}")
        print(f"valid: {result['valid']}")
        print(f"JSON files checked: {len(report.files)}")
        print(f"effective multiple-of-four prefix: {effective}")
        for message in report.warnings:
            print(f"warning: {message}")
        for message in report.errors:
            print(f"error: {message}")
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
