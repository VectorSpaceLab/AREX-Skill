#!/usr/bin/env python3
"""Check a Spleeter runtime without requiring the source repository.

The script verifies package metadata, core imports, CLI help/version, ffmpeg and
ffprobe discovery, optional evaluation imports, and TensorFlow device visibility.
It is safe to run before deciding which Spleeter workflow to use.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from importlib import metadata
from typing import Any, Dict, List, Tuple

CORE_IMPORTS = [
    "spleeter",
    "spleeter.__main__",
    "spleeter.separator",
    "spleeter.audio.adapter",
    "spleeter.audio.ffmpeg",
    "spleeter.dataset",
    "spleeter.model.provider",
]
OPTIONAL_EVALUATION_IMPORTS = ["musdb", "museval"]


def run_command(command: List[str], timeout: float = 20.0) -> Dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    except FileNotFoundError as exc:
        return {"command": command, "returncode": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": None,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": f"timed out after {timeout:g}s",
        }


def import_check(module_name: str) -> Tuple[bool, str]:
    try:
        importlib.import_module(module_name)
        return True, "ok"
    except Exception as exc:  # noqa: BLE001 - diagnostic helper.
        return False, f"{type(exc).__name__}: {exc}"


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def tensorflow_devices(skip: bool) -> Dict[str, Any]:
    if skip:
        return {"skipped": True}
    try:
        import tensorflow as tf  # type: ignore

        devices = tf.config.list_physical_devices()
        gpus = tf.config.list_physical_devices("GPU")
        return {
            "ok": True,
            "version": getattr(tf, "__version__", "unknown"),
            "devices": [f"{device.device_type}:{device.name}" for device in devices],
            "gpu_count": len(gpus),
        }
    except Exception as exc:  # noqa: BLE001 - diagnostic helper.
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    imports = {name: import_check(name) for name in CORE_IMPORTS}
    optional = {name: import_check(name) for name in OPTIONAL_EVALUATION_IMPORTS}
    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "distributions": {
            "spleeter": package_version("spleeter"),
            "tensorflow": package_version("tensorflow"),
            "musdb": package_version("musdb"),
            "museval": package_version("museval"),
        },
        "imports": {name: {"ok": ok, "detail": detail} for name, (ok, detail) in imports.items()},
        "optionalEvaluationImports": {
            name: {"ok": ok, "detail": detail} for name, (ok, detail) in optional.items()
        },
        "binaries": {
            "ffmpeg": shutil.which("ffmpeg"),
            "ffprobe": shutil.which("ffprobe"),
        },
        "cli": {
            "version": run_command([sys.executable, "-m", "spleeter", "--version"], args.timeout),
            "help": run_command([sys.executable, "-m", "spleeter", "--help"], args.timeout),
            "separateHelp": run_command([sys.executable, "-m", "spleeter", "separate", "--help"], args.timeout),
        },
        "tensorflow": tensorflow_devices(args.skip_tensorflow),
    }
    return report


def summarize(report: Dict[str, Any]) -> int:
    failures: List[str] = []
    warnings: List[str] = []

    if not report["distributions"].get("spleeter"):
        failures.append("Spleeter distribution metadata was not found")
    for name, result in report["imports"].items():
        if not result["ok"]:
            failures.append(f"import {name!r} failed: {result['detail']}")
    for binary in ("ffmpeg", "ffprobe"):
        if not report["binaries"].get(binary):
            failures.append(f"{binary} was not found on PATH")
    for label in ("version", "help", "separateHelp"):
        result = report["cli"][label]
        if result["returncode"] != 0:
            failures.append(f"CLI {label} check failed: {result['stderr'] or result['stdout']}")
    if report["tensorflow"].get("ok") is False:
        failures.append(f"TensorFlow import/device check failed: {report['tensorflow'].get('error')}")
    elif report["tensorflow"].get("ok") and report["tensorflow"].get("gpu_count", 0) == 0:
        warnings.append("TensorFlow did not report a GPU; CPU remains the baseline")
    if not all(result["ok"] for result in report["optionalEvaluationImports"].values()):
        warnings.append("evaluation extra imports are not all available; install spleeter[evaluation] for evaluate")

    print("Spleeter runtime check")
    print(f"  python: {report['python']}")
    print(f"  spleeter: {report['distributions'].get('spleeter') or 'missing'}")
    print(f"  tensorflow: {report['distributions'].get('tensorflow') or 'missing'}")
    print(f"  ffmpeg: {report['binaries'].get('ffmpeg') or 'missing'}")
    print(f"  ffprobe: {report['binaries'].get('ffprobe') or 'missing'}")
    if report["tensorflow"].get("ok"):
        print(f"  tensorflow devices: {', '.join(report['tensorflow'].get('devices', [])) or 'none'}")
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for failure in failures:
        print(f"ERROR: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("Status: OK for base Spleeter workflows")
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Spleeter install, CLI, ffmpeg, optional extras, and TensorFlow devices.")
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON instead of a text summary.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Timeout in seconds for each CLI probe.")
    parser.add_argument("--skip-tensorflow", action="store_true", help="Skip TensorFlow import/device probing.")
    args = parser.parse_args(argv)
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    return summarize(report)


if __name__ == "__main__":
    raise SystemExit(main())
