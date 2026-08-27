#!/usr/bin/env python3
"""Safely run or preview the AnyDoor SD2.1-to-control initialization helper.

The source helper expects a stale `./models/anydoor.yaml` path. This wrapper can
create a temporary working directory that provides that path without mutating
the repository checkout.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def ensure_path(path: Path, kind: str) -> None:
    if not path.exists():
        raise SystemExit(f"missing {kind}: {path}")


def prepare_workdir(repo_root: Path, config: Path) -> tuple[Path, list[Path]]:
    tempdir = Path(tempfile.mkdtemp(prefix="anydoor-convert-"))
    models_dir = tempdir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    target = models_dir / "anydoor.yaml"
    try:
        target.symlink_to(config.resolve())
    except Exception:
        shutil.copyfile(config, target)
    return tempdir, [target]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate or run the AnyDoor weight conversion helper.")
    parser.add_argument("--repo-root", type=Path, required=True, help="AnyDoor repository root.")
    parser.add_argument("--input", type=Path, required=True, help="Stable Diffusion checkpoint input.")
    parser.add_argument("--output", type=Path, required=True, help="Output checkpoint path.")
    parser.add_argument("--config", type=Path, default=Path("configs/anydoor.yaml"), help="AnyDoor config file to expose as models/anydoor.yaml.")
    parser.add_argument("--run", action="store_true", help="Actually run the source conversion helper.")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    config_path = (repo_root / args.config).resolve() if not args.config.is_absolute() else args.config.resolve()

    ensure_path(repo_root, "repo root")
    ensure_path(input_path, "input checkpoint")
    if output_path.exists():
        raise SystemExit(f"output already exists: {output_path}")
    ensure_path(config_path, "AnyDoor config")

    print("source helper caveat: tool_add_control_sd21.py expects ./models/anydoor.yaml")
    print(f"using config: {config_path}")

    if not args.run:
        print("dry-run only; rerun with --run to execute the source helper")
        return 0

    workdir, created = prepare_workdir(repo_root, config_path)
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join([str(repo_root), env.get("PYTHONPATH", "")]).strip(os.pathsep)
        cmd = [sys.executable, str(repo_root / "tool_add_control_sd21.py"), str(input_path), str(output_path)]
        print("running:", " ".join(cmd))
        subprocess.run(cmd, cwd=workdir, env=env, check=True)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
