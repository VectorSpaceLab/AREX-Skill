#!/usr/bin/env python3
"""Tiny PaLM smoke test for palm_rlhf_pytorch.

This helper is safe to run from any working directory. It builds a tiny PaLM,
checks loss, logits, embeddings, generation shape, and optional LoRA wiring.
"""
from __future__ import annotations

import argparse


def choose_device(requested: str) -> str:
    if requested != "auto":
        return requested
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny PaLM smoke check.")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--num-tokens", type=int, default=32)
    parser.add_argument("--dim", type=int, default=16)
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--heads", type=int, default=2)
    parser.add_argument("--dim-head", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--seq-len", type=int, default=6)
    parser.add_argument("--prompt-len", type=int, default=4)
    parser.add_argument("--flash-attn", action="store_true", help="Enable the PyTorch SDPA attention path.")
    parser.add_argument("--check-lora", action="store_true")
    args = parser.parse_args()

    import torch
    from palm_rlhf_pytorch import PaLM

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
        flash_attn=args.flash_attn,
    ).to(device)

    tokens = torch.randint(0, args.num_tokens, (args.batch_size, args.seq_len), device=device)
    loss = palm(tokens, return_loss=True)
    loss.backward()
    logits = palm(tokens)
    embeds = palm(tokens, return_only_embedding=True)
    logits2, embeds2 = palm(tokens, return_logits_with_embedding=True)

    assert logits.shape == (args.batch_size, args.seq_len, args.num_tokens), logits.shape
    assert embeds.shape == (args.batch_size, args.seq_len, args.dim), embeds.shape
    assert logits2.shape == logits.shape, logits2.shape
    assert embeds2.shape == embeds.shape, embeds2.shape

    prompt = torch.randint(0, args.num_tokens, (args.batch_size, args.prompt_len), device=device)
    suffix = palm.generate(args.prompt_len + 2, prompt=prompt, use_tqdm=False)
    full = palm.generate(
        args.prompt_len + 2,
        prompt=prompt,
        return_seq_without_prompt=False,
        use_tqdm=False,
    )
    assert suffix.shape == (args.batch_size, 2), suffix.shape
    assert full.shape == (args.batch_size, args.prompt_len + 2), full.shape

    if args.check_lora:
        palm.add_finetune_params("smoke", lora_r=4)
        finetune_params = list(palm.finetune_parameters("smoke"))
        assert finetune_params, "expected finetune parameters"
        lora_logits = palm(tokens, finetune_scope="smoke")
        assert lora_logits.shape == logits.shape, lora_logits.shape
        palm.remove_finetune_params("smoke")
        palm.add_finetune_params("merge", lora_r=4)
        palm.merge_finetune_params("merge")
        print(f"lora_params={len(finetune_params)}")

    print(f"loss={float(loss.detach()):.6f} logits_shape={tuple(logits.shape)} embeds_shape={tuple(embeds.shape)} suffix_shape={tuple(suffix.shape)}")
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
