#!/usr/bin/env python3
"""Run a tiny Transformer forward/loss smoke without data files or training.

The script searches upward from its own location for a repo root containing
src/models/transformer.py, adds that root to sys.path, instantiates a small model,
and runs one forward pass with non-contiguous next-token targets. It performs no
network access, checkpoint writes, or optimizer step.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _add_repo_root_to_path() -> None:
    """Allow the smoke script to run from the sub-skill directory or repo root."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "src" / "models" / "transformer.py").exists():
            sys.path.insert(0, str(parent))
            return


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Instantiate a tiny Transformer and run one forward/loss smoke.")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="Device for the smoke forward pass.")
    parser.add_argument("--batch-size", type=int, default=2, help="Tiny batch size.")
    parser.add_argument("--seq-len", type=int, default=8, help="Input sequence length for the smoke batch.")
    parser.add_argument("--context-length", type=int, default=16, help="Model context length; must be >= --seq-len.")
    parser.add_argument("--vocab-size", type=int, default=64, help="Tiny vocabulary size.")
    parser.add_argument("--n-embed", type=int, default=32, help="Tiny embedding width.")
    parser.add_argument("--n-head", type=int, default=4, help="Tiny attention head count.")
    parser.add_argument("--n-blocks", type=int, default=2, help="Tiny Transformer block count.")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for deterministic smoke tensors.")
    parser.add_argument("--generate", type=int, default=0, help="Optionally sample this many raw tokens after the forward smoke.")
    return parser.parse_args(argv)


def _validate(args: argparse.Namespace) -> None:
    if args.batch_size < 1:
        raise ValueError("--batch-size must be >= 1")
    if args.seq_len < 1:
        raise ValueError("--seq-len must be >= 1")
    if args.context_length < args.seq_len:
        raise ValueError("--context-length must be >= --seq-len")
    if args.vocab_size < 2:
        raise ValueError("--vocab-size must be >= 2")
    if args.n_embed < 1:
        raise ValueError("--n-embed must be >= 1")
    if args.n_head < 1:
        raise ValueError("--n-head must be >= 1")
    if args.n_embed % args.n_head != 0:
        raise ValueError("--n-embed must be divisible by --n-head")
    if args.n_blocks < 1:
        raise ValueError("--n-blocks must be >= 1")
    if args.generate < 0:
        raise ValueError("--generate must be >= 0")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        _validate(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    _add_repo_root_to_path()
    try:
        import torch
        from src.models.transformer import Transformer
    except Exception as exc:  # noqa: BLE001 - present actionable import failure
        print("error: could not import torch and src.models.transformer. Run from an installed repo environment.", file=sys.stderr)
        print(f"detail: {exc}", file=sys.stderr)
        return 2

    if args.device == "cuda" and not torch.cuda.is_available():
        print("error: --device cuda requested but CUDA is not available", file=sys.stderr)
        return 2

    torch.manual_seed(args.seed)
    device = torch.device(args.device)
    model = Transformer(
        n_head=args.n_head,
        n_embed=args.n_embed,
        context_length=args.context_length,
        vocab_size=args.vocab_size,
        N_BLOCKS=args.n_blocks,
    ).to(device)
    model.eval()

    # Slice a (B, T+1) tensor so targets are non-contiguous, matching the training loader path.
    tokens = torch.randint(0, args.vocab_size, (args.batch_size, args.seq_len + 1), device=device)
    idx = tokens[:, :-1]
    targets = tokens[:, 1:]

    with torch.no_grad():
        logits, loss = model(idx, targets)
        hidden = model.forward_hidden(idx)
        generated_shape = None
        if args.generate:
            generated = model.generate(idx[:, :1], max_new_tokens=args.generate)
            generated_shape = tuple(generated.shape)

    params = sum(p.numel() for p in model.parameters())
    print(f"device={device.type}")
    print(f"parameters={params:,}")
    print(f"idx_shape={tuple(idx.shape)} targets_shape={tuple(targets.shape)}")
    print(f"logits_shape={tuple(logits.shape)} hidden_shape={tuple(hidden.shape)}")
    print(f"loss={float(loss.item()):.6f}")
    print(f"targets_contiguous={targets.is_contiguous()} reshape_loss_path=ok")
    if generated_shape is not None:
        print(f"generated_shape={generated_shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
