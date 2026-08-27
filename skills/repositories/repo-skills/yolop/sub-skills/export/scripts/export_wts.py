#!/usr/bin/env python3
"""Convert a YOLOP PyTorch checkpoint to TensorRT .wts text format.

This is a safer adaptation of toolkits/deploy/gen_wts.py: it requires explicit
paths and supports --dry-run before writing a large text file.
"""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export YOLOP checkpoint tensors to .wts")
    parser.add_argument("--repo-root", required=True, help="Path to a YOLOP checkout")
    parser.add_argument("--checkpoint", required=True, help="YOLOP .pth checkpoint")
    parser.add_argument("--output", help="Output .wts path; required unless --dry-run")
    parser.add_argument("--dry-run", action="store_true", help="Only report tensor count and parameter count")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    checkpoint_path = Path(args.checkpoint).expanduser().resolve()
    if not (repo_root / "lib" / "models" / "YOLOP.py").is_file():
        print(f"ERROR: not a YOLOP checkout: {repo_root}", file=sys.stderr)
        return 2
    if not checkpoint_path.is_file():
        print(f"ERROR: checkpoint not found: {checkpoint_path}", file=sys.stderr)
        return 3
    if not args.dry_run and not args.output:
        print("ERROR: --output is required unless --dry-run is used", file=sys.stderr)
        return 4
    sys.path.insert(0, str(repo_root))

    import torch
    from lib.config import cfg
    from lib.models import get_net

    device = torch.device("cpu")
    model = get_net(cfg)
    checkpoint = torch.load(str(checkpoint_path), map_location=device)
    state_dict = checkpoint.get("state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint
    model.load_state_dict(state_dict)
    model.float().to(device).eval()
    items = list(model.state_dict().items())
    param_count = sum(v.numel() for _, v in items)
    print(f"tensors={len(items)} parameters={param_count}")
    if args.dry_run:
        return 0

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(f"{len(items)}\n")
        for key, tensor in items:
            values = tensor.reshape(-1).cpu().numpy()
            f.write(f"{key} {len(values)} ")
            for value in values:
                f.write(" ")
                f.write(struct.pack(">f", float(value)).hex())
            f.write("\n")
    print(f"wrote={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
