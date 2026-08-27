#!/usr/bin/env python3
"""Offline CellTypist annotation smoke check.

This helper creates synthetic expression data, fits a tiny local
CellTypist-compatible model, annotates a temporary count table, and validates
the core result shapes. It passes an explicit model path to avoid built-in
model downloads.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a tiny local CellTypist model and count table, run offline "
            "annotation, and validate predicted_labels, decision_matrix, and "
            "probability_matrix outputs."
        )
    )
    parser.add_argument(
        "--cells",
        type=int,
        default=60,
        help="Number of synthetic query/training cells. Keep above 50 for majority-voting smoke checks. Default: 60.",
    )
    parser.add_argument(
        "--genes",
        type=int,
        default=8,
        help="Number of synthetic genes. Must be at least 4. Default: 8.",
    )
    parser.add_argument(
        "--p-thres",
        type=float,
        default=0.45,
        help="Probability threshold for the probability-match smoke run. Default: 0.45.",
    )
    parser.add_argument(
        "--skip-majority",
        action="store_true",
        help="Skip the precomputed-over-clustering majority-voting smoke run.",
    )
    parser.add_argument(
        "--check-cli",
        action="store_true",
        help="Also run the CellTypist CLI module against the synthetic table and local model.",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="Directory for generated files. Defaults to a temporary directory.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary directory and print its path in the JSON summary.",
    )
    parser.add_argument(
        "--preserve-celltypist-folder",
        action="store_true",
        help="Do not override CELLTYPIST_FOLDER with an isolated temporary cache before importing CellTypist.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a compact JSON summary instead of a human-readable summary.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.cells < 4:
        raise SystemExit("--cells must be at least 4 so both synthetic classes have examples")
    if args.genes < 4:
        raise SystemExit("--genes must be at least 4 so both synthetic signatures have features")
    if not 0 < args.p_thres < 1:
        raise SystemExit("--p-thres must be between 0 and 1")
    if not args.skip_majority and args.cells <= 50:
        raise SystemExit("majority voting is skipped by CellTypist for <=50 cells; use --cells 51+ or --skip-majority")


def make_workdir(args: argparse.Namespace) -> tuple[Path, bool]:
    if args.workdir is not None:
        args.workdir.mkdir(parents=True, exist_ok=True)
        return args.workdir.resolve(), False
    return Path(tempfile.mkdtemp(prefix="celltypist-annotation-smoke-")), True


def make_synthetic_counts(cell_count: int, gene_count: int):
    import numpy as np
    import pandas as pd

    random_generator = np.random.default_rng(17)
    genes = [f"GENE{gene_index:02d}" for gene_index in range(gene_count)]
    cells = [f"cell_{cell_index:03d}" for cell_index in range(cell_count)]
    split_index = cell_count // 2
    labels = np.array(["type_alpha"] * split_index + ["type_beta"] * (cell_count - split_index))

    counts = random_generator.poisson(lam=1.0, size=(cell_count, gene_count)).astype(int)
    alpha_width = max(2, gene_count // 2)
    beta_start = min(alpha_width, gene_count - 2)
    counts[:split_index, :alpha_width] += random_generator.poisson(lam=7.0, size=(split_index, alpha_width))
    counts[split_index:, beta_start:] += random_generator.poisson(lam=7.0, size=(cell_count - split_index, gene_count - beta_start))
    counts += 1

    counts_frame = pd.DataFrame(counts, index=cells, columns=genes)
    return counts_frame, labels


def normalize_log1p(counts_frame):
    import numpy as np

    counts = counts_frame.to_numpy(dtype=float)
    totals = counts.sum(axis=1, keepdims=True)
    normalized = counts / totals * 10000.0
    return np.log1p(normalized)


def train_tiny_model(counts_frame, labels, model_path: Path):
    from celltypist.models import Model
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    normalized = normalize_log1p(counts_frame)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(normalized)
    classifier = LogisticRegression(max_iter=200, solver="lbfgs")
    classifier.fit(scaled, labels)
    classifier.features = counts_frame.columns.astype(str).to_numpy()
    classifier.n_features_in_ = len(classifier.features)

    model = Model(
        classifier,
        scaler,
        {
            "date": "synthetic-smoke",
            "details": "Tiny offline smoke-test model",
            "url": "",
            "source": "synthetic",
            "version": "1",
            "number_celltypes": len(classifier.classes_),
        },
    )
    model.write(str(model_path))
    return model_path.with_suffix(".pkl")


def validate_result(result, expected_cells: int, require_majority: bool = False) -> dict:
    import numpy as np

    if result.cell_count != expected_cells:
        raise AssertionError(f"Expected {expected_cells} cells, observed {result.cell_count}")
    if result.predicted_labels.shape[0] != expected_cells:
        raise AssertionError("predicted_labels row count does not match input cells")
    if result.decision_matrix.shape[0] != expected_cells:
        raise AssertionError("decision_matrix row count does not match input cells")
    if result.probability_matrix.shape != result.decision_matrix.shape:
        raise AssertionError("probability_matrix shape does not match decision_matrix shape")
    if "predicted_labels" not in result.predicted_labels.columns:
        raise AssertionError("predicted_labels column is missing")
    if require_majority and "majority_voting" not in result.predicted_labels.columns:
        raise AssertionError("majority_voting column is missing")
    if not np.isfinite(result.decision_matrix.to_numpy(dtype=float)).all():
        raise AssertionError("decision_matrix contains non-finite values")
    probabilities = result.probability_matrix.to_numpy(dtype=float)
    if not np.isfinite(probabilities).all() or (probabilities < 0).any() or (probabilities > 1).any():
        raise AssertionError("probability_matrix values must be finite and between 0 and 1")

    return {
        "predicted_label_columns": list(result.predicted_labels.columns),
        "decision_shape": list(result.decision_matrix.shape),
        "probability_shape": list(result.probability_matrix.shape),
        "label_counts": result.predicted_labels["predicted_labels"].astype(str).value_counts().sort_index().to_dict(),
    }


def validate_table_exports(result, output_dir: Path, prefix: str) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    result.to_table(folder=str(output_dir), prefix=prefix)
    expected_names = [
        f"{prefix}predicted_labels.csv",
        f"{prefix}decision_matrix.csv",
        f"{prefix}probability_matrix.csv",
    ]
    missing_names = [name for name in expected_names if not (output_dir / name).is_file()]
    if missing_names:
        raise AssertionError(f"Missing table exports: {missing_names}")
    return expected_names


def validate_adata_insertions(result, prefix: str, require_majority_conf: bool = False) -> list[str]:
    insert_conf_by = "majority_voting" if require_majority_conf else "predicted_labels"
    annotated = result.to_adata(
        insert_labels=True,
        insert_conf=True,
        insert_conf_by=insert_conf_by,
        insert_prob=True,
        prefix=prefix,
    )
    required_columns = {f"{prefix}predicted_labels", f"{prefix}conf_score"}
    if require_majority_conf:
        required_columns.add(f"{prefix}majority_voting")
    missing_columns = sorted(required_columns.difference(annotated.obs.columns))
    if missing_columns:
        raise AssertionError(f"Missing AnnData obs columns after to_adata: {missing_columns}")
    return [column for column in annotated.obs.columns if str(column).startswith(prefix)]


def run_cli_check(query_csv: Path, model_path: Path, output_dir: Path, env: dict[str, str]) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "celltypist.command_line",
        "--indata",
        str(query_csv),
        "--model",
        str(model_path),
        "--outdir",
        str(output_dir),
        "--prefix",
        "cli_",
        "--quiet",
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True, env=env)
    expected_names = ["cli_predicted_labels.csv", "cli_decision_matrix.csv", "cli_probability_matrix.csv"]
    missing_names = [name for name in expected_names if not (output_dir / name).is_file()]
    if missing_names:
        raise AssertionError(f"CLI did not create expected output files: {missing_names}")
    if completed.returncode != 0:
        raise AssertionError("CLI smoke command failed")
    return expected_names


def build_summary(args: argparse.Namespace, workdir: Path, created_temp: bool) -> dict:
    if not args.preserve_celltypist_folder:
        os.environ["CELLTYPIST_FOLDER"] = str(workdir / "celltypist_cache")

    import celltypist

    counts_frame, labels = make_synthetic_counts(args.cells, args.genes)
    query_csv = workdir / "query_counts.csv"
    counts_frame.to_csv(query_csv)
    model_path = train_tiny_model(counts_frame, labels, workdir / "tiny_celltypist_model.pkl")

    best_result = celltypist.annotate(str(query_csv), model=str(model_path), mode="best match")
    prob_result = celltypist.annotate(str(query_csv), model=str(model_path), mode="prob match", p_thres=args.p_thres)

    best_summary = validate_result(best_result, args.cells)
    prob_summary = validate_result(prob_result, args.cells)
    exported_tables = validate_table_exports(best_result, workdir / "tables", "best_")
    adata_columns = validate_adata_insertions(prob_result, "prob_")

    majority_summary = None
    majority_adata_columns = []
    if not args.skip_majority:
        cluster_count = 4
        over_clustering = [f"cluster_{cell_index % cluster_count}" for cell_index in range(args.cells)]
        majority_result = celltypist.annotate(
            str(query_csv),
            model=str(model_path),
            mode="prob match",
            p_thres=args.p_thres,
            majority_voting=True,
            over_clustering=over_clustering,
            min_prop=0,
        )
        majority_summary = validate_result(majority_result, args.cells, require_majority=True)
        majority_adata_columns = validate_adata_insertions(majority_result, "mv_", require_majority_conf=True)

    cli_exports = []
    if args.check_cli:
        cli_exports = run_cli_check(query_csv, model_path, workdir / "cli_tables", os.environ.copy())

    summary = {
        "ok": True,
        "celltypist_version": getattr(celltypist, "__version__", "unknown"),
        "cells": args.cells,
        "genes": args.genes,
        "workdir": str(workdir) if args.keep_temp or not created_temp else "removed after successful run",
        "query_table": query_csv.name,
        "model_file": model_path.name,
        "best_match": best_summary,
        "prob_match": prob_summary,
        "majority_voting": majority_summary,
        "table_exports": exported_tables,
        "adata_columns_checked": adata_columns,
        "majority_adata_columns_checked": majority_adata_columns,
        "cli_exports": cli_exports,
        "network_downloads": "not used; annotation receives an explicit local model path",
    }
    return summary


def print_summary(summary: dict, emit_json: bool) -> None:
    if emit_json:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return
    print("CellTypist annotation smoke check passed")
    print(f"- version: {summary['celltypist_version']}")
    print(f"- cells x genes: {summary['cells']} x {summary['genes']}")
    print(f"- best-match decision shape: {summary['best_match']['decision_shape']}")
    print(f"- probability-match labels: {summary['prob_match']['label_counts']}")
    if summary["majority_voting"] is not None:
        print(f"- majority-voting columns: {summary['majority_voting']['predicted_label_columns']}")
    if summary["cli_exports"]:
        print(f"- CLI exports: {summary['cli_exports']}")
    print(f"- workdir: {summary['workdir']}")


def main() -> None:
    args = parse_args()
    validate_args(args)
    workdir, created_temp = make_workdir(args)
    try:
        summary = build_summary(args, workdir, created_temp)
        print_summary(summary, args.json)
    finally:
        if created_temp and not args.keep_temp:
            shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
