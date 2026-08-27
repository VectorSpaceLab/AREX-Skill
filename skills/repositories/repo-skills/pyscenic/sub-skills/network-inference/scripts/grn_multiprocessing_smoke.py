#!/usr/bin/env python3
"""
Safe pySCENIC network-inference smoke helper.

This helper validates imports and prints command templates for `pyscenic grn`,
`pyscenic add_cor`, and `arboreto_with_multiprocessing.py`. By default it does
not run GRNBoost2, GENIE3, downloads, training, or destructive operations.
Use `--make-fixtures DIR` to create tiny deterministic expression/TF/adjacency
fixtures for command construction, and `--run-api-smoke` to exercise only
`add_correlation()` and `modules_from_adjacencies()` on an in-memory toy table.
"""

from __future__ import annotations

import argparse
import csv
import importlib
import shutil
import sys
from pathlib import Path


EXPR_ROWS = [
    ["cell", "TF_A", "TF_B", "Gene_1", "Gene_2", "Gene_3", "Gene_4"],
    ["cell_1", 8.0, 0.0, 6.0, 0.0, 2.0, 5.0],
    ["cell_2", 7.0, 1.0, 5.0, 0.0, 2.5, 4.5],
    ["cell_3", 1.0, 6.0, 0.0, 5.0, 4.0, 1.0],
    ["cell_4", 0.0, 7.0, 0.0, 6.0, 4.5, 0.5],
    ["cell_5", 6.0, 1.0, 4.0, 1.0, 2.5, 3.5],
    ["cell_6", 1.0, 6.0, 1.0, 5.5, 4.0, 1.5],
]

ADJ_ROWS = [
    ["TF", "target", "importance"],
    ["TF_A", "Gene_1", 0.95],
    ["TF_A", "Gene_2", 0.72],
    ["TF_A", "Gene_3", 0.55],
    ["TF_A", "Gene_4", 0.43],
    ["TF_B", "Gene_2", 0.96],
    ["TF_B", "Gene_3", 0.75],
    ["TF_B", "Gene_4", 0.47],
]

TF_NAMES = ["TF_A", "TF_B", "Missing_TF"]


class SmokeError(RuntimeError):
    pass


def import_required_modules() -> list[str]:
    modules = [
        "pyscenic",
        "pyscenic.utils",
        "pyscenic.math",
        "arboreto.algo",
        "arboreto.utils",
        "pandas",
        "numpy",
    ]
    failures: list[str] = []
    for module_name in modules:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - diagnostic path
            failures.append(f"{module_name}: {exc.__class__.__name__}: {exc}")
    return failures


