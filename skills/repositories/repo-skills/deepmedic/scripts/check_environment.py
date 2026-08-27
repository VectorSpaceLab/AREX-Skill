#!/usr/bin/env python3
"""Report DeepMedic, TensorFlow, scientific-stack, and CLI readiness.

This diagnostic is read-only and runs from any working directory. It does not
train a model, download data, alter CUDA visibility, or inspect private paths.
"""
from __future__ import print_function

import argparse
import json
import shutil
import subprocess
import sys


def _distribution_versions():
    from importlib import metadata

    names = ("deepmedic", "tensorflow", "numpy", "scipy", "pandas", "nibabel", "protobuf")
    result = {}
    for name in names:
        try:
            result[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            result[name] = None
    return result


def _run_help(command):
    executable = shutil.which(command[0])
    if executable is None:
        return {"available": False, "returncode": None, "error": "executable not found"}
    try:
        proc = subprocess.run(
            [executable] + list(command[1:]),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": True, "returncode": None, "error": str(exc)}
    return {
        "available": True,
        "returncode": proc.returncode,
        "first_line": next((line for line in proc.stdout.splitlines() if line.strip()), ""),
    }


def inspect(skip_cli=False):
    report = {"python": sys.version.split()[0], "versions": {}, "imports": {}, "cuda": {}}
    try:
        report["versions"] = _distribution_versions()
    except Exception as exc:
        report["versions_error"] = str(exc)
    for module in ("deepmedic", "numpy", "scipy", "pandas", "nibabel", "tensorflow"):
        try:
            imported = __import__(module)
            report["imports"][module] = {"ok": True, "version": getattr(imported, "__version__", None)}
        except Exception as exc:
            report["imports"][module] = {"ok": False, "error": "{}: {}".format(type(exc).__name__, exc)}
    tf = None
    try:
        import tensorflow as tf
        report["cuda"] = {
            "build": dict(tf.sysconfig.get_build_info()),
            "devices": [device.name for device in tf.config.list_physical_devices("GPU")],
        }
    except Exception as exc:
        report["cuda"] = {"error": "{}: {}".format(type(exc).__name__, exc)}
    if not skip_cli:
        report["cli"] = {
            "deepMedicRun": _run_help(("deepMedicRun", "-h")),
        }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only DeepMedic environment and CLI diagnostic.")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a human-readable summary")
    parser.add_argument("--skip-cli", action="store_true", help="do not execute CLI help")
    args = parser.parse_args(argv)
    report = inspect(skip_cli=args.skip_cli)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print("Python: {}".format(report["python"]))
        print("Versions: {}".format(report["versions"]))
        for module, result in report["imports"].items():
            print("Import {}: {}".format(module, "OK" if result["ok"] else result["error"]))
        print("CUDA: {} GPU device(s)".format(len(report.get("cuda", {}).get("devices", []))))
        if "cli" in report:
            print("deepMedicRun -h: return code {}".format(report["cli"]["deepMedicRun"]["returncode"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
