#!/usr/bin/env python3
"""Inspect a local scvi-tools saved model directory.

This script summarizes saved registry metadata, expected setup arguments, data
files, optional Hub metadata, and optional AnnData/MuData compatibility without
requiring access to the original source checkout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _json_default(value: Any) -> str:
    return repr(value)


def _load_registry(model_class: str, model_dir: Path, prefix: str | None) -> dict[str, Any]:
    import scvi

    if not hasattr(scvi.model, model_class):
        available = [name for name in dir(scvi.model) if name.isupper()]
        raise SystemExit(
            f"scvi.model has no class {model_class!r}. Common model classes: {', '.join(available[:20])}"
        )
    cls = getattr(scvi.model, model_class)
    return cls.load_registry(str(model_dir), prefix=prefix)


def _read_var_names(adata_path: Path) -> list[str] | dict[str, list[str]]:
    suffix = adata_path.suffix.lower()
    if suffix == ".h5mu":
        import mudata

        mdata = mudata.read_h5mu(adata_path)
        return {mod: list(mdata[mod].var_names.astype(str)) for mod in mdata.mod.keys()}

    import anndata

    adata = anndata.read_h5ad(adata_path)
    return list(adata.var_names.astype(str))


def _registry_summary(registry: dict[str, Any]) -> dict[str, Any]:
    field_registries = registry.get("field_registries", {}) or {}
    setup_args = registry.get("setup_args", {}) or {}
    return {
        "model_name": registry.get("model_name"),
        "scvi_version": registry.get("scvi_version"),
        "setup_method_name": registry.get("setup_method_name", "setup_anndata"),
        "setup_args": setup_args,
        "field_registry_keys": sorted(field_registries.keys()),
        "has_minified_registry": "minify_type" in field_registries,
    }


def _data_files(model_dir: Path, prefix: str | None) -> dict[str, bool]:
    file_prefix = prefix or ""
    return {
        "model_pt": (model_dir / f"{file_prefix}model.pt").is_file(),
        "adata_h5ad": (model_dir / f"{file_prefix}adata.h5ad").is_file(),
        "mdata_h5mu": (model_dir / f"{file_prefix}mdata.h5mu").is_file(),
        "hub_metadata": (model_dir / "_scvi_required_metadata.json").is_file(),
        "hub_readme": (model_dir / "README.md").is_file(),
    }


def _hub_metadata(model_dir: Path) -> dict[str, Any] | None:
    metadata_path = model_dir / "_scvi_required_metadata.json"
    if not metadata_path.is_file():
        return None
    with metadata_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _compare_var_names(saved_model_class: str, model_dir: Path, prefix: str | None, adata_path: Path) -> dict[str, Any]:
    import torch
    from scvi.model.base._constants import SAVE_KEYS

    file_prefix = prefix or ""
    model_path = model_dir / f"{file_prefix}model.pt"
    saved = torch.load(model_path, map_location="cpu", weights_only=False)
    saved_var_names = saved.get(SAVE_KEYS.VAR_NAMES_KEY)
    observed_var_names = _read_var_names(adata_path)

    def as_list(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: list(val) for key, val in value.items()}
        return list(value)

    saved_names = as_list(saved_var_names)
    same = saved_names == observed_var_names
    return {
        "model_class_checked": saved_model_class,
        "adata_path": str(adata_path),
        "var_names_match": same,
        "saved_var_count": {k: len(v) for k, v in saved_names.items()} if isinstance(saved_names, dict) else len(saved_names),
        "adata_var_count": {k: len(v) for k, v in observed_var_names.items()} if isinstance(observed_var_names, dict) else len(observed_var_names),
        "first_saved_var_names": {k: v[:5] for k, v in saved_names.items()} if isinstance(saved_names, dict) else saved_names[:5],
        "first_adata_var_names": {k: v[:5] for k, v in observed_var_names.items()} if isinstance(observed_var_names, dict) else observed_var_names[:5],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a local scvi-tools saved model directory.")
    parser.add_argument("--model-dir", required=True, help="Directory containing model.pt or prefixed model file.")
    parser.add_argument("--model-class", default="SCVI", help="Class under scvi.model used to read the registry, e.g. SCVI, SCANVI, TOTALVI.")
    parser.add_argument("--prefix", default=None, help="Optional prefix used when the model was saved.")
    parser.add_argument("--adata", default=None, help="Optional .h5ad or .h5mu path whose var_names should be compared to the saved model.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a readable text summary.")
    args = parser.parse_args()

    model_dir = Path(args.model_dir).expanduser().resolve()
    if not model_dir.is_dir():
        raise SystemExit(f"Model directory does not exist or is not a directory: {model_dir}")

    files = _data_files(model_dir, args.prefix)
    if not files["model_pt"]:
        expected = model_dir / f"{args.prefix or ''}model.pt"
        raise SystemExit(f"Missing saved model file: {expected}")

    registry = _load_registry(args.model_class, model_dir, args.prefix)
    report: dict[str, Any] = {
        "model_dir": str(model_dir),
        "requested_model_class": args.model_class,
        "files": files,
        "registry": _registry_summary(registry),
        "hub_metadata": _hub_metadata(model_dir),
    }

    if args.adata:
        adata_path = Path(args.adata).expanduser().resolve()
        if not adata_path.is_file():
            raise SystemExit(f"AnnData/MuData path does not exist: {adata_path}")
        report["adata_check"] = _compare_var_names(args.model_class, model_dir, args.prefix, adata_path)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=_json_default))
        return 0

    print(f"Saved model directory: {report['model_dir']}")
    print(f"Requested class: {args.model_class}")
    print("Files:")
    for key, exists in files.items():
        print(f"  - {key}: {'yes' if exists else 'no'}")
    print("Registry:")
    for key, value in report["registry"].items():
        print(f"  - {key}: {value}")
    if report["hub_metadata"]:
        print("Hub metadata:")
        for key, value in report["hub_metadata"].items():
            print(f"  - {key}: {value}")
    if "adata_check" in report:
        check = report["adata_check"]
        print("AnnData/MuData var_names check:")
        print(f"  - var_names_match: {check['var_names_match']}")
        print(f"  - saved_var_count: {check['saved_var_count']}")
        print(f"  - adata_var_count: {check['adata_var_count']}")
        print(f"  - first_saved_var_names: {check['first_saved_var_names']}")
        print(f"  - first_adata_var_names: {check['first_adata_var_names']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)
