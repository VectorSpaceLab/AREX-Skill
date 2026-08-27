#!/usr/bin/env python3
"""Safely inspect a Surprise installation without downloads or mutation.

Examples:
  python check_surprise_environment.py
  python check_surprise_environment.py --json
  python check_surprise_environment.py --smoke-fit
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from typing import Any


def distribution_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run_cli_help() -> dict[str, Any]:
    executable = shutil.which("surprise")
    if executable:
        command = [executable, "--help"]
        label = "surprise"
    else:
        command = [sys.executable, "-m", "surprise", "--help"]
        label = "python -m surprise"
    try:
        proc = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - defensive diagnostic
        return {"available": False, "ok": False, "label": label, "reason": f"{type(exc).__name__}: {exc}"}
    return {
        "available": True,
        "ok": proc.returncode == 0,
        "label": label,
        "returncode": proc.returncode,
        "stdout_head": proc.stdout.splitlines()[:8],
        "stderr_head": proc.stderr.splitlines()[:8],
    }


def run_smoke_fit() -> dict[str, Any]:
    if not has_module("pandas"):
        return {"requested": True, "ok": None, "skipped": True, "reason": "pandas is not installed"}

    try:
        import pandas as pd
        from surprise import Dataset, Reader, SVD, accuracy
    except Exception as exc:  # pragma: no cover - defensive diagnostic
        return {"requested": True, "ok": False, "error": f"{type(exc).__name__}: {exc}"}

    df = pd.DataFrame(
        {
            "user": ["u1", "u1", "u2", "u3"],
            "item": ["i1", "i2", "i1", "i3"],
            "rating": [4, 5, 3, 2],
        }
    )
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(df[["user", "item", "rating"]], reader)
    trainset = data.build_full_trainset()
    algo = SVD(n_factors=1, n_epochs=1, random_state=0)
    algo.fit(trainset)
    predictions = algo.test(trainset.build_testset())
    rmse = float(accuracy.rmse(predictions, verbose=False))
    return {
        "requested": True,
        "ok": True,
        "prediction_count": len(predictions),
        "rmse": rmse,
    }


def inspect_environment(smoke_fit: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "distributions": {
            name: distribution_version(name)
            for name in ["scikit-surprise", "numpy", "scipy", "joblib", "pandas", "pytest", "cython"]
        },
        "optional_imports": {name: has_module(name) for name in ["numpy", "scipy", "joblib", "pandas", "pytest", "cython"]},
        "surprise": {"import_ok": False},
        "cli": {},
        "smoke_fit": {"requested": smoke_fit, "ok": None, "skipped": True},
    }

    try:
        import surprise

        report["surprise"] = {
            "import_ok": True,
            "version": getattr(surprise, "__version__", None),
            "has_dataset": hasattr(surprise, "Dataset"),
            "has_reader": hasattr(surprise, "Reader"),
            "has_accuracy": hasattr(surprise, "accuracy"),
            "has_dump": hasattr(surprise, "dump"),
        }
    except Exception as exc:
        report["surprise"] = {"import_ok": False, "error": f"{type(exc).__name__}: {exc}"}

    report["cli"] = run_cli_help()
    if smoke_fit:
        report["smoke_fit"] = run_smoke_fit()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--smoke-fit", action="store_true", help="Run a tiny dataframe fit/test smoke when pandas is available.")
    args = parser.parse_args()

    report = inspect_environment(args.smoke_fit)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print(f"Surprise import: {report['surprise'].get('import_ok')} version={report['surprise'].get('version')}")
        print(f"CLI help: {report['cli'].get('ok')} ({report['cli'].get('reason', report['cli'].get('returncode'))})")
        missing = [name for name, ok in report['optional_imports'].items() if not ok]
        print("Missing optional imports: " + (", ".join(missing) if missing else "none"))
        smoke_fit = report.get("smoke_fit", {})
        if smoke_fit.get("requested"):
            if smoke_fit.get("ok"):
                print(f"Smoke fit: passed with {smoke_fit.get('prediction_count')} predictions, rmse={smoke_fit.get('rmse'):.4f}")
            elif smoke_fit.get("skipped"):
                print(f"Smoke fit: skipped ({smoke_fit.get('reason')})")
            else:
                print(f"Smoke fit: failed ({smoke_fit.get('error', 'unknown error')})")

    if not report["surprise"].get("import_ok"):
        return 1
    if not report["cli"].get("ok"):
        return 1
    smoke_fit = report.get("smoke_fit", {})
    if smoke_fit.get("requested") and smoke_fit.get("ok") is False:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
