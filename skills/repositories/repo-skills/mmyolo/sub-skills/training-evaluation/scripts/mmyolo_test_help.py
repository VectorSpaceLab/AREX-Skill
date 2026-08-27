#!/usr/bin/env python3
"""Build a safe OpenMIM MMYOLO testing/evaluation command without running it.

The helper mirrors the package-level `mim test mmyolo` path plus MMYOLO's
script-level testing flags, checks local input paths when requested, validates
pickle suffixes, and prints a command for review. It never imports MMYOLO and
never executes the generated command.
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path
from typing import Iterable, List, Sequence


PICKLE_SUFFIXES = (".pkl", ".pickle")


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
            "Build and preflight a package-level MMYOLO test/evaluation command. "
            "This helper prints the command only; it does not run evaluation."
        )
    )
    parser.add_argument("config", help="test/evaluation config file path")
    parser.add_argument("checkpoint", help="checkpoint file path or remote URI")
    parser.add_argument("--work-dir", help="directory for evaluation artifacts")
    parser.add_argument(
        "--out", help="pickle output path; must end with .pkl or .pickle"
    )
    parser.add_argument(
        "--json-prefix", help="JSON output prefix; pass a prefix, not a full .json file name"
    )
    parser.add_argument("--tta", action="store_true", help="add --tta")
    parser.add_argument("--show", action="store_true", help="add interactive --show")
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="switch supported modules to deploy mode during testing",
    )
    parser.add_argument("--show-dir", help="directory name for painted result images")
    parser.add_argument("--wait-time", type=float, help="interactive show interval")
    parser.add_argument(
        "--cfg-options",
        nargs="+",
        default=[],
        metavar="KEY=VALUE",
        help="MMEngine config overrides forwarded to testing",
    )
    parser.add_argument(
        "--gpus",
        type=int,
        default=1,
        help="GPU count to pass to OpenMIM; use 0 only for CPU-capable evaluation",
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
    parser.add_argument("--mim-executable", default="mim", help="OpenMIM executable token")
    parser.add_argument("--package", default="mmyolo", help="OpenMIM package name token")
    parser.add_argument("--cuda-visible-devices", help="optional CUDA_VISIBLE_DEVICES prefix")
    parser.add_argument(
        "--skip-exists-check",
        action="store_true",
        help="build a template even when config/checkpoint paths do not exist yet",
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

    if _is_remote(args.checkpoint):
        warnings.append("Checkpoint is remote; launching evaluation may perform network/file backend access.")
    elif not args.skip_exists_check and not Path(args.checkpoint).is_file():
        parser.error(
            f"checkpoint file does not exist: {args.checkpoint!r} "
            "(use --skip-exists-check only for template construction)"
        )

    if args.out:
        out_path = Path(args.out)
        if out_path.suffix.lower() not in PICKLE_SUFFIXES:
            parser.error("--out must end with .pkl or .pickle")
        parent = out_path.parent
        if str(parent) not in ("", ".") and not parent.exists():
            warnings.append(f"Parent directory for --out does not exist yet: {str(parent)!r}.")

    if args.json_prefix:
        prefix_path = Path(args.json_prefix)
        if prefix_path.suffix.lower() == ".json":
            warnings.append(
                "--json-prefix expects a prefix, not a complete .json filename; output may be '<prefix>.bbox.json'."
            )
        parent = prefix_path.parent
        if str(parent) not in ("", ".") and not parent.exists():
            warnings.append(f"Parent directory for --json-prefix does not exist yet: {str(parent)!r}.")

    if args.out and args.json_prefix:
        warnings.append(
            "Using --json-prefix configures JSON format-only evaluator behavior; verify this is intended when also dumping PKL."
        )
    if args.tta:
        warnings.append("--tta requires tta_model and tta_pipeline in the merged config.")
    if args.show:
        warnings.append("--show is interactive and may fail/hang on headless machines; prefer --show-dir.")
    if args.deploy:
        warnings.append("--deploy switches supported model modules for testing; it is not ONNX/TensorRT/RKNN export.")
    if args.gpus < 0:
        parser.error("--gpus cannot be negative")
    if args.gpus == 0:
        warnings.append("CPU evaluation/inference must be supported by the config and installed dependencies.")
    if args.launcher != "none" and not args.port:
        warnings.append("Distributed launchers should use a unique --port for concurrent jobs.")
    if args.launcher == "slurm" and not args.partition:
        warnings.append("Slurm launcher usually requires a real --partition value.")
    if args.work_dir:
        parent = Path(args.work_dir).parent
        if str(parent) not in ("", ".") and not parent.exists():
            warnings.append(f"Parent directory for work-dir does not exist yet: {str(parent)!r}.")

    for item in args.cfg_options:
        if _split_key_value(item) is None:
            warnings.append(f"cfg-option {item!r} has no '='; MMEngine DictAction expects KEY=VALUE.")

    return warnings


def build_command(args: argparse.Namespace) -> tuple[list[str], dict[str, str]]:
    argv: list[str] = [args.mim_executable, "test", args.package, args.config]
    argv.extend(["--checkpoint", args.checkpoint, "--gpus", str(args.gpus)])
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
    if args.out:
        argv.extend(["--out", args.out])
    if args.json_prefix:
        argv.extend(["--json-prefix", args.json_prefix])
    if args.tta:
        argv.append("--tta")
    if args.show:
        argv.append("--show")
    if args.deploy:
        argv.append("--deploy")
    if args.show_dir:
        argv.extend(["--show-dir", args.show_dir])
    if args.wait_time is not None:
        argv.extend(["--wait-time", str(args.wait_time)])
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

    print("SAFE MMYOLO TEST COMMAND (not executed)")
    print("Preflight: command constructed; this helper did not import MMYOLO or start evaluation.")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    print("Command:")
    print(_shell_join(command, env))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
