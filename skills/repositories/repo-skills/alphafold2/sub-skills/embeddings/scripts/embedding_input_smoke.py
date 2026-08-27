#!/usr/bin/env python3
"""Run a bounded, no-network synthetic precomputed-embedding smoke.

The fixture is ``embedds`` with shape ``(B, M, N, 1280)``. The checked
0.4.32 core exposes an ``embedd_project`` layer for this width, but its direct
``embedds`` forward branch is shadowed by MSA initialization. This helper
therefore checks that projection explicitly and then feeds the projected
sequence/MSA representations through the ordinary core contract. It never
constructs ESM, MSA Transformer, or ProtTrans wrappers and never downloads
model assets. The wrappers themselves remain network/cache-dependent.
"""

from __future__ import annotations

import argparse
import sys

EMBEDDING_WIDTH = 1280
MODEL_DIM = 32
BATCH = 1
MSA_ROWS = 1
SEQ_LEN = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a no-network synthetic (B,M,N,1280) embedding projection "
            "and tiny Alphafold2 core smoke. Pretrained wrappers require "
            "separately staged external model assets."
        )
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="torch device such as cpu or cuda (default: cpu); no implicit fallback",
    )
    return parser.parse_args()


def import_runtime():
    try:
        import torch
        from alphafold2_pytorch import Alphafold2
    except Exception as exc:
        print(
            "embedding_input_smoke: install a compatible alphafold2-pytorch "
            "environment before running this no-network check; it does not "
            "install packages or download model assets. "
            f"Original error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return torch, Alphafold2


def main() -> int:
    args = parse_args()
    torch, Alphafold2 = import_runtime()
    try:
        device = torch.device(args.device)
    except (RuntimeError, TypeError) as exc:
        print(f"invalid --device {args.device!r}: {exc}", file=sys.stderr)
        return 2

    if device.type == "cuda" and not torch.cuda.is_available():
        print("CUDA was requested but is not available; retry with --device cpu", file=sys.stderr)
        return 2

    torch.manual_seed(0)
    try:
        model = Alphafold2(
            dim=MODEL_DIM,
            depth=1,
            heads=1,
            dim_head=8,
            max_seq_len=SEQ_LEN,
            extra_msa_evoformer_layers=1,
            num_embedds=EMBEDDING_WIDTH,
        ).to(device)
        model.eval()

        seq = torch.randint(0, 21, (BATCH, SEQ_LEN), device=device)
        msa = torch.randint(0, 21, (BATCH, MSA_ROWS, SEQ_LEN), device=device)
        mask = torch.ones((BATCH, SEQ_LEN), dtype=torch.bool, device=device)
        msa_mask = torch.ones((BATCH, MSA_ROWS, SEQ_LEN), dtype=torch.bool, device=device)
        embedds = torch.randn(
            (BATCH, MSA_ROWS, SEQ_LEN, EMBEDDING_WIDTH), device=device
        )

        with torch.no_grad():
            projected = model.embedd_project(embedds)
        expected_projection = (BATCH, MSA_ROWS, SEQ_LEN, MODEL_DIM)
        assert tuple(projected.shape) == expected_projection, (
            "unexpected projected shape: "
            f"{tuple(projected.shape)} != {expected_projection}"
        )

        # The source's direct ``embedds`` branch is unreachable in an ordinary
        # 0.4.32 call: an explicit msa selects the token-MSA branch. Convert
        # the checked projection into the explicit seq_embed/msa_embed
        # interface so this smoke exercises the safe local representation path.
        seq_embed = projected[:, 0]
        msa_embed = projected
        with torch.no_grad():
            result = model(
                seq,
                msa=msa,
                mask=mask,
                msa_mask=msa_mask,
                seq_embed=seq_embed,
                msa_embed=msa_embed,
                embedds=embedds,
            )

        assert hasattr(result, "distance"), "core result must expose .distance"
        expected_distance = (BATCH, SEQ_LEN, SEQ_LEN, 37)
        assert tuple(result.distance.shape) == expected_distance, (
            "unexpected distance shape: "
            f"{tuple(result.distance.shape)} != {expected_distance}"
        )
    except (AssertionError, RuntimeError) as exc:
        print(
            "embedding_input_smoke: local projection/core check failed. "
            "Retry with --device cpu and tiny default dimensions. "
            f"Original error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    print(f"PASS synthetic embedds projection: {tuple(embedds.shape)} -> {tuple(projected.shape)}")
    print(f"PASS local projected-representation core distance: {tuple(result.distance.shape)}")
    print(
        "NOTE pretrained ESM/MSA/ProtTrans wrappers are network/cache-dependent; "
        "this smoke constructs none and does not claim direct embedds consumption "
        "by the unmodified 0.4.32 forward path."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
