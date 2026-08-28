#!/usr/bin/env python3
"""Convert a tensor-only PyTorch checkpoint to safetensors without overwriting by default."""
import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--key", default=None, help="Optional mapping key containing the tensor dict")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        parser.error(f"output exists; pass --force explicitly: {args.output}")
    try:
        import torch
        from safetensors.torch import save_file
    except ImportError as exc:
        print(f"missing conversion dependency: {exc}")
        return 2
    if not args.input.is_file():
        parser.error(f"input does not exist: {args.input}")
    payload = torch.load(args.input, map_location="cpu", weights_only=False)
    if args.key is not None:
        payload = payload[args.key]
    if not isinstance(payload, dict) or not payload or not all(torch.is_tensor(v) for v in payload.values()):
        parser.error("input must be a non-empty tensor mapping; use a model-specific converter for nested checkpoints")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_file({str(k): v.contiguous() for k, v in payload.items()}, str(args.output))
    print(f"wrote tensors={len(payload)} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
