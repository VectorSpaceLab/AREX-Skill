#!/usr/bin/env python3
"""Check an Aim installation for common operating-skill prerequisites.

The script is safe by default: it imports Aim, prints versions/signatures,
checks CLI help/version availability, and optionally probes optional integration
packages without installing anything or starting services.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Dict, Iterable, Optional

OPTIONAL_MODULES = {
    "torch": "PyTorch loops and pytorch helper probes",
    "pytorch_lightning": "PyTorch Lightning callback/logger integrations",
    "lightning": "Lightning package alternative for Lightning integrations",
    "transformers": "Hugging Face Trainer integration",
    "tensorflow": "TensorFlow/Keras and TensorBoard event tooling",
    "keras": "Keras callbacks",
    "xgboost": "XGBoost callback integration",
    "catboost": "CatBoost AimLogger integration",
    "lightgbm": "LightGBM callback integration",
    "optuna": "Optuna callback integration",
    "tensorboard": "TensorBoard event reading/conversion",
    "plotly": "Aim Figure object support for Plotly figures",
    "pandas": "Dataframe helper methods",
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Check Aim import, CLI, and optional integration package availability.")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    p.add_argument("--skip-cli", action="store_true", help="Do not run safe aim CLI help/version checks.")
    p.add_argument("--check-optional", action="store_true", help="Probe optional integration package imports.")
    return p


def run_cmd(argv: Iterable[str]) -> Dict[str, object]:
    argv = list(argv)
    proc = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    output = (proc.stdout or "") + (proc.stderr or "")
    return {"argv": argv, "returncode": proc.returncode, "output_tail": "\n".join(output.splitlines()[-12:])}


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parser().parse_args(argv)
    report: Dict[str, object] = {"ok": True, "python": sys.version.split()[0], "checks": {}, "warnings": []}

    try:
        import aim
        from aim import Distribution, Image, Repo, Run, Text
    except Exception as exc:
        report["ok"] = False
        report["checks"]["import"] = {"ok": False, "error": repr(exc)}
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"FAIL import aim: {exc}", file=sys.stderr)
        return 1

    try:
        dist_version = version("aim")
    except PackageNotFoundError:
        dist_version = getattr(aim, "__version__", "unknown")
        report["warnings"].append("Distribution metadata for aim was not found; import still succeeded.")

    report["checks"]["import"] = {
        "ok": True,
        "aim_version": dist_version,
        "run_signature": str(inspect.signature(Run)),
        "repo_signature": str(inspect.signature(Repo)),
        "image_signature": str(inspect.signature(Image)),
        "text_signature": str(inspect.signature(Text)),
        "distribution_signature": str(inspect.signature(Distribution)),
    }

    if not args.skip_cli:
        aim_bin = shutil.which("aim")
        if not aim_bin:
            sibling = Path(sys.executable).resolve().parent / "aim"
            aim_bin = str(sibling) if sibling.exists() else None
        if aim_bin:
            cli_results = {
                "aim --help": run_cmd([aim_bin, "--help"]),
                "aim version": run_cmd([aim_bin, "version"]),
                "aim up --help": run_cmd([aim_bin, "up", "--help"]),
                "aim server --help": run_cmd([aim_bin, "server", "--help"]),
            }
            report["checks"]["cli"] = cli_results
            for label, result in cli_results.items():
                if result["returncode"] != 0:
                    report["ok"] = False
                    report["warnings"].append(f"{label} returned {result['returncode']}")
        else:
            report["checks"]["cli"] = {"ok": False, "error": "aim executable not found on PATH or beside current Python"}
            report["warnings"].append("Aim import works, but aim CLI executable was not found.")

    if args.check_optional:
        optional = {}
        for module_name, purpose in OPTIONAL_MODULES.items():
            try:
                mod = importlib.import_module(module_name)
                optional[module_name] = {"available": True, "purpose": purpose, "version": getattr(mod, "__version__", None)}
            except Exception as exc:
                optional[module_name] = {"available": False, "purpose": purpose, "error": type(exc).__name__}
        report["checks"]["optional_modules"] = optional

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "PASS" if report["ok"] else "FAIL"
        print(f"{status} Aim environment check")
        print(f"Aim version: {dist_version}")
        print(f"Run signature: {report['checks']['import']['run_signature']}")
        print(f"Repo signature: {report['checks']['import']['repo_signature']}")
        if "cli" in report["checks"]:
            for label, result in report["checks"]["cli"].items():
                if isinstance(result, dict) and "returncode" in result:
                    print(f"{label}: rc={result['returncode']}")
        if "optional_modules" in report["checks"]:
            for module_name, result in report["checks"]["optional_modules"].items():
                mark = "yes" if result["available"] else "no"
                print(f"optional {module_name}: {mark} ({result['purpose']})")
        for warning in report["warnings"]:
            print(f"WARN: {warning}", file=sys.stderr)

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
