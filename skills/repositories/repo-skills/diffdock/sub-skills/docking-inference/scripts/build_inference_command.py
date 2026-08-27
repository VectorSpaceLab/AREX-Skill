#!/usr/bin/env python3
"""Build a safe DiffDock inference command without running inference.

This helper prints a shell-quoted `python -m inference` command for either
batch CSV mode or single-complex mode. It does not import DiffDock, validate
model files, download weights, or execute the command.

Example:
  python build_inference_command.py \
    --config default_inference_args.yaml \
    --protein-ligand-csv inputs/protein_ligand.csv \
    --out-dir results/user_predictions
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable, List, Optional


def non_empty(value: Optional[str]) -> bool:
    return value is not None and value.strip() != ""


def add_optional(command: List[str], flag: str, value: Optional[object]) -> None:
    if value is not None:
        command.extend([flag, str(value)])


def build_command(args: argparse.Namespace) -> List[str]:
    csv_mode = non_empty(args.protein_ligand_csv)
    has_single_protein = non_empty(args.protein_path) or non_empty(args.protein_sequence)
    has_single_ligand = non_empty(args.ligand_description)

    if csv_mode and (has_single_protein or has_single_ligand or non_empty(args.complex_name)):
        raise ValueError(
            "Use either --protein-ligand-csv batch mode or single-complex "
            "arguments, not both."
        )
    if not csv_mode:
        if not has_single_protein:
            raise ValueError(
                "Single-complex mode requires --protein-path or --protein-sequence."
            )
        if not has_single_ligand:
            raise ValueError("Single-complex mode requires --ligand-description.")
        if non_empty(args.protein_path) and non_empty(args.protein_sequence):
            raise ValueError(
                "Provide only one of --protein-path or --protein-sequence; "
                "DiffDock ignores sequence when protein_path is set."
            )

    command = [args.python_executable, "-m", "inference"]
    add_optional(command, "--config", args.config)

    if csv_mode:
        add_optional(command, "--protein_ligand_csv", args.protein_ligand_csv)
    else:
        add_optional(command, "--complex_name", args.complex_name)
        add_optional(command, "--protein_path", args.protein_path)
        add_optional(command, "--protein_sequence", args.protein_sequence)
        add_optional(command, "--ligand_description", args.ligand_description)

    add_optional(command, "--out_dir", args.out_dir)
    add_optional(command, "--samples_per_complex", args.samples_per_complex)
    add_optional(command, "--model_dir", args.model_dir)
    add_optional(command, "--confidence_model_dir", args.confidence_model_dir)
    add_optional(command, "--actual_steps", args.actual_steps)

    if args.save_visualisation:
        command.append("--save_visualisation")
    if args.gnina_minimize:
        command.append("--gnina_minimize")
        add_optional(command, "--gnina_path", args.gnina_path)
    elif non_empty(args.gnina_path):
        add_optional(command, "--gnina_path", args.gnina_path)

    return command


def quote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a shell-quoted DiffDock python -m inference command without running it."
    )
    parser.add_argument(
        "--python-executable",
        default="python",
        help="Python executable to place at the front of the printed command. Default: python.",
    )
    parser.add_argument(
        "--config",
        default="default_inference_args.yaml",
        help="Inference YAML config path to pass through as --config.",
    )

    mode = parser.add_argument_group("input mode")
    mode.add_argument("--protein-ligand-csv", help="Batch CSV input path.")
    mode.add_argument("--protein-path", help="Single-complex protein PDB path.")
    mode.add_argument("--protein-sequence", help="Single-complex protein sequence for ESMFold.")
    mode.add_argument("--ligand-description", help="Single-complex ligand SMILES or molecule file path.")
    mode.add_argument("--complex-name", help="Single-complex output name.")

    runtime = parser.add_argument_group("runtime options")
    runtime.add_argument("--out-dir", default="results/user_inference", help="Output directory.")
    runtime.add_argument("--samples-per-complex", type=int, help="Number of poses per complex.")
    runtime.add_argument("--model-dir", help="Score model directory.")
    runtime.add_argument("--confidence-model-dir", help="Confidence model directory.")
    runtime.add_argument("--actual-steps", type=int, help="Denoising steps actually performed.")
    runtime.add_argument("--save-visualisation", action="store_true", help="Add --save_visualisation.")
    runtime.add_argument("--gnina-minimize", action="store_true", help="Add --gnina_minimize.")
    runtime.add_argument("--gnina-path", help="GNINA executable path to pass through.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        command = build_command(args)
    except ValueError as exc:
        parser.error(str(exc))
        return 2
    print(quote_command(command))
    return 0


if __name__ == "__main__":
    sys.exit(main())
