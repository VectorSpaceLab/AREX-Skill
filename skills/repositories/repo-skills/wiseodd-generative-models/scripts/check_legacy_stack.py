#!/usr/bin/env python3
"""Check compatibility risks for the legacy Generative Models scripts.

The helper performs safe import and behavior probes only. It does not download
MNIST, execute training loops, write model outputs, or mutate the environment.

Examples:
  python scripts/check_legacy_stack.py
  python scripts/check_legacy_stack.py --strict
  python scripts/check_legacy_stack.py --repo-root /path/to/generative-models
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
from typing import Any, Dict, List


def result(name: str, status: str, detail: str, severity: str = "info") -> Dict[str, str]:
    return {"name": name, "status": status, "severity": severity, "detail": detail}


def probe_numpy() -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    try:
        np = importlib.import_module("numpy")
    except Exception as exc:  # pragma: no cover - diagnostic path
        return [result("numpy-import", "fail", f"numpy import failed: {type(exc).__name__}: {exc}", "error")]
    out.append(result("numpy-import", "pass", f"numpy {getattr(np, '__version__', 'unknown')} imported"))
    for alias in ("float", "int"):
        if hasattr(np, alias):
            out.append(result(f"numpy-alias-{alias}", "pass", f"np.{alias} is available"))
        else:
            out.append(result(
                f"numpy-alias-{alias}",
                "warn",
                f"np.{alias} is missing; unmodified legacy scripts using np.{alias} need a patch or older NumPy",
                "warning",
            ))
    return out


def probe_tensorflow() -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    try:
        tf = importlib.import_module("tensorflow")
    except Exception as exc:  # pragma: no cover - diagnostic path
        return [result("tensorflow-import", "fail", f"tensorflow import failed: {type(exc).__name__}: {exc}", "error")]
    out.append(result("tensorflow-import", "pass", f"tensorflow {getattr(tf, '__version__', 'unknown')} imported"))
    try:
        importlib.import_module("tensorflow.examples.tutorials.mnist.input_data")
    except Exception as exc:
        out.append(result(
            "tensorflow-examples-mnist-loader",
            "warn",
            "legacy tensorflow.examples.tutorials.mnist.input_data is unavailable; most scripts need TF1-style loader compatibility or a modern loader patch "
            f"({type(exc).__name__}: {exc})",
            "warning",
        ))
    else:
        out.append(result("tensorflow-examples-mnist-loader", "pass", "legacy TensorFlow MNIST loader is importable"))
    return out


def probe_torch() -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    try:
        torch = importlib.import_module("torch")
    except Exception as exc:  # pragma: no cover - diagnostic path
        return [result("torch-import", "warn", f"torch import failed: {type(exc).__name__}: {exc}", "warning")]
    out.append(result("torch-import", "pass", f"torch {getattr(torch, '__version__', 'unknown')} imported"))
    try:
        _ = torch.tensor(1.0).data[0]
    except Exception as exc:
        out.append(result(
            "torch-scalar-data-indexing",
            "warn",
            "legacy loss.data[0] scalar indexing fails; PyTorch scripts with that pattern need .item() patches or older torch "
            f"({type(exc).__name__}: {exc})",
            "warning",
        ))
    else:
        out.append(result("torch-scalar-data-indexing", "pass", "legacy .data[0] scalar indexing works"))
    try:
        cuda_available = bool(torch.cuda.is_available())
        if cuda_available:
            device_count = int(torch.cuda.device_count())
            detail = f"cuda_available=True, device_count={device_count}"
            status = "pass"
        else:
            detail = "cuda_available=False, device_count=n/a"
            status = "info"
        out.append(result("torch-cuda", status, detail))
    except Exception as exc:
        out.append(result("torch-cuda", "warn", f"could not query CUDA: {type(exc).__name__}: {exc}", "warning"))
    return out


def probe_matplotlib() -> List[Dict[str, str]]:
    try:
        mpl = importlib.import_module("matplotlib")
    except Exception as exc:  # pragma: no cover - diagnostic path
        return [result("matplotlib-import", "warn", f"matplotlib import failed: {type(exc).__name__}: {exc}", "warning")]
    return [result("matplotlib-import", "pass", f"matplotlib {getattr(mpl, '__version__', 'unknown')} imported")]


def probe_repo_root(repo_root: Path | None) -> List[Dict[str, str]]:
    if repo_root is None:
        return [result("repo-root", "info", "no --repo-root supplied; source checkout paths were not inspected")]
    out: List[Dict[str, str]] = []
    root = repo_root.expanduser().resolve()
    for rel in ["GAN", "VAE", "RBM", "HelmholtzMachine"]:
        path = root / rel
        out.append(result(f"repo-dir-{rel}", "pass" if path.is_dir() else "warn", f"{rel} exists={path.is_dir()}", "info" if path.is_dir() else "warning"))
    data_path = root / "MNIST_data"
    out.append(result("mnist-data", "pass" if data_path.exists() else "warn", f"MNIST_data exists={data_path.exists()}; scripts may download or fail if absent", "info" if data_path.exists() else "warning"))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Check legacy Generative Models stack compatibility without running training.")
    parser.add_argument("--repo-root", type=Path, help="Optional checkout root to inspect for family dirs and MNIST_data.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when warnings or errors are found.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable report.")
    args = parser.parse_args()

    checks: List[Dict[str, str]] = []
    checks.append(result("python-version", "pass", f"python {sys.version.split()[0]}"))
    checks.extend(probe_numpy())
    checks.extend(probe_tensorflow())
    checks.extend(probe_torch())
    checks.extend(probe_matplotlib())
    checks.extend(probe_repo_root(args.repo_root))

    summary = {
        "warnings": sum(1 for c in checks if c["status"] == "warn"),
        "failures": sum(1 for c in checks if c["status"] == "fail"),
        "checks": checks,
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print("Generative Models legacy-stack diagnostic")
        for c in checks:
            print(f"[{c['status'].upper()}] {c['name']}: {c['detail']}")
        print(f"Summary: {summary['warnings']} warning(s), {summary['failures']} failure(s)")

    if args.strict and (summary["warnings"] or summary["failures"]):
        return 1
    if summary["failures"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
