#!/usr/bin/env python3
"""Probe pySCENIC matrix I/O orientation and optional loom support.

The probe creates tiny CSV/TSV fixtures in a temporary directory, exercises
pySCENIC's load/save helpers, and removes the temporary files on success or
failure. It performs no network access, downloads, training, or destructive
operations.
"""

import argparse
import importlib.util
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Optional


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create tiny CSV/TSV matrices and verify pySCENIC load/save "
            "orientation. Loom checks run only when loom support imports."
        )
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary fixture directory and print its path.",
    )
    parser.add_argument(
        "--skip-loom",
        action="store_true",
        help="Skip optional loom write/read checks even if loompy is importable.",
    )
    return parser.parse_args(argv)


def require_imports():
    missing = [
        name
        for name in ("pyscenic", "pandas", "numpy")
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        raise RuntimeError(
            "Missing required import(s): {}. Activate an environment with "
            "pySCENIC and its core runtime dependencies installed.".format(
                ", ".join(missing)
            )
        )

    import pandas as pd
    from pyscenic.cli.utils import load_exp_matrix, save_matrix

    return pd, load_exp_matrix, save_matrix


def assert_frame_equal(actual, expected, label: str) -> None:
    if list(actual.index) != list(expected.index):
        raise AssertionError(
            f"{label}: index mismatch: {list(actual.index)} != {list(expected.index)}"
        )
    if list(actual.columns) != list(expected.columns):
        raise AssertionError(
            f"{label}: columns mismatch: {list(actual.columns)} != {list(expected.columns)}"
        )
    if actual.shape != expected.shape:
        raise AssertionError(f"{label}: shape mismatch: {actual.shape} != {expected.shape}")
    if not actual.equals(expected):
        raise AssertionError(f"{label}: values differ")


def run_probe(args: argparse.Namespace) -> int:
    pd, load_exp_matrix, save_matrix = require_imports()

    with tempfile.TemporaryDirectory(prefix="pyscenic-io-probe-") as temp_name:
        temp_dir = Path(temp_name)
        cells_by_genes = pd.DataFrame(
            [[1.0, 0.0, 3.5], [0.0, 2.0, 4.0]],
            index=["CellA", "CellB"],
            columns=["Gene1", "Gene2", "Gene3"],
        )

        csv_path = temp_dir / "cells_by_genes.csv"
        tsv_genes_by_cells_path = temp_dir / "genes_by_cells.tsv"
        saved_tsv_path = temp_dir / "saved_cells_by_genes.tsv"
        saved_transposed_csv_path = temp_dir / "saved_genes_by_cells.csv"

        cells_by_genes.to_csv(csv_path)
        cells_by_genes.T.to_csv(tsv_genes_by_cells_path, sep="\t")

        loaded_csv = load_exp_matrix(str(csv_path))
        assert_frame_equal(loaded_csv, cells_by_genes, "CSV cells x genes load")

        loaded_transposed_tsv = load_exp_matrix(str(tsv_genes_by_cells_path), transpose=True)
        assert_frame_equal(
            loaded_transposed_tsv,
            cells_by_genes,
            "TSV genes x cells load with transpose",
        )

        save_matrix(cells_by_genes, str(saved_tsv_path))
        reloaded_saved_tsv = load_exp_matrix(str(saved_tsv_path))
        assert_frame_equal(reloaded_saved_tsv, cells_by_genes, "TSV save/load")

        save_matrix(cells_by_genes, str(saved_transposed_csv_path), transpose=True)
        reloaded_saved_transposed = load_exp_matrix(
            str(saved_transposed_csv_path), transpose=True
        )
        assert_frame_equal(
            reloaded_saved_transposed,
            cells_by_genes,
            "CSV transposed save/load",
        )

        print("text_io: ok")
        print("orientation: cells x genes verified; transpose handles genes x cells text")

        loom_available = importlib.util.find_spec("loompy") is not None
        if args.skip_loom:
            print("loom_io: skipped by --skip-loom")
        elif not loom_available:
            print("loom_io: skipped because loompy is not importable")
        else:
            loom_path = temp_dir / "matrix.loom"
            save_matrix(cells_by_genes, str(loom_path))
            reloaded_loom = load_exp_matrix(str(loom_path))
            assert_frame_equal(reloaded_loom, cells_by_genes, "loom save/load")
            print("loom_io: ok")

        if args.keep_temp:
            keep_dir = Path(tempfile.mkdtemp(prefix="pyscenic-io-probe-kept-"))
            for fixture in temp_dir.iterdir():
                fixture.rename(keep_dir / fixture.name)
            print(f"kept_temp_dir: {keep_dir}")

    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    try:
        return run_probe(args)
    except Exception as exc:
        print(f"io_format_probe: ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
