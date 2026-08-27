#!/usr/bin/env python3
"""Build Chemprop predict and fingerprint commands safely.

The helper validates common planning mistakes without importing Chemprop or
loading model files. It prints a shell-ready command and notes about output
naming, model discovery, and likely flag mismatches.
"""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Iterable


PREDICT_SUFFIXES = {".csv", ".pkl"}
FINGERPRINT_SUFFIXES = {".csv", ".npz"}
MODEL_SUFFIXES = {".pt", ".ckpt"}


def planned_path(value: str) -> Path:
    return Path(value).expanduser()


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--test-path", required=True, type=planned_path)
    parser.add_argument(
        "--model-path",
        "--model-paths",
        dest="model_paths",
        nargs="+",
        required=True,
        type=planned_path,
        help="One or more .pt/.ckpt files or directories. Chemprop searches directories for .pt files.",
    )
    parser.add_argument("--output", "--preds-path", dest="output", type=planned_path)
    parser.add_argument("--smiles-columns", nargs="+")
    parser.add_argument("--reaction-columns", nargs="+")
    parser.add_argument("--rxn-mode", "--reaction-mode", dest="rxn_mode")
    parser.add_argument("--descriptors-path", type=planned_path)
    parser.add_argument("--descriptors-columns", nargs="+")
    parser.add_argument("--atom-features-path", nargs="+", action="append")
    parser.add_argument("--atom-descriptors-path", nargs="+", action="append")
    parser.add_argument("--bond-features-path", nargs="+", action="append")
    parser.add_argument("--bond-descriptors-path", nargs="+", action="append")
    parser.add_argument("--molecule-featurizers", "--features-generators", nargs="+")
    parser.add_argument("--multi-hot-atom-featurizer-mode")
    parser.add_argument("--keep-h", action="store_true")
    parser.add_argument("--add-h", action="store_true")
    parser.add_argument("--ignore-stereo", action="store_true")
    parser.add_argument("--reorder-atoms", action="store_true")
    parser.add_argument("--use-cuikmolmaker-featurization", action="store_true")
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--num-workers", type=int)
    parser.add_argument("--accelerator")
    parser.add_argument("--devices")
    parser.add_argument("--no-header-row", action="store_true")
    parser.add_argument("--json", action="store_true", help="Emit a JSON plan instead of text.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    predict = subparsers.add_parser("predict", help="Build a chemprop predict command")
    add_common_arguments(predict)
    predict.add_argument("--drop-extra-columns", action="store_true")
    predict.add_argument("--cal-path", type=planned_path)
    predict.add_argument("--uncertainty-method")
    predict.add_argument("--calibration-method")
    predict.add_argument("--evaluation-methods", nargs="+")
    predict.add_argument("--uncertainty-dropout-p", type=float)
    predict.add_argument("--dropout-sampling-size", type=int)
    predict.add_argument("--calibration-interval-percentile", type=float)
    predict.add_argument("--conformal-alpha", type=float)
    predict.add_argument("--cal-descriptors-path", nargs="+")
    predict.add_argument("--cal-atom-features-path", nargs="+", action="append")
    predict.add_argument("--cal-atom-descriptors-path", nargs="+", action="append")
    predict.add_argument("--cal-bond-features-path", nargs="+", action="append")
    predict.add_argument("--cal-bond-descriptors-path", nargs="+", action="append")
    predict.add_argument("--cal-constraints-path", type=planned_path)
    predict.add_argument("--constraints-path", type=planned_path)
    predict.add_argument("--constraints-to-targets", nargs="+")

    fingerprint = subparsers.add_parser("fingerprint", help="Build a chemprop fingerprint command")
    add_common_arguments(fingerprint)
    fingerprint.add_argument("--ffn-block-index", required=True, type=int)

    return parser


def append_optional_path(command: list[str], flag: str, value: Path | None) -> None:
    if value is not None:
        command.extend([flag, str(value)])


def append_optional_value(command: list[str], flag: str, value: object | None) -> None:
    if value is not None:
        command.extend([flag, str(value)])


def extend_flag(command: list[str], flag: str, values: Iterable[object] | None) -> None:
    if values:
        command.append(flag)
        command.extend(str(value) for value in values)


def append_repeated_groups(command: list[str], flag: str, groups: list[list[str]] | None) -> None:
    for group in groups or []:
        command.append(flag)
        command.extend(str(value) for value in group)


def default_output(args: argparse.Namespace) -> Path:
    if args.command == "predict":
        return args.test_path.with_name(f"{args.test_path.stem}_preds.csv")
    return args.test_path.with_name(f"{args.test_path.stem}_fps.csv")


def fingerprint_indexed_output(output: Path, model_index: int = 0) -> Path:
    return output.with_stem(f"{output.stem}_{model_index}")


def validate(args: argparse.Namespace) -> list[str]:
    notes: list[str] = []

    if args.test_path.suffix.lower() != ".csv":
        raise SystemExit(f"--test-path must end in .csv, got {args.test_path}")

    output = args.output or default_output(args)
    allowed_suffixes = PREDICT_SUFFIXES if args.command == "predict" else FINGERPRINT_SUFFIXES
    if output.suffix.lower() not in allowed_suffixes:
        allowed = ", ".join(sorted(allowed_suffixes))
        raise SystemExit(f"{args.command} output must end in {allowed}, got {output}")

    file_like_models = 0
    directory_like_models = 0
    for model_path in args.model_paths:
        suffix = model_path.suffix.lower()
        if suffix in MODEL_SUFFIXES:
            file_like_models += 1
            if suffix == ".ckpt":
                notes.append(f"Checkpoint {model_path} is valid only because it is passed explicitly.")
            continue
        directory_like_models += 1
        if suffix and not model_path.exists():
            notes.append(
                f"Model path {model_path} has an unusual suffix; Chemprop accepts it only if it is a directory."
            )
        else:
            notes.append(f"Directory model path {model_path} will be searched recursively for .pt files only.")

    if len(args.model_paths) > 1 or directory_like_models:
        if args.command == "predict":
            individual = output.with_name(f"{output.stem}_individual{output.suffix}")
            notes.append(f"Multiple discovered models produce averaged predictions plus {individual.name}.")
        else:
            notes.append(
                f"Fingerprint outputs append model indices, for example {fingerprint_indexed_output(output).name}."
            )
    elif args.command == "fingerprint":
        notes.append(f"Fingerprint output will be named {fingerprint_indexed_output(output).name}.")

    if args.smiles_columns and args.reaction_columns:
        notes.append("Both SMILES and reaction columns are set; this plans a mixed multicomponent workflow.")
    elif args.reaction_columns and not args.rxn_mode:
        notes.append("Reaction columns are set. Reuse the training reaction mode; Chemprop defaults to REAC_DIFF.")
    elif args.smiles_columns and len(args.smiles_columns) > 1:
        notes.append("Multiple SMILES columns are set; preserve the training-time component order.")
    elif not args.smiles_columns and not args.reaction_columns:
        notes.append("No structure columns are set; Chemprop parses the first CSV column as single-molecule SMILES.")

    if args.multi_hot_atom_featurizer_mode and args.multi_hot_atom_featurizer_mode.lower() == "v1":
        notes.append("V1 atom featurizer mode is appropriate for legacy artifacts that warn about v1 dimensions.")

    if args.use_cuikmolmaker_featurization:
        notes.append("cuik-molmaker is optional and only supports single-component molecule featurization.")
        blocked_flags = []
        if args.keep_h:
            blocked_flags.append("--keep-h")
        if args.ignore_stereo:
            blocked_flags.append("--ignore-stereo")
        if args.reorder_atoms:
            blocked_flags.append("--reorder-atoms")
        if args.reaction_columns or (args.smiles_columns and len(args.smiles_columns) > 1):
            blocked_flags.append("reaction or multicomponent columns")
        if blocked_flags:
            notes.append("Chemprop rejects --use-cuikmolmaker-featurization with " + ", ".join(blocked_flags) + ".")

    if args.command == "fingerprint" and args.ffn_block_index == 0:
        notes.append("ffn-block-index 0 returns the post-aggregation representation before FFN layers.")

    if file_like_models == 0 and directory_like_models == 0:
        raise SystemExit("At least one model path is required.")

    return notes


def build_command(args: argparse.Namespace) -> list[str]:
    output = args.output or default_output(args)
    command = ["chemprop", args.command, "--test-path", str(args.test_path), "--model-path"]
    command.extend(str(path) for path in args.model_paths)
    command.extend(["--output", str(output)])

    extend_flag(command, "--smiles-columns", args.smiles_columns)
    extend_flag(command, "--reaction-columns", args.reaction_columns)
    append_optional_value(command, "--rxn-mode", args.rxn_mode)
    append_optional_path(command, "--descriptors-path", args.descriptors_path)
    extend_flag(command, "--descriptors-columns", args.descriptors_columns)
    append_repeated_groups(command, "--atom-features-path", args.atom_features_path)
    append_repeated_groups(command, "--atom-descriptors-path", args.atom_descriptors_path)
    append_repeated_groups(command, "--bond-features-path", args.bond_features_path)
    append_repeated_groups(command, "--bond-descriptors-path", args.bond_descriptors_path)
    extend_flag(command, "--molecule-featurizers", args.molecule_featurizers)
    append_optional_value(command, "--multi-hot-atom-featurizer-mode", args.multi_hot_atom_featurizer_mode)
    append_optional_value(command, "--batch-size", args.batch_size)
    append_optional_value(command, "--num-workers", args.num_workers)
    append_optional_value(command, "--accelerator", args.accelerator)
    append_optional_value(command, "--devices", args.devices)

    boolean_flags = [
        "keep_h",
        "add_h",
        "ignore_stereo",
        "reorder_atoms",
        "use_cuikmolmaker_featurization",
        "no_header_row",
    ]
    for flag_name in boolean_flags:
        if getattr(args, flag_name):
            command.append("--" + flag_name.replace("_", "-"))

    if args.command == "predict":
        if args.drop_extra_columns:
            command.append("--drop-extra-columns")
        append_optional_path(command, "--cal-path", args.cal_path)
        append_optional_value(command, "--uncertainty-method", args.uncertainty_method)
        append_optional_value(command, "--calibration-method", args.calibration_method)
        extend_flag(command, "--evaluation-methods", args.evaluation_methods)
        append_optional_value(command, "--uncertainty-dropout-p", args.uncertainty_dropout_p)
        append_optional_value(command, "--dropout-sampling-size", args.dropout_sampling_size)
        append_optional_value(command, "--calibration-interval-percentile", args.calibration_interval_percentile)
        append_optional_value(command, "--conformal-alpha", args.conformal_alpha)
        extend_flag(command, "--cal-descriptors-path", args.cal_descriptors_path)
        append_repeated_groups(command, "--cal-atom-features-path", args.cal_atom_features_path)
        append_repeated_groups(command, "--cal-atom-descriptors-path", args.cal_atom_descriptors_path)
        append_repeated_groups(command, "--cal-bond-features-path", args.cal_bond_features_path)
        append_repeated_groups(command, "--cal-bond-descriptors-path", args.cal_bond_descriptors_path)
        append_optional_path(command, "--cal-constraints-path", args.cal_constraints_path)
        append_optional_path(command, "--constraints-path", args.constraints_path)
        extend_flag(command, "--constraints-to-targets", args.constraints_to_targets)
    else:
        command.extend(["--ffn-block-index", str(args.ffn_block_index)])

    return command


def main() -> None:
    args = build_parser().parse_args()
    notes = validate(args)
    command = build_command(args)
    shell = " ".join(shlex.quote(part) for part in command)

    if args.json:
        print(json.dumps({"command": command, "shell": shell, "notes": notes}, indent=2))
        return

    print(shell)
    if notes:
        print("\nNotes:")
        for note in notes:
            print(f"- {note}")


if __name__ == "__main__":
    main()
