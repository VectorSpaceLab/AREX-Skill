#!/usr/bin/env python3
"""Build a safe DiffDock evaluation command without running it."""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from typing import Iterable


DATASET_CHOICES = ("pdbbind", "moad", "posebusters")


def add_if_value(command: list[str], flag: str, value: object | None) -> None:
    if value is None:
        return
    if isinstance(value, str) and value == "":
        return
    command.extend([flag, str(value)])


def add_bool(command: list[str], flag: str, enabled: bool) -> None:
    if enabled:
        command.append(flag)


def existing_path_warnings(paths: Iterable[tuple[str, str | None]]) -> list[str]:
    warnings: list[str] = []
    for label, path in paths:
        if path and not os.path.exists(path):
            warnings.append(f"{label} does not exist from the current working directory: {path}")
    return warnings


def validate_args(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if args.dataset not in DATASET_CHOICES:
        errors.append(f"--dataset must be one of: {', '.join(DATASET_CHOICES)}")

    if not args.data_dir:
        errors.append("--data-dir is required")

    if args.dataset in {"pdbbind", "posebusters"} and not args.split_path:
        errors.append(f"--split-path is required for dataset {args.dataset}")

    if args.dataset == "moad":
        if args.split_path:
            warnings.append("MOAD/DockGen evaluation uses --split; --split-path is usually ignored by the MOAD loader")
        if not args.split:
            errors.append("--split is required for dataset moad")
        if args.esm_embeddings_path and not args.moad_esm_embeddings_sequences_path:
            errors.append("--moad-esm-embeddings-sequences-path is required for MOAD when --esm-embeddings-path is set")
        if args.protein_file != "protein_processed":
            warnings.append("MOAD does not use the PDBBind-style --protein-file suffix")
        if args.ligand_file != "ligand":
            warnings.append("MOAD does not use the PDBBind-style --ligand-file suffix")

    if args.dataset == "posebusters":
        if args.protein_file != "protein":
            errors.append("PoseBusters processed data normally requires --protein-file protein")
        if args.ligand_file != "ligands":
            errors.append("PoseBusters processed data normally requires --ligand-file ligands")

    if args.samples_per_complex is not None:
        if args.samples_per_complex <= 0:
            errors.append("--samples-per-complex must be positive")
        elif args.samples_per_complex < 5:
            warnings.append("top5/top10 metrics require at least 5/10 samples per complex")
        elif args.samples_per_complex < 10:
            warnings.append("top10 metrics require at least 10 samples per complex")

    if args.batch_size is not None and args.batch_size <= 0:
        errors.append("--batch-size must be positive")

    if args.limit_complexes is not None and args.limit_complexes < 0:
        errors.append("--limit-complexes must be non-negative")

    if args.gnina_poses_to_optimize is not None and args.gnina_poses_to_optimize <= 0:
        errors.append("--gnina-poses-to-optimize must be positive")

    if args.gnina_poses_to_optimize and args.samples_per_complex and args.gnina_poses_to_optimize > args.samples_per_complex:
        errors.append("--gnina-poses-to-optimize cannot exceed --samples-per-complex")

    if args.save_gnina_metrics and not args.gnina_minimize:
        warnings.append("--save-gnina-metrics is only useful when --gnina-minimize is enabled")

    if args.gnina_full_dock and not args.gnina_minimize:
        warnings.append("--gnina-full-dock has no effect unless --gnina-minimize is enabled")

    if args.gnina_minimize:
        warnings.append("GNINA is an external executable; verify --gnina-path and receptor naming before running")
        if not args.out_dir:
            warnings.append("provide --out-dir and pre-create its gnina_logs subdirectory before GNINA runs")

    if args.no_model and (args.model_dir or args.ckpt):
        warnings.append("--no-model skips score model loading even if model checkpoint flags are present")

    if args.check_paths:
        paths = [
            ("config", args.config),
            ("data dir", args.data_dir),
            ("split path", args.split_path),
            ("ESM embeddings", args.esm_embeddings_path),
            ("MOAD ESM sequence map", args.moad_esm_embeddings_sequences_path),
            ("model dir", args.model_dir),
            ("confidence model dir", args.confidence_model_dir),
        ]
        warnings.extend(existing_path_warnings(paths))

    return errors, warnings


def build_command(args: argparse.Namespace) -> list[str]:
    command = ["python", "-m", "evaluate"]

    add_if_value(command, "--config", args.config)
    add_if_value(command, "--dataset", args.dataset)
    add_if_value(command, "--data_dir", args.data_dir)
    add_if_value(command, "--split_path", args.split_path)
    add_if_value(command, "--split", args.split)
    add_if_value(command, "--esm_embeddings_path", args.esm_embeddings_path)
    add_if_value(command, "--moad_esm_embeddings_sequences_path", args.moad_esm_embeddings_sequences_path)
    add_if_value(command, "--model_dir", args.model_dir)
    add_if_value(command, "--ckpt", args.ckpt)
    add_if_value(command, "--confidence_model_dir", args.confidence_model_dir)
    add_if_value(command, "--confidence_ckpt", args.confidence_ckpt)
    add_if_value(command, "--out_dir", args.out_dir)
    add_if_value(command, "--run_name", args.run_name)
    add_if_value(command, "--batch_size", args.batch_size)
    add_if_value(command, "--samples_per_complex", args.samples_per_complex)
    add_if_value(command, "--inference_steps", args.inference_steps)
    add_if_value(command, "--actual_steps", args.actual_steps)
    add_if_value(command, "--chain_cutoff", args.chain_cutoff)
    add_if_value(command, "--limit_complexes", args.limit_complexes)
    add_if_value(command, "--num_workers", args.num_workers)
    add_if_value(command, "--num_cpu", args.num_cpu)
    add_if_value(command, "--protein_file", args.protein_file)
    add_if_value(command, "--ligand_file", args.ligand_file)
    add_if_value(command, "--min_ligand_size", args.min_ligand_size)
    add_if_value(command, "--max_receptor_size", args.max_receptor_size)
    add_if_value(command, "--remove_promiscuous_targets", args.remove_promiscuous_targets)
    add_if_value(command, "--cache_path", args.cache_path)

    add_bool(command, "--tqdm", args.tqdm)
    add_bool(command, "--restrict_cpu", args.restrict_cpu)
    add_bool(command, "--no_model", args.no_model)
    add_bool(command, "--no_random", args.no_random)
    add_bool(command, "--no_final_step_noise", args.no_final_step_noise)
    add_bool(command, "--save_visualisation", args.save_visualisation)
    add_bool(command, "--save_complexes", args.save_complexes)
    add_bool(command, "--unroll_clusters", args.unroll_clusters)
    add_bool(command, "--remove_pdbbind", args.remove_pdbbind)
    add_bool(command, "--skip_matching", args.skip_matching)

    add_bool(command, "--gnina_minimize", args.gnina_minimize)
    add_if_value(command, "--gnina_path", args.gnina_path if args.gnina_minimize else None)
    add_bool(command, "--gnina_full_dock", args.gnina_full_dock)
    add_bool(command, "--save_gnina_metrics", args.save_gnina_metrics)
    add_if_value(command, "--gnina_poses_to_optimize", args.gnina_poses_to_optimize if args.gnina_minimize else None)
    add_if_value(command, "--gnina_autobox_add", args.gnina_autobox_add if args.gnina_full_dock else None)

    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a validated python -m evaluate command for DiffDock benchmarks. This helper never runs evaluation.",
    )
    parser.add_argument("--dataset", required=True, choices=DATASET_CHOICES)
    parser.add_argument("--data-dir", dest="data_dir", required=True)
    parser.add_argument("--split-path", dest="split_path")
    parser.add_argument("--split", default=None)
    parser.add_argument("--config", default="default_inference_args.yaml")
    parser.add_argument("--esm-embeddings-path", dest="esm_embeddings_path")
    parser.add_argument("--moad-esm-embeddings-sequences-path", dest="moad_esm_embeddings_sequences_path")
    parser.add_argument("--model-dir", dest="model_dir")
    parser.add_argument("--ckpt")
    parser.add_argument("--confidence-model-dir", dest="confidence_model_dir")
    parser.add_argument("--confidence-ckpt", dest="confidence_ckpt")
    parser.add_argument("--out-dir", dest="out_dir")
    parser.add_argument("--run-name", dest="run_name")
    parser.add_argument("--batch-size", dest="batch_size", type=int, default=10)
    parser.add_argument("--samples-per-complex", dest="samples_per_complex", type=int, default=10)
    parser.add_argument("--inference-steps", dest="inference_steps", type=int)
    parser.add_argument("--actual-steps", dest="actual_steps", type=int)
    parser.add_argument("--chain-cutoff", dest="chain_cutoff", type=float, default=10)
    parser.add_argument("--limit-complexes", dest="limit_complexes", type=int)
    parser.add_argument("--num-workers", dest="num_workers", type=int)
    parser.add_argument("--num-cpu", dest="num_cpu", type=int)
    parser.add_argument("--protein-file", dest="protein_file", default="protein_processed")
    parser.add_argument("--ligand-file", dest="ligand_file", default="ligand")
    parser.add_argument("--min-ligand-size", dest="min_ligand_size", type=float)
    parser.add_argument("--max-receptor-size", dest="max_receptor_size", type=float)
    parser.add_argument("--remove-promiscuous-targets", dest="remove_promiscuous_targets", type=float)
    parser.add_argument("--cache-path", dest="cache_path")
    parser.add_argument("--tqdm", action="store_true")
    parser.add_argument("--restrict-cpu", dest="restrict_cpu", action="store_true")
    parser.add_argument("--no-model", dest="no_model", action="store_true")
    parser.add_argument("--no-random", dest="no_random", action="store_true")
    parser.add_argument("--no-final-step-noise", dest="no_final_step_noise", action="store_true")
    parser.add_argument("--save-visualisation", dest="save_visualisation", action="store_true")
    parser.add_argument("--save-complexes", dest="save_complexes", action="store_true")
    parser.add_argument("--unroll-clusters", dest="unroll_clusters", action="store_true")
    parser.add_argument("--remove-pdbbind", dest="remove_pdbbind", action="store_true")
    parser.add_argument("--skip-matching", dest="skip_matching", action="store_true")
    parser.add_argument("--gnina-minimize", dest="gnina_minimize", action="store_true")
    parser.add_argument("--gnina-path", dest="gnina_path", default="gnina")
    parser.add_argument("--gnina-full-dock", dest="gnina_full_dock", action="store_true")
    parser.add_argument("--save-gnina-metrics", dest="save_gnina_metrics", action="store_true")
    parser.add_argument("--gnina-poses-to-optimize", dest="gnina_poses_to_optimize", type=int, default=1)
    parser.add_argument("--gnina-autobox-add", dest="gnina_autobox_add", type=float, default=4.0)
    parser.add_argument("--check-paths", dest="check_paths", action="store_true", help="Warn when supplied paths do not exist from the current working directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors, warnings = validate_args(args)

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 2

    print(shlex.join(build_command(args)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
