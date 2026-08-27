#!/usr/bin/env python3
"""Inspect CellTypist model cache state without network access."""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


REQUIRED_PICKLE_KEYS = {"Model", "Scaler_", "description"}
DESCRIPTION_KEYS = ["date", "details", "url", "source", "version"]


def resolve_cache_root(celltypist_folder: Optional[Path]) -> Path:
    if celltypist_folder is not None:
        return celltypist_folder.expanduser().resolve()
    env_value = os.environ.get("CELLTYPIST_FOLDER")
    if env_value:
        return Path(env_value).expanduser().resolve()
    return Path.home().joinpath(".celltypist").resolve()


def model_cache_path(cache_root: Path) -> Path:
    return cache_root / "data" / "models"


def read_models_json(models_json_path: Path) -> Dict[str, Any]:
    with models_json_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    models = payload.get("models", [])
    if not isinstance(models, list):
        raise ValueError("models.json key 'models' is not a list")
    default_models = [item.get("filename") for item in models if isinstance(item, dict) and item.get("default")]
    return {
        "present": True,
        "path": str(models_json_path),
        "model_count": len(models),
        "default_models": default_models,
        "filenames": [item.get("filename") for item in models if isinstance(item, dict) and item.get("filename")],
    }


def inspect_pickle(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False, "valid": False, "error": "file does not exist"}
    if not path.is_file():
        return {"path": str(path), "exists": True, "valid": False, "error": "path is not a file"}

    try:
        with path.open("rb") as handle:
            payload = pickle.load(handle)
    except Exception as exc:  # noqa: BLE001 - pickle errors are intentionally reported to users.
        return {"path": str(path), "exists": True, "valid": False, "error": f"pickle load failed: {exc}"}

    if not isinstance(payload, dict):
        return {"path": str(path), "exists": True, "valid": False, "error": "pickle payload is not a dictionary"}

    missing_keys = sorted(REQUIRED_PICKLE_KEYS.difference(payload))
    classifier = payload.get("Model")
    scaler = payload.get("Scaler_")
    description = payload.get("description")
    errors: List[str] = []
    if missing_keys:
        errors.append(f"missing keys: {missing_keys}")
    if classifier is not None:
        for attribute in ("classes_", "coef_", "intercept_", "features"):
            if not hasattr(classifier, attribute):
                errors.append(f"classifier missing {attribute}")
        if not hasattr(classifier, "decision_function"):
            errors.append("classifier missing decision_function()")
    if scaler is not None:
        for attribute in ("mean_", "var_", "scale_"):
            if not hasattr(scaler, attribute):
                errors.append(f"scaler missing {attribute}")
    if not isinstance(description, dict):
        errors.append("description is not a dictionary")

    class_count = int(len(getattr(classifier, "classes_", []))) if classifier is not None else 0
    feature_count = int(len(getattr(classifier, "features", []))) if classifier is not None else 0
    description_summary = {}
    if isinstance(description, dict):
        description_summary = {key: description.get(key, "") for key in DESCRIPTION_KEYS if key in description}
        if "number_celltypes" in description:
            description_summary["number_celltypes"] = description.get("number_celltypes")

    return {
        "path": str(path),
        "exists": True,
        "valid": not errors,
        "errors": errors,
        "class_count": class_count,
        "classes": [str(value) for value in getattr(classifier, "classes_", [])],
        "feature_count": feature_count,
        "feature_preview": [str(value) for value in list(getattr(classifier, "features", []))[:8]],
        "description": description_summary,
    }


def list_cached_models(models_dir: Path, verify_cached: bool) -> List[Dict[str, Any]]:
    if not models_dir.is_dir():
        return []
    model_paths = sorted(path for path in models_dir.iterdir() if path.is_file() and path.suffix == ".pkl")
    if verify_cached:
        return [inspect_pickle(path) for path in model_paths]
    return [
        {
            "path": str(path),
            "name": path.name,
            "size_bytes": path.stat().st_size,
        }
        for path in model_paths
    ]


