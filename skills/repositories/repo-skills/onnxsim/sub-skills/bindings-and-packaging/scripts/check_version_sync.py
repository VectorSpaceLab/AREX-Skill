#!/usr/bin/env python3
"""Safely verify onnxsim binding version synchronization.

The checker is read-only. It compares the expected version (by default the root
VERSION file) with Rust workspace/dependency versions and the npm package version
when present. It never invokes git and never mutates files.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class CheckResult:
    name: str
    path: Path
    actual: Optional[str]
    expected: str
    required: bool = True
    note: str = ""

    @property
    def ok(self) -> bool:
        return self.actual == self.expected

    @property
    def missing(self) -> bool:
        return self.actual is None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_root_version(repo_root: Path) -> str:
    version_path = repo_root / "VERSION"
    try:
        version = read_text(version_path).strip()
    except FileNotFoundError as exc:
        raise SystemExit(f"ERROR: required version file not found: {version_path}") from exc
    if not version:
        raise SystemExit(f"ERROR: required version file is empty: {version_path}")
    return version.removeprefix("v")


def find_section(text: str, section: str) -> str:
    """Return the TOML-ish body for a top-level or dotted section."""
    header = f"[{section}]"
    start = text.find(header)
    if start < 0:
        return ""
    body_start = start + len(header)
    match = re.search(r"(?m)^\[[^\]]+\]", text[body_start:])
    if match:
        return text[body_start : body_start + match.start()]
    return text[body_start:]


def parse_section_version(path: Path, section: str) -> Optional[str]:
    try:
        body = find_section(read_text(path), section)
    except FileNotFoundError:
        return None
    match = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"\s*(?:#.*)?$', body)
    return match.group(1).removeprefix("v") if match else None


def parse_dependency_inline_version(path: Path, dep_name: str) -> Optional[str]:
    try:
        text = read_text(path)
    except FileNotFoundError:
        return None
    pattern = rf'(?m)^\s*{re.escape(dep_name)}\s*=\s*\{{[^\n}}]*\bversion\s*=\s*"([^"]+)"[^\n}}]*\}}'
    match = re.search(pattern, text)
    return match.group(1).removeprefix("v") if match else None


def parse_json_version(path: Path) -> Optional[str]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: invalid JSON in {path}: {exc}") from exc
    version = data.get("version")
    if not isinstance(version, str) or not version.strip():
        raise SystemExit(f"ERROR: package JSON has no string version: {path}")
    return version.strip().removeprefix("v")


def build_checks(repo_root: Path, expected: str) -> list[CheckResult]:
    checks: list[CheckResult] = []

    version_file = repo_root / "VERSION"
    checks.append(
        CheckResult(
            "VERSION",
            version_file,
            read_root_version(repo_root),
            expected,
            required=True,
        )
    )

    rust_workspace = repo_root / "rust" / "Cargo.toml"
    checks.append(
        CheckResult(
            "rust/Cargo.toml [workspace.package] version",
            rust_workspace,
            parse_section_version(rust_workspace, "workspace.package"),
            expected,
            required=True,
        )
    )

    rust_safe = repo_root / "rust" / "onnxsim" / "Cargo.toml"
    checks.append(
        CheckResult(
            "rust/onnxsim dependency on onnxsim-sys",
            rust_safe,
            parse_dependency_inline_version(rust_safe, "onnxsim-sys"),
            expected,
            required=True,
        )
    )

    npm_package = repo_root / "npm" / "onnxsim" / "package.json"
    checks.append(
        CheckResult(
            "npm/onnxsim/package.json version",
            npm_package,
            parse_json_version(npm_package),
            expected,
            required=False,
            note="npm package not present; skipped",
        )
    )

    return checks


def print_results(checks: Iterable[CheckResult]) -> int:
    status = 0
    for check in checks:
        rel = check.path.as_posix()
        if check.missing:
            if check.required:
                print(f"MISSING: {check.name} ({rel})")
                status = 1
            else:
                print(f"SKIP: {check.name} ({check.note})")
            continue
        if check.ok:
            print(f"OK: {check.name} is '{check.actual}'")
        else:
            print(
                f"MISMATCH: {check.name} is '{check.actual}', "
                f"expected '{check.expected}'"
            )
            status = 1
    return status


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read onnxsim VERSION, Rust Cargo manifests, and optional npm package "
            "metadata, then report version mismatches without modifying files."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Path to an onnxsim repository root or unpacked source tree (default: cwd).",
    )
    parser.add_argument(
        "--expected-version",
        help=(
            "Version to compare against. Defaults to the root VERSION file. "
            "A leading 'v' is ignored."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    expected = (
        args.expected_version.removeprefix("v")
        if args.expected_version
        else read_root_version(repo_root)
    )
    print(f"Expected version: {expected}")
    checks = build_checks(repo_root, expected)
    return print_results(checks)


if __name__ == "__main__":
    sys.exit(main())
