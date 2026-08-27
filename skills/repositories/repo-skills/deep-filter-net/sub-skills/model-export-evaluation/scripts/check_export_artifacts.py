#!/usr/bin/env python3
"""Validate a DeepFilterNet ONNX export directory without importing onnx."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

REQUIRED_CORE = ("enc.onnx", "erb_dec.onnx", "df_dec.onnx", "config.ini", "version.txt")

EXPECTED_NPZ: Dict[str, Tuple[str, ...]] = {
    "enc_input.npz": ("feat_erb", "feat_spec"),
    "enc_output.npz": ("e0", "e1", "e2", "e3", "emb", "c0", "lsnr"),
    "erb_dec_input.npz": ("emb", "e0", "e1", "e2", "e3"),
    "erb_dec_output.npz": ("m",),
    "df_dec_input.npz": ("emb", "c0"),
    "df_dec_output.npz": ("coefs",),
}

EXIT_OK = 0
EXIT_CORE_ERROR = 10
EXIT_NPZ_ERROR = 11
EXIT_TAR_ERROR = 12


def _file_error(path: Path, require_nonempty: bool = True) -> str | None:
    if not path.exists():
        return f"missing: {path.name}"
    if not path.is_file():
        return f"not a file: {path.name}"
    if require_nonempty and path.stat().st_size <= 0:
        return f"empty file: {path.name}"
    return None


def _read_version(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None
    return text or None


def check_core(export_dir: Path) -> Tuple[List[str], List[str], Dict[str, object]]:
    errors: List[str] = []
    warnings: List[str] = []
    details: Dict[str, object] = {"required_core": list(REQUIRED_CORE)}

    if not export_dir.exists():
        return [f"export directory does not exist: {export_dir}"], warnings, details
    if not export_dir.is_dir():
        return [f"export path is not a directory: {export_dir}"], warnings, details

    present = []
    for name in REQUIRED_CORE:
        err = _file_error(export_dir / name)
        if err is None:
            present.append(name)
        else:
            errors.append(err)
    details["present_core"] = present

    version_path = export_dir / "version.txt"
    if version_path.exists() and version_path.is_file():
        version_text = _read_version(version_path)
        if version_text is None:
            errors.append("version.txt is empty or unreadable")
        else:
            details["version"] = version_text
            if "_epoch_" not in version_text:
                warnings.append("version.txt does not contain the expected '_epoch_' marker")

    config_path = export_dir / "config.ini"
    if config_path.exists() and config_path.is_file() and config_path.stat().st_size <= 0:
        errors.append("config.ini is empty")

    return errors, warnings, details


def check_tar(export_dir: Path) -> Tuple[List[str], Dict[str, object]]:
    errors: List[str] = []
    archives = sorted(p.name for p in export_dir.glob("*_onnx.tar.gz") if p.is_file())
    nonempty = [name for name in archives if (export_dir / name).stat().st_size > 0]
    if not nonempty:
        errors.append("missing non-empty '*_onnx.tar.gz' archive")
    return errors, {"archives": archives, "nonempty_archives": nonempty}


def check_npz(export_dir: Path) -> Tuple[List[str], List[str], Dict[str, object]]:
    errors: List[str] = []
    warnings: List[str] = []
    details: Dict[str, object] = {"expected_npz": {k: list(v) for k, v in EXPECTED_NPZ.items()}}

    try:
        import numpy as np  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        errors.append(f"numpy import failed for --check-npz: {exc}")
        return errors, warnings, details

    inspected: Dict[str, object] = {}
    for filename, expected_keys in EXPECTED_NPZ.items():
        path = export_dir / filename
        err = _file_error(path)
        if err is not None:
            errors.append(err)
            continue
        try:
            with np.load(path) as data:
                files = tuple(data.files)
                missing = [key for key in expected_keys if key not in files]
                extra = [key for key in files if key not in expected_keys]
                if missing:
                    errors.append(f"{filename} missing arrays: {', '.join(missing)}")
                if extra:
                    warnings.append(f"{filename} has extra arrays: {', '.join(extra)}")
                arrays = {}
                for key in expected_keys:
                    if key not in files:
                        continue
                    arr = data[key]
                    arrays[key] = {"shape": list(arr.shape), "dtype": str(arr.dtype), "size": int(arr.size)}
                    if arr.size == 0:
                        errors.append(f"{filename}:{key} is empty")
                    if len(arr.shape) == 0:
                        warnings.append(f"{filename}:{key} is scalar; expected tensor-like array")
                inspected[filename] = {"arrays": arrays, "files": list(files)}
        except Exception as exc:
            errors.append(f"could not read {filename}: {exc}")
    details["inspected_npz"] = inspected
    return errors, warnings, details


def print_text(ok: bool, errors: Iterable[str], warnings: Iterable[str], details: Dict[str, object]) -> None:
    status = "OK" if ok else "FAILED"
    print(f"DeepFilterNet export artifact check: {status}")
    version = details.get("version")
    if version:
        print(f"version: {version}")
    archives = details.get("archives")
    if archives:
        print("archives: " + ", ".join(str(a) for a in archives))
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate required files in a DeepFilterNet ONNX export directory without onnx/onnxruntime.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exit codes:\n"
            "  0   validation passed\n"
            "  10  missing/invalid required core artifact\n"
            "  11  --check-npz requested and NPZ validation failed\n"
            "  12  --require-tar requested and no non-empty *_onnx.tar.gz archive was found\n\n"
            "Required core artifacts: enc.onnx, erb_dec.onnx, df_dec.onnx, config.ini, version.txt.\n"
            "With --check-npz, also requires enc/erb_dec/df_dec input and output NPZ debug files."
        ),
    )
    parser.add_argument("export_dir", type=Path, help="Directory produced by the DeepFilterNet export command.")
    parser.add_argument(
        "--check-npz",
        action="store_true",
        help="Require and inspect generated *_input.npz and *_output.npz files using numpy.",
    )
    parser.add_argument(
        "--require-tar",
        action="store_true",
        help="Require at least one non-empty '*_onnx.tar.gz' archive in the export directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print a JSON report instead of text output.")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    export_dir = args.export_dir

    errors, warnings, details = check_core(export_dir)
    exit_code = EXIT_CORE_ERROR if errors else EXIT_OK

    if args.require_tar and export_dir.exists() and export_dir.is_dir():
        tar_errors, tar_details = check_tar(export_dir)
        details.update(tar_details)
        if tar_errors:
            errors.extend(tar_errors)
            if exit_code == EXIT_OK:
                exit_code = EXIT_TAR_ERROR

    if args.check_npz and export_dir.exists() and export_dir.is_dir():
        npz_errors, npz_warnings, npz_details = check_npz(export_dir)
        warnings.extend(npz_warnings)
        details.update(npz_details)
        if npz_errors:
            errors.extend(npz_errors)
            if exit_code == EXIT_OK:
                exit_code = EXIT_NPZ_ERROR

    ok = not errors
    report = {
        "ok": ok,
        "export_dir": str(export_dir),
        "errors": errors,
        "warnings": warnings,
        "details": details,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(ok, errors, warnings, details)
    return EXIT_OK if ok else exit_code


if __name__ == "__main__":
    raise SystemExit(main())
