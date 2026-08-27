#!/usr/bin/env python3
"""Inspect an installed Vaex package set without depending on a source checkout.

The script reports installed distribution versions, importability of the main
Vaex modules, a tiny in-memory DataFrame smoke check, and optional safe CLI
help/settings probes. It avoids server startup, cloud access, destructive file
operations, and any repository-local paths.
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import shutil
import subprocess
import sys
from importlib import metadata
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_DISTRIBUTIONS = [
    "vaex",
    "vaex-core",
    "vaex-hdf5",
    "vaex-viz",
    "vaex-ml",
    "vaex-server",
    "vaex-astro",
    "vaex-jupyter",
    "vaex-graphql",
    "vaex-arrow",
    "numpy",
    "pandas",
    "pyarrow",
    "matplotlib",
    "scikit-learn",
    "fastapi",
    "uvicorn",
    "tornado",
    "h5py",
]

DEFAULT_MODULES = [
    "vaex",
    "vaex.hdf5",
    "vaex.viz",
    "vaex.ml",
    "vaex.server",
    "vaex.astro",
    "vaex.jupyter",
]


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect an installed Vaex distribution set and print a compact JSON summary.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--distributions",
        nargs="+",
        default=DEFAULT_DISTRIBUTIONS,
        help="Distribution names to probe with importlib.metadata.version.",
    )
    parser.add_argument(
        "--modules",
        nargs="+",
        default=DEFAULT_MODULES,
        help="Module names to import and report on.",
    )
    parser.add_argument(
        "--include-cli-help",
        action="store_true",
        help="Also run `vaex --help` and `vaex settings yaml` when the console command is available.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Per-command timeout in seconds for safe CLI help checks.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser.parse_args(argv)


def json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:  # noqa: BLE001 - fallback path for odd objects
            pass
    if hasattr(value, "tolist"):
        try:
            return value.tolist()
        except Exception:  # noqa: BLE001 - fallback path for odd objects
            pass
    return str(value)


def probe_distributions(names: Iterable[str]) -> Dict[str, Any]:
    report: Dict[str, Any] = {}
    for name in names:
        try:
            report[name] = {"version": metadata.version(name)}
        except metadata.PackageNotFoundError:
            report[name] = {"missing": True}
        except Exception as exc:  # noqa: BLE001 - diagnostic helper
            report[name] = {"error": f"{type(exc).__name__}: {exc}"}
    return report


def probe_modules(names: Iterable[str]) -> Dict[str, Any]:
    report: Dict[str, Any] = {}
    for name in names:
        try:
            module = importlib.import_module(name)
            report[name] = {
                "ok": True,
                "module": getattr(module, "__name__", name),
            }
        except Exception as exc:  # noqa: BLE001 - diagnostic helper
            report[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return report


def core_smoke() -> Dict[str, Any]:
    import vaex

    df = vaex.from_arrays(x=[1, 2, 3], y=[10, 20, 30])
    df["double"] = df.x * 2
    return {
        "vaex_version": getattr(vaex, "__version__", "unknown"),
        "shape": list(df.shape),
        "columns": df.get_column_names(),
        "count": int(df.count()),
        "sum_x": float(df.sum("x")),
        "double_preview": df.evaluate(df["double"], i1=0, i2=3, array_type="python"),
    }


def _run_cli(prefix: List[str], args: List[str], timeout: float) -> Dict[str, Any]:
    try:
        completed = subprocess.run(
            [*prefix, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "command": args,
            "timed_out": True,
            "returncode": None,
            "stdout_excerpt": (exc.stdout or "")[-2000:],
            "stderr_excerpt": (exc.stderr or "")[-2000:],
        }
    except OSError as exc:
        return {"command": args, "timed_out": False, "returncode": None, "error": f"{type(exc).__name__}: {exc}"}

    return {
        "command": args,
        "timed_out": False,
        "returncode": completed.returncode,
        "stdout_excerpt": completed.stdout[-2000:],
        "stderr_excerpt": completed.stderr[-2000:],
    }


def cli_smoke(timeout: float) -> Dict[str, Any]:
    executable = shutil.which("vaex")
    prefix: List[str]
    if executable:
        prefix = [executable]
        source = "vaex"
    else:
        probe = subprocess.run(
            [sys.executable, "-m", "vaex", "--help"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
            check=False,
        )
        if probe.returncode != 0:
            return {"available": False, "error": "Neither vaex nor python -m vaex is available"}
        prefix = [sys.executable, "-m", "vaex"]
        source = "python -m vaex"

    checks = [
        _run_cli(prefix, ["--help"], timeout),
        _run_cli(prefix, ["settings", "yaml"], timeout),
    ]
    return {
        "available": True,
        "source": source,
        "checks": checks,
        "ok": all(item.get("returncode") == 0 and not item.get("timed_out") for item in checks),
    }


def run(args: argparse.Namespace) -> Dict[str, Any]:
    import vaex

    report: Dict[str, Any] = {
        "ok": True,
        "python": {
            "version": sys.version.split()[0],
            "platform": platform.platform(),
            "implementation": platform.python_implementation(),
        },
        "vaex_version": getattr(vaex, "__version__", "unknown"),
        "distributions": probe_distributions(args.distributions),
        "modules": probe_modules(args.modules),
        "core_smoke": core_smoke(),
    }

    if args.include_cli_help:
        report["cli"] = cli_smoke(args.timeout)
        if not report["cli"].get("ok", False):
            report["ok"] = False

    missing_imports = [name for name, item in report["modules"].items() if not item.get("ok")]
    report["missing_imports"] = missing_imports
    if not report["core_smoke"]:
        report["ok"] = False
    return report


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        report = run(args)
    except Exception as exc:  # noqa: BLE001 - command-line diagnostic helper
        payload = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
        print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True), file=sys.stderr)
        return 1

    print(json.dumps(report, default=json_default, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
