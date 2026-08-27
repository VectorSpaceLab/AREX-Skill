#!/usr/bin/env python3
"""Tiny cross-cutting smoke for x-transformers model APIs.

The script stays CPU-friendly by default. It exercises a handful of representative
core and wrapper APIs with tiny tensors and prints shapes rather than training
quality metrics.
"""

from __future__ import annotations

import argparse
import random
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run tiny x-transformers model smoke checks.")
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="auto", help="runtime device (default: auto)")
    parser.add_argument("--threads", type=int, default=1, help="CPU torch thread cap when positive (default: 1)")
    parser.add_argument("--seed", type=int, default=7, help="random seed (default: 7)")
    parser.add_argument("--include-vision", action="store_true", default=True, help="run the tiny vision wrapper smoke (default: on)")
    parser.add_argument("--no-vision", action="store_false", dest="include_vision", help="skip the vision wrapper smoke")
    parser.add_argument("--include-xval", action="store_true", default=True, help="run the tiny xVal smoke (default: on)")
    parser.add_argument("--no-xval", action="store_false", dest="include_xval", help="skip the xVal smoke")
    return parser


def choose_device(torch: Any, requested: str):
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise SystemExit("--device cuda requested but CUDA is not available")
        return torch.device("cuda")
    if requested == "auto" and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def smoke_token_workflows(torch: Any, device: Any) -> None:
    from x_transformers import AutoregressiveWrapper, Decoder, TransformerWrapper, XTransformer

    token_model = TransformerWrapper(
        num_tokens=32,
        max_seq_len=8,
        attn_layers=Decoder(dim=32, depth=1, heads=2),
    ).to(device)

    ar = AutoregressiveWrapper(token_model)
    x = torch.randint(0, 32, (2, 8), dtype=torch.long, device=device)
    loss = ar(x)
    if not torch.isfinite(loss):
        raise SystemExit(f"non-finite autoregressive loss: {loss.item()}")
    print(f"AutoregressiveWrapper loss={float(loss.detach().cpu()):.4f}")

    prompt = torch.randint(0, 32, (1, 4), dtype=torch.long, device=device)
    generated = ar.generate(prompt, 4)
    print(f"AutoregressiveWrapper.generate shape={tuple(generated.shape)}")

    seq2seq = XTransformer(
        dim=32,
        tie_token_emb=True,
        return_tgt_loss=True,
        enc_num_tokens=32,
        enc_depth=1,
        enc_heads=2,
        enc_max_seq_len=8,
        dec_num_tokens=32,
        dec_depth=1,
        dec_heads=2,
        dec_max_seq_len=8,
    ).to(device)

    src = torch.randint(0, 32, (2, 8), dtype=torch.long, device=device)
    tgt = torch.randint(0, 32, (2, 8), dtype=torch.long, device=device)
    src_mask = torch.ones((2, 8), dtype=torch.bool, device=device)
    seq2seq_loss = seq2seq(src, tgt, mask=src_mask)
    print(f"XTransformer loss={float(seq2seq_loss.detach().cpu()):.4f}")


def smoke_continuous_workflows(torch: Any, device: Any) -> None:
    from x_transformers import ContinuousAutoregressiveWrapper, ContinuousTransformerWrapper, Decoder

    continuous = ContinuousTransformerWrapper(
        dim_in=4,
        dim_out=4,
        max_seq_len=4,
        attn_layers=Decoder(dim=16, depth=1, heads=2),
    ).to(device)

    car = ContinuousAutoregressiveWrapper(continuous)
    x = torch.randn((2, 4, 4), device=device)
    mask = torch.ones((2, 4), dtype=torch.bool, device=device)
    loss = car(x, mask=mask)
    if not torch.isfinite(loss):
        raise SystemExit(f"non-finite continuous loss: {loss.item()}")
    print(f"ContinuousAutoregressiveWrapper loss={float(loss.detach().cpu()):.4f}")

    start = torch.randn((1, 4), device=device)
    generated = car.generate(start, 2)
    print(f"ContinuousAutoregressiveWrapper.generate shape={tuple(generated.shape)}")


def smoke_vision_workflows(torch: Any, device: Any) -> None:
    from x_transformers import Encoder, ViTransformerWrapper

    vision = ViTransformerWrapper(
        image_size=8,
        patch_size=4,
        num_classes=4,
        attn_layers=Encoder(dim=16, depth=1, heads=2),
    ).to(device)

    img = torch.randn((1, 3, 8, 8), device=device)
    logits = vision(img)
    print(f"ViTransformerWrapper logits_shape={tuple(logits.shape)}")


def smoke_xval_workflows(torch: Any, device: Any) -> None:
    from x_transformers import Decoder, XValAutoregressiveWrapper, XValTransformerWrapper

    xval = XValTransformerWrapper(
        num_tokens=4,
        numerical_token_id=3,
        max_seq_len=4,
        attn_layers=Decoder(dim=16, depth=1, heads=2),
    ).to(device)
    wrapper = XValAutoregressiveWrapper(xval)

    ids = torch.randint(0, 4, (2, 4), dtype=torch.long, device=device)
    nums = torch.randn((2, 4), device=device)
    loss = wrapper(ids, nums)
    if not torch.isfinite(loss):
        raise SystemExit(f"non-finite xVal loss: {loss.item()}")
    print(f"XValAutoregressiveWrapper loss={float(loss.detach().cpu()):.4f}")

    start_ids = torch.randint(0, 4, (1, 2), dtype=torch.long, device=device)
    start_nums = torch.randn((1, 2), device=device)
    generated = wrapper.generate(start_ids, start_nums, 2)
    print(
        "XValAutoregressiveWrapper.generate shapes="
        f" tokens={tuple(generated.sampled_token_ids.shape)}"
        f" numbers={tuple(generated.sampled_numbers.shape)}"
        f" mask={tuple(generated.is_number_mask.shape)}"
    )


def run(args: argparse.Namespace) -> None:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - manual smoke only
        raise SystemExit(f"Could not import torch: {exc}") from exc

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if args.threads > 0:
        torch.set_num_threads(args.threads)

    device = choose_device(torch, args.device)
    print(f"device={device}")

    smoke_token_workflows(torch, device)
    smoke_continuous_workflows(torch, device)

    if args.include_vision:
        smoke_vision_workflows(torch, device)

    if args.include_xval:
        smoke_xval_workflows(torch, device)

    print("smoke_models: ok")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
