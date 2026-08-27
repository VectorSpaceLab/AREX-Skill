#!/usr/bin/env python3
"""Run a tiny stylegan2_pytorch CLI training smoke test.

The script wraps the installed `stylegan2_pytorch` console command with
one-step, low-capacity defaults and temporary output directories. It can also
create a deterministic image fixture using the companion make_tiny_fixture.py
script.

Examples:
    python scripts/train_smoke.py --work-dir /tmp/sg2-smoke --dry-run
    python scripts/train_smoke.py --work-dir /tmp/sg2-smoke
    python scripts/train_smoke.py --data-dir /path/to/tiny/images --work-dir /tmp/sg2-smoke
"""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _companion_fixture_script() -> Path:
    return Path(__file__).resolve().with_name("make_tiny_fixture.py")


def _make_fixture(output_dir: Path, count: int, size: int, transparent: bool, overwrite: bool) -> None:
    script = _companion_fixture_script()
    cmd = [sys.executable, str(script), "--output-dir", str(output_dir), "--count", str(count), "--size", str(size)]
    if transparent:
        cmd.append("--transparent")
    if overwrite:
        cmd.append("--overwrite")
    subprocess.run(cmd, check=True)


def _find_cli() -> str:
    exe = shutil.which("stylegan2_pytorch")
    if exe is None:
        raise SystemExit("Could not find `stylegan2_pytorch` on PATH. Install the package in the active environment first.")
    return exe


def build_command(args: argparse.Namespace, data_dir: Path, work_dir: Path) -> list[str]:
    exe = _find_cli()
    cmd = [
        exe,
        "--data",
        str(data_dir),
        "--results_dir",
        str(work_dir / "results"),
        "--models_dir",
        str(work_dir / "models"),
        "--name",
        args.name,
        "--new",
        "--image_size",
        str(args.image_size),
        "--batch_size",
        str(args.batch_size),
        "--gradient_accumulate_every",
        str(args.gradient_accumulate_every),
        "--network_capacity",
        str(args.network_capacity),
        "--num_train_steps",
        str(args.steps),
        "--save_every",
        "1",
        "--evaluate_every",
        "1",
        "--num_image_tiles",
        "1",
        "--num_workers",
        "0",
    ]
    if args.transparent:
        cmd.append("--transparent")
    return cmd


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a tiny stylegan2_pytorch CLI smoke test.")
    parser.add_argument("--data-dir", type=Path, help="Existing tiny image folder. If omitted, a synthetic fixture is created.")
    parser.add_argument("--work-dir", type=Path, help="Directory for fixture, models, and results. Defaults to a new temp directory.")
    parser.add_argument("--name", default="smoke", help="Project name under models/results.")
    parser.add_argument("--image-size", "--image_size", dest="image_size", type=int, default=64, help="Power-of-two image size for smoke run.")
    parser.add_argument("--batch-size", "--batch_size", dest="batch_size", type=int, default=2, help="Small batch size for smoke run.")
    parser.add_argument("--gradient-accumulate-every", "--gradient_accumulate_every", dest="gradient_accumulate_every", type=int, default=1)
    parser.add_argument("--network-capacity", "--network_capacity", dest="network_capacity", type=int, default=8)
    parser.add_argument("--steps", type=int, default=1, help="Number of train steps; keep at 1 for a smoke test.")
    parser.add_argument("--fixture-count", type=int, default=8, help="Synthetic fixture image count if --data-dir is omitted.")
    parser.add_argument("--transparent", action="store_true", help="Generate/use transparent RGBA fixture and pass --transparent.")
    parser.add_argument("--overwrite-fixture", action="store_true", help="Allow regenerating a non-empty synthetic fixture directory.")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing training.")
    parser.add_argument("--timeout", type=float, default=300.0, help="Seconds allowed for the smoke command.")
    args = parser.parse_args()

    if args.steps <= 0:
        raise SystemExit("--steps must be positive")
    if args.image_size & (args.image_size - 1):
        raise SystemExit("--image-size must be a power of two")

    work_dir = args.work_dir or Path(tempfile.mkdtemp(prefix="sg2-smoke-"))
    work_dir = work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    if args.data_dir is None:
        data_dir = work_dir / "fixture"
        if not args.dry_run:
            _make_fixture(data_dir, count=args.fixture_count, size=args.image_size, transparent=args.transparent, overwrite=args.overwrite_fixture)
        else:
            print(f"Would create synthetic fixture at {data_dir}")
    else:
        data_dir = args.data_dir.resolve()
        if not data_dir.exists():
            raise SystemExit(f"--data-dir does not exist: {data_dir}")

    cmd = build_command(args, data_dir=data_dir, work_dir=work_dir)
    print("Command:")
    print(" ".join(shlex.quote(part) for part in cmd))
    print(f"Work dir: {work_dir}")

    if args.dry_run:
        return

    try:
        subprocess.run(cmd, check=True, timeout=args.timeout)
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"Smoke command timed out after {exc.timeout} seconds") from exc

    print("Smoke training completed.")
    print(f"Expected checkpoint dir: {work_dir / 'models' / args.name}")
    print(f"Expected results dir: {work_dir / 'results' / args.name}")


if __name__ == "__main__":
    main()
