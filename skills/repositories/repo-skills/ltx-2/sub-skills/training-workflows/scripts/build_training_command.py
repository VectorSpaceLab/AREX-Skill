#!/usr/bin/env python3
"""Build an LTX Trainer launch command without executing it.

The default launcher path points at the bundled `launch_training.py` helper in
this skill tree so the command is self-contained.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

ACCELERATE_CONFIGS = {
    "ddp": "configs/accelerate/ddp.yaml",
    "ddp_compile": "configs/accelerate/ddp_compile.yaml",
    "fsdp": "configs/accelerate/fsdp.yaml",
    "fsdp_compile": "configs/accelerate/fsdp_compile.yaml",
}

BUNDLED_ACCELERATE_CONFIGS = {
    name: Path(__file__).resolve().parents[1] / "references" / "accelerate" / Path(rel).name
    for name, rel in ACCELERATE_CONFIGS.items()
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Training YAML config path")
    parser.add_argument(
        "--trainer-root",
        type=Path,
        default=None,
        help="Optional external LTX-Trainer checkout root used for source-compatible launcher and config paths",
    )
    parser.add_argument(
        "--train-script",
        type=Path,
        default=None,
        help="Explicit launcher path; overrides --trainer-root for the script path",
    )
    parser.add_argument(
        "--distributed",
        choices=["none", "default", "ddp", "ddp_compile", "fsdp", "fsdp_compile"],
        default="none",
        help="Launch style: none=single process, default=accelerate profile, or a named Accelerate config",
    )
    parser.add_argument("--accelerate-config-path", type=Path, help="Explicit Accelerate config path")
    parser.add_argument("--num-processes", type=int, help="Accelerate --num_processes value")
    parser.add_argument("--cuda-visible-devices", help="Optional CUDA_VISIBLE_DEVICES prefix, e.g. 0,1")
    parser.add_argument(
        "--launcher",
        choices=["uv", "python"],
        default="uv",
        help="Use 'uv run python'/'uv run accelerate' or raw 'python'/'accelerate'",
    )
    parser.add_argument(
        "--disable-progress-bars",
        action="store_true",
        help="Append launcher --disable-progress-bars",
    )
    parser.add_argument(
        "--extra-train-arg",
        action="append",
        default=[],
        help="Additional argument appended after the config path; may be repeated",
    )
    parser.add_argument("--check-paths", action="store_true", help="Fail if config/train/accelerate paths are missing")
    parser.add_argument("--json", action="store_true", help="Emit JSON with argv and shell command")
    return parser.parse_args()


def train_script_path(args: argparse.Namespace) -> Path:
    if args.train_script is not None:
        return args.train_script
    if args.trainer_root is not None:
        return args.trainer_root / "scripts" / "train.py"
    return Path(__file__).with_name("launch_training.py")


def accelerate_config_path(args: argparse.Namespace) -> Path | None:
    if args.accelerate_config_path is not None:
        return args.accelerate_config_path
    if args.distributed in ACCELERATE_CONFIGS:
        rel = Path(ACCELERATE_CONFIGS[args.distributed])
        if args.trainer_root is not None:
            return args.trainer_root / rel
        return BUNDLED_ACCELERATE_CONFIGS[args.distributed]
    return None


def build_argv(args: argparse.Namespace) -> list[str]:
    script = train_script_path(args)
    cfg = args.config
    train_args = [str(script), str(cfg)]
    if args.disable_progress_bars:
        train_args.append("--disable-progress-bars")
    train_args.extend(args.extra_train_arg)

    if args.distributed == "none":
        if args.launcher == "uv":
            return ["uv", "run", "python", *train_args]
        return ["python", *train_args]

    argv = ["uv", "run", "accelerate", "launch"] if args.launcher == "uv" else ["accelerate", "launch"]
    accel_cfg = accelerate_config_path(args)
    if accel_cfg is not None:
        argv.extend(["--config_file", str(accel_cfg)])
    if args.num_processes is not None:
        argv.extend(["--num_processes", str(args.num_processes)])
    argv.extend(train_args)
    return argv


def check_paths(args: argparse.Namespace) -> list[str]:
    missing: list[str] = []
    if not args.config.exists():
        missing.append(f"config does not exist: {args.config}")
    script = train_script_path(args)
    if not script.exists():
        missing.append(f"launcher does not exist: {script}")
    accel_cfg = accelerate_config_path(args)
    if accel_cfg is not None and not accel_cfg.exists():
        missing.append(f"accelerate config does not exist: {accel_cfg}")
    return missing


def shell_command(args: argparse.Namespace, argv: list[str]) -> str:
    command = shlex.join(argv)
    if args.cuda_visible_devices:
        command = f"CUDA_VISIBLE_DEVICES={shlex.quote(args.cuda_visible_devices)} {command}"
    return command


def main() -> int:
    args = parse_args()
    errors = check_paths(args) if args.check_paths else []
    argv = build_argv(args)
    command = shell_command(args, argv)
    report = {
        "ok": not errors,
        "executes_training": False,
        "distributed": args.distributed,
        "argv": argv,
        "shell_command": command,
        "errors": errors,
        "note": "This helper only prints a command. Review and run it manually after approval.",
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        if errors:
            print("Command not ready:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
        print(command)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
