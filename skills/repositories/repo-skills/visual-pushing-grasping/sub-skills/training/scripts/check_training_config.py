#!/usr/bin/env python3
"""Validate VPG training/test paths and flags without starting the application.

This helper intentionally has no torch, torchvision, OpenCV, source-module,
network, simulator, or robot imports. It never creates directories, loads a
state dict, downloads weights, or reads image contents.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple


REQUIRED_LOGS = (
    "executed-action.log.txt",
    "label-value.log.txt",
    "predicted-value.log.txt",
    "reward-value.log.txt",
    "use-heuristic.log.txt",
    "is-exploit.log.txt",
    "clearance.log.txt",
)
SCALAR_LOGS = set(REQUIRED_LOGS) - {"executed-action.log.txt"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely validate historical VPG main.py flags, snapshot paths, "
            "and continuation logs; this command never starts training."
        )
    )

    # These defaults mirror the historical parser. Keep this helper source-free.
    parser.add_argument("--is_sim", dest="is_sim", action="store_true", default=False)
    parser.add_argument("--obj_mesh_dir", default="objects/blocks")
    parser.add_argument("--num_obj", type=int, default=10)
    parser.add_argument("--tcp_host_ip", default="<operator-approved-controller-host>")
    parser.add_argument("--tcp_port", type=int, default=30002)
    parser.add_argument("--rtc_host_ip", default="<operator-approved-controller-host>")
    parser.add_argument("--rtc_port", type=int, default=30003)
    parser.add_argument("--heightmap_resolution", type=float, default=0.002)
    parser.add_argument("--random_seed", type=int, default=1234)
    parser.add_argument("--cpu", dest="force_cpu", action="store_true", default=False)

    parser.add_argument("--method", default="reinforcement")
    parser.add_argument("--push_rewards", action="store_true", default=False)
    parser.add_argument("--future_reward_discount", type=float, default=0.5)
    parser.add_argument("--experience_replay", action="store_true", default=False)
    parser.add_argument("--heuristic_bootstrap", action="store_true", default=False)
    parser.add_argument("--explore_rate_decay", action="store_true", default=False)
    parser.add_argument("--grasp_only", action="store_true", default=False)

    parser.add_argument("--is_testing", action="store_true", default=False)
    parser.add_argument("--max_test_trials", type=int, default=30)
    parser.add_argument("--test_preset_cases", action="store_true", default=False)
    parser.add_argument("--test_preset_file", default="test-10-obj-01.txt")

    parser.add_argument("--load_snapshot", action="store_true", default=False)
    parser.add_argument("--snapshot_file", default=None)
    parser.add_argument("--continue_logging", action="store_true", default=False)
    parser.add_argument("--logging_directory", default=None)
    parser.add_argument("--save_visualizations", action="store_true", default=False)

    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="treat non-fatal source-semantics warnings as validation errors",
    )
    return parser


def _regular_file(path_value: str | None, label: str, errors: List[str], warnings: List[str]) -> Path | None:
    if not path_value:
        errors.append(f"{label} was not supplied")
        return None
    path = Path(path_value).expanduser()
    if not path.exists():
        errors.append(f"{label} does not exist: {path}")
        return None
    if not path.is_file():
        errors.append(f"{label} is not a regular file: {path}")
        return None
    try:
        if path.stat().st_size == 0:
            errors.append(f"{label} is empty: {path}")
    except OSError as exc:
        errors.append(f"cannot stat {label} {path}: {exc}")
    return path


def _check_port(value: int, label: str, errors: List[str]) -> None:
    if not 1 <= value <= 65535:
        errors.append(f"{label} must be in 1..65535, got {value}")


def _read_numeric_rows(path: Path) -> Tuple[List[List[float]], str | None]:
    rows: List[List[float]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, 1):
                fields = raw_line.split()
                if not fields:
                    continue
                try:
                    row = [float(field) for field in fields]
                except ValueError as exc:
                    return [], f"line {line_number} is not numeric ({exc})"
                if not all(math.isfinite(value) for value in row):
                    return [], f"line {line_number} contains NaN or infinity"
                rows.append(row)
    except OSError as exc:
        return [], str(exc)
    return rows, None


def _validate_transition_logs(session: Path, errors: List[str], warnings: List[str]) -> None:
    transitions = session / "transitions"
    if not transitions.is_dir():
        errors.append(f"continuation session has no transitions directory: {transitions}")
        return

    data_dir = transitions / "data"
    if not data_dir.is_dir():
        warnings.append(f"replay image directory is missing (resume may work, replay will not): {data_dir}")

    parsed = {}
    for filename in REQUIRED_LOGS:
        path = transitions / filename
        if not path.exists():
            errors.append(f"required continuation log is missing: {path}")
            continue
        if not path.is_file():
            errors.append(f"required continuation log is not a file: {path}")
            continue
        try:
            if path.stat().st_size == 0:
                errors.append(f"required continuation log is empty: {path}")
                continue
        except OSError as exc:
            errors.append(f"cannot stat continuation log {path}: {exc}")
            continue
        rows, parse_error = _read_numeric_rows(path)
        if parse_error:
            errors.append(f"invalid continuation log {path}: {parse_error}")
            continue
        if not rows:
            errors.append(f"required continuation log has no data rows: {path}")
            continue
        parsed[filename] = rows

    action_name = "executed-action.log.txt"
    action_rows = parsed.get(action_name, [])
    if action_rows:
        bad_width = [index + 1 for index, row in enumerate(action_rows) if len(row) != 4]
        if bad_width:
            errors.append(
                f"{action_name} must have four columns [primitive, rotation, y, x]; "
                f"bad rows include {bad_width[:3]}"
            )
        for index, row in enumerate(action_rows, 1):
            if len(row) != 4:
                continue
            primitive, rotation, y_value, x_value = row
            if primitive not in (0.0, 1.0):
                errors.append(f"{action_name} row {index} has primitive {primitive}; expected 0 or 1")
            if not float(rotation).is_integer() or not 0 <= rotation <= 15:
                errors.append(f"{action_name} row {index} has rotation {rotation}; expected integer 0..15")
            if not float(y_value).is_integer() or y_value < 0 or not float(x_value).is_integer() or x_value < 0:
                errors.append(f"{action_name} row {index} has invalid non-negative integer pixel coordinates")

        # Historical preload uses iteration = action_rows - 2.
        iteration = len(action_rows) - 2
        if iteration < 0:
            errors.append(f"{action_name} has fewer than two rows; historical preload cannot derive iteration")
        for filename in SCALAR_LOGS - {"clearance.log.txt"}:
            rows = parsed.get(filename)
            if rows is not None and len(rows) < max(iteration, 1):
                errors.append(
                    f"{filename} has {len(rows)} rows but resume needs at least "
                    f"{max(iteration, 1)} for {len(action_rows)} action rows"
                )


def validate(args: argparse.Namespace) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if args.method not in ("reactive", "reinforcement"):
        errors.append("--method must be exactly 'reactive' or 'reinforcement'")
    if args.num_obj < 1:
        errors.append(f"--num_obj must be positive, got {args.num_obj}")
    if args.heightmap_resolution <= 0 or not math.isfinite(args.heightmap_resolution):
        errors.append("--heightmap_resolution must be a finite positive number")
    if args.max_test_trials <= 0:
        errors.append(f"--max_test_trials must be positive, got {args.max_test_trials}")
    if not 0 <= args.future_reward_discount <= 1 or not math.isfinite(args.future_reward_discount):
        errors.append("--future_reward_discount must be finite and in 0..1")
    _check_port(args.tcp_port, "--tcp_port", errors)
    _check_port(args.rtc_port, "--rtc_port", errors)

    if args.is_sim:
        mesh_dir = Path(args.obj_mesh_dir).expanduser()
        if not mesh_dir.is_dir():
            errors.append(f"simulation --obj_mesh_dir is not an existing directory: {mesh_dir}")
    else:
        if args.obj_mesh_dir != "objects/blocks":
            warnings.append("--obj_mesh_dir is ignored when --is_sim is absent")
        if args.num_obj != 10:
            warnings.append("--num_obj is ignored when --is_sim is absent")

    if args.test_preset_cases:
        _regular_file(args.test_preset_file, "--test_preset_file", errors, warnings)
    elif args.test_preset_file != "test-10-obj-01.txt":
        warnings.append("--test_preset_file is ignored unless --test_preset_cases is set")

    snapshot: Path | None = None
    if args.load_snapshot:
        snapshot = _regular_file(args.snapshot_file, "--snapshot_file", errors, warnings)
        if snapshot is not None and snapshot.suffix.lower() != ".pth":
            warnings.append(f"snapshot does not use the usual .pth suffix: {snapshot}")
        if snapshot is not None:
            expected = f".{args.method}.pth"
            if not snapshot.name.endswith(expected):
                warnings.append(
                    f"snapshot name does not end with {expected}; method/state-dict compatibility remains unproven"
                )
    elif args.snapshot_file:
        warnings.append("--snapshot_file is ignored unless --load_snapshot is set")

    if args.continue_logging:
        if not args.logging_directory:
            errors.append("--continue_logging requires --logging_directory")
        else:
            session = Path(args.logging_directory).expanduser()
            if not session.is_dir():
                errors.append(f"--logging_directory is not an existing session directory: {session}")
            else:
                _validate_transition_logs(session, errors, warnings)
        if not args.load_snapshot:
            warnings.append("continuing logs without --load_snapshot resumes history with a new random model")
    elif args.logging_directory:
        warnings.append("--logging_directory is ignored unless --continue_logging is set")

    if args.push_rewards and args.method == "reactive":
        warnings.append("--push_rewards is ignored for --method reactive")
    if args.is_testing and args.experience_replay:
        warnings.append("experience replay is skipped by the source loop in --is_testing mode")
    if args.is_testing and args.explore_rate_decay:
        warnings.append("explore-rate decay is ineffective in --is_testing mode because explore_prob starts at zero")
    if args.is_testing and not args.load_snapshot:
        warnings.append("testing without --load_snapshot evaluates a newly initialized model")
    if args.is_sim and (args.tcp_host_ip != "<operator-approved-controller-host>" or args.tcp_port != 30002 or args.rtc_host_ip != "<operator-approved-controller-host>" or args.rtc_port != 30003):
        warnings.append("real-robot TCP options are ignored by the simulation branch")

    if args.strict and warnings:
        errors.extend(f"strict mode: {warning}" for warning in warnings)
    return errors, warnings


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    errors, warnings = validate(args)

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        print("Training configuration rejected; no training, import, load, download, or directory creation was performed.", file=sys.stderr)
        return 2

    print("Configuration validated: paths and flags are coherent.")
    print("No training loop, torch state-dict load, weight download, robot, camera, or simulator was started.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
