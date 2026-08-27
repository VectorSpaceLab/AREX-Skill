#!/usr/bin/env python3
"""Build or launch a bounded DINO checkpoint evaluation command.

This bundled helper replaces the repository's shell evaluation launchers. It
never downloads data/checkpoints and only launches the project entry point when
--launch is explicit; otherwise it prints a reviewable command.
"""
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Plan or launch one DINO COCO checkpoint evaluation.")
    p.add_argument("--project-root", type=Path, required=True, help="DINO project root containing main.py")
    p.add_argument("--config", required=True, help="config path, relative to project root")
    p.add_argument("--coco-path", type=Path, required=True, help="existing COCO root")
    p.add_argument("--checkpoint", type=Path, required=True, help="local checkpoint file")
    p.add_argument("--output-dir", type=Path, required=True, help="writable evaluation output directory")
    p.add_argument("--device", default="cuda")
    p.add_argument("--num-workers", type=int, default=2)
    p.add_argument("--amp", action="store_true")
    p.add_argument("--option", action="append", default=[], metavar="KEY=VALUE", help="repeatable config override")
    p.add_argument("--python", default=sys.executable, help="Python executable for the project command")
    p.add_argument("--launch", action="store_true", help="launch after printing the command")
    return p


def resolve(root: Path, value: str | Path, label: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.project_root.expanduser().resolve()
    if not (root / "main.py").is_file():
        parser().error("--project-root must contain main.py")
    config = resolve(root, args.config, "config")
    checkpoint = resolve(root, args.checkpoint, "checkpoint")
    coco = resolve(root, args.coco_path, "COCO root")
    output = resolve(root, args.output_dir, "output directory")
    if not config.is_file():
        parser().error(f"config does not exist: {config}")
    if not checkpoint.is_file():
        parser().error(f"checkpoint does not exist: {checkpoint}")
    if not coco.is_dir():
        parser().error(f"COCO root does not exist: {coco}")
    if args.num_workers < 0:
        parser().error("--num-workers cannot be negative")
    for option in args.option:
        if "=" not in option:
            parser().error(f"invalid --option {option!r}; use KEY=VALUE")
    command = [
        args.python, str(root / "main.py"), "--output_dir", str(output),
        "-c", str(config), "--coco_path", str(coco), "--eval", "--resume", str(checkpoint),
        "--device", args.device, "--num_workers", str(args.num_workers),
    ]
    if args.amp:
        command.append("--amp")
    if args.option:
        command += ["--options", *args.option]
    print("COMMAND (not launched unless --launch):")
    print(" ".join(shlex.quote(item) for item in command))
    if not args.launch:
        return 0
    output.mkdir(parents=True, exist_ok=True)
    return subprocess.run(command, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
