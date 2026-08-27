#!/usr/bin/env python3
"""Print a shell-safe `chemprop train` or `chemprop hpopt` command.

This helper performs lightweight argument and CSV-header checks that are useful
before launching expensive Chemprop training. It intentionally does not import
Chemprop and does not execute the generated command.
"""

from __future__ import annotations

import argparse
import csv
import shlex
import sys
from pathlib import Path


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

COMMANDS = {"train", "hpopt"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and print a shell-safe Chemprop train or hpopt command. The command is not run.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--command", choices=sorted(COMMANDS), default="train", help="Chemprop subcommand to print.")
    parser.add_argument("--data-path", nargs="+", required=True, help="One, two, or three input CSV paths.")
    parser.add_argument("--output-dir", help="Training output directory for chemprop train.")
    parser.add_argument("--hpopt-save-dir", help="Hpopt output directory for chemprop hpopt.")
    parser.add_argument("--config-path", help="Config file to include in the command.")
    parser.add_argument("--task-type", default="regression", choices=sorted(TASK_TYPES))
    parser.add_argument("--smiles-columns", nargs="+", help="Molecule SMILES column names.")
    parser.add_argument("--reaction-columns", nargs="+", help="Reaction SMILES column names.")
    parser.add_argument("--target-columns", nargs="+", help="Target column names.")
    parser.add_argument("--ignore-columns", nargs="+", default=[], help="Metadata columns to ignore if targets are inferred.")
    parser.add_argument("--descriptors-columns", nargs="+", default=[], help="Descriptor columns stored in the CSV.")
    parser.add_argument("--weight-column", help="Per-row weight column.")
    parser.add_argument("--splits-column", help="Column containing train/val/test assignments.")
    parser.add_argument("--split-type", help="Split type, for example random or scaffold_balanced.")
    parser.add_argument("--split-sizes", nargs=3, type=float, metavar=("TRAIN", "VAL", "TEST"), help="Train/val/test split fractions.")
    parser.add_argument("--splits-file", help="JSON split file path.")
    parser.add_argument("--data-seed", type=int, help="Split/random seed.")
    parser.add_argument("--metric", dest="metrics", action="append", help="Metric to include; repeat for multiple metrics.")
    parser.add_argument("--loss-function", help="Training loss function.")
    parser.add_argument("--tracking-metric", help="Metric monitored for checkpointing, early stopping, and hpopt objective.")
    parser.add_argument("--epochs", type=int, help="Number of training epochs.")
    parser.add_argument("--warmup-epochs", type=int, help="Warmup epochs.")
    parser.add_argument("--batch-size", type=int, help="Batch size.")
    parser.add_argument("--num-workers", type=int, help="Dataloader workers.")
    parser.add_argument("--ensemble-size", type=int, help="Models per split.")
    parser.add_argument("--num-replicates", type=int, help="Replicate split/training runs.")
    parser.add_argument("--accelerator", help="Lightning accelerator, e.g. cpu, gpu, auto.")
    parser.add_argument("--devices", help="Lightning devices string.")
    parser.add_argument("--message-hidden-dim", nargs="+", type=int, help="Message hidden dimension values.")
    parser.add_argument("--depth", nargs="+", type=int, help="Message-passing depth values.")
    parser.add_argument("--ffn-hidden-dim", nargs="+", type=int, help="FFN hidden dimension values.")
    parser.add_argument("--ffn-num-layers", type=int, help="FFN hidden layer count.")
    parser.add_argument("--aggregation", choices=["mean", "sum", "norm"], help="Graph aggregation mode.")
    parser.add_argument("--molecule-featurizers", nargs="+", help="Molecule featurizers to include.")
    parser.add_argument("--multiclass-num-classes", type=int, help="Class count for multiclass tasks.")
    parser.add_argument("--checkpoint", nargs="+", help="Checkpoint/model paths for transfer learning.")
    parser.add_argument("--freeze-encoder", action="store_true", help="Add --freeze-encoder.")
    parser.add_argument("--frzn-ffn-layers", type=int, help="Number of FFN layers to freeze.")
    parser.add_argument("--from-foundation", help="Foundation model name or local model file.")
    parser.add_argument("--class-balance", action="store_true", help="Add --class-balance.")
    parser.add_argument("--save-data-splits", action="store_true", help="Add --save-data-splits.")
    parser.add_argument("--save-smiles-splits", action="store_true", help="Add --save-smiles-splits.")
    parser.add_argument("--remove-checkpoints", action="store_true", help="Add --remove-checkpoints.")
    parser.add_argument("--descriptors-path", help="External descriptors .npz path.")
    parser.add_argument("--atom-features-path", nargs="+", help="External atom features .npz path or component/path pairs.")
    parser.add_argument("--bond-features-path", nargs="+", help="External bond features .npz path or component/path pairs.")
    parser.add_argument("--atom-descriptors-path", nargs="+", help="External atom descriptors .npz path or component/path pairs.")
    parser.add_argument("--bond-descriptors-path", nargs="+", help="External bond descriptors .npz path or component/path pairs.")
    parser.add_argument("--use-cuikmolmaker-featurization", action="store_true", help="Add optional cuik_molmaker featurization flag.")
    parser.add_argument("--no-header-row", action="store_true", help="Add --no-header-row and skip header-based schema checks.")
    parser.add_argument("--no-cache", action="store_true", help="Add --no-cache.")
    parser.add_argument("--search-parameter-keywords", nargs="+", help="Hpopt search parameter keywords.")
    parser.add_argument("--raytune-num-samples", type=int, help="Hpopt Ray Tune sample count.")
    parser.add_argument("--raytune-search-algorithm", choices=["random", "hyperopt", "optuna"], help="Hpopt search algorithm.")
    parser.add_argument("--raytune-trial-scheduler", choices=["FIFO", "AsyncHyperBand"], help="Hpopt trial scheduler.")
    parser.add_argument("--raytune-num-workers", type=int, help="Hpopt Ray Tune worker count.")
    parser.add_argument("--raytune-use-gpu", action="store_true", help="Add hpopt GPU resource flag.")
    parser.add_argument("--check-schema", action="store_true", help="Read the first CSV header and warn about common schema mistakes.")
    parser.add_argument("--allow-config-output", action="store_true", help="Allow omitting output directory when relying on config-path.")
    parser.add_argument("--dry-run-note", action="store_true", help="Print a note that the command was not executed.")

    args, unknown = parser.parse_known_args()
    if "-k" in unknown or "--num-folds" in unknown:
        raise SystemExit("error: -k/--num-folds was removed; use --num-replicates")
    if unknown:
        raise SystemExit("error: unsupported argument(s): " + " ".join(unknown))
    return args


def csv_header(path: str) -> list[str]:
    with Path(path).open(newline="") as csv_file:
        reader = csv.reader(csv_file)
        try:
            return next(reader)
        except StopIteration:
            return []


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def validate(args: argparse.Namespace) -> None:
    if args.command == "train" and not args.output_dir and not (args.config_path and args.allow_config_output):
        raise SystemExit("error: --output-dir is recommended for train; pass it or use --allow-config-output with --config-path")
    if args.command == "hpopt" and not args.hpopt_save_dir:
        warn("--hpopt-save-dir omitted; Chemprop will use its default hpopt output location")

    if len(args.data_path) > 3:
        raise SystemExit("error: --data-path accepts at most three CSV paths for training")

    non_csv = [path for path in args.data_path if Path(path).suffix.lower() != ".csv"]
    if non_csv:
        raise SystemExit("error: training inputs must be CSV files: " + ", ".join(non_csv))

    if args.class_balance and args.task_type != "classification":
        raise SystemExit("error: --class-balance is only valid with --task-type classification")

    if args.split_sizes is not None:
        total = sum(args.split_sizes)
        if abs(total - 1.0) > 1e-6:
            warn(f"--split-sizes sum to {total:.6g}, not 1.0")
        if len(args.data_path) == 2 and args.split_sizes[2] != 0 and not args.splits_column and not args.splits_file:
            raise SystemExit("error: with two --data-path CSVs, set test split size to 0.0 unless using --splits-column or --splits-file")
    elif len(args.data_path) == 2 and not args.splits_column and not args.splits_file:
        warn("two CSV paths mean trainval/test; add --split-sizes TRAIN VAL 0.0 to avoid Chemprop's default test fraction error")

    if len(args.data_path) == 3 and args.num_replicates and args.num_replicates != 1:
        warn("three separate CSVs map directly to train/val/test; Chemprop fixes replicate splitting to one direct split")

    uses_npz = any(
        value
        for value in [
            args.descriptors_path,
            args.atom_features_path,
            args.bond_features_path,
            args.atom_descriptors_path,
            args.bond_descriptors_path,
        ]
    )
    if len(args.data_path) > 1 and uses_npz:
        warn("separate train/val/test CSV files are not supported for external feature/descriptor .npz workflows")

    if args.epochs is not None and args.warmup_epochs is not None and args.epochs != -1 and args.epochs <= args.warmup_epochs:
        raise SystemExit("error: --epochs should be greater than --warmup-epochs")

    component_count = max(1, len(args.smiles_columns or []) + len(args.reaction_columns or []))
    if component_count == 1:
        if args.message_hidden_dim and len(args.message_hidden_dim) > 1:
            raise SystemExit("error: single-component data accepts only one --message-hidden-dim value")
        if args.depth and len(args.depth) > 1:
            raise SystemExit("error: single-component data accepts only one --depth value")

    if args.ffn_hidden_dim and len(args.ffn_hidden_dim) > 1 and args.ffn_num_layers and len(args.ffn_hidden_dim) != args.ffn_num_layers:
        raise SystemExit("error: multiple --ffn-hidden-dim values must match --ffn-num-layers")

    if args.checkpoint and args.from_foundation:
        raise SystemExit("error: --checkpoint and --from-foundation are mutually exclusive")
    if args.freeze_encoder and not args.checkpoint:
        raise SystemExit("error: --freeze-encoder requires --checkpoint")
    if args.frzn_ffn_layers and args.frzn_ffn_layers > 0 and args.checkpoint and not args.freeze_encoder:
        raise SystemExit("error: --frzn-ffn-layers with --checkpoint also requires --freeze-encoder")

    if args.from_foundation:
        if args.message_hidden_dim or args.depth or args.aggregation:
            warn("foundation initialization may ignore message-passing architecture flags")
        if args.atom_features_path or args.atom_descriptors_path or args.bond_features_path:
            warn("some foundation models, including CheMeleon, reject external atom/bond feature paths")

    if args.use_cuikmolmaker_featurization and (args.reaction_columns or len(args.smiles_columns or []) > 1):
        warn("cuik_molmaker support is optional and limited; verify compatibility for reaction or multicomponent data")

    if args.check_schema:
        if args.no_header_row:
            warn("--check-schema skipped because --no-header-row was set")
        else:
            header = csv_header(args.data_path[0])
            if not header:
                raise SystemExit("error: first CSV appears empty")
            check_columns(args, header)


def check_columns(args: argparse.Namespace, header: list[str]) -> None:
    header_set = set(header)
    smiles = set(args.smiles_columns or ([] if args.reaction_columns else [header[0]]))
    reactions = set(args.reaction_columns or [])
    targets = set(args.target_columns or [])
    ignored = set(args.ignore_columns or [])
    descriptors = set(args.descriptors_columns or [])
    special = {value for value in [args.weight_column, args.splits_column] if value}

    roles = {
        "smiles": smiles,
        "reaction": reactions,
        "target": targets,
        "ignore": ignored,
        "descriptor": descriptors,
        "special": special,
    }
    for role, columns in roles.items():
        missing = sorted(columns - header_set)
        if missing:
            warn(f"{role} column(s) not found in first CSV header: {', '.join(missing)}")

    role_items = list(roles.items())
    for index, (left_name, left_cols) in enumerate(role_items):
        for right_name, right_cols in role_items[index + 1 :]:
            overlap = sorted(left_cols & right_cols)
            if overlap:
                warn(f"columns used as both {left_name} and {right_name}: {', '.join(overlap)}")

    if not args.target_columns:
        inferred_targets = [
            column
            for column in header
            if column not in (smiles | reactions | ignored | descriptors | special)
        ]
        if not inferred_targets:
            warn("no target columns would be inferred from the first CSV header")
        else:
            warn("inferred target columns: " + ", ".join(inferred_targets))


def extend(command: list[str], flag: str, values: list[object] | tuple[object, ...] | None) -> None:
    if values:
        command.append(flag)
        command.extend(str(value) for value in values)


def append_optional(command: list[str], flag: str, value: object | None) -> None:
    if value is not None:
        command.extend([flag, str(value)])


def build_command(args: argparse.Namespace) -> list[str]:
    command = ["chemprop", args.command]
    append_optional(command, "--config-path", args.config_path)
    extend(command, "--data-path", args.data_path)
    command.extend(["--task-type", args.task_type])
    if args.command == "train":
        append_optional(command, "--output-dir", args.output_dir)
    else:
        append_optional(command, "--hpopt-save-dir", args.hpopt_save_dir)
    extend(command, "--smiles-columns", args.smiles_columns)
    extend(command, "--reaction-columns", args.reaction_columns)
    extend(command, "--target-columns", args.target_columns)
    extend(command, "--ignore-columns", args.ignore_columns)
    extend(command, "--descriptors-columns", args.descriptors_columns)
    append_optional(command, "--weight-column", args.weight_column)
    append_optional(command, "--splits-column", args.splits_column)
    append_optional(command, "--split-type", args.split_type)
    if args.split_sizes is not None:
        command.append("--split-sizes")
        command.extend(f"{value:g}" for value in args.split_sizes)
    append_optional(command, "--splits-file", args.splits_file)
    append_optional(command, "--data-seed", args.data_seed)
    extend(command, "--metrics", args.metrics)
    append_optional(command, "--loss-function", args.loss_function)
    append_optional(command, "--tracking-metric", args.tracking_metric)
    append_optional(command, "--epochs", args.epochs)
    append_optional(command, "--warmup-epochs", args.warmup_epochs)
    append_optional(command, "--batch-size", args.batch_size)
    append_optional(command, "--num-workers", args.num_workers)
    append_optional(command, "--ensemble-size", args.ensemble_size)
    append_optional(command, "--num-replicates", args.num_replicates)
    append_optional(command, "--accelerator", args.accelerator)
    append_optional(command, "--devices", args.devices)
    extend(command, "--message-hidden-dim", args.message_hidden_dim)
    extend(command, "--depth", args.depth)
    extend(command, "--ffn-hidden-dim", args.ffn_hidden_dim)
    append_optional(command, "--ffn-num-layers", args.ffn_num_layers)
    append_optional(command, "--aggregation", args.aggregation)
    extend(command, "--molecule-featurizers", args.molecule_featurizers)
    append_optional(command, "--multiclass-num-classes", args.multiclass_num_classes)
    extend(command, "--checkpoint", args.checkpoint)
    append_optional(command, "--frzn-ffn-layers", args.frzn_ffn_layers)
    append_optional(command, "--from-foundation", args.from_foundation)
    append_optional(command, "--descriptors-path", args.descriptors_path)
    extend(command, "--atom-features-path", args.atom_features_path)
    extend(command, "--bond-features-path", args.bond_features_path)
    extend(command, "--atom-descriptors-path", args.atom_descriptors_path)
    extend(command, "--bond-descriptors-path", args.bond_descriptors_path)
    if args.class_balance:
        command.append("--class-balance")
    if args.freeze_encoder:
        command.append("--freeze-encoder")
    if args.save_data_splits:
        command.append("--save-data-splits")
    if args.save_smiles_splits:
        command.append("--save-smiles-splits")
    if args.remove_checkpoints:
        command.append("--remove-checkpoints")
    if args.use_cuikmolmaker_featurization:
        command.append("--use-cuikmolmaker-featurization")
    if args.no_header_row:
        command.append("--no-header-row")
    if args.no_cache:
        command.append("--no-cache")
    if args.command == "hpopt":
        extend(command, "--search-parameter-keywords", args.search_parameter_keywords)
        append_optional(command, "--raytune-num-samples", args.raytune_num_samples)
        append_optional(command, "--raytune-search-algorithm", args.raytune_search_algorithm)
        append_optional(command, "--raytune-trial-scheduler", args.raytune_trial_scheduler)
        append_optional(command, "--raytune-num-workers", args.raytune_num_workers)
        if args.raytune_use_gpu:
            command.append("--raytune-use-gpu")
    return command


def main() -> None:
    args = parse_args()
    validate(args)
    print(shlex.join(build_command(args)))
    if args.dry_run_note:
        print("# command printed only; not executed")


if __name__ == "__main__":
    main()
