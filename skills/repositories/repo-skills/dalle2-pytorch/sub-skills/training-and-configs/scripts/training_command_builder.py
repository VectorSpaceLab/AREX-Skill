#!/usr/bin/env python3
"""Print a safe DALLE2-pytorch training command without executing it."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


SCRIPT_BY_KIND = {
    "decoder": "run_decoder_training.py",
    "prior": "run_diffusion_prior_training.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build, but do not run, a DALLE2-pytorch training command.")
    parser.add_argument("--kind", choices=("decoder", "prior"), required=True, help="Training target.")
    parser.add_argument("--config", required=True, help="Path to config JSON to pass as --config_file.")
    parser.add_argument("--launcher", choices=("python", "accelerate"), default="python", help="Launcher to print.")
    parser.add_argument(
        "--num-processes",
        type=int,
        default=None,
        help="Optional Accelerate --num_processes value. Only valid with --launcher accelerate.",
    )
    return parser


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def display_path(path: Path) -> str:
    """Prefer a cwd-relative path so printed commands use bundled skill names."""
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def main() -> int:
    args = build_parser().parse_args()
    if args.num_processes is not None:
        if args.launcher != "accelerate":
            raise SystemExit("--num-processes is only valid with --launcher accelerate")
        if args.num_processes <= 0:
            raise SystemExit("--num-processes must be a positive integer")

    script_dir = Path(__file__).parent
    wrapper = display_path(script_dir / SCRIPT_BY_KIND[args.kind])
    config = Path(args.config)

    if args.launcher == "python":
        command = ["python", wrapper, "--config_file", str(config)]
    else:
        command = ["accelerate", "launch"]
        if args.num_processes is not None:
            command.extend(["--num_processes", str(args.num_processes)])
        command.extend([wrapper, "--config_file", str(config)])

    print(shell_join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
