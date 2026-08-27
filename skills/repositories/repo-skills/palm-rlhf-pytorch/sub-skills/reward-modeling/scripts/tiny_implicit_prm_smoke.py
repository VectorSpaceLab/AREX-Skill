#!/usr/bin/env python3
"""Tiny ImplicitPRM smoke test for palm_rlhf_pytorch.

This helper is safe to run from any working directory. It builds a tiny PaLM
backbone, wraps it in ImplicitPRM, and checks both the training loss path and
inference reward shape.
"""
from __future__ import annotations

import argparse


def choose_device(requested: str) -> str:
    if requested != "auto":
        return requested
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny ImplicitPRM smoke check.")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--num-tokens", type=int, default=32)
    parser.add_argument("--dim", type=int, default=16)
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--heads", type=int, default=2)
    parser.add_argument("--dim-head", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--seq-len", type=int, default=8)
    args = parser.parse_args()

    import torch
    from palm_rlhf_pytorch import PaLM, ImplicitPRM

    device = torch.device(choose_device(args.device))
    torch.manual_seed(0)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(0)

    model = PaLM(
        num_tokens=args.num_tokens,
        dim=args.dim,
        depth=args.depth,
        heads=args.heads,
        dim_head=args.dim_head,
        flash_attn=False,
    ).to(device)
    ref_model = PaLM(
        num_tokens=args.num_tokens,
        dim=args.dim,
        depth=args.depth,
        heads=args.heads,
        dim_head=args.dim_head,
        flash_attn=False,
    ).to(device)
    prm = ImplicitPRM(model, ref_model=ref_model, beta=0.1).to(device)

    seq = torch.randint(0, args.num_tokens, (args.batch_size, args.seq_len), device=device)
    labels = torch.randint(0, 2, (args.batch_size,), device=device)

    loss = prm(seq, labels)
    loss.backward()
    rewards = prm(seq)
    assert rewards.shape == (args.batch_size, args.seq_len - 1), rewards.shape
    print(f"loss={float(loss.detach()):.6f} rewards_shape={tuple(rewards.shape)}")
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
