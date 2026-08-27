#!/usr/bin/env python3
"""Remove optimizer/scheduler/iteration keys from an FCOS-style checkpoint."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description="Write a checkpoint copy without solver state")
    p.add_argument("model", help="Input .pth checkpoint")
    p.add_argument("--output", help="Output path; default appends _wo_solver_states before suffix")
    p.add_argument("--ignore-missing", action="store_true", help="Do not fail if a solver key is absent")
    args = p.parse_args()
    try:
        import torch  # type: ignore
    except Exception as exc:
        raise SystemExit(f"torch is required to edit checkpoints: {type(exc).__name__}: {exc}")
    src = Path(args.model)
    if not src.exists():
        p.error(f"checkpoint not found: {src}")
    dst = Path(args.output) if args.output else src.with_name(src.stem + "_wo_solver_states" + src.suffix)
    ckpt = torch.load(str(src), map_location="cpu")
    if not isinstance(ckpt, dict):
        raise SystemExit("checkpoint is not a dictionary")
    missing = []
    for key in ["optimizer", "scheduler", "iteration"]:
        if key in ckpt:
            del ckpt[key]
        else:
            missing.append(key)
    if missing and not args.ignore_missing:
        raise SystemExit(f"missing solver key(s): {', '.join(missing)}; pass --ignore-missing to continue")
    torch.save(ckpt, str(dst))
    print(f"wrote {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
