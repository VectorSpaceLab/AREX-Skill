#!/usr/bin/env python3
"""Build Chemprop commands for specialized molecular workflows.

The script prints a shell-safe command string and, with --json, the underlying
argv array. It does not inspect local repositories or require Chemprop imports.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Iterable

RXN_MODES = {
    "REAC_PROD",
    "REAC_PROD_BALANCE",
    "REAC_DIFF",
    "REAC_DIFF_BALANCE",
    "PROD_DIFF",
    "PROD_DIFF_BALANCE",
}

TASK_TYPES = {
    "regression",
    "regression-mve",
    "regression-evidential",
    "regression-quantile",
    "classification",
    "classification-dirichlet",
    "multiclass",
    "multiclass-dirichlet",
    "spectral",
}


def add_many(cmd: list[str], flag: str, values: Iterable[str] | None) -> None:
    values = [str(value) for value in values or []]
    if values:
        cmd.extend([flag, *values])


def add_optional(cmd: list[str], flag: str, value: str | int | float | Path | None) -> None:
    if value is not None:
        cmd.extend([flag, str(value)])


def parse_indexed_path(value: str) -> list[str]:
    parts = value.split("=", 1)
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1]:
        raise argparse.ArgumentTypeError(
            "indexed paths must use INDEX=PATH syntax, for example 1=solvent_atom_descs.npz"
        )
    return [parts[0], parts[1]]


def add_indexed_paths(cmd: list[str], flag: str, values: list[list[str]] | None) -> None:
    for pair in values or []:
        cmd.extend([flag, *pair])


def component_count(args: argparse.Namespace) -> int:
    return max(1, len(args.reaction_columns or []) + len(args.smiles_columns or []))


def validate_common(args: argparse.Namespace) -> None:
    if args.task_type and args.task_type not in TASK_TYPES:
        raise SystemExit(f"unsupported task type: {args.task_type}")
    if args.rxn_mode and args.rxn_mode.upper() not in RXN_MODES:
        raise SystemExit(f"unsupported rxn mode: {args.rxn_mode}")
    if args.reorder_atoms and args.use_cuikmolmaker_featurization:
        raise SystemExit("--reorder-atoms cannot be combined with --use-cuikmolmaker-featurization")

    count = component_count(args)
    if len(args.message_hidden_dim or []) > 1 and len(args.message_hidden_dim) != count:
        raise SystemExit(
            f"--message-hidden-dim must have one value or exactly {count} component values"
        )
    if len(args.depth or []) > 1 and len(args.depth) != count:
        raise SystemExit(f"--depth must have one value or exactly {count} component values")
    if args.mpn_shared and ((args.message_hidden_dim and len(args.message_hidden_dim) > 1) or (args.depth and len(args.depth) > 1)):
        raise SystemExit("--mpn-shared cannot be combined with component-specific dimensions")
    if args.mpn_shared and args.reaction_columns and args.smiles_columns:
        raise SystemExit("--mpn-shared is not valid for mixed reaction+molecule data")


def build_base_command(args: argparse.Namespace) -> list[str]:
    cmd = ["chemprop", args.subcommand, "-i", str(args.input)]
    add_many(cmd, "--smiles-columns", args.smiles_columns)
    add_many(cmd, "--reaction-columns", args.reaction_columns)
    if args.rxn_mode:
        cmd.extend(["--rxn-mode", args.rxn_mode.upper()])
    add_optional(cmd, "--model-path", args.model_path)
    add_optional(cmd, "-o", args.output)
    add_optional(cmd, "--save-dir", args.save_dir)
    add_optional(cmd, "--epochs", args.epochs)
    add_optional(cmd, "--num-workers", args.num_workers)
    add_optional(cmd, "--accelerator", args.accelerator)
    add_optional(cmd, "--split-key-molecule", args.split_key_molecule)
    add_many(cmd, "--message-hidden-dim", args.message_hidden_dim)
    add_many(cmd, "--depth", args.depth)
    if args.mpn_shared:
        cmd.append("--mpn-shared")
    if args.keep_h:
        cmd.append("--keep-h")
    if args.reorder_atoms:
        cmd.append("--reorder-atoms")
    if args.use_cuikmolmaker_featurization:
        cmd.append("--use-cuikmolmaker-featurization")
    return cmd


def add_training_options(cmd: list[str], args: argparse.Namespace) -> None:
    add_many(cmd, "--target-columns", args.target_columns)
    add_many(cmd, "--mol-target-columns", args.mol_target_columns)
    add_many(cmd, "--atom-target-columns", args.atom_target_columns)
    add_many(cmd, "--bond-target-columns", args.bond_target_columns)
    add_optional(cmd, "--weight-column", args.weight_column)
    if args.task_type:
        cmd.extend(["--task-type", args.task_type])
    add_optional(cmd, "--loss-function", args.loss_function)
    add_many(cmd, "--metrics", args.metrics)
    add_optional(cmd, "--tracking-metric", args.tracking_metric)
    add_optional(cmd, "--evidential-regularization", args.evidential_regularization)
    add_optional(cmd, "--alpha", args.alpha)
    add_optional(cmd, "--constraints-path", args.constraints_path)
    add_many(cmd, "--constraints-to-targets", args.constraints_to_targets)
    if args.show_individual_scores:
        cmd.append("--show-individual-scores")


def add_feature_options(cmd: list[str], args: argparse.Namespace) -> None:
    add_optional(cmd, "--descriptors-path", args.descriptors_path)
    add_many(cmd, "--descriptors-columns", args.descriptors_columns)
    add_many(cmd, "--molecule-featurizers", args.molecule_featurizers)
    add_indexed_paths(cmd, "--atom-features-path", args.atom_features_path)
    add_indexed_paths(cmd, "--atom-descriptors-path", args.atom_descriptors_path)
    add_indexed_paths(cmd, "--bond-features-path", args.bond_features_path)
    add_indexed_paths(cmd, "--bond-descriptors-path", args.bond_descriptors_path)
    if args.no_descriptor_scaling:
        cmd.append("--no-descriptor-scaling")
    if args.no_atom_feature_scaling:
        cmd.append("--no-atom-feature-scaling")
    if args.no_atom_descriptor_scaling:
        cmd.append("--no-atom-descriptor-scaling")
    if args.no_bond_feature_scaling:
        cmd.append("--no-bond-feature-scaling")
    if args.no_bond_descriptor_scaling:
        cmd.append("--no-bond-descriptor-scaling")


def build_command(args: argparse.Namespace) -> list[str]:
    validate_common(args)
    cmd = build_base_command(args)
    if args.subcommand == "train":
        add_training_options(cmd, args)
    add_feature_options(cmd, args)
    return cmd


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build shell-safe Chemprop commands for reaction, multicomponent, MolAtomBond, constrained, and spectral workflows."
    )
    parser.add_argument("subcommand", choices=["train", "predict", "fingerprint"])
    parser.add_argument("-i", "--input", required=True, type=Path)
    parser.add_argument("--smiles-columns", nargs="+")
    parser.add_argument("--reaction-columns", nargs="+")
    parser.add_argument("--rxn-mode", default=None)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--save-dir", type=Path)
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--num-workers", type=int)
    parser.add_argument("--accelerator")
    parser.add_argument("--split-key-molecule", type=int)
    parser.add_argument("--message-hidden-dim", nargs="+")
    parser.add_argument("--depth", nargs="+")
    parser.add_argument("--mpn-shared", action="store_true")
    parser.add_argument("--keep-h", action="store_true")
    parser.add_argument("--reorder-atoms", action="store_true")
    parser.add_argument("--use-cuikmolmaker-featurization", action="store_true")

    parser.add_argument("--target-columns", nargs="+")
    parser.add_argument("--mol-target-columns", nargs="+")
    parser.add_argument("--atom-target-columns", nargs="+")
    parser.add_argument("--bond-target-columns", nargs="+")
    parser.add_argument("--weight-column")
    parser.add_argument("--task-type")
    parser.add_argument("--loss-function")
    parser.add_argument("--metrics", nargs="+")
    parser.add_argument("--tracking-metric")
    parser.add_argument("--evidential-regularization", type=float)
    parser.add_argument("--alpha", type=float)
    parser.add_argument("--constraints-path", type=Path)
    parser.add_argument("--constraints-to-targets", nargs="+")
    parser.add_argument("--show-individual-scores", action="store_true")

    parser.add_argument("--descriptors-path", type=Path)
    parser.add_argument("--descriptors-columns", nargs="+")
    parser.add_argument("--molecule-featurizers", nargs="+")
    parser.add_argument("--atom-features-path", action="append", type=parse_indexed_path)
    parser.add_argument("--atom-descriptors-path", action="append", type=parse_indexed_path)
    parser.add_argument("--bond-features-path", action="append", type=parse_indexed_path)
    parser.add_argument("--bond-descriptors-path", action="append", type=parse_indexed_path)
    parser.add_argument("--no-descriptor-scaling", action="store_true")
    parser.add_argument("--no-atom-feature-scaling", action="store_true")
    parser.add_argument("--no-atom-descriptor-scaling", action="store_true")
    parser.add_argument("--no-bond-feature-scaling", action="store_true")
    parser.add_argument("--no-bond-descriptor-scaling", action="store_true")

    parser.add_argument("--json", action="store_true", help="Also print the argv array as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    cmd = build_command(args)
    print(shlex.join(cmd))
    if args.json:
        print(json.dumps(cmd, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
