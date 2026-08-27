#!/usr/bin/env python3
"""Safe PySR runtime/environment probe.

The probe can inspect package metadata without importing PySR. Importing PySR is
optional because a fresh PySR import can initialize JuliaCall and resolve/compile
Julia packages.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import inspect
import json
import os
import platform
import subprocess
import sys
import time
import warnings
from typing import Any

WATCH_ENV_VARS = [
    "PYTHON_JULIACALL_THREADS",
    "PYTHON_JULIACALL_HANDLE_SIGNALS",
    "PYTHON_JULIACALL_OPTLEVEL",
    "PYTHON_JULIACALL_AUTOLOAD_IPYTHON_EXTENSION",
    "PYSR_AUTOLOAD_EXTENSIONS",
]

PACKAGE_NAMES = [
    "pysr",
    "juliacall",
    "numpy",
    "pandas",
    "sympy",
    "scikit-learn",
    "click",
]

SIGNATURE_FIELDS = [
    "parallelism",
    "procs",
    "cluster_manager",
    "batching",
    "batch_size",
    "timeout_in_seconds",
    "max_evals",
    "early_stop_condition",
    "random_state",
    "deterministic",
    "input_stream",
    "worker_timeout",
    "worker_imports",
    "heap_size_hint_in_bytes",
]


def package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in PACKAGE_NAMES:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def watched_environment() -> dict[str, str | None]:
    return {name: os.environ.get(name) for name in WATCH_ENV_VARS}


def parameter_defaults(callable_obj: Any) -> dict[str, str]:
    signature = inspect.signature(callable_obj)
    defaults: dict[str, str] = {}
    for name in SIGNATURE_FIELDS:
        parameter = signature.parameters.get(name)
        if parameter is None:
            continue
        if parameter.default is inspect._empty:
            defaults[name] = "<required>"
        else:
            defaults[name] = repr(parameter.default)
    return defaults


def summarize_exception(exc: BaseException) -> dict[str, str]:
    message = str(exc).replace(os.path.expanduser("~"), "~")
    if len(message) > 500:
        message = message[:497] + "..."
    return {"type": type(exc).__name__, "message": message}


def import_probe() -> dict[str, Any]:
    started = time.monotonic()
    result: dict[str, Any] = {"status": "unknown"}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            import pysr  # type: ignore

            result.update(
                {
                    "status": "ok",
                    "import_seconds": round(time.monotonic() - started, 3),
                    "pysr_version": getattr(pysr, "__version__", "unknown"),
                    "has_PySRRegressor": hasattr(pysr, "PySRRegressor"),
                    "julia_version": None,
                    "symbolic_regression_loaded": hasattr(pysr, "SymbolicRegression"),
                    "regressor_defaults": parameter_defaults(pysr.PySRRegressor),
                }
            )
            try:
                version = pysr.jl.VERSION
                result["julia_version"] = f"{version.major}.{version.minor}.{version.patch}"
            except Exception as exc:  # pragma: no cover - best-effort metadata
                result["julia_version_error"] = summarize_exception(exc)
        except Exception as exc:
            result.update(
                {
                    "status": "error",
                    "import_seconds": round(time.monotonic() - started, 3),
                    "error": summarize_exception(exc),
                }
            )

    if caught:
        result["warnings"] = [
            {
                "category": warning.category.__name__,
                "message": str(warning.message).replace(os.path.expanduser("~"), "~"),
            }
            for warning in caught
        ]
    return result


def check_cli(timeout: float) -> dict[str, Any]:
    started = time.monotonic()
    command = [sys.executable, "-m", "pysr", "--help"]
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "timeout_seconds": timeout,
            "note": "The CLI imports PySR before printing help; first-import Julia setup may be in progress.",
        }
    except Exception as exc:
        return {"status": "error", "error": summarize_exception(exc)}

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    return {
        "status": "ok" if completed.returncode == 0 else "error",
        "returncode": completed.returncode,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "stdout_lines": len(stdout.splitlines()),
        "stderr_lines": len(stderr.splitlines()),
        "has_usage": "Usage:" in stdout,
        "has_test_command": "test" in stdout,
        "has_install_command": "install" in stdout,
    }


def build_payload(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    payload: dict[str, Any] = {
        "probe": "pysr_environment_probe",
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "packages": package_versions(),
        "environment": watched_environment(),
        "import": {"status": "skipped"},
        "cli": {"status": "not_requested"},
    }

    exit_code = 0
    if not args.skip_import:
        payload["import"] = import_probe()
        if payload["import"].get("status") != "ok":
            exit_code = 1

    if args.check_cli:
        if args.skip_import:
            payload["cli"] = {
                "status": "skipped",
                "reason": "--skip-import was set; python -m pysr imports PySR before displaying help.",
            }
        else:
            payload["cli"] = check_cli(args.cli_timeout)
            if payload["cli"].get("status") != "ok":
                exit_code = 1

    return payload, exit_code


def print_text(payload: dict[str, Any]) -> None:
    print("PySR environment probe")
    print(f"Python: {payload['python']['implementation']} {payload['python']['version']}")
    print(f"Platform: {payload['python']['platform']}")
    print("Packages:")
    for name, version in payload["packages"].items():
        print(f"  {name}: {version or 'not installed'}")
    print("Environment:")
    for name, value in payload["environment"].items():
        print(f"  {name}: {value if value is not None else '<unset>'}")

    import_status = payload["import"].get("status")
    print(f"Import: {import_status}")
    if import_status == "ok":
        print(f"  PySR version: {payload['import'].get('pysr_version')}")
        print(f"  Julia version: {payload['import'].get('julia_version')}")
        print(f"  Import seconds: {payload['import'].get('import_seconds')}")
    elif import_status == "error":
        error = payload["import"].get("error", {})
        print(f"  Error: {error.get('type')}: {error.get('message')}")

    cli_status = payload["cli"].get("status")
    print(f"CLI: {cli_status}")
    if cli_status == "ok":
        print(f"  returncode: {payload['cli'].get('returncode')}")
        print(f"  has usage: {payload['cli'].get('has_usage')}")
    elif cli_status in {"error", "timeout", "skipped"}:
        detail = payload["cli"].get("reason") or payload["cli"].get("note") or payload["cli"].get("error")
        if detail:
            print(f"  {detail}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Probe PySR package metadata, JuliaCall-related environment variables, "
            "optional PySR import, and optional CLI help without fitting a model."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of text.",
    )
    parser.add_argument(
        "--skip-import",
        action="store_true",
        help="Do not import PySR. Use this for metadata-only checks that cannot trigger Julia setup.",
    )
    parser.add_argument(
        "--check-cli",
        action="store_true",
        help=(
            "Run 'python -m pysr --help' in a subprocess. Ignored when --skip-import is set "
            "because the CLI imports PySR before printing help."
        ),
    )
    parser.add_argument(
        "--cli-timeout",
        type=float,
        default=30.0,
        help="Seconds to wait for the optional CLI help subprocess (default: 30).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    payload, exit_code = build_payload(args)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
