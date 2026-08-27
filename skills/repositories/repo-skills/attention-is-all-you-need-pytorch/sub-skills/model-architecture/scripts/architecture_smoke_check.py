#!/usr/bin/env python3
"""Architecture smoke checks for attention-is-all-you-need-pytorch.

The script is deterministic, CPU-safe by default, and can be run from any
current directory. It imports repository source only after the caller provides an
explicit --repo-root.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run tiny Transformer, mask, attention-broadcast, and ScheduledOptim "
            "smoke checks against an attention-is-all-you-need-pytorch checkout."
        )
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Path to a checkout containing transformer/Models.py. Added to sys.path for imports.",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="cpu",
        help="Device for tensor/model checks. Default is cpu; auto uses cuda only when available.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Torch random seed used before constructing smoke modules.",
    )
    parser.add_argument(
        "--skip-negative-checks",
        action="store_true",
        help="Skip expected-failure checks for invalid constructor settings.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary instead of human-readable status lines.",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    raise AssertionError(message)


def expect_shape(tensor, expected, label: str) -> None:
    actual = tuple(tensor.shape)
    if actual != tuple(expected):
        fail(f"{label} shape mismatch: expected {tuple(expected)}, got {actual}")


def expect(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def choose_device(torch, requested: str):
    if requested == "cpu":
        return torch.device("cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            fail("--device cuda requested, but torch.cuda.is_available() is false")
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def tensor_to_bool_list(tensor):
    return tensor.detach().cpu().bool().tolist()


def run_checks(args: argparse.Namespace) -> dict:
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not (repo_root / "transformer" / "Models.py").is_file():
        fail("--repo-root must contain transformer/Models.py")

    sys.path.insert(0, str(repo_root))

    import torch
    from transformer.Models import Transformer, get_pad_mask, get_subsequent_mask
    from transformer.SubLayers import MultiHeadAttention
    from transformer.Optim import ScheduledOptim

    torch.manual_seed(args.seed)
    device = choose_device(torch, args.device)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)

    src_pad_idx = 0
    trg_pad_idx = 0
    n_src_vocab = 17
    n_trg_vocab = 19

    model = Transformer(
        n_src_vocab=n_src_vocab,
        n_trg_vocab=n_trg_vocab,
        src_pad_idx=src_pad_idx,
        trg_pad_idx=trg_pad_idx,
        d_word_vec=16,
        d_model=16,
        d_inner=32,
        n_layers=2,
        n_head=2,
        d_k=8,
        d_v=8,
        dropout=0.0,
        n_position=16,
        trg_emb_prj_weight_sharing=False,
        emb_src_trg_weight_sharing=False,
        scale_emb_or_prj="none",
    ).to(device)
    model.eval()

    src_seq = torch.tensor([[2, 5, 0, 0], [3, 4, 6, 0]], dtype=torch.long, device=device)
    trg_seq = torch.tensor([[1, 7, 8], [1, 9, 0]], dtype=torch.long, device=device)

    src_mask = get_pad_mask(src_seq, src_pad_idx)
    subsequent_mask = get_subsequent_mask(trg_seq)
    trg_mask = get_pad_mask(trg_seq, trg_pad_idx) & subsequent_mask

    expect_shape(src_mask, (2, 1, 4), "source pad mask")
    expect_shape(subsequent_mask, (1, 3, 3), "target subsequent mask")
    expect_shape(trg_mask, (2, 3, 3), "combined target mask")
    expect(src_mask.dtype == torch.bool, "source pad mask should be boolean")
    expect(subsequent_mask.dtype == torch.bool, "subsequent mask should be boolean")
    expect(src_mask.device == device, "source mask is not on the requested device")
    expect(subsequent_mask.device == device, "subsequent mask is not on the requested device")

    expected_src_mask = [[[True, True, False, False]], [[True, True, True, False]]]
    expected_subsequent = [[[True, False, False], [True, True, False], [True, True, True]]]
    expected_trg_mask = [
        [[True, False, False], [True, True, False], [True, True, True]],
        [[True, False, False], [True, True, False], [True, True, False]],
    ]
    expect(tensor_to_bool_list(src_mask) == expected_src_mask, "source pad mask values changed")
    expect(tensor_to_bool_list(subsequent_mask) == expected_subsequent, "subsequent mask values changed")
    expect(tensor_to_bool_list(trg_mask) == expected_trg_mask, "combined target mask values changed")

    with torch.no_grad():
        flat_logits = model(src_seq, trg_seq)
    expect_shape(flat_logits, (src_seq.size(0) * trg_seq.size(1), n_trg_vocab), "flattened logits")
    expect(torch.isfinite(flat_logits).all().item(), "Transformer logits contain non-finite values")
    restored = flat_logits.view(src_seq.size(0), trg_seq.size(1), n_trg_vocab)
    expect_shape(restored, (2, 3, n_trg_vocab), "restored logits")

    with torch.no_grad():
        enc_output, enc_attns = model.encoder(src_seq, src_mask, return_attns=True)
        dec_output, dec_slf_attns, dec_enc_attns = model.decoder(
            trg_seq, trg_mask, enc_output, src_mask, return_attns=True
        )
    expect_shape(enc_output, (2, 4, 16), "encoder output")
    expect_shape(dec_output, (2, 3, 16), "decoder output")
    expect(len(enc_attns) == 2, "expected one encoder attention tensor per layer")
    expect(len(dec_slf_attns) == 2, "expected one decoder self-attention tensor per layer")
    expect(len(dec_enc_attns) == 2, "expected one decoder-encoder attention tensor per layer")
    expect_shape(enc_attns[0], (2, 2, 4, 4), "encoder attention")
    expect_shape(dec_slf_attns[0], (2, 2, 3, 3), "decoder self attention")
    expect_shape(dec_enc_attns[0], (2, 2, 3, 4), "decoder-encoder attention")

    mha = MultiHeadAttention(n_head=2, d_model=16, d_k=8, d_v=8, dropout=0.0).to(device)
    mha.eval()
    q = torch.randn(2, 3, 16, device=device)
    k = torch.randn(2, 4, 16, device=device)
    v = torch.randn(2, 4, 16, device=device)
    keep_mask = torch.tensor([[[1, 1, 0, 0]], [[1, 1, 1, 0]]], dtype=torch.bool, device=device)
    with torch.no_grad():
        mha_output, mha_attn = mha(q, k, v, mask=keep_mask)
    expect_shape(mha_output, (2, 3, 16), "multi-head attention output")
    expect_shape(mha_attn, (2, 2, 3, 4), "multi-head attention weights")
    masked_tail = mha_attn[0, :, :, 2:]
    expect(torch.allclose(masked_tail, torch.zeros_like(masked_tail), atol=1e-6), "masked keys received attention")

    probe_linear = torch.nn.Linear(2, 2).to(device)
    optimizer = torch.optim.Adam(probe_linear.parameters(), lr=0.0, betas=(0.9, 0.98), eps=1e-9)
    scheduled = ScheduledOptim(optimizer, lr_mul=1.0, d_model=16, n_warmup_steps=2)
    learning_rates = []
    for _ in range(3):
        scheduled.zero_grad()
        scheduled.step_and_update_lr()
        learning_rates.append(optimizer.param_groups[0]["lr"])
    expect(scheduled.n_steps == 3, "ScheduledOptim did not advance three steps")
    expect(learning_rates[1] > learning_rates[0], "ScheduledOptim warmup did not increase lr")
    expect(learning_rates[2] < learning_rates[1], "ScheduledOptim did not decay after warmup")
    expected_step2 = (16 ** -0.5) * min(2 ** -0.5, 2 * (2 ** -1.5))
    expect(math.isclose(learning_rates[1], expected_step2, rel_tol=1e-12), "ScheduledOptim step-2 lr formula changed")

    negative_checks = []
    if not args.skip_negative_checks:
        try:
            Transformer(
                n_src_vocab=8,
                n_trg_vocab=8,
                src_pad_idx=0,
                trg_pad_idx=0,
                d_word_vec=8,
                d_model=8,
                d_inner=16,
                n_layers=1,
                n_head=1,
                d_k=8,
                d_v=8,
                dropout=0.0,
                n_position=8,
                scale_emb_or_prj="bad",
            )
        except AssertionError:
            negative_checks.append("invalid scale_emb_or_prj rejected")
        else:
            fail("invalid scale_emb_or_prj was accepted")

        try:
            Transformer(
                n_src_vocab=8,
                n_trg_vocab=8,
                src_pad_idx=0,
                trg_pad_idx=0,
                d_word_vec=10,
                d_model=8,
                d_inner=16,
                n_layers=1,
                n_head=1,
                d_k=8,
                d_v=8,
                dropout=0.0,
                n_position=8,
                trg_emb_prj_weight_sharing=False,
                emb_src_trg_weight_sharing=False,
                scale_emb_or_prj="none",
            )
        except AssertionError:
            negative_checks.append("d_model/d_word_vec mismatch rejected")
        else:
            fail("d_model != d_word_vec was accepted")

        shared = Transformer(
            n_src_vocab=23,
            n_trg_vocab=5,
            src_pad_idx=0,
            trg_pad_idx=0,
            d_word_vec=8,
            d_model=8,
            d_inner=16,
            n_layers=1,
            n_head=1,
            d_k=8,
            d_v=8,
            dropout=0.0,
            n_position=8,
            trg_emb_prj_weight_sharing=False,
            emb_src_trg_weight_sharing=True,
            scale_emb_or_prj="none",
        )
        expect(
            shared.encoder.src_word_emb.weight is shared.decoder.trg_word_emb.weight,
            "source-target embedding sharing did not tie weights",
        )
        expect(
            shared.encoder.src_word_emb.weight.shape[0] == 5,
            "shared source embedding did not take target vocabulary size",
        )
        negative_checks.append("incompatible source-target sharing hazard exposed")

    return {
        "status": "ok",
        "device": str(device),
        "seed": args.seed,
        "checks": [
            "tiny Transformer forward",
            "pad and subsequent masks",
            "encoder/decoder attention return shapes",
            "MultiHeadAttention mask broadcasting",
            "ScheduledOptim warmup/decay",
        ],
        "negative_checks": negative_checks,
        "flat_logits_shape": list(flat_logits.shape),
        "learning_rates": learning_rates,
    }


def main() -> int:
    args = parse_args()
    try:
        result = run_checks(args)
    except Exception as exc:  # CLI should surface any failure clearly.
        if args.json:
            print(json.dumps({"status": "failed", "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"architecture smoke check FAILED: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("architecture smoke check OK")
        print(f"device: {result['device']}")
        print(f"flat logits shape: {result['flat_logits_shape']}")
        print(f"learning rates: {[round(x, 12) for x in result['learning_rates']]}")
        if result["negative_checks"]:
            print(f"negative checks: {', '.join(result['negative_checks'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