def build_summary(args: argparse.Namespace) -> Dict[str, Any]:
    cache_root = resolve_cache_root(args.celltypist_folder)
    models_dir = model_cache_path(cache_root)
    models_json_path = models_dir / "models.json"

    summary: Dict[str, Any] = {
        "celltypist_folder_source": "argument" if args.celltypist_folder else ("environment" if os.environ.get("CELLTYPIST_FOLDER") else "home_default"),
        "celltypist_folder": str(cache_root),
        "models_path": str(models_dir),
        "models_path_exists": models_dir.is_dir(),
        "models_json": {"present": False, "path": str(models_json_path)},
        "cached_models": list_cached_models(models_dir, args.verify_cached),
        "verified_models": [],
        "network_used": False,
    }

    if models_json_path.exists():
        try:
            summary["models_json"] = read_models_json(models_json_path)
        except Exception as exc:  # noqa: BLE001 - report malformed local index.
            summary["models_json"] = {"present": True, "path": str(models_json_path), "error": str(exc)}

    for model_path in args.verify_model:
        summary["verified_models"].append(inspect_pickle(model_path.expanduser().resolve()))

    return summary


def print_text_summary(summary: Dict[str, Any]) -> None:
    print(f"CELLTYPIST_FOLDER source: {summary['celltypist_folder_source']}")
    print(f"CELLTYPIST_FOLDER: {summary['celltypist_folder']}")
    print(f"models_path: {summary['models_path']}")
    print(f"models_path exists: {summary['models_path_exists']}")
    models_json = summary["models_json"]
    print(f"models.json present: {models_json.get('present', False)}")
    if models_json.get("present") and "error" not in models_json:
        print(f"models.json model count: {models_json.get('model_count', 0)}")
        defaults = models_json.get("default_models") or []
        print(f"models.json defaults: {', '.join(defaults) if defaults else '(none marked)'}")
    elif models_json.get("error"):
        print(f"models.json error: {models_json['error']}")

    cached_models = summary["cached_models"]
    print(f"cached .pkl models: {len(cached_models)}")
    for item in cached_models:
        name = Path(item["path"]).name
        if "valid" in item:
            status = "valid" if item["valid"] else "invalid"
            details = f"{status}, classes={item.get('class_count', 0)}, features={item.get('feature_count', 0)}"
            if item.get("errors"):
                details += f", errors={item['errors']}"
        else:
            details = f"{item.get('size_bytes', 0)} bytes"
        print(f"  - {name}: {details}")

    for item in summary["verified_models"]:
        status = "valid" if item.get("valid") else "invalid"
        print(f"verified {item['path']}: {status}")
        if item.get("errors"):
            print(f"  errors: {item['errors']}")
        elif item.get("error"):
            print(f"  error: {item['error']}")
        else:
            print(f"  classes={item.get('classes', [])}")
            print(f"  features={item.get('feature_count', 0)} preview={item.get('feature_preview', [])}")
    print("network used: false")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the CellTypist model cache and optionally verify local model pickle structure. "
            "This helper never imports CellTypist and never performs network requests."
        )
    )
    parser.add_argument(
        "--celltypist-folder",
        type=Path,
        help="Cache root to inspect. Defaults to CELLTYPIST_FOLDER if set, otherwise ~/.celltypist.",
    )
    parser.add_argument(
        "--verify-model",
        type=Path,
        action="append",
        default=[],
        help="Local CellTypist model pickle path to verify. May be provided multiple times.",
    )
    parser.add_argument(
        "--verify-cached",
        action="store_true",
        help="Open each cached .pkl and verify CellTypist pickle structure. Without this, cached models are listed by name and size only.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a text summary.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    summary = build_summary(args)
    if args.json:
        json.dump(summary, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print_text_summary(summary)

    invalid = [item for item in summary["verified_models"] if not item.get("valid")]
    if invalid:
        return 2
    if args.verify_cached and any(not item.get("valid") for item in summary["cached_models"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
