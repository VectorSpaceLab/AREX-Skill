#!/usr/bin/env python3
"""Render MMDetection3D train/test command strings without executing them.

The generated commands follow the v1.4 train.py/test.py parser and the bundled
single-node distributed and Slurm launchers. This script prints shell text only;
it never imports mmdet3d, opens configs/checkpoints, starts workers, or submits
Slurm jobs.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from itertools import chain
from typing import Iterable, List, Optional, Sequence, Tuple

TASK_CHOICES = (
    "mono_det",
    "multi-view_det",
    "lidar_det",
    "lidar_seg",
    "multi-modality_det",
)
SYNC_BN_CHOICES = ("none", "torch", "mmcv")
LAUNCHER_CHOICES = ("none", "pytorch", "slurm", "mpi")


def _shell_join(tokens: Iterable[object]) -> str:
    return " ".join(shlex.quote(str(token)) for token in tokens)


def _env_token(key: str, value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value)
    if text == "":
        return None
    return f"{key}={shlex.quote(text)}"


def _render(env: Sequence[Tuple[str, object]], argv: Sequence[object]) -> str:
    env_tokens = [token for key, value in env if (token := _env_token(key, value))]
    return " ".join(env_tokens + [_shell_join(argv)])


def _flatten_cfg_options(args: argparse.Namespace) -> List[str]:
    repeated = getattr(args, "cfg_option", None) or []
    grouped = list(chain.from_iterable(getattr(args, "cfg_options", None) or []))
    cfg_options = [*repeated, *grouped]
    bad = [item for item in cfg_options if "=" not in item]
    if bad:
        joined = ", ".join(bad)
        raise ValueError(f"--cfg-option/--cfg-options values must be KEY=VALUE: {joined}")
    return cfg_options


def _add_cfg_options(argv: List[object], args: argparse.Namespace) -> None:
    cfg_options = _flatten_cfg_options(args)
    if cfg_options:
        argv.append("--cfg-options")
        argv.extend(cfg_options)


def _add_cfg_option_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--cfg-option",
        dest="cfg_option",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="append one config override; repeat for multiple overrides",
    )
    parser.add_argument(
        "--cfg-options",
        dest="cfg_options",
        nargs="+",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="append one or more config overrides exactly as train.py/test.py will receive them",
    )


def _add_common_env_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--cuda-visible-devices",
        help="optional CUDA_VISIBLE_DEVICES value, e.g. 0,1,2,3 or -1 for CPU debug",
    )


def _add_train_flags(parser: argparse.ArgumentParser, *, include_work_dir: bool) -> None:
    if include_work_dir:
        parser.add_argument("--work-dir", help="directory for logs/checkpoints")
    parser.add_argument("--amp", action="store_true", help="render --amp")
    parser.add_argument(
        "--sync_bn",
        "--sync-bn",
        dest="sync_bn",
        choices=SYNC_BN_CHOICES,
        default="none",
        help="render --sync_bn with the selected implementation",
    )
    parser.add_argument(
        "--auto-scale-lr",
        action="store_true",
        help="render --auto-scale-lr",
    )
    parser.add_argument(
        "--resume",
        nargs="?",
        const="auto",
        help="render --resume, optionally with a checkpoint path",
    )
    parser.add_argument("--ceph", action="store_true", help="render --ceph")
    _add_cfg_option_args(parser)


def _add_test_flags(parser: argparse.ArgumentParser, *, include_work_dir: bool) -> None:
    if include_work_dir:
        parser.add_argument("--work-dir", help="directory for evaluation metric files/logs")
    parser.add_argument("--ceph", action="store_true", help="render --ceph")
    parser.add_argument("--show", action="store_true", help="render --show")
    parser.add_argument("--show-dir", help="render --show-dir DIR")
    parser.add_argument("--score-thr", type=float, help="render --score-thr FLOAT")
    parser.add_argument("--task", choices=TASK_CHOICES, help="visualization task mode")
    parser.add_argument("--wait-time", type=float, help="render --wait-time FLOAT")
    parser.add_argument("--tta", action="store_true", help="render --tta")
    _add_cfg_option_args(parser)


def _append_train_runtime(argv: List[object], args: argparse.Namespace, *, include_work_dir: bool) -> None:
    if include_work_dir and getattr(args, "work_dir", None):
        argv.extend(["--work-dir", args.work_dir])
    if args.amp:
        argv.append("--amp")
    if args.sync_bn != "none":
        argv.extend(["--sync_bn", args.sync_bn])
    if args.auto_scale_lr:
        argv.append("--auto-scale-lr")
    if args.resume is not None:
        if args.resume == "auto":
            argv.append("--resume")
        else:
            argv.extend(["--resume", args.resume])
    if args.ceph:
        argv.append("--ceph")
    _add_cfg_options(argv, args)


def _append_test_runtime(argv: List[object], args: argparse.Namespace, *, include_work_dir: bool) -> None:
    if include_work_dir and getattr(args, "work_dir", None):
        argv.extend(["--work-dir", args.work_dir])
    if args.ceph:
        argv.append("--ceph")
    if args.show:
        argv.append("--show")
    if args.show_dir:
        argv.extend(["--show-dir", args.show_dir])
    if args.score_thr is not None:
        argv.extend(["--score-thr", args.score_thr])
    if args.task:
        argv.extend(["--task", args.task])
    if args.wait_time is not None:
        argv.extend(["--wait-time", args.wait_time])
    if args.tta:
        argv.append("--tta")
    _add_cfg_options(argv, args)


def _dist_env(args: argparse.Namespace) -> List[Tuple[str, object]]:
    return [
        ("CUDA_VISIBLE_DEVICES", getattr(args, "cuda_visible_devices", None)),
        ("NNODES", args.nodes),
        ("NODE_RANK", args.node_rank),
        ("PORT", args.port),
        ("MASTER_ADDR", args.master_addr),
    ]


def _slurm_env(args: argparse.Namespace) -> List[Tuple[str, object]]:
    return [
        ("CUDA_VISIBLE_DEVICES", getattr(args, "cuda_visible_devices", None)),
        ("GPUS", args.gpus),
        ("GPUS_PER_NODE", args.gpus_per_node),
        ("CPUS_PER_TASK", args.cpus_per_task),
        ("SRUN_ARGS", args.srun_args),
    ]


def render_command(args: argparse.Namespace) -> str:
    command = args.command

    if command == "train":
        argv: List[object] = [args.python, "tools/train.py", args.config]
        _append_train_runtime(argv, args, include_work_dir=True)
        if args.launcher != "none":
            argv.extend(["--launcher", args.launcher])
        return _render([("CUDA_VISIBLE_DEVICES", args.cuda_visible_devices)], argv)

    if command == "test":
        argv = [args.python, "tools/test.py", args.config, args.checkpoint]
        _append_test_runtime(argv, args, include_work_dir=True)
        if args.launcher != "none":
            argv.extend(["--launcher", args.launcher])
        return _render([("CUDA_VISIBLE_DEVICES", args.cuda_visible_devices)], argv)

    if command == "dist-train":
        argv = ["./tools/dist_train.sh", args.config, args.gpus]
        _append_train_runtime(argv, args, include_work_dir=True)
        return _render(_dist_env(args), argv)

    if command == "dist-test":
        argv = ["./tools/dist_test.sh", args.config, args.checkpoint, args.gpus]
        _append_test_runtime(argv, args, include_work_dir=True)
        return _render(_dist_env(args), argv)

    if command == "slurm-train":
        argv = ["./tools/slurm_train.sh", args.partition, args.job_name, args.config, args.work_dir]
        _append_train_runtime(argv, args, include_work_dir=False)
        return _render(_slurm_env(args), argv)

    if command == "slurm-test":
        argv = ["./tools/slurm_test.sh", args.partition, args.job_name, args.config, args.checkpoint]
        _append_test_runtime(argv, args, include_work_dir=True)
        return _render(_slurm_env(args), argv)

    raise AssertionError(f"unhandled command: {command}")


def positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render safe MMDetection3D train/test/dist/slurm command strings without executing them."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    train = subparsers.add_parser("train", help="render python tools/train.py command")
    train.add_argument("config")
    train.add_argument("--python", default="python", help="Python executable token to render")
    train.add_argument("--launcher", choices=LAUNCHER_CHOICES, default="none")
    _add_common_env_arg(train)
    _add_train_flags(train, include_work_dir=True)

    test = subparsers.add_parser("test", help="render python tools/test.py command")
    test.add_argument("config")
    test.add_argument("checkpoint")
    test.add_argument("--python", default="python", help="Python executable token to render")
    test.add_argument("--launcher", choices=LAUNCHER_CHOICES, default="none")
    _add_common_env_arg(test)
    _add_test_flags(test, include_work_dir=True)

    dist_train = subparsers.add_parser("dist-train", help="render ./tools/dist_train.sh command")
    dist_train.add_argument("config")
    dist_train.add_argument("--gpus", type=positive_int, required=True, help="processes/GPUs per node")
    dist_train.add_argument("--nodes", type=positive_int, default=1, help="NNODES value")
    dist_train.add_argument("--node-rank", type=int, default=0, help="NODE_RANK value")
    dist_train.add_argument("--port", type=int, default=29500, help="distributed master port")
    dist_train.add_argument("--master-addr", default="127.0.0.1", help="MASTER_ADDR value")
    _add_common_env_arg(dist_train)
    _add_train_flags(dist_train, include_work_dir=True)

    dist_test = subparsers.add_parser("dist-test", help="render ./tools/dist_test.sh command")
    dist_test.add_argument("config")
    dist_test.add_argument("checkpoint")
    dist_test.add_argument("--gpus", type=positive_int, required=True, help="processes/GPUs per node")
    dist_test.add_argument("--nodes", type=positive_int, default=1, help="NNODES value")
    dist_test.add_argument("--node-rank", type=int, default=0, help="NODE_RANK value")
    dist_test.add_argument("--port", type=int, default=29500, help="distributed master port")
    dist_test.add_argument("--master-addr", default="127.0.0.1", help="MASTER_ADDR value")
    _add_common_env_arg(dist_test)
    _add_test_flags(dist_test, include_work_dir=True)

    slurm_train = subparsers.add_parser("slurm-train", help="render ./tools/slurm_train.sh command")
    slurm_train.add_argument("config")
    slurm_train.add_argument("work_dir")
    slurm_train.add_argument("--partition", required=True)
    slurm_train.add_argument("--job-name", required=True)
    slurm_train.add_argument("--gpus", type=positive_int, default=8)
    slurm_train.add_argument("--gpus-per-node", type=positive_int, default=8)
    slurm_train.add_argument("--cpus-per-task", type=positive_int, default=5)
    slurm_train.add_argument("--srun-args", default="")
    _add_common_env_arg(slurm_train)
    _add_train_flags(slurm_train, include_work_dir=False)

    slurm_test = subparsers.add_parser("slurm-test", help="render ./tools/slurm_test.sh command")
    slurm_test.add_argument("config")
    slurm_test.add_argument("checkpoint")
    slurm_test.add_argument("--partition", required=True)
    slurm_test.add_argument("--job-name", required=True)
    slurm_test.add_argument("--gpus", type=positive_int, default=8)
    slurm_test.add_argument("--gpus-per-node", type=positive_int, default=8)
    slurm_test.add_argument("--cpus-per-task", type=positive_int, default=5)
    slurm_test.add_argument("--srun-args", default="")
    _add_common_env_arg(slurm_test)
    _add_test_flags(slurm_test, include_work_dir=True)

    return parser


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.command in {"test", "dist-test", "slurm-test"}:
        if (args.show or args.show_dir) and not args.task:
            parser.error("--show/--show-dir activate the visualization hook; pass --task with one of: " + ", ".join(TASK_CHOICES))
    if hasattr(args, "node_rank") and args.node_rank < 0:
        parser.error("--node-rank must be >= 0")
    if hasattr(args, "port") and not (0 < args.port < 65536):
        parser.error("--port must be in 1..65535")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)
    try:
        print(render_command(args))
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
