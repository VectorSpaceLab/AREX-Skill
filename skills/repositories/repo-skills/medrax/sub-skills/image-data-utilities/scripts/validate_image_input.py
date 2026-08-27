#!/usr/bin/env python3
"""Safely validate a CXR image/DICOM path and an optional output directory.

The validator checks path metadata, conventional suffixes, and a few file
signature bytes. It intentionally does not decode pixels or parse DICOM tags,
so it does not inspect PHI. It is a preflight check, not a medical-image
validator.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

IMAGE_SIGNATURES = {
    ".png": b"\x89PNG\r\n\x1a\n",
    ".jpg": b"\xff\xd8",
    ".jpeg": b"\xff\xd8",
}
DICOM_SUFFIXES = {".dcm", ".dicom"}
SUPPORTED_SUFFIXES = set(IMAGE_SIGNATURES) | DICOM_SUFFIXES


def _read_prefix(path: Path, count: int, offset: int = 0) -> bytes:
    """Read a small non-PHI prefix without decoding the file."""

    with path.open("rb") as handle:
        if offset:
            handle.seek(offset)
        return handle.read(count)


def _check_signature(path: Path, suffix: str, result: Dict[str, Any]) -> None:
    """Add lightweight signature errors/warnings to *result*.

    DICOM files without a Part 10 preamble can still be valid, so a missing
    ``DICM`` marker is a warning rather than a rejection. Pixel readability is
    deliberately left to the DICOM decoder.
    """

    try:
        if suffix in IMAGE_SIGNATURES:
            signature = IMAGE_SIGNATURES[suffix]
            prefix = _read_prefix(path, len(signature))
            if not prefix.startswith(signature):
                result["errors"].append(
                    f"{suffix} signature mismatch; the file may be mislabeled or truncated"
                )
            return

        if suffix in DICOM_SUFFIXES:
            if path.stat().st_size < 4:
                result["errors"].append("DICOM file is empty or too short to contain data")
                return
            marker = _read_prefix(path, 4, offset=128)
            if marker != b"DICM":
                result["warnings"].append(
                    "DICOM preamble marker DICM was not found; some valid DICOM files omit it; "
                    "pixel decoding is still unverified"
                )
    except OSError as exc:
        result["errors"].append(f"could not read a lightweight file signature: {exc}")


def _check_output_dir(output_dir: Path) -> Dict[str, Any]:
    """Check a caller-provided directory without creating or deleting files."""

    check: Dict[str, Any] = {
        "path": str(output_dir),
        "exists": output_dir.exists(),
        "is_directory": output_dir.is_dir(),
        "writable": False,
        "errors": [],
    }
    if not check["exists"]:
        check["errors"].append("output directory does not exist")
        return check
    if not check["is_directory"]:
        check["errors"].append("output path exists but is not a directory")
        return check

    try:
        mode = output_dir.stat().st_mode
        has_write_bit = bool(mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
        check["writable"] = bool(has_write_bit and os.access(output_dir, os.W_OK))
    except OSError as exc:
        check["errors"].append(f"could not inspect output directory permissions: {exc}")
        return check

    if not check["writable"]:
        check["errors"].append("output directory is not writable by the current process")
    return check


def validate_input(input_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Validate an input path and optionally its output directory.

    Only path metadata and a few magic bytes are read. The result is suitable
    for human or JSON output and contains no decoded DICOM metadata.
    """

    path = Path(input_path).expanduser()
    suffix = path.suffix.lower()
    result: Dict[str, Any] = {
        "path": str(path),
        "suffix": suffix,
        "kind": "dicom" if suffix in DICOM_SUFFIXES else "image" if suffix in IMAGE_SIGNATURES else None,
        "exists": path.exists(),
        "is_file": path.is_file(),
        "errors": [],
        "warnings": [],
    }

    if not result["exists"]:
        result["errors"].append("input path does not exist")
    elif not result["is_file"]:
        result["errors"].append("input path exists but is not a regular file")

    if suffix not in SUPPORTED_SUFFIXES:
        result["errors"].append(
            "unsupported suffix; expected .png, .jpg, .jpeg, .dcm, or .dicom"
        )

    if result["is_file"] and suffix in SUPPORTED_SUFFIXES:
        _check_signature(path, suffix, result)

    if output_dir is not None:
        result["output_directory"] = _check_output_dir(Path(output_dir).expanduser())
        result["errors"].extend(
            f"output directory: {error}"
            for error in result["output_directory"]["errors"]
        )

    result["ok"] = not result["errors"]
    return result


def _self_test() -> Dict[str, Any]:
    """Run deterministic, dependency-free fixture and error checks."""

    with tempfile.TemporaryDirectory(prefix="image-data-utilities-") as temp:
        root = Path(temp)
        valid_png = root / "valid.png"
        valid_jpg = root / "valid.jpg"
        valid_dcm = root / "valid.dcm"
        malformed_png = root / "malformed.png"
        valid_png.write_bytes(b"\x89PNG\r\n\x1a\nfixture")
        valid_jpg.write_bytes(b"\xff\xd8\xff\xd9")
        valid_dcm.write_bytes(b"\x00" * 128 + b"DICM" + b"fixture")
        malformed_png.write_bytes(b"not-an-image")

        cases = {
            "png": validate_input(str(valid_png), str(root)),
            "jpg": validate_input(str(valid_jpg)),
            "dicom": validate_input(str(valid_dcm)),
            "missing": validate_input(str(root / "missing.png")),
            "bad_signature": validate_input(str(malformed_png)),
            "bad_suffix": validate_input(str(root / "note.txt")),
        }
        expected_valid = {"png", "jpg", "dicom"}
        for name in expected_valid:
            if not cases[name]["ok"]:
                raise AssertionError(f"self-test expected {name} to pass: {cases[name]}")
        for name in {"missing", "bad_signature", "bad_suffix"}:
            if cases[name]["ok"]:
                raise AssertionError(f"self-test expected {name} to fail: {cases[name]}")
        if not cases["png"]["output_directory"]["writable"]:
            raise AssertionError("self-test expected temporary output directory to be writable")

        return {"ok": True, "cases": sorted(cases), "message": "self-test passed"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check a PNG/JPG/DICOM path and optionally an output directory. "
            "Reads only path metadata and lightweight signatures; does not parse PHI."
        )
    )
    parser.add_argument("input", nargs="?", help="image or DICOM path to validate")
    parser.add_argument(
        "--output-dir",
        help="optional existing directory that must be writable for generated output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the result as indented JSON",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run deterministic temporary-fixture and error checks",
    )
    return parser


def _print_result(result: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    if result.get("message"):
        print(result["message"])
        return

    status = "OK" if result.get("ok") else "INVALID"
    print(f"{status}: {result.get('path', '<input>')}")
    if result.get("kind"):
        print(f"kind: {result['kind']} (suffix {result.get('suffix') or '<none>'})")
    for warning in result.get("warnings", []):
        print(f"warning: {warning}")
    for error in result.get("errors", []):
        print(f"error: {error}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.self_test:
        if args.input or args.output_dir:
            parser.error("--self-test cannot be combined with an input or --output-dir")
        try:
            result = _self_test()
        except AssertionError as exc:
            result = {"ok": False, "message": f"self-test failed: {exc}"}
            _print_result(result, args.json)
            return 1
        _print_result(result, args.json)
        return 0

    if not args.input:
        parser.error("an input path is required unless --self-test is used")
    result = validate_input(args.input, args.output_dir)
    _print_result(result, args.json)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
