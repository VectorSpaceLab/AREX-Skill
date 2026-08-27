#!/usr/bin/env python3
"""Read-only ClawBio package/output diagnostic.

This helper deliberately has no dependency on the ClawBio checkout. It can be
run from any current directory against an output bundle produced by either an
installed wheel or a source checkout.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_status() -> dict[str, Any]:
    spec = importlib.util.find_spec("clawbio")
    if spec is None:
        return {"installed": False, "message": "clawbio is not importable"}
    return {
        "installed": True,
        "origin": str(spec.origin or "unknown"),
        "message": "clawbio import spec found",
    }


def _check_output(
    output: Path,
    *,
    require_report: bool,
    require_result: bool,
    verify_checksums: bool,
) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {"output": str(output.resolve()), "files": []}

    if not output.exists():
        return [f"output does not exist: {output}"], warnings, details
    if not output.is_dir():
        return [f"output is not a directory: {output}"], warnings, details

    files = sorted(str(path.relative_to(output)) for path in output.rglob("*") if path.is_file())
    details["files"] = files

    report = output / "report.md"
    result = output / "result.json"
    if require_report and not report.is_file():
        errors.append("required report.md is missing")
    elif not report.is_file():
        warnings.append("report.md is absent (the selected skill may not emit one)")
    elif not report.read_text(encoding="utf-8", errors="replace").strip():
        errors.append("report.md exists but is empty")

    payload: dict[str, Any] | None = None
    if require_result and not result.is_file():
        errors.append("required result.json is missing")
    elif result.is_file():
        try:
            parsed = json.loads(result.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"result.json is not valid JSON: {exc}")
        else:
            if not isinstance(parsed, dict):
                errors.append("result.json top level is not an object")
            else:
                payload = parsed
                details["result_keys"] = sorted(parsed)
                for key in ("skill", "version", "completed_at", "summary", "data"):
                    if key not in parsed:
                        warnings.append(f"result.json lacks common key: {key}")
    elif not require_result:
        warnings.append("result.json is absent (the selected skill may not emit one)")

    checksum_file = output / "reproducibility" / "checksums.sha256"
    details["reproducibility"] = checksum_file.parent.is_dir()
    if checksum_file.is_file() and verify_checksums:
        checked = 0
        for line_number, line in enumerate(checksum_file.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                expected, label = line.split(None, 1)
                label = label.strip()
                if label.startswith("*"):
                    label = label[1:].lstrip()
            except ValueError:
                errors.append(f"checksums.sha256 line {line_number} is malformed")
                continue
            target = output / label
            if not target.is_file():
                errors.append(f"checksum target is missing: {label}")
                continue
            actual = _sha256(target)
            checked += 1
            if actual.lower() != expected.lower():
                errors.append(f"checksum mismatch: {label}")
        details["checksums_checked"] = checked
    elif checksum_file.is_file():
        warnings.append("checksums.sha256 found; rerun with --verify-checksums to verify it")
    else:
        warnings.append("reproducibility/checksums.sha256 is absent")

    return errors, warnings, details


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only diagnostic for a ClawBio output bundle or local package."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output bundle to inspect; relative paths are resolved from the current directory.",
    )
    parser.add_argument("--require-report", action="store_true", help="Fail if report.md is absent.")
    parser.add_argument("--require-result", action="store_true", help="Fail if result.json is absent or invalid.")
    parser.add_argument(
        "--verify-checksums",
        action="store_true",
        help="Verify reproducibility/checksums.sha256 when present.",
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit a machine-readable diagnostic.")
    args = parser.parse_args(argv)

    errors: list[str] = []
    warnings: list[str] = []
    report: dict[str, Any] = {"package": _package_status()}
    if args.output is not None:
        output_errors, output_warnings, details = _check_output(
            args.output.expanduser(),
            require_report=args.require_report,
            require_result=args.require_result,
            verify_checksums=args.verify_checksums,
        )
        errors.extend(output_errors)
        warnings.extend(output_warnings)
        report["output"] = details
    else:
        warnings.append("no --output supplied; package diagnostic only")

    report["ok"] = not errors
    report["errors"] = errors
    report["warnings"] = warnings
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        package = report["package"]
        print(f"package: {'OK' if package.get('installed') else 'MISSING'} ({package['message']})")
        if args.output is not None:
            print(f"output: {'OK' if not errors else 'FAILED'} ({args.output.expanduser()})")
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
