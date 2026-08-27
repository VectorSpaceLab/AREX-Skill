#!/usr/bin/env python3
"""Build LightlySSL CLI commands without executing them.

This helper validates common Hydra override keys from Lightly's CLI config and
prints a shell-quoted command line for train/embed/magic/crop/version workflows.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from collections import Counter
from typing import Iterable, Sequence

COMMANDS = {
    "version": "lightly-version",
    "train": "lightly-ssl-train",
    "embed": "lightly-embed",
    "magic": "lightly-magic",
    "crop": "lightly-crop",
}

VALID_OVERRIDE_KEYS = {
    "input_dir",
    "output_dir",
    "embeddings",
    "checkpoint",
    "label_dir",
    "label_names_file",
    "pre_trained",
    "crop_padding",
    "seed",
    "model.name",
    "model.out_dim",
    "model.num_ftrs",
    "model.width",
    "criterion.temperature",
    "criterion.memory_bank_size",
    "optimizer.lr",
    "optimizer.weight_decay",
    "collate.input_size",
    "collate.cj_prob",
    "collate.cj_bright",
    "collate.cj_contrast",
    "collate.cj_sat",
    "collate.cj_hue",
    "collate.min_scale",
    "collate.random_gray_scale",
    "collate.gaussian_blur",
    "collate.sigmas",
    "collate.kernel_size",
    "collate.vf_prob",
    "collate.hf_prob",
    "collate.rr_prob",
    "collate.rr_degrees",
    "loader.batch_size",
    "loader.shuffle",
    "loader.num_workers",
    "loader.drop_last",
    "trainer.gpus",
    "trainer.max_epochs",
    "trainer.precision",
    "trainer.enable_model_summary",
    "trainer.weights_summary",
    "checkpoint_callback.save_last",
    "checkpoint_callback.save_top_k",
    "checkpoint_callback.dirpath",
    "summary_callback.max_depth",
    "environment_variable_names.lightly_last_checkpoint_path",
    "environment_variable_names.lightly_last_embedding_path",
    "hydra.run.dir",
}

ALIASES = {
    "input": "input_dir",
    "labels_dir": "label_dir",
    "checkpoint_path": "checkpoint",
    "max_epochs": "trainer.max_epochs",
    "batch_size": "loader.batch_size",
    "num_workers": "loader.num_workers",
    "input_size": "collate.input_size",
}


def parse_bool(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y"}:
        return "True"
    if normalized in {"0", "false", "f", "no", "n"}:
        return "False"
    raise argparse.ArgumentTypeError(
        f"expected boolean value such as true/false, got {value!r}"
    )


def shell_token(token: str) -> str:
    return shlex.quote(token)


def override_key(token: str) -> str:
    if "=" not in token:
        raise ValueError(f"override {token!r} must have KEY=VALUE form")
    key = token.split("=", 1)[0]
    # Support common Hydra add/force-add prefixes for validation purposes.
    while key.startswith("+"):
        key = key[1:]
    if key.startswith("~"):
        key = key[1:]
    return key


def make_override(key: str, value: object) -> str:
    return f"{key}={value}"


def add_if_present(overrides: list[str], key: str, value: object | None) -> None:
    if value is not None:
        overrides.append(make_override(key, value))


def validate_overrides(overrides: Sequence[str], allow_unknown: bool) -> list[str]:
    warnings: list[str] = []
    seen_keys: list[str] = []
    for token in overrides:
        key = override_key(token)
        seen_keys.append(key)
        if key in ALIASES:
            raise ValueError(
                f"override key {key!r} is a common misspelling/shortcut; "
                f"use {ALIASES[key]!r} instead"
            )
        elif key not in VALID_OVERRIDE_KEYS and not allow_unknown:
            valid = ", ".join(sorted(VALID_OVERRIDE_KEYS))
            raise ValueError(
                f"unknown override key {key!r}. Use --allow-unknown-overrides "
                f"for advanced Hydra keys. Known keys: {valid}"
            )
    for key, count in Counter(seen_keys).items():
        if count > 1:
            warnings.append(
                f"override key {key!r} appears {count} times; Hydra will use the last value"
            )
    return warnings


def command_warnings(command: str, overrides: Iterable[str]) -> list[str]:
    keys = {override_key(token) for token in overrides}
    warnings: list[str] = []
    if command in {"train", "embed", "magic"} and "input_dir" not in keys:
        warnings.append(f"{COMMANDS[command]} usually needs input_dir=<folder>")
    if command == "crop":
        for required in ("input_dir", "label_dir", "output_dir"):
            if required not in keys:
                warnings.append(f"lightly-crop usually needs {required}=<path>")
    return warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a LightlySSL CLI command without executing it. The helper "
            "validates common Hydra override names from the Lightly CLI config."
        )
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=sorted(COMMANDS),
        default=None,
        help="Workflow to build. Defaults to version if neither positional nor --command is set.",
    )
    parser.add_argument(
        "--command",
        dest="command_option",
        choices=sorted(COMMANDS),
        help="Workflow to build; equivalent to the positional command.",
    )
    parser.add_argument("--input-dir", help="Maps to input_dir=<path>.")
    parser.add_argument("--output-dir", help="Maps to output_dir=<path> for crop.")
    parser.add_argument("--label-dir", help="Maps to label_dir=<path> for crop.")
    parser.add_argument(
        "--label-names-file", help="Maps to label_names_file=<yaml> for crop."
    )
    parser.add_argument("--checkpoint", help="Maps to checkpoint=<path>.")
    parser.add_argument("--max-epochs", type=int, help="Maps to trainer.max_epochs=<n>.")
    parser.add_argument("--batch-size", type=int, help="Maps to loader.batch_size=<n>.")
    parser.add_argument("--num-workers", type=int, help="Maps to loader.num_workers=<n>.")
    parser.add_argument("--input-size", type=int, help="Maps to collate.input_size=<px>.")
    parser.add_argument("--gpus", type=int, help="Maps to trainer.gpus=<n>.")
    parser.add_argument("--precision", type=int, choices=(16, 32, 64), help="Maps to trainer.precision.")
    parser.add_argument(
        "--pre-trained",
        type=parse_bool,
        metavar="BOOL",
        help="Maps to pre_trained=True/False.",
    )
    parser.add_argument("--crop-padding", type=float, help="Maps to crop_padding=<fraction>.")
    parser.add_argument(
        "--hydra-run-dir", help="Maps to hydra.run.dir=<path> for deterministic outputs."
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Additional Hydra override. Repeat for multiple overrides.",
    )
    parser.add_argument(
        "--allow-unknown-overrides",
        action="store_true",
        help="Allow advanced Hydra keys not listed in the verified Lightly CLI config.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when required path overrides for the selected command are missing.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command_option or args.command or "version"

    if args.command and args.command_option and args.command != args.command_option:
        parser.error("positional command and --command disagree")

    overrides: list[str] = []
    add_if_present(overrides, "input_dir", args.input_dir)
    add_if_present(overrides, "output_dir", args.output_dir)
    add_if_present(overrides, "label_dir", args.label_dir)
    add_if_present(overrides, "label_names_file", args.label_names_file)
    add_if_present(overrides, "checkpoint", args.checkpoint)
    add_if_present(overrides, "trainer.max_epochs", args.max_epochs)
    add_if_present(overrides, "loader.batch_size", args.batch_size)
    add_if_present(overrides, "loader.num_workers", args.num_workers)
    add_if_present(overrides, "collate.input_size", args.input_size)
    add_if_present(overrides, "trainer.gpus", args.gpus)
    add_if_present(overrides, "trainer.precision", args.precision)
    add_if_present(overrides, "pre_trained", args.pre_trained)
    add_if_present(overrides, "crop_padding", args.crop_padding)
    add_if_present(overrides, "hydra.run.dir", args.hydra_run_dir)
    overrides.extend(args.override)

    if command == "version" and overrides:
        parser.error("lightly-version does not accept Lightly Hydra overrides")

    try:
        validation_warnings = validate_overrides(
            overrides, allow_unknown=args.allow_unknown_overrides
        )
        missing_warnings = command_warnings(command, overrides)
    except ValueError as exc:
        parser.error(str(exc))

    for warning in validation_warnings + missing_warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if args.strict and missing_warnings:
        return 2

    tokens = [COMMANDS[command], *overrides]
    print(" ".join(shell_token(token) for token in tokens))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
