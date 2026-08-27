#!/usr/bin/env python3
"""Probe an installed cuML environment without depending on a source checkout.

Examples:
  python scripts/cuml_environment_probe.py --checks import cuda health
  python scripts/cuml_environment_probe.py --checks import optional --optional dask umap hdbscan
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


def _module_version(module):
    return getattr(module, "__version__", "unknown")


def check_import() -> CheckResult:
    try:
        import cuml  # type: ignore
        import libcuml  # noqa: F401  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on host env
        return CheckResult(
            "import",
            "FAIL",
            f"Could not import cuml/libcuml: {type(exc).__name__}: {exc}. Install a CUDA-capable RAPIDS cuML package that matches the Python, CUDA, and RAPIDS versions.",
        )
    return CheckResult("import", "OK", f"cuml {_module_version(cuml)} imported")


def check_cuda() -> CheckResult:
    try:
        import cupy as cp  # type: ignore
    except Exception as exc:  # pragma: no cover
        return CheckResult(
            "cuda",
            "FAIL",
            f"CuPy import failed: {type(exc).__name__}: {exc}. Install the matching cupy-cuda12x or cupy-cuda13x package.",
        )
    try:
        count = cp.cuda.runtime.getDeviceCount()
        if count < 1:
            return CheckResult("cuda", "FAIL", "CuPy sees no CUDA devices; check NVIDIA driver, container GPU passthrough, and CUDA_VISIBLE_DEVICES.")
        props = cp.cuda.runtime.getDeviceProperties(0)
        name = props.get("name", b"unknown")
        if isinstance(name, bytes):
            name = name.decode(errors="replace")
        x = cp.asarray([1, 2, 3], dtype=cp.float32)
        total = float(x.sum().get())
        return CheckResult("cuda", "OK", f"{count} CUDA device(s); device0={name}; tiny CuPy sum={total}")
    except Exception as exc:  # pragma: no cover
        return CheckResult("cuda", "FAIL", f"CUDA allocation/sum failed: {type(exc).__name__}: {exc}")


def check_health() -> CheckResult:
    cmd = [
        sys.executable,
        "-m",
        "cuml.health_checks",
        "-v",
        "import",
        "functional",
        "accel-basic",
        "accel-cli",
    ]
    try:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    except Exception as exc:  # pragma: no cover
        return CheckResult("health", "FAIL", f"Could not run cuml.health_checks: {type(exc).__name__}: {exc}")
    output = " ".join(proc.stdout.strip().split())
    if proc.returncode == 0:
        return CheckResult("health", "OK", output[:1000])
    return CheckResult("health", "FAIL", f"exit={proc.returncode}: {output[:1000]}")


def check_optional(names: Iterable[str]) -> list[CheckResult]:
    module_map = {
        "dask": ["dask", "dask_cuda", "dask_cudf", "cuml.dask"],
        "umap": ["umap", "cuml.manifold"],
        "hdbscan": ["hdbscan", "cuml.cluster"],
        "xgboost": ["xgboost"],
        "shap": ["shap", "cuml.explainer"],
    }
    results: list[CheckResult] = []
    for name in names:
        modules = module_map.get(name, [name])
        missing = []
        loaded = []
        for mod_name in modules:
            try:
                mod = importlib.import_module(mod_name)
                loaded.append(f"{mod_name}={_module_version(mod)}")
            except Exception as exc:  # pragma: no cover
                missing.append(f"{mod_name}: {type(exc).__name__}: {exc}")
        if missing:
            results.append(CheckResult(f"optional:{name}", "WARN", "missing " + "; ".join(missing)))
        else:
            results.append(CheckResult(f"optional:{name}", "OK", ", ".join(loaded)))
    return results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe an installed cuML runtime.")
    parser.add_argument(
        "--checks",
        nargs="+",
        choices=["import", "cuda", "health", "optional"],
        default=["import", "cuda"],
        help="Checks to run. Use explicit health subchecks to avoid version-specific no-argument CLI behavior.",
    )
    parser.add_argument(
        "--optional",
        nargs="+",
        default=["dask", "umap", "hdbscan"],
        help="Optional dependency groups/modules to probe when --checks includes optional.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    results: list[CheckResult] = []
    if "import" in args.checks:
        results.append(check_import())
    if "cuda" in args.checks:
        results.append(check_cuda())
    if "health" in args.checks:
        results.append(check_health())
    if "optional" in args.checks:
        results.extend(check_optional(args.optional))

    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2, sort_keys=True))
    else:
        for result in results:
            print(f"{result.status:4} {result.name}: {result.detail}")
    return 1 if any(r.status == "FAIL" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
