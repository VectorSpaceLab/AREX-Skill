#!/usr/bin/env python3
"""Build MMAction2 train/test command templates without executing them.

The script has no MMAction2 dependency. It validates required command-shape
arguments and prints a shell command preview plus safety notes. It does not run
training, testing, downloads, Slurm submission, or any destructive operation.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable, List, Optional

TRAIN_MODES = {"train", "dist-train", "slurm-train"}
TEST_MODES = {"test", "dist-test", "slurm-test"}
DIST_MODES = {"dist-train", "dist-test"}
SLURM_MODES = {"slurm-train", "slurm-test"}
SINGLE_MODES = {"train", "test"}


def q(value: object) -> str:
    """Shell-quote one token deterministically."""

    return shlex.quote(str(value))


def extend_cfg_options(cmd: List[str], cfg_options: Optional[List[str]]) -> None:
    if cfg_options:
        cmd.append("--cfg-options")
        cmd.extend(cfg_options)


def train_args(args: argparse.Namespace) -> List[str]:
    cmd: List[str] = []
    if args.work_dir:
        cmd.extend(["--work-dir", args.work_dir])
    if args.resume is not None:
        cmd.append("--resume")
        if args.resume != "auto":
            cmd.append(args.resume)
    if args.amp:
        cmd.append("--amp")
    if args.no_validate:
        cmd.append("--no-validate")
    if args.auto_scale_lr:
        cmd.append("--auto-scale-lr")
    if args.seed is not None:
        cmd.extend(["--seed", str(args.seed)])
    if args.diff_rank_seed:
        cmd.append("--diff-rank-seed")
    if args.deterministic:
        cmd.append("--deterministic")
    extend_cfg_options(cmd, args.cfg_option)
    return cmd


def test_args(args: argparse.Namespace) -> List[str]:
    cmd: List[str] = []
    if args.work_dir:
        cmd.extend(["--work-dir", args.work_dir])
    if args.dump:
        cmd.extend(["--dump", args.dump])
    if args.show_dir:
        cmd.extend(["--show-dir", args.show_dir])
    if args.show:
        cmd.append("--show")
    if args.interval is not None:
        cmd.extend(["--interval", str(args.interval)])
    if args.wait_time is not None:
        cmd.extend(["--wait-time", str(args.wait_time)])
    extend_cfg_options(cmd, args.cfg_option)
    return cmd


def join_cmd(tokens: Iterable[object]) -> str:
    return " ".join(q(t) for t in tokens)


def env_prefix(pairs: Iterable[tuple[str, object]]) -> str:
    return " ".join(f"{key}={q(value)}" for key, value in pairs if value is not None)


def validate(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if not args.config or not args.config.strip():
        parser.error("--config is required and must be non-empty")

    if args.mode in TEST_MODES and not args.checkpoint:
        parser.error(f"--checkpoint is required for {args.mode}")
    if args.mode in TRAIN_MODES and args.checkpoint:
        parser.error("--checkpoint is only valid for test, dist-test, or slurm-test modes")

    if args.mode not in TRAIN_MODES:
        bad_train_flags = []
        if args.resume is not None:
            bad_train_flags.append("--resume")
        if args.amp:
            bad_train_flags.append("--amp")
        if args.no_validate:
            bad_train_flags.append("--no-validate")
        if args.auto_scale_lr:
            bad_train_flags.append("--auto-scale-lr")
        if args.seed is not None:
            bad_train_flags.append("--seed")
        if args.diff_rank_seed:
            bad_train_flags.append("--diff-rank-seed")
        if args.deterministic:
            bad_train_flags.append("--deterministic")
        if bad_train_flags:
            parser.error(", ".join(bad_train_flags) + " are train-only flags")

    if args.mode not in TEST_MODES:
        bad_test_flags = []
        if args.dump:
            bad_test_flags.append("--dump")
        if args.show_dir:
            bad_test_flags.append("--show-dir")
        if args.show:
            bad_test_flags.append("--show")
        if args.interval is not None:
            bad_test_flags.append("--interval")
        if args.wait_time is not None:
            bad_test_flags.append("--wait-time")
        if bad_test_flags:
            parser.error(", ".join(bad_test_flags) + " are test-only flags")

    if args.dump and not args.dump.endswith((".pkl", ".pickle")):
        parser.error("--dump must end with .pkl or .pickle to match MMAction2 test validation")

    if args.mode in DIST_MODES:
        if args.gpus is None:
            parser.error(f"--gpus is required for {args.mode}")
        if args.gpus <= 0:
            parser.error("--gpus must be a positive integer")
    elif args.mode in SINGLE_MODES and args.gpus is not None:
        parser.error("--gpus is only valid for dist-* or slurm-* modes")

    if args.mode in SLURM_MODES:
        if not args.partition:
            parser.error(f"--partition is required for {args.mode}")
        if not args.job_name:
            parser.error(f"--job-name is required for {args.mode}")
        if args.gpus is not None and args.gpus <= 0:
            parser.error("--gpus must be a positive integer")
        if args.gpus_per_node is not None and args.gpus_per_node <= 0:
            parser.error("--gpus-per-node must be a positive integer")
        if args.cpus_per_task is not None and args.cpus_per_task <= 0:
            parser.error("--cpus-per-task must be a positive integer")
    else:
        if args.partition:
            parser.error("--partition is only valid for slurm-* modes")
        if args.job_name:
            parser.error("--job-name is only valid for slurm-* modes")
        if args.gpus_per_node is not None:
            parser.error("--gpus-per-node is only valid for slurm-* modes")
        if args.cpus_per_task is not None:
            parser.error("--cpus-per-task is only valid for slurm-* modes")
        if args.srun_arg:
            parser.error("--srun-arg is only valid for slurm-* modes")

    if args.cpu and args.mode not in SINGLE_MODES:
        parser.error("--cpu is only valid for single-process train/test commands")

    if args.nnodes <= 0:
        parser.error("--nnodes must be a positive integer")
    if args.node_rank < 0:
        parser.error("--node-rank must be zero or a positive integer")
    if args.port <= 0:
        parser.error("--port must be a positive integer")
    if args.mode not in DIST_MODES and (
        args.nnodes != 1 or args.node_rank != 0 or args.master_addr != "127.0.0.1" or args.port != 29500
    ):
        parser.error("--nnodes, --node-rank, --master-addr, and --port are only valid for dist-* modes")


def tool_path(args: argparse.Namespace, filename: str) -> str:
    """Return a user-runtime MMAction2 tool path without assuming this skill owns it."""

    return f"{args.tools_dir.rstrip('/')}/{filename}"


def build_command(args: argparse.Namespace) -> str:
    if args.mode == "train":
        cmd = ["python", tool_path(args, "train.py"), args.config] + train_args(args)
        prefix = "CUDA_VISIBLE_DEVICES=-1 " if args.cpu else ""
        return prefix + join_cmd(cmd)

    if args.mode == "test":
        cmd = ["python", tool_path(args, "test.py"), args.config, args.checkpoint] + test_args(args)
        prefix = "CUDA_VISIBLE_DEVICES=-1 " if args.cpu else ""
        return prefix + join_cmd(cmd)

    if args.mode == "dist-train":
        env = env_prefix(
            [
                ("NNODES", args.nnodes),
                ("NODE_RANK", args.node_rank),
                ("PORT", args.port),
                ("MASTER_ADDR", args.master_addr),
            ]
        )
        cmd = ["bash", tool_path(args, "dist_train.sh"), args.config, args.gpus] + train_args(args)
        return f"{env} {join_cmd(cmd)}".strip()

    if args.mode == "dist-test":
        env = env_prefix(
            [
                ("NNODES", args.nnodes),
                ("NODE_RANK", args.node_rank),
                ("PORT", args.port),
                ("MASTER_ADDR", args.master_addr),
            ]
        )
        cmd = ["bash", tool_path(args, "dist_test.sh"), args.config, args.checkpoint, args.gpus] + test_args(args)
        return f"{env} {join_cmd(cmd)}".strip()

    if args.mode == "slurm-train":
        slurm_gpus = args.gpus if args.gpus is not None else 8
        slurm_gpus_per_node = args.gpus_per_node if args.gpus_per_node is not None else slurm_gpus
        slurm_cpus = args.cpus_per_task if args.cpus_per_task is not None else 5
        env_pairs = [
            ("GPUS", slurm_gpus),
            ("GPUS_PER_NODE", slurm_gpus_per_node),
            ("CPUS_PER_TASK", slurm_cpus),
        ]
        if args.srun_arg:
            env_pairs.append(("SRUN_ARGS", " ".join(args.srun_arg)))
        cmd = ["bash", tool_path(args, "slurm_train.sh"), args.partition, args.job_name, args.config] + train_args(args)
        return f"{env_prefix(env_pairs)} {join_cmd(cmd)}"

    if args.mode == "slurm-test":
        slurm_gpus = args.gpus if args.gpus is not None else 8
        slurm_gpus_per_node = args.gpus_per_node if args.gpus_per_node is not None else slurm_gpus
        slurm_cpus = args.cpus_per_task if args.cpus_per_task is not None else 5
        env_pairs = [
            ("GPUS", slurm_gpus),
            ("GPUS_PER_NODE", slurm_gpus_per_node),
            ("CPUS_PER_TASK", slurm_cpus),
        ]
        if args.srun_arg:
            env_pairs.append(("SRUN_ARGS", " ".join(args.srun_arg)))
        cmd = ["bash", tool_path(args, "slurm_test.sh"), args.partition, args.job_name, args.config, args.checkpoint] + test_args(args)
        return f"{env_prefix(env_pairs)} {join_cmd(cmd)}"

    raise AssertionError(f"unhandled mode: {args.mode}")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print an MMAction2 train/test command template. The command is "
            "not executed; no training, testing, downloads, Slurm submission, "
            "or file writes are performed by this helper."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "mode",
        choices=sorted(TRAIN_MODES | TEST_MODES),
        help="Command family to build.",
    )
    parser.add_argument("--config", required=True, help="MMAction2 config path to place in the command.")
    parser.add_argument("--checkpoint", help="Checkpoint path or URL; required for test modes.")
    parser.add_argument(
        "--tools-dir",
        default="<MMAction2_TOOLS>",
        help=(
            "Directory in the user's runtime that contains MMAction2 train/test helper entrypoints. "
            "For a source checkout this is often the repository's tools directory; the default is a placeholder."
        ),
    )
    parser.add_argument("--cpu", action="store_true", help="Prefix single-process command with CUDA_VISIBLE_DEVICES=-1.")
    parser.add_argument("--work-dir", help="Work directory argument for train/test scripts.")
    parser.add_argument(
        "--cfg-option",
        "--cfg-options",
        action="append",
        dest="cfg_option",
        metavar="KEY=VALUE",
        help="Append one config override; repeated values are emitted after --cfg-options.",
    )

    train_group = parser.add_argument_group("train-only options")
    train_group.add_argument("--amp", action="store_true", help="Add --amp for compatible training configs.")
    train_group.add_argument(
        "--resume",
        nargs="?",
        const="auto",
        help="Add --resume, optionally with a checkpoint path; no value means auto-resume.",
    )
    train_group.add_argument("--auto-scale-lr", action="store_true", help="Add --auto-scale-lr.")
    train_group.add_argument("--no-validate", action="store_true", help="Add --no-validate.")
    train_group.add_argument("--seed", type=int, help="Add --seed.")
    train_group.add_argument("--diff-rank-seed", action="store_true", help="Add --diff-rank-seed.")
    train_group.add_argument("--deterministic", action="store_true", help="Add --deterministic.")

    test_group = parser.add_argument_group("test-only options")
    test_group.add_argument("--dump", help="Prediction dump path; must end with .pkl or .pickle.")
    test_group.add_argument("--show-dir", help="Visualization output directory.")
    test_group.add_argument("--show", action="store_true", help="Add GUI --show flag.")
    test_group.add_argument("--interval", type=int, help="Visualization interval.")
    test_group.add_argument("--wait-time", type=float, help="GUI wait time per sample.")

    dist_group = parser.add_argument_group("distributed options")
    dist_group.add_argument("--gpus", type=int, help="GPU count for dist modes; GPUS env for Slurm modes.")
    dist_group.add_argument("--nnodes", type=int, default=1, help="Number of nodes for dist-* modes.")
    dist_group.add_argument("--node-rank", type=int, default=0, help="Node rank for dist-* modes.")
    dist_group.add_argument("--port", type=int, default=29500, help="Master port for dist-* modes.")
    dist_group.add_argument("--master-addr", default="127.0.0.1", help="Master address for dist-* modes.")

    slurm_group = parser.add_argument_group("slurm options")
    slurm_group.add_argument("--partition", help="Slurm partition; required for slurm-* modes.")
    slurm_group.add_argument("--job-name", help="Slurm job name; required for slurm-* modes.")
    slurm_group.add_argument("--gpus-per-node", type=int, help="GPUS_PER_NODE env for Slurm modes.")
    slurm_group.add_argument("--cpus-per-task", type=int, help="CPUS_PER_TASK env for Slurm modes.")
    slurm_group.add_argument(
        "--srun-arg",
        action="append",
        help="Append an srun option string; repeated values are joined into SRUN_ARGS.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    validate(args, parser)
    command = build_command(args)

    print("# Preview only: this helper did not execute training, testing, downloads, or Slurm submission.")
    print("# Ensure MMAction2, PyTorch, MMEngine/MMCV, data, checkpoints, and optional CUDA/Slurm resources exist in the target environment.")
    if args.cpu:
        print("# CPU mode hides GPUs with CUDA_VISIBLE_DEVICES=-1; expect slow video workloads.")
    if args.mode in SLURM_MODES:
        print("# Slurm resources are cluster-specific; review partition, GPU counts, CPU counts, account/SRUN_ARGS, and output paths before submission.")
    if args.mode in DIST_MODES:
        print("# Distributed jobs require matching NNODES/NODE_RANK/MASTER_ADDR/PORT across nodes and a free communication port.")
    print(command)
    return 0


if __name__ == "__main__":
    sys.exit(main())
