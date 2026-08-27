#!/usr/bin/env python3
"""Validate two pytorch-fid comparison inputs without importing torch.

The helper accepts image directories and .npz statistics files, checks schema and
basic shape compatibility, and exits nonzero when the pair is not safe to pass
to pytorch-fid. It does not construct models or download weights.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

SUPPORTED_EXTENSIONS = {"bmp", "jpg", "jpeg", "pgm", "png", "ppm", "tif", "tiff", "webp"}
SUPPORTED_DIMS = {64, 192, 768, 2048}


def _json_default(value: Any) -> Any:
    try:
        import numpy as np  # type: ignore

        if isinstance(value, np.generic):
            return value.item()
    except Exception:
        pass
    return str(value)


def _finite_array(array: Any) -> Tuple[bool | None, str | None]:
    try:
        import numpy as np  # type: ignore

        return bool(np.isfinite(array).all()), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _symmetry_summary(array: Any) -> Tuple[bool | None, float | None, str | None]:
    try:
        import numpy as np  # type: ignore

        if array.ndim != 2 or array.shape[0] != array.shape[1]:
            return None, None, "not a square matrix"
        diff = array - array.T
        max_abs = float(np.max(np.abs(diff))) if diff.size else 0.0
        return bool(np.allclose(array, array.T, rtol=1e-5, atol=1e-6)), max_abs, None
    except Exception as exc:
        return None, None, f"{type(exc).__name__}: {exc}"


def _direct_image_files(path: Path) -> List[Path]:
    return sorted(
        [child for child in path.iterdir() if child.is_file() and child.suffix.lower().lstrip(".") in SUPPORTED_EXTENSIONS],
        key=lambda item: item.name,
    )


def _extension_counts(files: Iterable[Path]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for file in files:
        ext = file.suffix.lower().lstrip(".")
        counts[ext] = counts.get(ext, 0) + 1
    return dict(sorted(counts.items()))


def inspect_image_dir(path: Path, sample_limit: int) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    files = _direct_image_files(path)
    if not files:
        errors.append("directory contains no directly supported image files")
        has_subdirs = any(child.is_dir() for child in path.iterdir())
        if has_subdirs:
            warnings.append("input has subdirectories; pytorch-fid image discovery is shallow")

    uppercase_like = [
        child.name
        for child in path.iterdir()
        if child.is_file()
        and child.suffix
        and child.suffix.lstrip(".").lower() in SUPPORTED_EXTENSIONS
        and child.suffix.lstrip(".") != child.suffix.lstrip(".").lower()
    ]
    if uppercase_like:
        warnings.append("some supported extensions are uppercase; use lowercase suffixes for portable matching")

    return {
        "kind": "image_directory",
        "path": str(path),
        "exists": True,
        "file_count": len(files),
        "extension_counts": _extension_counts(files),
        "sample_files": [str(item) for item in files[:sample_limit]],
        "errors": errors,
        "warnings": warnings,
        "ok": not errors,
    }


def inspect_npz(path: Path, expected_dims: int | None) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    result: Dict[str, Any] = {
        "kind": "stats_npz",
        "path": str(path),
        "exists": True,
        "keys": [],
        "mu_shape": None,
        "sigma_shape": None,
        "mu_dtype": None,
        "sigma_dtype": None,
        "dims": None,
        "mu_finite": None,
        "sigma_finite": None,
        "sigma_square": None,
        "sigma_symmetric_ish": None,
        "sigma_symmetry_max_abs_diff": None,
        "errors": errors,
        "warnings": warnings,
    }

    try:
        import numpy as np  # type: ignore
    except Exception as exc:
        errors.append(f"numpy import failed while reading .npz: {type(exc).__name__}: {exc}")
        result["ok"] = False
        return result

    try:
        with np.load(path, allow_pickle=False) as archive:
            keys = sorted(str(key) for key in archive.files)
            result["keys"] = keys
            if "mu" not in archive.files:
                errors.append("missing required key 'mu'")
                mu = None
            else:
                mu = np.asarray(archive["mu"])
            if "sigma" not in archive.files:
                errors.append("missing required key 'sigma'")
                sigma = None
            else:
                sigma = np.asarray(archive["sigma"])
    except Exception as exc:
        errors.append(f"failed to load .npz: {type(exc).__name__}: {exc}")
        result["ok"] = False
        return result

    if mu is not None:
        result["mu_shape"] = list(mu.shape)
        result["mu_dtype"] = str(mu.dtype)
        finite, finite_error = _finite_array(mu)
        result["mu_finite"] = finite
        if finite is False:
            errors.append("mu contains non-finite values")
        if finite_error:
            errors.append(f"mu finiteness check failed: {finite_error}")
        if mu.ndim != 1:
            errors.append("mu must be one-dimensional")
        else:
            result["dims"] = int(mu.shape[0])
            if result["dims"] not in SUPPORTED_DIMS:
                warnings.append("mu length is not one of pytorch-fid's standard dims: 64, 192, 768, 2048")
            if expected_dims is not None and result["dims"] != expected_dims:
                errors.append(f"mu dimension {result['dims']} does not match expected dims {expected_dims}")

    if sigma is not None:
        result["sigma_shape"] = list(sigma.shape)
        result["sigma_dtype"] = str(sigma.dtype)
        finite, finite_error = _finite_array(sigma)
        result["sigma_finite"] = finite
        if finite is False:
            errors.append("sigma contains non-finite values")
        if finite_error:
            errors.append(f"sigma finiteness check failed: {finite_error}")
        square = bool(sigma.ndim == 2 and sigma.shape[0] == sigma.shape[1])
        result["sigma_square"] = square
        if not square:
            errors.append("sigma must be a square two-dimensional matrix")
        symmetric, max_abs, sym_error = _symmetry_summary(sigma)
        result["sigma_symmetric_ish"] = symmetric
        result["sigma_symmetry_max_abs_diff"] = max_abs
        if symmetric is False:
            warnings.append("sigma is not approximately symmetric under rtol=1e-5, atol=1e-6")
        if sym_error and square:
            warnings.append(f"sigma symmetry check failed: {sym_error}")

    if mu is not None and sigma is not None and mu.ndim == 1 and sigma.ndim == 2:
        if sigma.shape[0] != mu.shape[0] or sigma.shape[1] != mu.shape[0]:
            errors.append("sigma shape is not compatible with mu length")

    result["ok"] = not errors
    return result


def inspect_path(path_arg: str, expected_dims: int | None, sample_limit: int) -> Dict[str, Any]:
    path = Path(path_arg)
    if not path.exists():
        return {
            "kind": "missing",
            "path": str(path),
            "exists": False,
            "ok": False,
            "errors": ["path does not exist"],
            "warnings": [],
        }
    if path.is_dir():
        return inspect_image_dir(path, sample_limit)
    if path.is_file() and path.suffix.lower() == ".npz":
        return inspect_npz(path, expected_dims)
    return {
        "kind": "unsupported_file",
        "path": str(path),
        "exists": True,
        "ok": False,
        "errors": ["path is neither an image directory nor a .npz stats file"],
        "warnings": [],
    }


def build_report(path_a: str, path_b: str, expected_dims: int | None, sample_limit: int) -> Dict[str, Any]:
    pair_errors: List[str] = []
    pair_warnings: List[str] = []
    if expected_dims is not None and expected_dims not in SUPPORTED_DIMS:
        pair_errors.append("expected dims must be one of 64, 192, 768, 2048")

    inputs = [
        inspect_path(path_a, expected_dims, sample_limit),
        inspect_path(path_b, expected_dims, sample_limit),
    ]

    npz_dims = [item.get("dims") for item in inputs if item.get("kind") == "stats_npz" and item.get("dims") is not None]
    if len(npz_dims) == 2 and npz_dims[0] != npz_dims[1]:
        pair_errors.append(f"stats dimensions differ: {npz_dims[0]} vs {npz_dims[1]}")
    if expected_dims is None and npz_dims:
        pair_warnings.append(f"stats dimension inferred from .npz: {npz_dims[0]}")

    ok = not pair_errors and all(bool(item.get("ok")) for item in inputs)
    return {
        "ok": ok,
        "expected_dims": expected_dims,
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
        "supported_dims": sorted(SUPPORTED_DIMS),
        "inputs": inputs,
        "pair_errors": pair_errors,
        "pair_warnings": pair_warnings,
    }


def _print_text(report: Dict[str, Any]) -> None:
    print(f"pytorch-fid input validation: {'OK' if report['ok'] else 'ISSUES'}")
    if report.get("expected_dims") is not None:
        print(f"expected dims: {report['expected_dims']}")
    for index, item in enumerate(report["inputs"], start=1):
        print(f"input {index}: {item['path']}")
        print(f"  kind: {item['kind']}")
        if item["kind"] == "image_directory":
            print(f"  supported image count: {item['file_count']}")
            print(f"  extension counts: {item['extension_counts']}")
        elif item["kind"] == "stats_npz":
            print(f"  keys: {item['keys']}")
            print(f"  mu shape: {item['mu_shape']} dtype={item['mu_dtype']}")
            print(f"  sigma shape: {item['sigma_shape']} dtype={item['sigma_dtype']}")
            print(f"  dims: {item['dims']}")
            print(f"  finite: mu={item['mu_finite']} sigma={item['sigma_finite']}")
            print(f"  sigma square: {item['sigma_square']}")
            print(f"  sigma symmetric-ish: {item['sigma_symmetric_ish']}")
        for warning in item.get("warnings", []):
            print(f"  warning: {warning}")
        for error in item.get("errors", []):
            print(f"  error: {error}")
    for warning in report.get("pair_warnings", []):
        print(f"pair warning: {warning}")
    for error in report.get("pair_errors", []):
        print(f"pair error: {error}")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate two pytorch-fid inputs as image directories or .npz stats files without model imports."
    )
    parser.add_argument("path_a", help="First FID comparison input: image directory or .npz stats file.")
    parser.add_argument("path_b", help="Second FID comparison input: image directory or .npz stats file.")
    parser.add_argument(
        "--expected-dims",
        type=int,
        default=None,
        help="Expected Inception feature dimension: 64, 192, 768, or 2048.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=5,
        help="Maximum number of image paths to show per directory in the report.",
    )
    args = parser.parse_args(argv)

    sample_limit = max(0, args.sample_limit)
    report = build_report(args.path_a, args.path_b, args.expected_dims, sample_limit)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=_json_default))
    else:
        _print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
