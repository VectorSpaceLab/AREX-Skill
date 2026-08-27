#!/usr/bin/env python3
"""Inspect pytorch-fid .npz statistics files without importing torch.

The helper reports mu/sigma shapes, inferred dimensions, finite values, and
covariance sanity checks. It does not construct models or download weights.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

SUPPORTED_DIMS = {64, 192, 768, 2048}


def _json_default(value: Any) -> Any:
    try:
        import numpy as np  # type: ignore

        if isinstance(value, np.generic):
            return value.item()
    except Exception:
        pass
    return str(value)


def inspect_file(path_arg: str, expected_dims: int | None = None) -> Dict[str, Any]:
    path = Path(path_arg)
    errors: List[str] = []
    warnings: List[str] = []
    report: Dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "suffix": path.suffix,
        "keys": [],
        "mu_shape": None,
        "mu_dtype": None,
        "sigma_shape": None,
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

    if not path.exists():
        errors.append("path does not exist")
        report["ok"] = False
        return report
    if not path.is_file():
        errors.append("path is not a file")
        report["ok"] = False
        return report
    if path.suffix.lower() != ".npz":
        warnings.append("file suffix is not .npz; attempting NumPy archive load anyway")

    try:
        import numpy as np  # type: ignore
    except Exception as exc:
        errors.append(f"numpy import failed: {type(exc).__name__}: {exc}")
        report["ok"] = False
        return report

    try:
        with np.load(path, allow_pickle=False) as archive:
            report["keys"] = sorted(str(key) for key in archive.files)
            mu = np.asarray(archive["mu"]) if "mu" in archive.files else None
            sigma = np.asarray(archive["sigma"]) if "sigma" in archive.files else None
    except KeyError as exc:
        errors.append(f"missing required key: {exc}")
        report["ok"] = False
        return report
    except Exception as exc:
        errors.append(f"failed to load archive: {type(exc).__name__}: {exc}")
        report["ok"] = False
        return report

    if mu is None:
        errors.append("missing required key 'mu'")
    else:
        report["mu_shape"] = list(mu.shape)
        report["mu_dtype"] = str(mu.dtype)
        try:
            report["mu_finite"] = bool(np.isfinite(mu).all())
        except Exception as exc:
            errors.append(f"mu finiteness check failed: {type(exc).__name__}: {exc}")
        if report["mu_finite"] is False:
            errors.append("mu contains non-finite values")
        if mu.ndim != 1:
            errors.append("mu must be one-dimensional")
        else:
            report["dims"] = int(mu.shape[0])
            if report["dims"] not in SUPPORTED_DIMS:
                warnings.append("mu length is not one of pytorch-fid's standard dims: 64, 192, 768, 2048")
            if expected_dims is not None and report["dims"] != expected_dims:
                errors.append(f"mu dimension {report['dims']} does not match expected dims {expected_dims}")

    if sigma is None:
        errors.append("missing required key 'sigma'")
    else:
        report["sigma_shape"] = list(sigma.shape)
        report["sigma_dtype"] = str(sigma.dtype)
        try:
            report["sigma_finite"] = bool(np.isfinite(sigma).all())
        except Exception as exc:
            errors.append(f"sigma finiteness check failed: {type(exc).__name__}: {exc}")
        if report["sigma_finite"] is False:
            errors.append("sigma contains non-finite values")
        square = bool(sigma.ndim == 2 and sigma.shape[0] == sigma.shape[1])
        report["sigma_square"] = square
        if not square:
            errors.append("sigma must be a square two-dimensional matrix")
        if square:
            try:
                diff = sigma - sigma.T
                report["sigma_symmetry_max_abs_diff"] = float(np.max(np.abs(diff))) if diff.size else 0.0
                report["sigma_symmetric_ish"] = bool(np.allclose(sigma, sigma.T, rtol=1e-5, atol=1e-6))
            except Exception as exc:
                warnings.append(f"sigma symmetry check failed: {type(exc).__name__}: {exc}")
            if report["sigma_symmetric_ish"] is False:
                warnings.append("sigma is not approximately symmetric under rtol=1e-5, atol=1e-6")

    if mu is not None and sigma is not None and mu.ndim == 1 and sigma.ndim == 2:
        if sigma.shape[0] != mu.shape[0] or sigma.shape[1] != mu.shape[0]:
            errors.append("sigma shape is not compatible with mu length")

    report["ok"] = not errors
    return report


def build_report(paths: List[str], expected_dims: int | None = None) -> Dict[str, Any]:
    pair_errors: List[str] = []
    if expected_dims is not None and expected_dims not in SUPPORTED_DIMS:
        pair_errors.append("expected dims must be one of 64, 192, 768, 2048")
    files = [inspect_file(path, expected_dims=expected_dims) for path in paths]
    dims = [item.get("dims") for item in files if item.get("dims") is not None]
    if len(set(dims)) > 1:
        pair_errors.append("not all stats files have the same inferred dimension")
    return {
        "ok": not pair_errors and all(bool(item.get("ok")) for item in files),
        "expected_dims": expected_dims,
        "supported_dims": sorted(SUPPORTED_DIMS),
        "files": files,
        "pair_errors": pair_errors,
    }


def _print_text(report: Dict[str, Any]) -> None:
    print(f"pytorch-fid stats inspection: {'OK' if report['ok'] else 'ISSUES'}")
    if report.get("expected_dims") is not None:
        print(f"expected dims: {report['expected_dims']}")
    for item in report["files"]:
        print(f"file: {item['path']}")
        print(f"  keys: {item['keys']}")
        print(f"  mu shape: {item['mu_shape']} dtype={item['mu_dtype']}")
        print(f"  sigma shape: {item['sigma_shape']} dtype={item['sigma_dtype']}")
        print(f"  dims: {item['dims']}")
        print(f"  finite: mu={item['mu_finite']} sigma={item['sigma_finite']}")
        print(f"  sigma square: {item['sigma_square']}")
        print(f"  sigma symmetric-ish: {item['sigma_symmetric_ish']}")
        if item.get("sigma_symmetry_max_abs_diff") is not None:
            print(f"  sigma symmetry max abs diff: {item['sigma_symmetry_max_abs_diff']}")
        for warning in item.get("warnings", []):
            print(f"  warning: {warning}")
        for error in item.get("errors", []):
            print(f"  error: {error}")
    for error in report.get("pair_errors", []):
        print(f"pair error: {error}")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize one or more pytorch-fid .npz stats files without importing torch."
    )
    parser.add_argument("paths", nargs="+", help="One or more .npz stats files to inspect.")
    parser.add_argument(
        "--expected-dims",
        type=int,
        default=None,
        help="Optional expected feature dimension: 64, 192, 768, or 2048.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    args = parser.parse_args(argv)

    report = build_report(args.paths, expected_dims=args.expected_dims)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=_json_default))
    else:
        _print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
