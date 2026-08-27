#!/usr/bin/env python3
"""Build safe VLA-Adapter LIBERO or CALVIN evaluation commands.

This helper only prints a shell command. It does not import VLA-Adapter,
validate checkpoint contents, create benchmark assets, or run an evaluation.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class SuiteSpec:
    benchmark: str
    suite: str
    display_name: str
    original_checkpoint: str | None
    pro_checkpoint: str | None
    default_log: str


SUITES: dict[str, SuiteSpec] = {
    "libero_spatial": SuiteSpec(
        benchmark="libero",
        suite="libero_spatial",
        display_name="LIBERO-Spatial",
        original_checkpoint="outputs/LIBERO-Spatial",
        pro_checkpoint="outputs/LIBERO-Spatial-Pro",
        default_log="eval_logs/Spatial--chkpt.log",
    ),
    "libero_object": SuiteSpec(
        benchmark="libero",
        suite="libero_object",
        display_name="LIBERO-Object",
        original_checkpoint="outputs/LIBERO-Object",
        pro_checkpoint="outputs/LIBERO-Object-Pro",
        default_log="eval_logs/Object--chkpt.log",
    ),
    "libero_goal": SuiteSpec(
        benchmark="libero",
        suite="libero_goal",
        display_name="LIBERO-Goal",
        original_checkpoint="outputs/LIBERO-Goal",
        pro_checkpoint="outputs/LIBERO-Goal-Pro",
        default_log="eval_logs/Goal--chkpt.log",
    ),
    "libero_10": SuiteSpec(
        benchmark="libero",
        suite="libero_10",
        display_name="LIBERO-Long / LIBERO-10",
        original_checkpoint="outputs/LIBERO-Long",
        pro_checkpoint="outputs/LIBERO-Long-Pro",
        default_log="eval_logs/Long--chkpt.log",
    ),
    "calvin_abc": SuiteSpec(
        benchmark="calvin",
        suite="calvin_abc",
        display_name="CALVIN ABC→D",
        original_checkpoint=None,
        pro_checkpoint="outputs/CALVIN-ABC-Pro",
        default_log="eval_logs/CALVIN--ABC.log",
    ),
}


GPU_RE = re.compile(r"^[0-9]+(?:,[0-9]+)*$")


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def bool_word(value: bool) -> str:
    return "True" if value else "False"


def default_checkpoint(spec: SuiteSpec, use_pro_version: bool) -> str:
    checkpoint = spec.pro_checkpoint if use_pro_version else spec.original_checkpoint
    if checkpoint is None:
        raise ValueError(
            f"No default original checkpoint is recorded for {spec.display_name}; "
            "pass --checkpoint explicitly."
        )
    return checkpoint


def log_prefix_and_suffix(log_file: str, repo_root: str) -> tuple[str, str]:
    """Return mkdir prefix and redirection suffix, resolving relative logs in repo root."""
    if log_file == "-":
        return "", ""

    if "\n" in log_file or "\r" in log_file or not log_file.strip():
        raise ValueError("--log-file must be a non-empty single-line path, or '-' to disable redirection")

    log_path = PurePosixPath(log_file)
    parent = log_path.parent
    prefix = ""
    if parent not in (PurePosixPath(""), PurePosixPath(".")):
        parent_path = parent if parent.is_absolute() else PurePosixPath(repo_root) / parent
        prefix = f"mkdir -p {shlex.quote(str(parent_path))} && "
    suffix = f" > {shlex.quote(log_file)} 2>&1"
    return prefix, suffix


def warn_for_checkpoint(benchmark: str, checkpoint: str, use_pro_version: bool) -> list[str]:
    warnings: list[str] = []
    if benchmark == "calvin" and checkpoint.startswith("VLA-Adapter/"):
        warnings.append(
            "CALVIN evaluation is most reliable with a local checkpoint directory; "
            "the component-loading helper may not support every CALVIN Hub id."
        )
    if benchmark == "libero" and checkpoint.startswith("VLA-Adapter/LIBERO") and not use_pro_version:
        warnings.append(
            "Original LIBERO Hub ids may not be covered by the component-loading helper; "
            "prefer a local checkpoint directory for original or custom checkpoints."
        )
    return warnings


def build_libero(args: argparse.Namespace, spec: SuiteSpec, checkpoint: str) -> str:
    trials = args.num_trials_per_task if args.num_trials_per_task is not None else 50
    if trials <= 0:
        raise ValueError("--num-trials-per-task must be positive")

    command = [
        f"CUDA_VISIBLE_DEVICES={args.gpu}",
        "python",
        "experiments/robot/libero/run_libero_eval.py",
        "--use_proprio",
        "True",
        "--num_images_in_input",
        "2",
        "--use_film",
        "False",
        "--pretrained_checkpoint",
        checkpoint,
        "--task_suite_name",
        spec.suite,
        "--use_pro_version",
        bool_word(args.use_pro_version),
        "--num_trials_per_task",
        str(trials),
    ]
    return f"cd {shlex.quote(args.repo_root)} && {shell_join(command)}"


def build_calvin(args: argparse.Namespace, checkpoint: str) -> str:
    if args.num_trials_per_task is not None:
        print(
            "warning: --num-trials-per-task is LIBERO-only; CALVIN evaluator uses 1,000 sequences internally.",
            file=sys.stderr,
        )
    if not args.use_pro_version:
        print(
            "warning: --no-use-pro-version is not forwarded to evaluate_calvin.py; ensure the checkpoint matches the intended action-head layout.",
            file=sys.stderr,
        )

    command = [
        f"CUDA_VISIBLE_DEVICES={args.gpu}",
        "python",
        "vla-scripts/evaluate_calvin.py",
        "--pretrained_checkpoint",
        checkpoint,
    ]
    return f"cd {shlex.quote(args.repo_root)} && {shell_join(command)}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print a shell command for VLA-Adapter LIBERO or CALVIN evaluation. "
            "The command is generated safely with shell quoting but is not executed."
        )
    )
    parser.add_argument("--repo-root", required=True, help="Absolute VLA-Adapter source checkout root; generated command runs from here.")
    parser.add_argument("--suite", choices=tuple(SUITES), required=True, help="Benchmark suite to evaluate, for example libero_spatial or calvin_abc.")
    parser.add_argument("--benchmark", choices=("libero", "calvin"), required=True, help="Benchmark family to evaluate.")
    parser.add_argument(
        "--checkpoint",
        default=None,
        help=(
            "Checkpoint directory or model id. If omitted, a suite-specific Pro checkpoint under outputs/ is used; "
            "for original CALVIN, pass this explicitly."
        ),
    )
    parser.add_argument(
        "--gpu",
        default="0",
        help="CUDA_VISIBLE_DEVICES value as a comma-separated list of GPU ids, for example 0 or 0,1.",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="stdout/stderr log file. Defaults to a suite-specific eval_logs/*.log path. Use '-' to disable redirection.",
    )
    pro_group = parser.add_mutually_exclusive_group()
    pro_group.add_argument("--use-pro-version", dest="use_pro_version", action="store_true", default=True)
    pro_group.add_argument("--no-use-pro-version", dest="use_pro_version", action="store_false")
    parser.add_argument(
        "--num-trials-per-task",
        type=int,
        default=None,
        help="LIBERO rollouts per task. Defaults to 50. Accepted for CALVIN but not forwarded.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    spec = SUITES[args.suite]

    if spec.benchmark != args.benchmark:
        print(
            f"error: suite {args.suite!r} belongs to benchmark {spec.benchmark!r}, not {args.benchmark!r}",
            file=sys.stderr,
        )
        return 2

    if not os.path.isabs(args.repo_root):
        print("error: --repo-root must be an absolute VLA-Adapter source checkout path", file=sys.stderr)
        return 2

    if not GPU_RE.fullmatch(args.gpu):
        print("error: --gpu must be a comma-separated list of non-negative integer ids, such as 0 or 0,1", file=sys.stderr)
        return 2

    log_file = args.log_file if args.log_file is not None else spec.default_log
    try:
        checkpoint = args.checkpoint if args.checkpoint is not None else default_checkpoint(spec, args.use_pro_version)
        prefix, suffix = log_prefix_and_suffix(log_file, args.repo_root)
        if args.benchmark == "libero":
            command = build_libero(args, spec, checkpoint)
        else:
            command = build_calvin(args, checkpoint)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for warning in warn_for_checkpoint(args.benchmark, checkpoint, args.use_pro_version):
        print(f"warning: {warning}", file=sys.stderr)

    print(f"{prefix}{command}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
