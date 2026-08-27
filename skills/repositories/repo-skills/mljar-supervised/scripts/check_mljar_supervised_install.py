#!/usr/bin/env python3
"""Check an installed MLJAR Supervised environment without training a model.

Run this from any working directory in the Python environment that should use
`mljar-supervised`. It prints import, version, `AutoML` signature, optional
package, Graphviz, and Mercury availability signals.
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Iterable


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect mljar-supervised import/version/signature and optional runtime dependencies."
    )
    parser.add_argument("--json", action="store_true", help="Emit compact JSON only.")
    parser.add_argument(
        "--check-dot",
        action="store_true",
        help="Also run `dot -V` when Graphviz is present on PATH.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def optional_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run(check_dot: bool = False) -> dict[str, Any]:
    signals: dict[str, Any] = {"status": "passed"}
    try:
        dist_version = version("mljar-supervised")
    except PackageNotFoundError:
        dist_version = None
    signals["distribution"] = {"name": "mljar-supervised", "version": dist_version}

    import supervised
    from supervised import AutoML

    signals["import"] = {
        "module": "supervised",
        "version": getattr(supervised, "__version__", None),
        "automl_class": str(AutoML),
    }
    signals["automl_signatures"] = {
        "__init__": str(inspect.signature(AutoML.__init__)),
        "fit": str(inspect.signature(AutoML.fit)),
        "predict": str(inspect.signature(AutoML.predict)),
        "predict_proba": str(inspect.signature(AutoML.predict_proba)),
        "predict_all": str(inspect.signature(AutoML.predict_all)),
        "score": str(inspect.signature(AutoML.score)),
        "report_structured": str(inspect.signature(AutoML.report_structured)),
        "app": str(inspect.signature(AutoML.app)),
        "publish_app": str(inspect.signature(AutoML.publish_app)),
        "local_app": str(inspect.signature(AutoML.local_app)),
        "need_retrain": str(inspect.signature(AutoML.need_retrain)),
    }
    optional = {
        name: optional_module(name)
        for name in [
            "numpy",
            "pandas",
            "sklearn",
            "xgboost",
            "lightgbm",
            "catboost",
            "shap",
            "dtreeviz",
            "graphviz",
            "mercury",
        ]
    }
    signals["optional_modules"] = optional
    dot_path = shutil.which("dot")
    signals["graphviz_dot"] = {"on_path": bool(dot_path)}
    if check_dot and dot_path:
        proc = subprocess.run([dot_path, "-V"], text=True, capture_output=True, timeout=10)
        signals["graphviz_dot"].update(
            {"exit_code": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
        )
    signals["notes"] = []
    if not optional.get("mercury"):
        signals["notes"].append("Mercury is optional and required only for local app serving, not for basic AutoML training.")
    if not dot_path:
        signals["notes"].append("Graphviz `dot` is optional but needed for some decision-tree visualizations.")
    return signals


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        signals = run(check_dot=args.check_dot)
        if args.json:
            print(json.dumps(signals, sort_keys=True))
        else:
            print(json.dumps(signals, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - user-facing diagnostic
        print(json.dumps({"status": "failed", "error": type(exc).__name__, "message": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
