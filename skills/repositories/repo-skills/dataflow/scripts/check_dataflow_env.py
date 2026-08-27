#!/usr/bin/env python3
"""Check that the DataFlow package imports cleanly and that the selected backend is visible.

This helper is offline-safe. It only imports the package, reports basic runtime
facts, and optionally checks CLI help from the installed package.

Examples:
  python scripts/check_dataflow_env.py
  python scripts/check_dataflow_env.py --json
  python scripts/check_dataflow_env.py --check-cli-help
  python scripts/check_dataflow_env.py --repo-root /path/to/DataFlow
"""
from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path

REQUIRED_MODULES = [
    "dataflow",
    "dataflow.cli",
    "dataflow.pipeline",
    "dataflow.core.operator",
    "dataflow.core.prompt",
    "dataflow.utils.storage",
]

OPTIONAL_MODULES = [
    "dataflow.serving",
    "dataflow.rayorch",
]

DEFAULT_MODULES = REQUIRED_MODULES + OPTIONAL_MODULES


def _maybe_add_repo_root(repo_root: Path | None) -> None:
    if repo_root is None:
        return
    repo_root = repo_root.expanduser().resolve()
    if (repo_root / "dataflow" / "__init__.py").is_file() and str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check the DataFlow package and backend availability.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional checkout root to add to sys.path before import.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a human-readable summary.")
    parser.add_argument("--check-cli-help", action="store_true", help="Also run `python -m dataflow.cli --help`.")
    parser.add_argument("--module", action="append", default=[], help="Extra module to import and report. Repeatable.")
    parser.add_argument("--strict-optional", action="store_true", help="Treat optional module import failures as exit-status failures.")
    parser.add_argument("--self-check-help", action="store_true", help="Verify argparse help text and exit.")
    return parser


def _import_module(name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(name)
        return {
            "ok": True,
            "file": getattr(module, "__file__", None),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": f"{exc.__class__.__name__}: {exc}",
        }


def _check_cli_help() -> dict[str, object]:
    cmd = [sys.executable, "-m", "dataflow.cli", "--help"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "ok": proc.returncode == 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.self_check_help:
        help_text = parser.format_help()
        if "--check-cli-help" not in help_text or "--repo-root" not in help_text:
            raise AssertionError("argparse help text did not include expected options")
        print("OK: argparse --help text is available.")
        return 0

    _maybe_add_repo_root(args.repo_root)

    required = list(dict.fromkeys(REQUIRED_MODULES + list(args.module)))
    optional = [name for name in OPTIONAL_MODULES if name not in required]
    result: dict[str, object] = {
        "python_version": sys.version.split()[0],
        "cwd": str(Path.cwd()),
        "required_modules": {},
        "optional_modules": {},
    }

    for name in required:
        result["required_modules"][name] = _import_module(name)
    for name in optional:
        result["optional_modules"][name] = _import_module(name)

    try:
        import dataflow

        result["dataflow_version"] = getattr(dataflow, "__version__", None)
        result["hello"] = dataflow.hello()
    except Exception as exc:  # noqa: BLE001
        result["dataflow_error"] = f"{exc.__class__.__name__}: {exc}"

    try:
        import torch

        cuda_available = bool(torch.cuda.is_available())
        gpu_info = {
            "torch_version": torch.__version__,
            "cuda_available": cuda_available,
            "device_count": int(torch.cuda.device_count()) if cuda_available else 0,
        }
        if cuda_available:
            gpu_info["device0"] = torch.cuda.get_device_name(0)
        result["torch"] = gpu_info
    except Exception as exc:  # noqa: BLE001
        result["torch_error"] = f"{exc.__class__.__name__}: {exc}"

    if args.check_cli_help:
        result["cli_help"] = _check_cli_help()

    required_ok = all(bool(entry.get("ok", False)) for entry in result["required_modules"].values())
    optional_ok = all(bool(entry.get("ok", False)) for entry in result["optional_modules"].values())
    ok = required_ok and (optional_ok or not args.strict_optional)
    if args.check_cli_help:
        ok = ok and bool(result["cli_help"]["ok"])

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python_version']}")
        print(f"DataFlow: {result.get('dataflow_version', 'unknown')}")
        print(f"hello(): {result.get('hello', '<unavailable>')}")
        print("Required modules:")
        for name, entry in result["required_modules"].items():
            status = "OK" if entry.get("ok") else f"FAIL ({entry.get('error')})"
            print(f"- {name}: {status}")
        if result["optional_modules"]:
            print("Optional modules:")
            for name, entry in result["optional_modules"].items():
                status = "OK" if entry.get("ok") else f"MISSING ({entry.get('error')})"
                print(f"- {name}: {status}")
        if "torch" in result:
            torch_info = result["torch"]
            print(
                "Torch: {torch_version}, cuda={cuda_available}, devices={device_count}".format(
                    **torch_info,
                )
            )
            if torch_info.get("device0"):
                print(f"CUDA device 0: {torch_info['device0']}")
        if result.get("torch_error"):
            print(f"Torch import error: {result['torch_error']}")
        if args.check_cli_help:
            cli_help = result["cli_help"]
            print(f"CLI help: {'OK' if cli_help['ok'] else 'FAIL'}")
            print(cli_help["stdout"].rstrip())
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
