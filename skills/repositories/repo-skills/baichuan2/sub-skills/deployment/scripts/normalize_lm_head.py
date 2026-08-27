#!/usr/bin/env python3
"""Normalize Baichuan2 lm_head.weight in a copied checkpoint directory.

This helper implements the documented Baichuan2-to-Baichuan1 optimization
migration step for a single-file pytorch_model.bin checkpoint. Use --dry-run
first, and only load checkpoints that you trust.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable


WEIGHT_LIKE_SUFFIXES = {".bin", ".safetensors", ".h5", ".msgpack", ".ckpt", ".pt", ".pth"}
COMMON_SIDECAR_SUFFIXES = {".json", ".model", ".py", ".txt", ".md"}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalize lm_head.weight in a Baichuan2 pytorch_model.bin checkpoint.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input-dir", required=True, type=Path, help="Directory containing pytorch_model.bin.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for the converted checkpoint.")
    parser.add_argument("--checkpoint-name", default="pytorch_model.bin", help="Checkpoint filename inside input/output directories.")
    parser.add_argument("--key", default="lm_head.weight", help="State-dict key to normalize.")
    parser.add_argument("--dim", type=int, default=1, help="Dimension used for L2 normalization.")
    parser.add_argument("--eps", type=float, default=1e-12, help="Epsilon passed to torch.nn.functional.normalize.")
    parser.add_argument("--map-location", default="cpu", help="map_location for torch.load.")
    parser.add_argument("--copy-sidecars", action=argparse.BooleanOptionalAction, default=True, help="Copy common non-weight config/tokenizer sidecar files.")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting an existing output checkpoint.")
    parser.add_argument("--validate-key", action="store_true", help="During dry-run, load the checkpoint and verify the target key.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions; only loads the checkpoint when --validate-key is set.")
    return parser


def _import_torch() -> Any:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - depends on host env
        raise SystemExit(f"Torch import failed: {exc}") from exc
    return torch


def _resolve_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    input_dir = args.input_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    input_checkpoint = input_dir / args.checkpoint_name
    output_checkpoint = output_dir / args.checkpoint_name

    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input directory does not exist or is not a directory: {input_dir}")
    if not input_checkpoint.exists() or not input_checkpoint.is_file():
        raise SystemExit(f"Checkpoint file not found: {input_checkpoint}")
    if input_checkpoint.resolve() == output_checkpoint.resolve():
        raise SystemExit("Refusing to overwrite the input checkpoint in place. Choose a separate --output-dir.")
    if output_checkpoint.exists() and not args.overwrite and not args.dry_run:
        raise SystemExit(f"Output checkpoint already exists; pass --overwrite to replace it: {output_checkpoint}")
    return input_checkpoint, output_checkpoint


def _load_checkpoint(torch: Any, checkpoint_path: Path, map_location: str) -> Any:
    # Explicit weights_only=False preserves compatibility with older checkpoint
    # dictionaries. Only use this helper for trusted local checkpoints.
    try:
        return torch.load(checkpoint_path, map_location=map_location, weights_only=False)
    except TypeError:
        return torch.load(checkpoint_path, map_location=map_location)


def _validate_checkpoint(torch: Any, checkpoint: Any, key: str, dim: int) -> Any:
    if not isinstance(checkpoint, dict):
        raise SystemExit("Checkpoint is not a dict/state-dict-like mapping.")
    if key not in checkpoint:
        sample = ", ".join(list(map(str, checkpoint.keys()))[:20])
        raise SystemExit(f"Key {key!r} not found in checkpoint. First keys: {sample}")
    tensor = checkpoint[key]
    if not hasattr(tensor, "dim"):
        raise SystemExit(f"Checkpoint value for {key!r} is not a tensor-like object.")
    if tensor.dim() <= dim or dim < -tensor.dim():
        raise SystemExit(f"Cannot normalize tensor with shape {tuple(tensor.shape)} along dim={dim}.")
    if not torch.is_floating_point(tensor):
        raise SystemExit(f"Tensor {key!r} must be floating point, got dtype={tensor.dtype}.")
    return tensor


def _iter_sidecars(input_dir: Path, checkpoint_name: str) -> Iterable[Path]:
    for child in input_dir.iterdir():
        if not child.is_file():
            continue
        if child.name == checkpoint_name:
            continue
        if child.suffix in WEIGHT_LIKE_SUFFIXES:
            continue
        if child.name.endswith(".index.json") and "model" in child.name:
            continue
        if child.suffix in COMMON_SIDECAR_SUFFIXES:
            yield child


def _copy_sidecars(input_dir: Path, output_dir: Path, checkpoint_name: str, overwrite: bool) -> list[str]:
    copied: list[str] = []
    for source in _iter_sidecars(input_dir, checkpoint_name):
        target = output_dir / source.name
        if target.exists() and not overwrite:
            continue
        shutil.copy2(source, target)
        copied.append(source.name)
    return copied


def _norm_stats(torch: Any, tensor: Any, dim: int) -> dict[str, float]:
    norms = tensor.norm(p=2, dim=dim).detach().float().cpu()
    return {
        "min": float(norms.min().item()),
        "mean": float(norms.mean().item()),
        "max": float(norms.max().item()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    input_checkpoint, output_checkpoint = _resolve_paths(args)

    print(f"input_checkpoint={input_checkpoint}")
    print(f"output_checkpoint={output_checkpoint}")
    print("warning=Only load trusted PyTorch .bin checkpoints; torch.load can execute pickle payloads.")

    if args.dry_run and not args.validate_key:
        print("dry_run=path checks passed; checkpoint was not loaded")
        return 0

    torch = _import_torch()
    checkpoint = _load_checkpoint(torch, input_checkpoint, args.map_location)
    tensor = _validate_checkpoint(torch, checkpoint, args.key, args.dim)
    before = _norm_stats(torch, tensor, args.dim)
    print(f"key={args.key}")
    print(f"shape={tuple(tensor.shape)} dtype={tensor.dtype} dim={args.dim}")
    print(f"norm_before={before}")

    if args.dry_run:
        print("dry_run=checkpoint key validation passed; no files written")
        return 0

    output_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint[args.key] = torch.nn.functional.normalize(tensor, p=2, dim=args.dim, eps=args.eps)
    after = _norm_stats(torch, checkpoint[args.key], args.dim)
    torch.save(checkpoint, output_checkpoint)
    print(f"wrote={output_checkpoint}")
    print(f"norm_after={after}")

    if args.copy_sidecars:
        copied = _copy_sidecars(input_checkpoint.parent, output_checkpoint.parent, args.checkpoint_name, args.overwrite)
        print(f"copied_sidecars={copied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
