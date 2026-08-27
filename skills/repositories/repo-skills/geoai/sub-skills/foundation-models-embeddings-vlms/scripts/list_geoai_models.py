#!/usr/bin/env python3
"""Report GeoAI model registries and optional dependencies without downloads.

This script is safe by default:
- no model downloads
- no network calls
- no training
- no file writes unless the caller redirects output

Examples:
    python list_geoai_models.py
    python list_geoai_models.py --query Prithvi-EO-2.0-300M
    python list_geoai_models.py --json
    python list_geoai_models.py --deps-only
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import re
import sys
from typing import Any, Dict, Iterable, List, Optional

OPTIONAL_DEPS = (
    "terratorch",
    "torchgeo",
    "geotessera",
    "vllm",
    "spacy",
    "transformers",
    "accelerate",
)

WORKFLOW_DEFAULTS: Dict[str, Any] = {
    "foundation_models": {
        "registry_key_style": "lower-case hyphenated GeoAI keys",
        "prithvi_registry_key": "prithvi-eo-2.0-300m",
    },
    "dino_v3": {
        "default_model_name": "dinov3_vitl16",
        "default_weights_path": None,
    },
    "prithvi": {
        "default_model_name": "Prithvi-EO-2.0-300M-TL",
    },
    "universat": {
        "default_model_name_or_path": "g-astruc/UniverSat",
    },
    "tessera": {
        "embedding_dim": 128,
        "dataset_version": "v1",
    },
    "moondream": {
        "default_model_name": "vikhyatk/moondream2",
        "alternate_model_name": "moondream/moondream3-preview",
    },
    "vllm_geo": {
        "default_model_id": "Qwen/Qwen2-VL-7B-Instruct",
        "default_base_url": "http://localhost:8000/v1",
    },
    "caption": {
        "default_blip_model": "Salesforce/blip-image-captioning-base",
        "default_spacy_model": "en_core_web_sm",
    },
}


def normalize(text: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def safe_import(module_name: str):
    try:
        return importlib.import_module(module_name), None
    except Exception as exc:  # pragma: no cover - exercised by optional deps
        return None, f"{exc.__class__.__name__}: {exc}"


def optional_dependency_matrix() -> Dict[str, bool]:
    return {name: importlib.util.find_spec(name) is not None for name in OPTIONAL_DEPS}


def record_matches_query(record: Dict[str, Any], query: Optional[str]) -> bool:
    if not query:
        return True
    q = normalize(query)
    blob = normalize(
        " ".join(
            str(part)
            for part in (
                record.get("key"),
                record.get("name"),
                record.get("abbreviation"),
                record.get("category"),
                record.get("modality"),
                record.get("tasks"),
                record.get("huggingface_id"),
                record.get("terratorch_key"),
                record.get("class_name"),
                record.get("kind"),
                record.get("base"),
                record.get("spatial_extent"),
                record.get("spatial_resolution"),
                record.get("temporal_extent"),
                record.get("description"),
            )
            if part is not None
        )
    )
    return q in blob


def build_report(include_registry: bool = True) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "package": {"name": "geoai-py", "version": None},
        "optional_dependencies": optional_dependency_matrix(),
        "workflow_defaults": WORKFLOW_DEFAULTS,
        "foundation_models": [],
        "embedding_datasets": [],
        "prithvi_models": [],
        "module_status": {},
    }

    geoai_mod, err = safe_import("geoai")
    if geoai_mod is not None:
        report["package"]["version"] = getattr(geoai_mod, "__version__", None)
    elif err is not None:
        report["module_status"]["geoai"] = err

    if not include_registry:
        return report

    fm_mod, err = safe_import("geoai.foundation_models")
    if fm_mod is not None:
        for key, info in fm_mod.FOUNDATION_MODELS.items():
            report["foundation_models"].append(
                {
                    "key": key,
                    "normalized_key": normalize(key),
                    "name": info.get("name"),
                    "abbreviation": info.get("abbreviation"),
                    "category": info.get("category"),
                    "modality": info.get("modality"),
                    "tasks": info.get("tasks", []),
                    "year": info.get("year"),
                    "huggingface_id": info.get("huggingface_id"),
                    "terratorch_supported": info.get("terratorch_supported"),
                    "terratorch_key": info.get("terratorch_key"),
                }
            )
    elif err is not None:
        report["module_status"]["geoai.foundation_models"] = err

    emb_mod, err = safe_import("geoai.embeddings")
    if emb_mod is not None:
        for key, info in emb_mod.EMBEDDING_DATASETS.items():
            report["embedding_datasets"].append(
                {
                    "key": key,
                    "normalized_key": normalize(key),
                    "class_name": info.get("class_name"),
                    "kind": info.get("kind"),
                    "base": info.get("base"),
                    "spatial_extent": info.get("spatial_extent"),
                    "spatial_resolution": info.get("spatial_resolution"),
                    "temporal_extent": info.get("temporal_extent"),
                    "dimensions": info.get("dimensions"),
                    "dtype": info.get("dtype"),
                    "license": info.get("license"),
                }
            )
    elif err is not None:
        report["module_status"]["geoai.embeddings"] = err

    prithvi_mod, err = safe_import("geoai.prithvi")
    if prithvi_mod is not None:
        report["prithvi_models"] = list(getattr(prithvi_mod, "AVAILABLE_MODELS", []))
    elif err is not None:
        report["module_status"]["geoai.prithvi"] = err

    return report


def filter_report(report: Dict[str, Any], query: Optional[str]) -> Dict[str, Any]:
    if not query:
        return report
    filtered = dict(report)
    filtered["foundation_models"] = [
        row for row in report["foundation_models"] if record_matches_query(row, query)
    ]
    filtered["embedding_datasets"] = [
        row for row in report["embedding_datasets"] if record_matches_query(row, query)
    ]
    filtered["prithvi_models"] = [
        model for model in report["prithvi_models"] if normalize(query) in normalize(model)
    ]
    return filtered


def _col_width(rows: Iterable[Dict[str, Any]], key: str, minimum: int = 0) -> int:
    width = max((len(str(row.get(key, ""))) for row in rows), default=0)
    return max(width, minimum)


def print_table(title: str, rows: List[Dict[str, Any]], columns: List[str]) -> None:
    print(f"\n{title} ({len(rows)})")
    if not rows:
        print("  <none>")
        return
    widths = {col: max(len(col), _col_width(rows, col)) for col in columns}
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    print("  " + header)
    print("  " + "-+-".join("-" * widths[col] for col in columns))
    for row in rows:
        print("  " + " | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns))


def print_text_report(report: Dict[str, Any]) -> None:
    pkg = report["package"]
    print("GeoAI registry report")
    print(f"Package: {pkg.get('name')} {pkg.get('version') or 'unknown'}")

    if report["module_status"]:
        print("Module import notes:")
        for name, status in sorted(report["module_status"].items()):
            print(f"  {name}: {status}")

    print("\nOptional dependencies:")
    for name, available in report["optional_dependencies"].items():
        print(f"  {name}: {'yes' if available else 'no'}")

    print_table(
        "Foundation models",
        report["foundation_models"],
        ["key", "name", "category", "modality", "terratorch_supported", "huggingface_id"],
    )
    print_table(
        "Embedding datasets",
        report["embedding_datasets"],
        ["key", "class_name", "kind", "dimensions", "license"],
    )

    print("\nPrithvi model names")
    if report["prithvi_models"]:
        for model in report["prithvi_models"]:
            print(f"  - {model}")
    else:
        print("  <none>")

    print("\nWorkflow defaults")
    for family, defaults in report["workflow_defaults"].items():
        print(f"  {family}:")
        for key, value in defaults.items():
            print(f"    {key}: {value}")

    print("\nNo downloads were attempted.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List GeoAI foundation models, embedding datasets, and optional dependencies without downloads.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python list_geoai_models.py\n"
            "  python list_geoai_models.py --query Prithvi-EO-2.0-300M\n"
            "  python list_geoai_models.py --json\n"
            "  python list_geoai_models.py --deps-only"
        ),
    )
    parser.add_argument(
        "--query",
        help="Filter registry rows by a name, key, HF id, task, or class substring.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a text summary.",
    )
    parser.add_argument(
        "--deps-only",
        action="store_true",
        help="Skip registry imports and report only optional-dependency availability plus static defaults.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(include_registry=not args.deps_only)
    report = filter_report(report, args.query)

    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print_text_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
