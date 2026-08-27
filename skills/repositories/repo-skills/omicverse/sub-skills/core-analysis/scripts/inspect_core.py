#!/usr/bin/env python3
"""Inspect an installed OmicVerse core-analysis runtime.

This script is self-contained: it imports the installed package, probes lazy root
attributes, checks selected core modules, summarizes registry metadata, and can
optionally create a tiny synthetic AnnData without downloads.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import inspect
import json
import sys
from typing import Any


CORE_MODULES = ("io", "datasets", "pp", "pl", "report", "utils")
ROOT_ATTRS = (
    "read",
    "set_seed",
    "list_functions",
    "get_function_help",
    "recommend_function",
    "find_function",
    "export_registry",
)
SIGNATURE_TARGETS = (
    ("omicverse.io", "read"),
    ("omicverse.io", "read_h5ad"),
    ("omicverse.io", "read_10x_mtx"),
    ("omicverse.pp", "qc_metrics"),
    ("omicverse.pp", "qc"),
    ("omicverse.pp", "preprocess"),
    ("omicverse.pp", "scale"),
    ("omicverse.pp", "pca"),
    ("omicverse.pp", "neighbors"),
    ("omicverse.pp", "umap"),
    ("omicverse.pl", "embedding"),
    ("omicverse.pl", "qc"),
    ("omicverse.datasets", "create_mock_dataset"),
    ("omicverse.report", "from_anndata"),
)


def status_ok(value: Any = True) -> dict[str, Any]:
    return {"ok": True, "value": value}


def status_error(exc: BaseException) -> dict[str, Any]:
    return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def safe_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # noqa: BLE001
        return f"<signature unavailable: {type(exc).__name__}: {exc}>"


def inspect_runtime(include_registry: bool, smoke_mock: bool, mock_cells: int, mock_genes: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "python": sys.version.split()[0],
        "omicverse": {},
        "root_attrs": {},
        "modules": {},
        "signatures": {},
        "registry": {},
        "mock_smoke": None,
    }

    try:
        import omicverse as ov
    except Exception as exc:  # noqa: BLE001
        result["omicverse"] = status_error(exc)
        return result

    try:
        package_version = metadata.version("omicverse")
    except Exception:  # noqa: BLE001
        package_version = None

    result["omicverse"] = status_ok({
        "module_version": getattr(ov, "__version__", None),
        "package_version": package_version,
    })

    for attr in ROOT_ATTRS:
        try:
            value = getattr(ov, attr)
            result["root_attrs"][attr] = status_ok(type(value).__name__)
        except Exception as exc:  # noqa: BLE001
            result["root_attrs"][attr] = status_error(exc)

    for module_name in CORE_MODULES:
        full_name = f"omicverse.{module_name}"
        try:
            module = importlib.import_module(full_name)
            exported = getattr(module, "__all__", [])
            result["modules"][module_name] = status_ok({
                "module": full_name,
                "all_count": len(exported) if exported is not None else None,
            })
        except Exception as exc:  # noqa: BLE001
            result["modules"][module_name] = status_error(exc)

    for module_name, attr in SIGNATURE_TARGETS:
        key = f"{module_name}.{attr}"
        try:
            module = importlib.import_module(module_name)
            value = getattr(module, attr)
            result["signatures"][key] = status_ok(safe_signature(value))
        except Exception as exc:  # noqa: BLE001
            result["signatures"][key] = status_error(exc)

    if include_registry:
        try:
            registry_data = ov.export_registry(format="dict", include_source=False)
            metadata_block = registry_data.get("metadata", {})
            functions = registry_data.get("functions", {})
            categories: dict[str, int] = {}
            for entry in functions.values():
                category = str(entry.get("category", "uncategorized"))
                categories[category] = categories.get(category, 0) + 1
            result["registry"] = status_ok({
                "total_functions": metadata_block.get("total_functions", len(functions)),
                "categories": categories,
            })
        except Exception as exc:  # noqa: BLE001
            result["registry"] = status_error(exc)
    else:
        result["registry"] = {"ok": None, "value": "skipped"}

    if smoke_mock:
        try:
            adata = ov.datasets.create_mock_dataset(
                n_cells=mock_cells,
                n_genes=mock_genes,
                n_cell_types=min(4, max(2, mock_cells // 10)),
                with_clustering=True,
                random_state=0,
            )
            result["mock_smoke"] = status_ok({
                "shape": [int(adata.n_obs), int(adata.n_vars)],
                "obs_columns": list(map(str, adata.obs.columns[:10])),
                "var_columns": list(map(str, adata.var.columns[:10])),
                "layers": list(map(str, adata.layers.keys())),
                "obsm": list(map(str, adata.obsm.keys())),
                "has_umap": "X_umap" in adata.obsm,
            })
        except Exception as exc:  # noqa: BLE001
            result["mock_smoke"] = status_error(exc)

    return result


def print_text(report: dict[str, Any]) -> None:
    print("OmicVerse core runtime inspection")
    print(f"Python: {report.get('python')}")

    ov_status = report.get("omicverse", {})
    if ov_status.get("ok"):
        value = ov_status.get("value", {})
        print(f"OmicVerse module version: {value.get('module_version')}")
        print(f"OmicVerse package version: {value.get('package_version')}")
    else:
        print(f"OmicVerse import failed: {ov_status.get('error_type')}: {ov_status.get('error')}")
        return

    print("\nRoot lazy attributes:")
    for name, item in report.get("root_attrs", {}).items():
        marker = "ok" if item.get("ok") else "FAIL"
        detail = item.get("value") if item.get("ok") else f"{item.get('error_type')}: {item.get('error')}"
        print(f"  {marker:4} {name}: {detail}")

    print("\nCore modules:")
    for name, item in report.get("modules", {}).items():
        marker = "ok" if item.get("ok") else "FAIL"
        if item.get("ok"):
            detail = f"exports={item.get('value', {}).get('all_count')}"
        else:
            detail = f"{item.get('error_type')}: {item.get('error')}"
        print(f"  {marker:4} {name}: {detail}")

    print("\nSelected signatures:")
    for name, item in report.get("signatures", {}).items():
        marker = "ok" if item.get("ok") else "FAIL"
        detail = item.get("value") if item.get("ok") else f"{item.get('error_type')}: {item.get('error')}"
        print(f"  {marker:4} {name}{detail if str(detail).startswith('(') else ': ' + str(detail)}")

    registry = report.get("registry", {})
    print("\nRegistry:")
    if registry.get("ok") is True:
        value = registry.get("value", {})
        print(f"  total_functions={value.get('total_functions')}")
        top_categories = sorted(value.get("categories", {}).items(), key=lambda item: (-item[1], item[0]))[:12]
        for category, count in top_categories:
            print(f"  {category}: {count}")
    elif registry.get("ok") is None:
        print("  skipped")
    else:
        print(f"  FAIL {registry.get('error_type')}: {registry.get('error')}")

    smoke = report.get("mock_smoke")
    if smoke is not None:
        print("\nMock AnnData smoke:")
        if smoke.get("ok"):
            value = smoke.get("value", {})
            print(f"  shape={value.get('shape')} has_umap={value.get('has_umap')}")
            print(f"  obs_columns={value.get('obs_columns')}")
            print(f"  obsm={value.get('obsm')}")
        else:
            print(f"  FAIL {smoke.get('error_type')}: {smoke.get('error')}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect an installed OmicVerse core-analysis runtime without reading repository source paths.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    parser.add_argument(
        "--skip-registry",
        action="store_true",
        help="Skip registry export hydration. Faster, but omits function counts.",
    )
    parser.add_argument(
        "--smoke-mock",
        action="store_true",
        help="Create a tiny synthetic AnnData with ov.datasets.create_mock_dataset. No downloads are performed.",
    )
    parser.add_argument("--mock-cells", type=int, default=50, help="Synthetic cell count for --smoke-mock.")
    parser.add_argument("--mock-genes", type=int, default=100, help="Synthetic gene count for --smoke-mock.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.mock_cells <= 0 or args.mock_genes <= 1:
        parser.error("--mock-cells must be > 0 and --mock-genes must be > 1")

    report = inspect_runtime(
        include_registry=not args.skip_registry,
        smoke_mock=args.smoke_mock,
        mock_cells=args.mock_cells,
        mock_genes=args.mock_genes,
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    if not report.get("omicverse", {}).get("ok"):
        return 2
    failed_modules = [name for name, item in report.get("modules", {}).items() if not item.get("ok")]
    failed_attrs = [name for name, item in report.get("root_attrs", {}).items() if not item.get("ok")]
    if failed_modules or failed_attrs:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
