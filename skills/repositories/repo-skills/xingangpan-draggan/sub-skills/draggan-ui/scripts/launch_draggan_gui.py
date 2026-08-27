#!/usr/bin/env python3
"""Build or execute a safe DragGAN desktop GUI launch command.

The helper wraps a local DragGAN checkout's `visualizer_drag.py` without relying
on the generated skill living inside that checkout. By default it prints the
command and performs preflight checks; pass --execute to start the GUI.
"""
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

DEFAULT_ORDER = [
    "stylegan2_lions_512_pytorch.pkl",
    "stylegan2-ffhq-512x512.pkl",
    "stylegan2-afhqcat-512x512.pkl",
    "stylegan2-car-config-f.pkl",
    "stylegan2_dogs_1024_pytorch.pkl",
    "stylegan2_horses_256_pytorch.pkl",
    "stylegan2-cat-config-f.pkl",
    "stylegan2_elephants_512_pytorch.pkl",
    "stylegan_human_v2_512.pkl",
    "stylegan2-lhq-256x256.pkl",
]


def infer_family(path: Path) -> str:
    name = path.name.lower()
    if "stylegan_human" in name:
        return "stylegan_human"
    if "stylegan3" in name:
        return "stylegan3"
    if "stylegan2" in name:
        return "stylegan2"
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight and launch DragGAN desktop visualizer.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Local DragGAN checkout containing visualizer_drag.py.")
    parser.add_argument("--checkpoint-dir", type=Path, default=Path("checkpoints"), help="Directory containing .pkl checkpoints, relative to repo root unless absolute.")
    parser.add_argument("--pkl", action="append", default=[], help="Checkpoint path or URL to pass to visualizer_drag.py. May be repeated.")
    parser.add_argument("--capture-dir", type=Path, help="Optional screenshot capture directory passed through to visualizer_drag.py.")
    parser.add_argument("--browse-dir", type=Path, help="Optional browse directory passed through to visualizer_drag.py.")
    parser.add_argument("--execute", action="store_true", help="Actually run the GUI. Without this flag the command is printed only.")
    args = parser.parse_args()

    repo_root = args.repo_root.expanduser().resolve()
    script = repo_root / "visualizer_drag.py"
    if not script.exists():
        print(f"ERROR: cannot find visualizer_drag.py under repo root: {repo_root}", file=sys.stderr)
        return 2

    checkpoint_dir = args.checkpoint_dir.expanduser()
    if not checkpoint_dir.is_absolute():
        checkpoint_dir = repo_root / checkpoint_dir
    checkpoint_dir = checkpoint_dir.resolve()

    pkls = [Path(p).expanduser() if not (p.startswith("http://") or p.startswith("https://")) else p for p in args.pkl]
    if not pkls:
        ordered = [checkpoint_dir / name for name in DEFAULT_ORDER if (checkpoint_dir / name).exists()]
        extras = sorted(p for p in checkpoint_dir.glob("*.pkl") if p not in ordered) if checkpoint_dir.exists() else []
        pkls = ordered + extras

    if not pkls:
        print(f"ERROR: no checkpoint .pkl files found. Checked: {checkpoint_dir}", file=sys.stderr)
        print("Place pretrained DragGAN/StyleGAN2/StyleGAN-Human .pkl files in the checkpoint directory, or pass --pkl.", file=sys.stderr)
        return 3

    warnings = []
    resolved_pkls = []
    for p in pkls:
        if isinstance(p, Path):
            if not p.exists():
                warnings.append(f"missing checkpoint: {p}")
            if infer_family(p) == "unknown":
                warnings.append(f"renderer may not infer generator class from filename: {p.name}")
            resolved_pkls.append(str(p))
        else:
            resolved_pkls.append(p)

    cmd = [sys.executable, str(script), *resolved_pkls]
    if args.capture_dir:
        cmd.extend(["--capture-dir", str(args.capture_dir.expanduser())])
    if args.browse_dir:
        cmd.extend(["--browse-dir", str(args.browse_dir.expanduser())])

    print("Command:")
    print(" ".join(shlex.quote(part) for part in cmd))
    for warning in warnings:
        print(f"WARNING: {warning}")
    if warnings and args.execute:
        print("ERROR: fix warnings before launching with --execute.", file=sys.stderr)
        return 4
    if args.execute:
        return subprocess.call(cmd, cwd=str(repo_root))
    print("Dry run only. Pass --execute to start the desktop GUI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
