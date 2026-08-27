#!/usr/bin/env python3
"""Inspect AutoGluon Tabular imports, versions, optional packages, and saved predictors."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import platform
from pathlib import Path


OPTIONAL_PACKAGES = [
    "lightgbm",
    "catboost",
    "xgboost",
    "ray",
    "torch",
    "fastai",
    "imodels",
    "onnx",
    "onnxruntime",
]


def package_version(distribution_name):
    try:
        return importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def import_status(module_name):
    try:
        module = importlib.import_module(module_name)
    except Exception as error:  # pragma: no cover - intentionally diagnostic
        return {"importable": False, "error": f"{type(error).__name__}: {error}"}
    version = getattr(module, "__version__", None) or package_version(module_name)
    return {"importable": True, "version": version}


def inspect_environment(show_optional):
    status = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {
            "autogluon.tabular": import_status("autogluon.tabular"),
            "autogluon.common": import_status("autogluon.common"),
            "autogluon.core": import_status("autogluon.core"),
            "autogluon.features": import_status("autogluon.features"),
        },
    }
    if show_optional:
        status["optional_packages"] = {name: import_status(name) for name in OPTIONAL_PACKAGES}
    return status


def inspect_predictor(path, args):
    from autogluon.tabular import TabularPredictor

    predictor_path = Path(path).expanduser().resolve()
    result = {
        "path": str(predictor_path),
        "exists": predictor_path.exists(),
        "is_dir": predictor_path.is_dir(),
        "load_attempted": False,
    }
    if not predictor_path.exists():
        return result

    version_file = predictor_path / "version.txt"
    metadata_file = predictor_path / "metadata.json"
    if version_file.exists():
        result["saved_autogluon_version"] = version_file.read_text(encoding="utf-8", errors="replace").strip()
    if metadata_file.exists():
        try:
            result["metadata"] = json.loads(metadata_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            result["metadata_error"] = f"JSONDecodeError: {error}"

    if args.no_load:
        return result

    result["load_attempted"] = True
    try:
        predictor = TabularPredictor.load(
            str(predictor_path),
            verbosity=args.verbosity,
            require_version_match=not args.allow_version_mismatch,
            require_py_version_match=not args.allow_python_mismatch,
            check_packages=args.check_packages,
        )
    except Exception as error:  # pragma: no cover - intentionally diagnostic
        result["load_ok"] = False
        result["load_error"] = f"{type(error).__name__}: {error}"
        return result

    result.update(
        {
            "load_ok": True,
            "label": predictor.label,
            "problem_type": predictor.problem_type,
            "eval_metric": predictor.eval_metric.name if predictor.eval_metric is not None else None,
            "path_after_load": predictor.path,
            "is_fit": predictor.is_fit,
        }
    )
    if predictor.is_fit:
        try:
            result["model_names"] = predictor.model_names()
            result["model_best"] = predictor.model_best
        except Exception as error:  # pragma: no cover - intentionally diagnostic
            result["model_error"] = f"{type(error).__name__}: {error}"
        try:
            result["feature_metadata_in"] = str(predictor.feature_metadata_in)
        except Exception as error:  # pragma: no cover - intentionally diagnostic
            result["feature_metadata_error"] = f"{type(error).__name__}: {error}"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictor-path", action="append", default=[], help="Saved TabularPredictor directory to inspect. Can be repeated.")
    parser.add_argument("--show-optional", action="store_true", help="Inspect optional model/backend package imports.")
    parser.add_argument("--check-packages", action="store_true", help="Ask TabularPredictor.load to compare saved/current package metadata.")
    parser.add_argument("--allow-version-mismatch", action="store_true", help="Relax AutoGluon version match during load. Use only for controlled migration checks.")
    parser.add_argument("--allow-python-mismatch", action="store_true", help="Relax Python version match during load. Use only for controlled migration checks.")
    parser.add_argument("--no-load", action="store_true", help="Inspect saved files without unpickling/loading the predictor.")
    parser.add_argument("--verbosity", type=int, default=0, choices=range(0, 5), help="Verbosity passed to TabularPredictor.load.")
    args = parser.parse_args()

    report = inspect_environment(show_optional=args.show_optional)
    if args.predictor_path:
        report["predictors"] = [inspect_predictor(path, args) for path in args.predictor_path]
    print(json.dumps(report, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
