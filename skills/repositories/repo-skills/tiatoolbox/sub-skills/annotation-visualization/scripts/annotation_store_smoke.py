#!/usr/bin/env python3
"""Safe smoke checks for TIAToolbox annotation stores.

This script creates tiny in-memory stores and never launches TileServer,
Bokeh, Flask, or a browser.
"""

from __future__ import annotations

import argparse
import json
import logging
from typing import Any, Iterable


def import_annotation_api() -> tuple[Any, Any, Any, Any, Any]:
    """Import optional runtime dependencies after argparse has handled help."""
    try:
        from shapely.geometry import Point, Polygon
        from tiatoolbox.annotation.storage import Annotation, DictionaryStore, SQLiteStore
    except ModuleNotFoundError as exc:
        missing = exc.name or "required dependency"
        raise SystemExit(
            f"Missing {missing!r}. Run this script in an environment where "
            "TIAToolbox and its annotation dependencies are installed.",
        ) from exc
    logging.getLogger().setLevel(logging.ERROR)
    return Annotation, DictionaryStore, SQLiteStore, Point, Polygon


def build_annotations(annotation_cls: Any, point_cls: Any) -> list[Any]:
    """Return a tiny, deterministic set of annotations."""
    return [
        annotation_cls(
            point_cls(1, 1),
            {"type": "tumour", "score": 0.95, "color": [1.0, 0.0, 0.0]},
        ),
        annotation_cls(
            point_cls(5, 5),
            {"type": "stroma", "score": 0.20, "color": [0.0, 0.5, 1.0]},
        ),
    ]


def check_store(
    store_name: str,
    annotations: Iterable[Any],
    where: str,
    store_classes: dict[str, Any],
    polygon_cls: Any,
) -> dict[str, object]:
    """Populate and query one in-memory store backend."""
    store = store_classes[store_name](":memory:")
    try:
        keys = store.append_many(list(annotations), keys=["ann-1", "ann-2"])
        query_region = polygon_cls.from_bounds(0, 0, 3, 3)
        spatial = store.query(query_region)
        filtered = store.query(where=where)
        type_values = sorted(store.pquery('props["type"]'))
        geojson = json.loads(store.to_geojson())
        return {
            "backend": store_name,
            "keys": keys,
            "count": len(store),
            "spatial_count": len(spatial),
            "filtered_keys": sorted(filtered.keys()),
            "types": type_values,
            "geojson_type": geojson["type"],
        }
    finally:
        store.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run safe in-memory TIAToolbox AnnotationStore smoke checks.",
    )
    parser.add_argument(
        "--backend",
        choices=["dictionary", "sqlite", "both"],
        default="both",
        help="Store backend to check. Defaults to both.",
    )
    parser.add_argument(
        "--where",
        default='props["score"] > 0.5',
        help="Trusted DSL filter used for the tiny query check.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    annotation_cls, dictionary_store, sqlite_store, point_cls, polygon_cls = import_annotation_api()
    store_classes = {"dictionary": dictionary_store, "sqlite": sqlite_store}
    backends = ["dictionary", "sqlite"] if args.backend == "both" else [args.backend]
    annotations = build_annotations(annotation_cls, point_cls)
    results = [
        check_store(name, annotations, args.where, store_classes, polygon_cls)
        for name in backends
    ]
    print(json.dumps({"ok": True, "results": results}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
