#!/usr/bin/env python3
"""Validate AnnData-like spatial structure for Squidpy workflows.

This script performs local structural checks only. It does not download data,
read bundled fixtures, or run Squidpy computations.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


def _shape(value: Any) -> tuple[int | None, ...]:
    shape = getattr(value, "shape", None)
    if shape is None:
        try:
            return (len(value),)
        except Exception:
            return ()
    try:
        return tuple(int(part) for part in shape)
    except Exception:
        return tuple(shape)


def _is_numeric_matrix(value: Any) -> bool:
    dtype = getattr(value, "dtype", None)
    if dtype is not None:
        try:
            kind = dtype.kind
        except Exception:
            kind = None
        if kind in {"i", "u", "f", "c"}:
            return True
        if kind in {"O", "U", "S", "b"}:
            return False
    try:
        import numpy as np

        array = np.asarray(value)
        return array.ndim == 2 and array.dtype.kind in {"i", "u", "f", "c"}
    except Exception:
        return False


def _mapping_keys(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        return [str(key) for key in value.keys()]
    keys = getattr(value, "keys", None)
    if callable(keys):
        try:
            return [str(key) for key in keys()]
        except Exception:
            return []
    return []


def _get_mapping_value(value: Any, key: str, default: Any = None) -> Any:
    try:
        return value[key]
    except Exception:
        return default


def _is_categorical(series: Any) -> bool:
    dtype = getattr(series, "dtype", None)
    if dtype is not None and str(dtype) == "category":
        return True
    cat = getattr(series, "cat", None)
    return cat is not None and hasattr(cat, "categories")


def _read_h5ad(path: Path, backed: str | None) -> Any:
    try:
        import anndata as ad
    except Exception as exc:  # pragma: no cover - depends on user environment
        raise RuntimeError("Reading .h5ad requires the 'anndata' package") from exc
    return ad.read_h5ad(path, backed=backed)


def _load_from_callable(spec: str) -> Any:
    if ":" not in spec:
        raise ValueError("Callable spec must be in 'module:function' form")
    module_name, attr_path = spec.split(":", 1)
    if not module_name or not attr_path:
        raise ValueError("Callable spec must include both module and function")
    module = importlib.import_module(module_name)
    obj: Any = module
    for part in attr_path.split("."):
        obj = getattr(obj, part)
    if not callable(obj):
        raise TypeError(f"{spec!r} resolved to a non-callable object")
    return obj()


def _extract_table_if_spatialdata(obj: Any, table_key: str | None) -> tuple[Any, list[str]]:
    notes: list[str] = []
    tables = getattr(obj, "tables", None)
    if tables is None:
        return obj, notes
    table_names = _mapping_keys(tables)
    if table_key is None:
        notes.append(
            "object has SpatialData-like '.tables'; pass --table-key to validate one table "
            f"(available: {table_names})"
        )
        return obj, notes
    table = _get_mapping_value(tables, table_key)
    if table is None:
        notes.append(f"table_key {table_key!r} not found in SpatialData-like object; available: {table_names}")
        return obj, notes
    notes.append(f"validated SpatialData-like table {table_key!r}")
    return table, notes


def validate_adata(obj: Any, args: argparse.Namespace) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": True,
        "errors": [],
        "warnings": [],
        "notes": [],
        "summary": {},
    }

    obj, spatialdata_notes = _extract_table_if_spatialdata(obj, args.table_key)
    result["notes"].extend(spatialdata_notes)

    n_obs = getattr(obj, "n_obs", None)
    if n_obs is None:
        shape = _shape(getattr(obj, "X", []))
        n_obs = shape[0] if shape else None
    result["summary"]["n_obs"] = n_obs

    obs = getattr(obj, "obs", None)
    obsm = getattr(obj, "obsm", None)
    uns = getattr(obj, "uns", None)

    if obsm is None:
        result["errors"].append("object has no '.obsm' mapping")
    else:
        obsm_keys = _mapping_keys(obsm)
        result["summary"]["obsm_keys"] = obsm_keys
        coords = _get_mapping_value(obsm, args.spatial_key)
        if coords is None:
            result["errors"].append(f"missing obsm[{args.spatial_key!r}]")
        else:
            coord_shape = _shape(coords)
            result["summary"]["spatial_shape"] = coord_shape
            if len(coord_shape) != 2:
                result["errors"].append(f"obsm[{args.spatial_key!r}] must be 2-dimensional, got shape {coord_shape}")
            else:
                if coord_shape[1] < 2:
                    result["errors"].append(f"obsm[{args.spatial_key!r}] must have at least 2 coordinate columns")
                if n_obs is not None and coord_shape[0] != n_obs:
                    result["errors"].append(
                        f"obsm[{args.spatial_key!r}] rows ({coord_shape[0]}) do not match n_obs ({n_obs})"
                    )
            if not _is_numeric_matrix(coords):
                result["errors"].append(f"obsm[{args.spatial_key!r}] must be numeric")

    if uns is None:
        message = "object has no '.uns' mapping"
        (result["errors"] if args.require_uns_spatial else result["warnings"]).append(message)
    else:
        uns_keys = _mapping_keys(uns)
        result["summary"]["uns_keys"] = uns_keys
        spatial_uns = _get_mapping_value(uns, args.uns_spatial_key)
        if spatial_uns is None:
            message = f"missing uns[{args.uns_spatial_key!r}]"
            (result["errors"] if args.require_uns_spatial else result["warnings"]).append(message)
        else:
            library_ids = _mapping_keys(spatial_uns)
            result["summary"]["library_ids"] = library_ids
            selected_ids = [args.library_id] if args.library_id else library_ids
            if args.library_id and args.library_id not in library_ids:
                result["errors"].append(
                    f"library_id {args.library_id!r} not found in uns[{args.uns_spatial_key!r}]; available: {library_ids}"
                )
                selected_ids = []
            if not library_ids:
                message = f"uns[{args.uns_spatial_key!r}] contains no library entries"
                (result["errors"] if args.require_uns_spatial else result["warnings"]).append(message)
            for library_id in selected_ids:
                entry = _get_mapping_value(spatial_uns, library_id, {})
                entry_keys = _mapping_keys(entry)
                result["summary"].setdefault("library_entries", {})[library_id] = entry_keys

                images = _get_mapping_value(entry, "images")
                image_keys = _mapping_keys(images) if images is not None else []
                if args.require_images and not image_keys:
                    result["errors"].append(f"library {library_id!r} has no images mapping")
                elif images is None:
                    result["warnings"].append(f"library {library_id!r} has no images mapping")
                elif args.require_images and not {"hires", "lowres"}.intersection(image_keys):
                    result["errors"].append(
                        f"library {library_id!r} images should include 'hires' or 'lowres', got {image_keys}"
                    )

                scalefactors = _get_mapping_value(entry, "scalefactors")
                scale_keys = _mapping_keys(scalefactors) if scalefactors is not None else []
                if args.require_scalefactors and not scale_keys:
                    result["errors"].append(f"library {library_id!r} has no scalefactors mapping")
                elif scalefactors is None:
                    result["warnings"].append(f"library {library_id!r} has no scalefactors mapping")
                elif args.require_scalefactors:
                    expected = {"spot_diameter_fullres", "tissue_hires_scalef"}
                    missing = sorted(expected.difference(scale_keys))
                    if missing:
                        result["errors"].append(
                            f"library {library_id!r} scalefactors missing expected keys: {missing}"
                        )

    if args.library_key:
        if obs is None:
            result["errors"].append("object has no '.obs' table for library_key validation")
        else:
            try:
                library_column = obs[args.library_key]
            except Exception:
                result["errors"].append(f"missing obs[{args.library_key!r}] library column")
            else:
                if args.require_categorical_library and not _is_categorical(library_column):
                    result["errors"].append(f"obs[{args.library_key!r}] must be categorical")
                elif not _is_categorical(library_column):
                    result["warnings"].append(f"obs[{args.library_key!r}] is not categorical")

    result["ok"] = not result["errors"]
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate AnnData-like spatial structure for Squidpy data loading workflows.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("h5ad", nargs="?", type=Path, help="Path to a local .h5ad file to validate.")
    source.add_argument(
        "--callable",
        dest="callable_spec",
        metavar="MODULE:FUNCTION",
        help="Import and call a zero-argument function returning an AnnData-like or SpatialData-like object.",
    )
    parser.add_argument("--backed", choices=["r", "r+"], default=None, help="Read .h5ad in backed mode.")
    parser.add_argument("--spatial-key", default="spatial", help="Key in .obsm containing spatial coordinates.")
    parser.add_argument("--uns-spatial-key", default="spatial", help="Key in .uns containing spatial metadata.")
    parser.add_argument("--library-id", help="Require and validate one .uns['spatial'] library id.")
    parser.add_argument("--library-key", help="Optional .obs column containing library ids.")
    parser.add_argument(
        "--table-key",
        help="For a SpatialData-like object returned by --callable, validate this .tables entry.",
    )
    parser.add_argument(
        "--require-uns-spatial",
        action="store_true",
        help="Treat missing .uns['spatial'] as an error instead of a warning.",
    )
    parser.add_argument(
        "--require-images",
        action="store_true",
        help="Require image metadata under selected .uns['spatial'] library entries.",
    )
    parser.add_argument(
        "--require-scalefactors",
        action="store_true",
        help="Require Visium-style scalefactors under selected .uns['spatial'] library entries.",
    )
    parser.add_argument(
        "--require-categorical-library",
        action="store_true",
        help="Require --library-key column to be pandas categorical.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.h5ad is not None:
            if not args.h5ad.exists():
                raise FileNotFoundError(args.h5ad)
            obj = _read_h5ad(args.h5ad, args.backed)
            source = str(args.h5ad)
        else:
            obj = _load_from_callable(args.callable_spec)
            source = args.callable_spec
        report = validate_adata(obj, args)
        report["source"] = source
    except Exception as exc:
        report = {
            "ok": False,
            "source": str(args.h5ad or args.callable_spec),
            "errors": [f"{type(exc).__name__}: {exc}"],
            "warnings": [],
            "notes": [],
            "summary": {},
        }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        status = "OK" if report["ok"] else "FAILED"
        print(f"Squidpy spatial AnnData check: {status}")
        print(f"Source: {report['source']}")
        summary = report.get("summary") or {}
        if summary:
            print("Summary:")
            for key, value in summary.items():
                print(f"  - {key}: {value}")
        for label in ["notes", "warnings", "errors"]:
            items = report.get(label) or []
            if items:
                print(f"{label.title()}:")
                for item in items:
                    print(f"  - {item}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
