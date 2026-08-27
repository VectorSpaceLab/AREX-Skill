#!/usr/bin/env python3
"""Tiny deterministic pySCENIC AUCell smoke helper.

The helper generates a small expression matrix and two in-memory gene
signatures, runs the AUCell API, checks cells x regulons orientation, and can
optionally run binarization or print equivalent CLI guidance. It performs no
network access, downloads, training, or destructive actions.
"""

import argparse
import shutil
import sys
from typing import List, Optional, Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a tiny deterministic pySCENIC AUCell API smoke test."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=13,
        help="Seed for AUCell ranking tie handling and thresholding. Default: 13.",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=1,
        help="Worker count for AUCell and binarization. Default: 1 for safe smoke tests.",
    )
    parser.add_argument(
        "--auc-threshold",
        type=float,
        default=0.5,
        help="Fraction of ranked genes used for AUC. Default: 0.5 for the tiny fixture.",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Normalize each regulon's AUC values to a maximum of 1.0.",
    )
    parser.add_argument(
        "--binarize",
        action="store_true",
        help="Also run pyscenic.binarization.binarize on the tiny AUC matrix.",
    )
    parser.add_argument(
        "--show-cli",
        action="store_true",
        help="Print equivalent pyscenic aucell CLI guidance for user-provided files.",
    )
    return parser


def import_dependencies():
    try:
        import pandas as pd
        from ctxcore.genesig import GeneSignature
        from pyscenic.aucell import aucell, derive_auc_threshold
        from pyscenic.binarization import binarize
    except ImportError as exc:
        print(
            "ERROR: Could not import pySCENIC AUCell dependencies. "
            "Install pySCENIC and ctxcore in the active Python environment.",
            file=sys.stderr,
        )
        print(f"Import detail: {exc}", file=sys.stderr)
        return None
    return pd, GeneSignature, aucell, derive_auc_threshold, binarize


def print_cli_guidance() -> None:
    executable = shutil.which("pyscenic")
    command_name = executable or "pyscenic"
    print("\nEquivalent CLI guidance for real files:")
    print(
        f"  {command_name} aucell expression.cells_x_genes.csv signatures.gmt "
        "--auc_threshold 0.05 --num_workers 1 --seed 13 -o auc.csv"
    )
    print(
        f"  {command_name} aucell --transpose expression.genes_x_cells.tsv "
        "signatures.gmt --num_workers 1 --seed 13 -o auc.csv"
    )
    if executable is None:
        print("  Note: no 'pyscenic' executable was found on PATH; API imports may still work.")


def run_smoke(args: argparse.Namespace) -> int:
    deps = import_dependencies()
    if deps is None:
        return 2

    pd, GeneSignature, aucell, derive_auc_threshold, binarize = deps

    expression = pd.DataFrame(
        data=[
            [9.0, 8.0, 0.0, 0.0],
            [8.0, 7.0, 0.0, 1.0],
            [0.0, 1.0, 9.0, 8.0],
            [1.0, 0.0, 8.0, 7.0],
        ],
        index=["Cell_A1", "Cell_A2", "Cell_B1", "Cell_B2"],
        columns=["GeneA", "GeneB", "GeneC", "GeneD"],
    )
    signatures = [
        GeneSignature(name="Regulon_AB", gene2weight={"GeneA": 1.0, "GeneB": 1.0}),
        GeneSignature(name="Regulon_CD", gene2weight={"GeneC": 1.0, "GeneD": 1.0}),
    ]

    try:
        threshold_candidates = derive_auc_threshold(expression)
        auc_matrix = aucell(
            expression,
            signatures,
            auc_threshold=args.auc_threshold,
            noweights=False,
            normalize=args.normalize,
            seed=args.seed,
            num_workers=args.num_workers,
        )
    except Exception as exc:  # pragma: no cover - helper prints runtime diagnostics.
        print(f"ERROR: AUCell smoke run failed: {exc}", file=sys.stderr)
        return 1

    expected_cells = list(expression.index)
    expected_regulons = [signature.name for signature in signatures]
    failures: List[str] = []
    if list(auc_matrix.index) != expected_cells:
        failures.append(
            f"AUC index should be cells {expected_cells}, got {list(auc_matrix.index)}"
        )
    if list(auc_matrix.columns) != expected_regulons:
        failures.append(
            "AUC columns should be regulons "
            f"{expected_regulons}, got {list(auc_matrix.columns)}"
        )
    if auc_matrix.loc[["Cell_A1", "Cell_A2"], "Regulon_AB"].mean() <= auc_matrix.loc[
        ["Cell_B1", "Cell_B2"], "Regulon_AB"
    ].mean():
        failures.append("Regulon_AB should score higher in Cell_A* than Cell_B*.")
    if auc_matrix.loc[["Cell_B1", "Cell_B2"], "Regulon_CD"].mean() <= auc_matrix.loc[
        ["Cell_A1", "Cell_A2"], "Regulon_CD"
    ].mean():
        failures.append("Regulon_CD should score higher in Cell_B* than Cell_A*.")

    print("Expression matrix shape:", expression.shape, "(cells x genes)")
    print("AUC threshold candidates:")
    print(threshold_candidates.to_string())
    print("AUC matrix shape:", auc_matrix.shape, "(cells x regulons)")
    print(auc_matrix.round(6).to_string())

    if args.binarize:
        try:
            binary_matrix, thresholds = binarize(
                auc_matrix,
                threshold_overides={
                    "Regulon_AB": float(auc_matrix["Regulon_AB"].mean()),
                    "Regulon_CD": float(auc_matrix["Regulon_CD"].mean()),
                },
                seed=args.seed,
                num_workers=args.num_workers,
            )
        except Exception as exc:  # pragma: no cover - helper prints runtime diagnostics.
            print(f"ERROR: Binarization smoke run failed: {exc}", file=sys.stderr)
            return 1
        print("Binarization thresholds:")
        print(thresholds.to_string())
        print("Binary activity matrix:")
        print(binary_matrix.to_string())

    if failures:
        print("ERROR: AUCell smoke assertions failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    if args.show_cli:
        print_cli_guidance()

    print("AUCell smoke test passed.")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_smoke(args)


if __name__ == "__main__":
    raise SystemExit(main())
