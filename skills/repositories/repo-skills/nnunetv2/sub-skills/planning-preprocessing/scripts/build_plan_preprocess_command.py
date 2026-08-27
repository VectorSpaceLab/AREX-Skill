#!/usr/bin/env python3
"""Build nnU-Net v2 planning/preprocessing commands without running them."""

from __future__ import annotations

import argparse
import shlex
from typing import Iterable, List


DEFAULT_CONFIGURATIONS = ["2d", "3d_fullres", "3d_lowres"]


def shell_join(parts: Iterable[object]) -> str:
    return shlex.join(str(part) for part in parts)


def add_common_stage_options(command: List[str], args: argparse.Namespace) -> None:
    if args.verbose:
        command.append("--verbose")
    if args.no_pbar:
        command.append("--no_pbar")


def add_planner_options(command: List[str], args: argparse.Namespace) -> None:
    if args.planner:
        command.extend(["-pl", args.planner])
    if args.gpu_memory_target is not None:
        command.extend(["-gpu_memory_target", str(args.gpu_memory_target)])
    if args.preprocessor_name:
        command.extend(["-preprocessor_name", args.preprocessor_name])
    if args.overwrite_target_spacing:
        command.append("-overwrite_target_spacing")
        command.extend(str(value) for value in args.overwrite_target_spacing)
    if args.overwrite_plans_name:
        command.extend(["-overwrite_plans_name", args.overwrite_plans_name])


def add_preprocess_options(command: List[str], args: argparse.Namespace, include_plans_name: bool) -> None:
    if include_plans_name and args.plans_name:
        command.extend(["-plans_name", args.plans_name])
    if args.configurations:
        command.append("-c")
        command.extend(args.configurations)
    if args.num_processes:
        command.append("-np")
        command.extend(str(value) for value in args.num_processes)


def validate_args(args: argparse.Namespace) -> None:
    if args.num_processes and len(args.num_processes) not in (1, len(args.configurations)):
        raise SystemExit("--num-processes must have length 1 or match --configurations length")
    if args.overwrite_target_spacing and len(args.overwrite_target_spacing) != 3:
        raise SystemExit("--overwrite-target-spacing requires exactly three numbers")
    if args.mode == "preprocess" and args.skip_preprocessing:
        raise SystemExit("--skip-preprocessing is not valid with --mode preprocess")
    if args.mode == "combined" and args.plans_name:
        raise SystemExit("--plans-name is only valid for split/preprocess modes; use --overwrite-plans-name while planning")


def build_combined(args: argparse.Namespace) -> List[List[str]]:
    command = ["nnUNetv2_plan_and_preprocess", "-d"] + [str(value) for value in args.dataset_id]
    if args.fingerprint_extractor:
        command.extend(["-fpe", args.fingerprint_extractor])
    if args.fingerprint_processes is not None:
        command.extend(["-npfp", str(args.fingerprint_processes)])
    if args.verify_dataset_integrity:
        command.append("--verify_dataset_integrity")
    if args.clean:
        command.append("--clean")
    if args.skip_preprocessing:
        command.append("--no_pp")
    add_planner_options(command, args)
    add_preprocess_options(command, args, include_plans_name=False)
    add_common_stage_options(command, args)
    return [command]


def build_split(args: argparse.Namespace) -> List[List[str]]:
    commands: List[List[str]] = []
    if not args.skip_fingerprint:
        fingerprint = ["nnUNetv2_extract_fingerprint", "-d"] + [str(value) for value in args.dataset_id]
        if args.fingerprint_extractor:
            fingerprint.extend(["-fpe", args.fingerprint_extractor])
        if args.fingerprint_processes is not None:
            fingerprint.extend(["-np", str(args.fingerprint_processes)])
        if args.verify_dataset_integrity:
            fingerprint.append("--verify_dataset_integrity")
        if args.clean:
            fingerprint.append("--clean")
        add_common_stage_options(fingerprint, args)
        commands.append(fingerprint)

    if not args.skip_planning:
        planning = ["nnUNetv2_plan_experiment", "-d"] + [str(value) for value in args.dataset_id]
        add_planner_options(planning, args)
        commands.append(planning)

    if not args.skip_preprocessing:
        preprocess = ["nnUNetv2_preprocess", "-d"] + [str(value) for value in args.dataset_id]
        add_preprocess_options(preprocess, args, include_plans_name=True)
        add_common_stage_options(preprocess, args)
        commands.append(preprocess)

    return commands


def build_preprocess_only(args: argparse.Namespace) -> List[List[str]]:
    command = ["nnUNetv2_preprocess", "-d"] + [str(value) for value in args.dataset_id]
    add_preprocess_options(command, args, include_plans_name=True)
    add_common_stage_options(command, args)
    return [command]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print nnU-Net v2 planning/preprocessing commands. This helper never executes them."
    )
    parser.add_argument("--mode", choices=("combined", "split", "preprocess"), default="combined")
    parser.add_argument("--dataset-id", type=int, nargs="+", required=True, help="One or more numeric dataset IDs.")
    parser.add_argument("--verify-dataset-integrity", action="store_true")
    parser.add_argument("--clean", action="store_true", help="Overwrite existing fingerprints.")
    parser.add_argument("--fingerprint-extractor", default=None)
    parser.add_argument("--fingerprint-processes", type=int, default=None)
    parser.add_argument("--planner", default=None, help="Experiment planner class, for example nnUNetPlannerResEncL.")
    parser.add_argument("--gpu-memory-target", type=float, default=None)
    parser.add_argument("--preprocessor-name", default=None)
    parser.add_argument("--overwrite-target-spacing", type=float, nargs="*")
    parser.add_argument("--overwrite-plans-name", default=None)
    parser.add_argument("--plans-name", default=None, help="Existing plans identifier for preprocessing-only commands.")
    parser.add_argument("--configurations", nargs="+", default=DEFAULT_CONFIGURATIONS)
    parser.add_argument("--num-processes", type=int, nargs="*")
    parser.add_argument("--skip-fingerprint", action="store_true", help="Split mode only.")
    parser.add_argument("--skip-planning", action="store_true", help="Split mode only.")
    parser.add_argument("--skip-preprocessing", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--no-pbar", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    validate_args(args)
    if args.mode == "combined":
        commands = build_combined(args)
    elif args.mode == "split":
        commands = build_split(args)
    else:
        commands = build_preprocess_only(args)

    for command in commands:
        print(shell_join(command))


if __name__ == "__main__":
    main()
