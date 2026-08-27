#!/usr/bin/env python3
"""Tiny reward-model smoke test for palm_rlhf_pytorch.

This helper is safe to run from any working directory. It builds tiny PaLM and
RewardModel instances, checks scalar and binned reward paths, and verifies that
prompt-mask / prompt-length handling behaves as documented.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass


def choose_device(requested: str) -> str:
    if requested != "auto":
        return requested
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


def make_tokens(torch, device, batch: int, seq_len: int, num_tokens: int):
    return torch.randint(0, num_tokens, (batch, seq_len), device=device)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny RewardModel smoke check.")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--num-tokens", type=int, default=32)
    parser.add_argument("--dim", type=int, default=16)
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--heads", type=int, default=2)
    parser.add_argument("--dim-head", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--seq-len", type=int, default=8)
    parser.add_argument("--prompt-len", type=int, default=4)
    parser.add_argument("--num-bins", type=int, default=3)
    parser.add_argument("--check-lora", action="store_true")
    args = parser.parse_args()

    import torch
    from palm_rlhf_pytorch import PaLM, RewardModel

    device = torch.device(choose_device(args.device))
    torch.manual_seed(0)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(0)

    palm = PaLM(
        num_tokens=args.num_tokens,
        dim=args.dim,
        depth=args.depth,
        heads=args.heads,
        dim_head=args.dim_head,
        flash_attn=False,
    ).to(device)

    seq = make_tokens(torch, device, args.batch_size, args.seq_len, args.num_tokens)
    prompt_lengths = torch.full((args.batch_size,), args.prompt_len, dtype=torch.long, device=device)
    prompt_mask = torch.arange(args.seq_len, device=device).unsqueeze(0) < prompt_lengths.unsqueeze(1)
    full_mask = torch.ones_like(seq, dtype=torch.bool)

    scalar_reward = RewardModel(palm, num_binned_output=0, dropout=0.0, use_lora=True, reward_lora_scope="reward_smoke")
    scalar_reward = scalar_reward.to(device)
    scalar_labels = torch.linspace(0.0, 1.0, steps=args.batch_size, device=device)
    scalar_loss = scalar_reward(seq, prompt_lengths=prompt_lengths, mask=full_mask, labels=scalar_labels)
    scalar_loss.backward()
    scalar_scores = scalar_reward(seq, prompt_mask=prompt_mask, mask=full_mask)
    assert scalar_scores.shape == (args.batch_size,), scalar_scores.shape
    print(f"scalar_loss={float(scalar_loss.detach()):.6f} scalar_scores_shape={tuple(scalar_scores.shape)}")

    binned_logits_reward = RewardModel(
        palm,
        num_binned_output=args.num_bins,
        dropout=0.0,
        use_lora=False,
        sample_from_bins=False,
    ).to(device)
    binned_labels = torch.randint(0, args.num_bins, (args.batch_size,), device=device)
    binned_loss = binned_logits_reward(seq, prompt_mask=prompt_mask, mask=full_mask, labels=binned_labels)
    binned_loss.backward()
    logits = binned_logits_reward(seq, prompt_mask=prompt_mask, mask=full_mask)
    assert logits.shape == (args.batch_size, args.num_bins), logits.shape
    print(f"binned_loss={float(binned_loss.detach()):.6f} logits_shape={tuple(logits.shape)}")

    sampled_reward = RewardModel(palm, num_binned_output=args.num_bins, dropout=0.0, use_lora=False).to(device)
    sampled = sampled_reward(seq, prompt_mask=prompt_mask, mask=full_mask)
    assert sampled.shape == (args.batch_size,), sampled.shape
    print(f"sampled_bins_shape={tuple(sampled.shape)}")

    if args.check_lora:
        extra = RewardModel(palm, num_binned_output=0, dropout=0.0, use_lora=True, reward_lora_scope="reward_extra").to(device)
        params = list(extra.finetune_parameters())
        assert params, "expected reward finetune parameters"
        print(f"reward_lora_params={len(params)}")

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
