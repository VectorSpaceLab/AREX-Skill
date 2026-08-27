#!/usr/bin/env python3
"""Check that Squidpy imports and exposes the public modules covered by this skill."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys

PUBLIC_TARGETS = {
    "datasets": ["visium", "visium_hne_adata", "visium_hne_image", "visium_hne_sdata", "cells"],
    "read": ["visium", "vizgen", "nanostring"],
    "gr": ["spatial_neighbors_knn", "spatial_neighbors_radius", "nhood_enrichment", "spatial_autocorr"],
    "im": ["ImageContainer", "process", "segment", "calculate_image_features"],
    "pl": ["spatial_scatter", "spatial_segment", "var_by_distance"],
    "tl": ["sliding_window", "var_by_distance"],
    "experimental.im": ["detect_tissue", "make_tiles", "qc_image", "fit_stain_reference"],
    "experimental.tl": ["calculate_tiling_qc", "assign_stitch_groups"],
    "experimental.pl": ["qc_image", "tiling_qc"],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    import squidpy as sq

    modules = {"squidpy": sq}
    missing: dict[str, list[str]] = {}
    signatures: dict[str, str] = {}

    for suffix, names in PUBLIC_TARGETS.items():
        module = importlib.import_module(f"squidpy.{suffix}")
        modules[suffix] = module
        for name in names:
            obj = getattr(module, name, None)
            if obj is None:
                missing.setdefault(suffix, []).append(name)
                continue
            try:
                signatures[f"{suffix}.{name}"] = str(inspect.signature(obj))
            except (TypeError, ValueError):
                signatures[f"{suffix}.{name}"] = "<signature unavailable>"

    result = {
        "ok": not missing,
        "version": getattr(sq, "__version__", ""),
        "modules": sorted(modules),
        "missing": missing,
        "signature_count": len(signatures),
    }

    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(f"Squidpy version: {result['version']}")
        print(f"Checked modules: {', '.join(result['modules'])}")
        print(f"Checked public callables/classes: {result['signature_count']}")
        if missing:
            print(f"Missing targets: {missing}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
