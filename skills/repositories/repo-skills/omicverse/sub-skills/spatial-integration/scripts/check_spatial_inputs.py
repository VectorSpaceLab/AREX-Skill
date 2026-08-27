#!/usr/bin/env python3
"""Validate OmicVerse spatial input layouts and AnnData spatial slots.

This script performs read-only checks. It does not download data, train models,
start services, or run histology inference.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterable


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def ok(self, message: str) -> None:
        self.info.append(f"OK: {message}")

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def print(self) -> None:
        for line in self.info:
            print(line)
        for line in self.warnings:
            print(f"WARNING: {line}")
        for line in self.errors:
            print(f"ERROR: {line}")
        print(f"SUMMARY: ERRORS: {len(self.errors)} WARNINGS: {len(self.warnings)}")


def existing(root: Path, candidates: Iterable[str]) -> list[Path]:
    return [root / name for name in candidates if (root / name).exists()]


def has_any(root: Path, candidates: Iterable[str], reporter: Reporter, label: str, required: bool = True) -> list[Path]:
    found = existing(root, candidates)
    if found:
        reporter.ok(f"{label}: {', '.join(path.name for path in found[:3])}")
    elif required:
        reporter.error(f"Missing {label}; tried: {', '.join(candidates)}")
    else:
        reporter.warn(f"Optional {label} not found; tried: {', '.join(candidates)}")
    return found


def read_header(path: Path) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    if path.suffix == ".parquet":
        return []
    try:
        with path.open("r", newline="", encoding="utf-8", errors="replace") as handle:
            sample = handle.read(4096)
            handle.seek(0)
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;") if sample.strip() else csv.excel
            reader = csv.reader(handle, dialect)
            return next(reader, [])
    except Exception:
        return []


def check_columns(path: Path, accepted_pairs: list[tuple[str, str]], reporter: Reporter, label: str) -> None:
    if path.suffix == ".parquet":
        reporter.warn(f"{label} is parquet; column names were not inspected without pandas/pyarrow")
        return
    header = read_header(path)
    if not header:
        reporter.warn(f"Could not inspect columns for {label}: {path.name}")
        return
    header_set = set(header)
    for left, right in accepted_pairs:
        if left in header_set and right in header_set:
            reporter.ok(f"{label} contains coordinate columns {left}/{right}")
            return
    reporter.error(f"{label} lacks accepted coordinate pairs; saw columns: {header[:12]}")


def infer_kind(path: Path) -> str:
    if path.is_file() and path.suffix.lower() == ".h5ad":
        return "h5ad"
    if (path / "cell_feature_matrix.h5").exists() and existing(path, ["cells.parquet", "cells.csv.gz", "cells.csv"]):
        return "xenium"
    if (path / "filtered_feature_cell_matrix.h5").exists() or existing(
        path,
        [
            "graphclust_annotated_cell_segmentations.geojson",
            "cell_segmentations.geojson",
            "cell_segmentations_annotated.geojson",
            "annotated_cell_segmentations.geojson",
        ],
    ):
        return "visium-hd-cellseg"
    if (path / "spatial").is_dir() and (
        (path / "filtered_feature_bc_matrix.h5").exists() or (path / "filtered_feature_bc_matrix").exists()
    ):
        return "visium-hd-bin"
    if (path / "CellComposite").is_dir() or (path / "CellLabels").is_dir():
        return "nanostring"
    return "unknown"


def check_visium_hd_bin(path: Path, reporter: Reporter) -> None:
    has_any(path, ["filtered_feature_bc_matrix.h5", "filtered_feature_bc_matrix"], reporter, "Visium HD bin count matrix")
    tissue = has_any(
        path,
        ["spatial/tissue_positions.parquet", "spatial/tissue_positions.csv"],
        reporter,
        "Visium HD tissue positions",
    )
    if tissue:
        check_columns(
            tissue[0],
            [
                ("pxl_col_in_fullres", "pxl_row_in_fullres"),
                ("pxl_col", "pxl_row"),
                ("x", "y"),
                ("array_col", "array_row"),
            ],
            reporter,
            "tissue positions",
        )
    has_any(path, ["spatial/tissue_hires_image.png"], reporter, "hires tissue image", required=False)
    has_any(path, ["spatial/tissue_lowres_image.png"], reporter, "lowres tissue image", required=False)
    scalefactors = has_any(path, ["spatial/scalefactors_json.json"], reporter, "scalefactors JSON", required=False)
    for sf in scalefactors:
        try:
            data = json.loads(sf.read_text(encoding="utf-8"))
            for key in ("tissue_hires_scalef", "spot_diameter_fullres"):
                if key in data:
                    reporter.ok(f"scalefactors contains {key}")
                else:
                    reporter.warn(f"scalefactors missing {key}")
        except Exception as exc:
            reporter.warn(f"Could not parse scalefactors JSON: {exc}")


def check_visium_hd_cellseg(path: Path, reporter: Reporter) -> None:
    has_any(path, ["filtered_feature_cell_matrix.h5"], reporter, "Visium HD cell matrix")
    has_any(
        path,
        [
            "graphclust_annotated_cell_segmentations.geojson",
            "cell_segmentations.geojson",
            "cell_segmentations_annotated.geojson",
            "annotated_cell_segmentations.geojson",
        ],
        reporter,
        "cell segmentation GeoJSON",
    )
    has_any(path, ["spatial/tissue_hires_image.png"], reporter, "hires tissue image", required=False)
    has_any(path, ["spatial/tissue_lowres_image.png"], reporter, "lowres tissue image", required=False)
    has_any(path, ["spatial/scalefactors_json.json"], reporter, "scalefactors JSON", required=False)


def check_xenium(path: Path, reporter: Reporter) -> None:
    has_any(path, ["cell_feature_matrix.h5"], reporter, "Xenium cell_feature_matrix.h5")
    cells = has_any(path, ["cells.parquet", "cells.csv.gz", "cells.csv"], reporter, "Xenium cells metadata")
    if cells:
        check_columns(
            cells[0],
            [("x_centroid", "y_centroid"), ("CenterX_local_px", "CenterY_local_px")],
            reporter,
            "Xenium cells metadata",
        )
    has_any(path, ["experiment.xenium"], reporter, "experiment.xenium", required=False)
    has_any(path, ["cell_boundaries.parquet", "cell_boundaries.csv.gz", "cell_boundaries.csv"], reporter, "cell boundaries", required=False)
    morphology = existing(
        path,
        ["morphology_focus.ome.tif", "morphology_mip.ome.tif"],
    )
    morphology.extend(sorted((path / "morphology_focus").glob("morphology_focus_*.ome.tif")) if (path / "morphology_focus").is_dir() else [])
    morphology.extend(sorted(path.glob("morphology_focus_*.ome.tif")))
    if morphology:
        reporter.ok(f"morphology candidates: {len(morphology)} file(s); first={morphology[0].name}")
    else:
        reporter.warn("No Xenium morphology OME-TIFF found; use load_image=False or provide image files for overlay")


def check_nanostring(path: Path, reporter: Reporter, counts_file: str | None, meta_file: str | None, fov_file: str | None) -> None:
    if not counts_file:
        reporter.error("NanoString requires --counts-file")
        return
    if not meta_file:
        reporter.error("NanoString requires --meta-file")
        return
    counts = path / counts_file
    meta = path / meta_file
    if counts.exists():
        reporter.ok(f"counts file exists: {counts.name}")
    else:
        reporter.error(f"counts file not found: {counts}")
    if meta.exists():
        reporter.ok(f"metadata file exists: {meta.name}")
        check_columns(
            meta,
            [
                ("CenterX_local_px", "CenterY_local_px"),
                ("centerx_local_px", "centery_local_px"),
                ("center_x_local_px", "center_y_local_px"),
                ("CenterX", "CenterY"),
            ],
            reporter,
            "NanoString metadata",
        )
    else:
        reporter.error(f"metadata file not found: {meta}")
    if fov_file:
        if (path / fov_file).exists():
            reporter.ok(f"FOV file exists: {fov_file}")
        else:
            reporter.warn(f"FOV file not found: {path / fov_file}")
    has_any(path, ["CellComposite"], reporter, "CellComposite image directory", required=False)
    has_any(path, ["CellLabels"], reporter, "CellLabels segmentation directory", required=False)


def h5_group_has_key(group, key: str) -> bool:
    try:
        return key in group
    except Exception:
        return False


def check_h5ad(path: Path, reporter: Reporter) -> None:
    if not path.is_file():
        reporter.error(f"H5AD path is not a file: {path}")
        return
    try:
        import h5py  # type: ignore
    except Exception as exc:
        reporter.error(f"h5py is required for safe H5AD slot inspection: {exc}")
        return

    try:
        with h5py.File(path, "r") as handle:
            for key in ("X", "obs", "var"):
                if h5_group_has_key(handle, key):
                    reporter.ok(f"h5ad contains /{key}")
                else:
                    reporter.error(f"h5ad missing /{key}")
            if h5_group_has_key(handle, "obsm") and h5_group_has_key(handle["obsm"], "spatial"):
                reporter.ok("h5ad contains obsm['spatial']")
            else:
                reporter.error("h5ad missing obsm['spatial']")
            if h5_group_has_key(handle, "uns") and h5_group_has_key(handle["uns"], "spatial"):
                reporter.ok("h5ad contains uns['spatial']")
            else:
                reporter.warn("h5ad missing uns['spatial']; image-backed spatial plotting may be unavailable")
            if h5_group_has_key(handle, "layers") and h5_group_has_key(handle["layers"], "counts"):
                reporter.ok("h5ad contains layers['counts']")
            else:
                reporter.warn("h5ad missing layers['counts']; deconvolution/split workflows prefer raw counts")
            if h5_group_has_key(handle, "obsp") and h5_group_has_key(handle["obsp"], "spatial_connectivities"):
                reporter.ok("h5ad contains obsp['spatial_connectivities']")
            else:
                reporter.warn("h5ad missing obsp['spatial_connectivities']; run ov.space.spatial_neighbors if needed")
            obs_has_geometry = h5_group_has_key(handle, "obs") and h5_group_has_key(handle["obs"], "geometry")
            if obs_has_geometry:
                reporter.ok("h5ad contains obs['geometry']")
            else:
                reporter.warn("h5ad missing obs['geometry']; segmentation plotting may be unavailable")
    except Exception as exc:
        reporter.error(f"Could not inspect H5AD file: {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only validator for OmicVerse spatial layouts and AnnData spatial slots."
    )
    parser.add_argument("--path", required=True, help="Input directory or .h5ad file to validate")
    parser.add_argument(
        "--kind",
        default="auto",
        choices=["auto", "h5ad", "visium-hd-bin", "visium-hd-cellseg", "xenium", "nanostring"],
        help="Input type. Use auto to infer from path contents.",
    )
    parser.add_argument("--counts-file", help="NanoString/CosMx counts CSV filename relative to --path")
    parser.add_argument("--meta-file", help="NanoString/CosMx metadata CSV filename relative to --path")
    parser.add_argument("--fov-file", help="Optional NanoString/CosMx FOV positions CSV filename relative to --path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    reporter = Reporter()
    path = Path(args.path).expanduser()

    if not path.exists():
        reporter.error(f"Path does not exist: {path}")
        reporter.print()
        return 2

    kind = infer_kind(path) if args.kind == "auto" else args.kind
    if kind == "unknown":
        reporter.error("Could not infer kind. Re-run with --kind h5ad|visium-hd-bin|visium-hd-cellseg|xenium|nanostring")
        reporter.print()
        return 2

    reporter.ok(f"kind={kind}")
    if kind == "h5ad":
        check_h5ad(path, reporter)
    elif kind == "visium-hd-bin":
        check_visium_hd_bin(path, reporter)
    elif kind == "visium-hd-cellseg":
        check_visium_hd_cellseg(path, reporter)
    elif kind == "xenium":
        check_xenium(path, reporter)
    elif kind == "nanostring":
        check_nanostring(path, reporter, args.counts_file, args.meta_file, args.fov_file)
    else:
        reporter.error(f"Unsupported kind: {kind}")

    reporter.print()
    return 1 if reporter.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
