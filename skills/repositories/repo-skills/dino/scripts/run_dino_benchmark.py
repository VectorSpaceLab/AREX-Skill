#!/usr/bin/env python3
"""Plan or launch DINO's bounded architecture benchmark.

The benchmark implementation is repository-specific and is invoked only via
this skill-owned wrapper. No checkpoint/data download is performed by the
wrapper; --launch is required to run it.
"""
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Plan or launch a DINO GFLOPS/FPS benchmark.")
    p.add_argument("--project-root", type=Path, required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--coco-path", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--python", default=sys.executable)
    p.add_argument("--launch", action="store_true")
    return p
def resolve(root: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()



def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.project_root.expanduser().resolve()
    benchmark = root / "tools" / "benchmark.py"
    config = resolve(root, args.config)
    coco = resolve(root, args.coco_path)
    output = resolve(root, args.output_dir)
    if not benchmark.is_file():
        parser().error("project root must contain tools/benchmark.py")
    if not config.is_file():
        parser().error(f"config does not exist: {config}")
    if not coco.is_dir():
        parser().error(f"COCO root does not exist: {coco}")
    if args.batch_size < 1:
        parser().error("--batch-size must be positive")
    command = [args.python, str(benchmark), "--output_dir", str(output), "-c", str(config),
               "--options", f"batch_size={args.batch_size}", "--coco_path", str(coco)]
    print("COMMAND (not launched unless --launch):")
    print(" ".join(shlex.quote(item) for item in command))
    if not args.launch:
        return 0
    output.mkdir(parents=True, exist_ok=True)
    return subprocess.run(command, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
