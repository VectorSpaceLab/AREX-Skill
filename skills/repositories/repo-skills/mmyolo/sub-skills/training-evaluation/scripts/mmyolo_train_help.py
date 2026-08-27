#!/usr/bin/env python3
"""Build a safe OpenMIM MMYOLO training command without launching training.

The helper mirrors the package-level `mim train mmyolo` path plus MMYOLO's
training flags, performs small path/argument checks, and prints a command a
human or agent can review. It never imports MMYOLO and never executes the
generated command.
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path
from typing import Iterable, List, Sequence


def _is_remote(value: str) -> bool:
    return value.startswith(("http://", "https://", "s3://", "gs://"))


def _shell_join(argv: Sequence[str], env: dict[str, str]) -> str:
    parts: List[str] = []
    for key, value in env.items():
        if value:
            parts.append(f"{key}={shlex.quote(value)}")
    parts.extend(shlex.quote(str(item)) for item in argv)
    return " ".join(parts)


def _split_key_value(option: str) -> tuple[str, str] | None:
    if "=" not in option:
        return None
    key, value = option.split("=", 1)
    return key, value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build and preflight a package-level MMYOLO training command. "
            "This helper prints the command only; it does not run training."
        )
    )
    parser.add_argument("config", help="training config file path")
    parser.add_argument("--work-dir", help="directory for logs/checkpoints")
    parser.add_argument("--amp", action="store_true", help="add --amp to enable AMP")
    parser.add_argument(
        "--resume",
        nargs="?",
        const="auto",
        help="resume training; omit value for auto-resume, or pass a checkpoint path",
    )
    parser.add_argument(
        "--cfg-options",
        nargs="+",
        default=[],
        metavar="KEY=VALUE",
        help="MMEngine config overrides forwarded to the training command",
    )
    parser.add_argument(
        "--gpus",
        type=int,
        default=1,
        help="GPU count to pass to OpenMIM; use 0 only for a CPU-capable config/workflow",
    )
    parser.add_argument(
        "--launcher",
        choices=["none", "pytorch", "slurm"],
        default="none",
        help="OpenMIM job launcher",
    )
    parser.add_argument("--gpus-per-node", type=int, help="Slurm GPUs per node")
    parser.add_argument("--cpus-per-task", type=int, help="Slurm CPUs per task")
    parser.add_argument("--partition", help="Slurm partition")
    parser.add_argument("--port", type=int, help="distributed master port")
    parser.add_argument(
        "--mim-executable", default="mim", help="OpenMIM executable token"
    )
    parser.add_argument(
        "--package", default="mmyolo", help="OpenMIM package name token"
    )
    parser.add_argument(
        "--cuda-visible-devices",
        help="optional CUDA_VISIBLE_DEVICES prefix for the printed command",
    )
    parser.add_argument(
        "--skip-exists-check",
        action="store_true",
        help="build a template even when config/resume paths do not exist yet",
    )
    return parser


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> list[str]:
    warnings: list[str] = []

    if _is_remote(args.config):
        parser.error("CONFIG must be a local MMEngine config file path")

    config_path = Path(args.config)
    if not args.skip_exists_check and not config_path.is_file():
        parser.error(
            f"config file does not exist: {args.config!r} "
            "(use --skip-exists-check only for template construction)"
        )
    if config_path.suffix and config_path.suffix != ".py":
        warnings.append(
            f"Config suffix is {config_path.suffix!r}; MMYOLO examples normally use .py configs."
        )

    if args.resume not in (None, "auto"):
        if _is_remote(args.resume):
            warnings.append(
                "Resume checkpoint is remote; launching the command may perform network/file backend access."
            )
        elif not args.skip_exists_check and not Path(args.resume).is_file():
            parser.error(
                f"resume checkpoint does not exist: {args.resume!r} "
                "(use --skip-exists-check only for template construction)"
            )

    for item in args.cfg_options:
        if _split_key_value(item) is None:
            warnings.append(
                f"cfg-option {item!r} has no '='; MMEngine DictAction expects KEY=VALUE."
            )

    if args.amp:
        wrapper_override = None
        for item in args.cfg_options:
            pair = _split_key_value(item)
            if pair and pair[0] == "optim_wrapper.type":
                wrapper_override = pair[1].strip("'\"")
        if wrapper_override == "AmpOptimWrapper":
            warnings.append(
                "--amp plus optim_wrapper.type=AmpOptimWrapper will produce an 'AMP already enabled' warning."
            )
        elif wrapper_override and wrapper_override != "OptimWrapper":
            warnings.append(
                "--amp asserts unless optim_wrapper.type is OptimWrapper or already AmpOptimWrapper."
            )
        else:
            warnings.append(
                "--amp requires the merged config optim_wrapper.type to be OptimWrapper, or already AmpOptimWrapper."
            )

    if args.gpus < 0:
        parser.error("--gpus cannot be negative")
    if args.gpus == 0:
        warnings.append(
            "CPU training is often only a smoke/debug path for detection configs; confirm the config and dependencies support it."
        )
    if args.launcher != "none" and not args.port:
        warnings.append(
            "Distributed launchers should use a unique --port for concurrent jobs."
        )
    if args.launcher == "slurm" and not args.partition:
        warnings.append("Slurm launcher usually requires a real --partition value.")
    if args.work_dir:
        parent = Path(args.work_dir).parent
        if str(parent) not in ("", ".") and not parent.exists():
            warnings.append(f"Parent directory for work-dir does not exist yet: {str(parent)!r}.")

    return warnings


def build_command(args: argparse.Namespace) -> tuple[list[str], dict[str, str]]:
    argv: list[str] = [args.mim_executable, "train", args.package, args.config]
    argv.extend(["--gpus", str(args.gpus)])
    if args.launcher != "none":
        argv.extend(["--launcher", args.launcher])
    if args.port is not None:
        argv.extend(["--port", str(args.port)])
    if args.gpus_per_node is not None:
        argv.extend(["--gpus-per-node", str(args.gpus_per_node)])
    if args.cpus_per_task is not None:
        argv.extend(["--cpus-per-task", str(args.cpus_per_task)])
    if args.partition:
        argv.extend(["--partition", args.partition])
    if args.work_dir:
        argv.extend(["--work-dir", args.work_dir])
    if args.amp:
        argv.append("--amp")
    if args.resume is not None:
        argv.append("--resume")
        if args.resume != "auto":
            argv.append(args.resume)
    if args.cfg_options:
        argv.append("--cfg-options")
        argv.extend(args.cfg_options)

    env: dict[str, str] = {}
    if args.cuda_visible_devices is not None:
        env["CUDA_VISIBLE_DEVICES"] = args.cuda_visible_devices
    return argv, env


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    warnings = validate_args(args, parser)
    command, env = build_command(args)

    print("SAFE MMYOLO TRAIN COMMAND (not executed)")
    print("Preflight: command constructed; this helper did not import MMYOLO or start training.")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    print("Command:")
    print(_shell_join(command, env))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
