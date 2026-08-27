#!/usr/bin/env python3
"""Validated wrapper for AdelaiDet onnx/export_model_to_onnx.py."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path


def resolve_existing(base: Path, value: str, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    if not path.exists():
        raise SystemExit(f"{label} does not exist: {path}")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export AdelaiDet model to ONNX with preflight checks")
    parser.add_argument("--repo-root", required=True, help="AdelaiDet source checkout root")
    parser.add_argument("--config", required=True, help="Config YAML, absolute or relative to repo root")
    parser.add_argument("--weights", required=True, help="Model weights path")
    parser.add_argument("--output", required=True, help="Output ONNX path")
    parser.add_argument("--width", type=int, default=0)
    parser.add_argument("--height", type=int, default=0)
    parser.add_argument("--level", type=int, default=0)
    parser.add_argument("--opts", nargs=argparse.REMAINDER, default=[], help="Extra config KEY VALUE pairs")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo_root).resolve()
    exporter = repo / "onnx" / "export_model_to_onnx.py"
    if not exporter.exists():
        raise SystemExit(f"missing ONNX exporter: {exporter}")
    config = resolve_existing(repo, args.config, "config")
    weights = resolve_existing(repo, args.weights, "weights")
    output = Path(args.output)
    if not output.is_absolute():
        output = Path.cwd() / output
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(exporter),
        "--config-file",
        str(config),
        "--output",
        str(output),
        "--width",
        str(args.width),
        "--height",
        str(args.height),
        "--level",
        str(args.level),
        "--opts",
        "MODEL.WEIGHTS",
        str(weights),
        *args.opts,
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
    print(" ".join(shlex.quote(part) for part in cmd))
    if args.dry_run:
        return 0
    return subprocess.call(cmd, cwd=str(repo), env=env)


if __name__ == "__main__":
    raise SystemExit(main())