def write_csv(path: Path, rows: list[list[object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


def write_fixtures(output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    expr_path = output_dir / "toy_expression_cells_by_genes.csv"
    tfs_path = output_dir / "toy_tfs.txt"
    adj_path = output_dir / "toy_adjacencies.csv"
    existing_paths = [path for path in (expr_path, tfs_path, adj_path) if path.exists()]
    if existing_paths:
        paths = ", ".join(str(path) for path in existing_paths)
        raise SmokeError(f"refusing to overwrite existing fixture file(s): {paths}")
    write_csv(expr_path, EXPR_ROWS)
    tfs_path.write_text("\n".join(TF_NAMES) + "\n")
    write_csv(adj_path, ADJ_ROWS)
    return {"expr": expr_path, "tfs": tfs_path, "adj": adj_path}


def check_executables() -> dict[str, str | None]:
    return {
        "pyscenic": shutil.which("pyscenic"),
        "arboreto_with_multiprocessing.py": shutil.which("arboreto_with_multiprocessing.py"),
    }


def print_templates(expr_path: Path, tfs_path: Path, adj_path: Path) -> None:
    print("\nCommand templates only; no expensive inference was run.\n")
    print("Dask-backed pySCENIC GRNBoost2:")
    print(
        "  pyscenic grn --method grnboost2 --num_workers 4 --seed 777 "
        f"-o adjacencies.tsv {expr_path} {tfs_path}"
    )
    print("\nDask-backed pySCENIC GENIE3:")
    print(
        "  pyscenic grn --method genie3 --num_workers 4 --seed 777 "
        f"-o adjacencies.tsv {expr_path} {tfs_path}"
    )
    print("\nDask-free Arboreto multiprocessing fallback:")
    print(
        "  arboreto_with_multiprocessing.py --method grnboost2 --num_workers 4 --seed 777 "
        f"--output adjacencies.tsv {expr_path} {tfs_path}"
    )
    print("\nAdd Pearson correlations to an adjacency table:")
    print(f"  pyscenic add_cor --mask_dropouts -o adjacencies_with_rho.csv {adj_path} {expr_path}")
    print("\nIf the expression file is genes-by-cells CSV/TSV, add `--transpose` to GRN and add_cor commands.")


def run_api_smoke() -> None:
    import pandas as pd
    from pyscenic.utils import add_correlation, modules_from_adjacencies

    expression = pd.DataFrame(
        data=[row[1:] for row in EXPR_ROWS[1:]],
        index=[row[0] for row in EXPR_ROWS[1:]],
        columns=EXPR_ROWS[0][1:],
        dtype=float,
    )
    adjacencies = pd.DataFrame(ADJ_ROWS[1:], columns=ADJ_ROWS[0])
    adjacencies["importance"] = adjacencies["importance"].astype(float)

    with_rho = add_correlation(adjacencies, expression, mask_dropouts=True)
    expected_columns = {"TF", "target", "importance", "regulation", "rho"}
    if not expected_columns.issubset(with_rho.columns):
        raise SmokeError(f"add_correlation missing expected columns: {sorted(with_rho.columns)}")
    if with_rho["rho"].isna().all():
        raise SmokeError("add_correlation returned only NaN rho values for the toy fixture")

    modules = modules_from_adjacencies(
        with_rho,
        expression,
        thresholds=(0.5,),
        top_n_targets=(3,),
        top_n_regulators=(2,),
        min_genes=2,
        keep_only_activating=False,
        rho_mask_dropouts=True,
    )
    if not modules:
        raise SmokeError("modules_from_adjacencies returned no modules for the toy fixture")
    print(f"API smoke passed: {len(with_rho)} links with rho/regulation; {len(modules)} modules built.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate pySCENIC network-inference imports and print safe GRN/add_cor templates."
    )
    parser.add_argument(
        "--make-fixtures",
        type=Path,
        help="Create tiny expression, TF-list, and adjacency fixtures in this directory.",
    )
    parser.add_argument(
        "--run-api-smoke",
        action="store_true",
        help="Run only add_correlation/modules_from_adjacencies on deterministic in-memory toy data.",
    )
    parser.add_argument(
        "--expr",
        type=Path,
        help="Expression matrix path to show in command templates instead of the toy fixture path.",
    )
    parser.add_argument(
        "--tfs",
        type=Path,
        help="TF list path to show in command templates instead of the toy fixture path.",
    )
    parser.add_argument(
        "--adjacencies",
        type=Path,
        help="Adjacency table path to show in add_cor templates instead of the toy fixture path.",
    )
    parser.add_argument(
        "--no-templates",
        action="store_true",
        help="Only perform import/executable checks and optional API smoke; do not print command templates.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    failures = import_required_modules()
    if failures:
        print("Import check failed. Install pySCENIC with its Arboreto dependencies before GRN inference:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 2
    print("Import check passed for pySCENIC, Arboreto, pandas, and numpy.")

    executables = check_executables()
    for name, path in executables.items():
        if path:
            print(f"Executable found: {name} -> {path}")
        else:
            print(f"Executable not found on PATH: {name}. Use `python -m pyscenic.cli.pyscenic` or check installation.")

    fixture_paths: dict[str, Path] = {}
    if args.make_fixtures:
        try:
            fixture_paths = write_fixtures(args.make_fixtures)
        except SmokeError as exc:
            print(f"Fixture creation failed: {exc}", file=sys.stderr)
            return 3
        print(f"Wrote toy fixtures under: {args.make_fixtures}")

    expr_path = args.expr or fixture_paths.get("expr") or Path("expression_cells_by_genes.csv")
    tfs_path = args.tfs or fixture_paths.get("tfs") or Path("tfs.txt")
    adj_path = args.adjacencies or fixture_paths.get("adj") or Path("adjacencies.csv")

    if args.run_api_smoke:
        try:
            run_api_smoke()
        except SmokeError as exc:
            print(f"API smoke failed: {exc}", file=sys.stderr)
            return 3
        except Exception as exc:  # pragma: no cover - diagnostic path
            print(f"API smoke raised {exc.__class__.__name__}: {exc}", file=sys.stderr)
            return 3

    if not args.no_templates:
        print_templates(expr_path, tfs_path, adj_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
