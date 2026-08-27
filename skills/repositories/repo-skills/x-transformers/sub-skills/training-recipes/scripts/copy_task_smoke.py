#!/usr/bin/env python3
"""Tiny synthetic copy-task smoke for x-transformers.

This helper is intentionally much smaller than the repository's native
``train_copy.py`` example. It checks that a minimal XTransformer can run a
forward/backward optimizer step and a short generation call on CPU by default.
It is not a convergence benchmark.
"""

from __future__ import annotations

import argparse
import random
from typing import Any


def bounded_steps(value: str) -> int:
    steps = int(value)
    if not 1 <= steps <= 3:
        raise argparse.ArgumentTypeError("steps must be between 1 and 3 for this smoke")
    return steps


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny CPU-friendly XTransformer copy-task smoke. "
            "The check trains for 1-3 steps and then generates a short sample."
        )
    )
    parser.add_argument("--steps", type=bounded_steps, default=2, help="training steps, bounded to 1..3 (default: 2)")
    parser.add_argument("--batch-size", type=int, default=2, help="synthetic batch size (default: 2)")
    parser.add_argument("--enc-seq-len", type=int, default=8, help="source sequence length (default: 8)")
    parser.add_argument("--num-tokens", type=int, default=18, help="vocabulary size including 0/1 sentinels (default: 18)")
    parser.add_argument("--dim", type=int, default=32, help="model dimension (default: 32)")
    parser.add_argument("--heads", type=int, default=2, help="attention heads (default: 2)")
    parser.add_argument("--depth", type=int, default=1, help="encoder and decoder depth (default: 1)")
    parser.add_argument("--lr", type=float, default=3e-4, help="Adam learning rate (default: 3e-4)")
    parser.add_argument("--seed", type=int, default=7, help="random seed (default: 7)")
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="cpu",
        help="runtime device; cpu is the safe default (default: cpu)",
    )
    parser.add_argument("--threads", type=int, default=1, help="CPU torch thread cap when positive (default: 1)")
    return parser


def make_batch(torch: Any, *, batch_size: int, enc_seq_len: int, num_tokens: int, device: Any):
    # Token 1 is the decoder start token. Random source tokens begin at 2.
    src = torch.randint(2, num_tokens, (batch_size, enc_seq_len), dtype=torch.long, device=device)
    prefix = torch.ones((batch_size, 1), dtype=torch.long, device=device)
    tgt = torch.cat((prefix, src), dim=1)
    src_mask = torch.ones((batch_size, enc_seq_len), dtype=torch.bool, device=device)
    return src, tgt, src_mask


def run(args: argparse.Namespace) -> None:
    try:
        import torch
        from x_transformers import XTransformer
    except Exception as exc:  # pragma: no cover - exercised manually by users with broken envs
        raise SystemExit(f"Could not import torch and x_transformers: {exc}") from exc

    if args.batch_size < 1:
        raise SystemExit("--batch-size must be positive")
    if args.enc_seq_len < 2:
        raise SystemExit("--enc-seq-len must be at least 2")
    if args.num_tokens < 4:
        raise SystemExit("--num-tokens must be at least 4")
    if args.dim % args.heads != 0:
        raise SystemExit("--dim must be divisible by --heads")
    if args.threads > 0:
        torch.set_num_threads(args.threads)

    random.seed(args.seed)
    torch.manual_seed(args.seed)

    if args.device == "cuda":
        if not torch.cuda.is_available():
            raise SystemExit("--device cuda requested but CUDA is not available")
        device = torch.device("cuda")
    elif args.device == "auto" and torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    model = XTransformer(
        dim=args.dim,
        tie_token_emb=True,
        return_tgt_loss=True,
        enc_num_tokens=args.num_tokens,
        enc_depth=args.depth,
        enc_heads=args.heads,
        enc_max_seq_len=args.enc_seq_len,
        dec_num_tokens=args.num_tokens,
        dec_depth=args.depth,
        dec_heads=args.heads,
        dec_max_seq_len=args.enc_seq_len + 1,
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    losses: list[float] = []
    for step in range(1, args.steps + 1):
        model.train()
        src, tgt, src_mask = make_batch(
            torch,
            batch_size=args.batch_size,
            enc_seq_len=args.enc_seq_len,
            num_tokens=args.num_tokens,
            device=device,
        )
        loss = model(src, tgt, mask=src_mask)
        if not torch.isfinite(loss):
            raise SystemExit(f"non-finite loss at step {step}: {loss.item()}")
        loss.backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        losses.append(float(loss.detach().cpu()))
        print(f"step {step}: loss={losses[-1]:.4f}")

    model.eval()
    src, _, src_mask = make_batch(
        torch,
        batch_size=1,
        enc_seq_len=args.enc_seq_len,
        num_tokens=args.num_tokens,
        device=device,
    )
    start_tokens = torch.ones((1, 1), dtype=torch.long, device=device)

    with torch.no_grad():
        sample = model.generate(src, start_tokens, args.enc_seq_len, mask=src_mask)

    if sample.shape != src.shape:
        raise SystemExit(f"unexpected generated shape {tuple(sample.shape)}; expected {tuple(src.shape)}")

    mismatches = int((sample != src).sum().detach().cpu())
    print(f"device={device.type} generated_shape={tuple(sample.shape)} mismatches={mismatches}/{src.numel()}")
    print("input:", src[0].detach().cpu().tolist())
    print("sample:", sample[0].detach().cpu().tolist())
    print("copy_task_smoke: ok")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
