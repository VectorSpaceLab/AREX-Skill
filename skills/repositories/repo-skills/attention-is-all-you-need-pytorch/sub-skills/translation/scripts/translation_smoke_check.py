#!/usr/bin/env python3
"""Run a tiny deterministic Translator beam-search smoke check.

This helper does not require a trained checkpoint or data pickle. It imports the
repository source only after the caller supplies --repo-root.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Exercise transformer.Translator beam search with a tiny randomly initialized Transformer."
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Repository root containing the transformer package; added to sys.path explicitly.",
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda", "auto"],
        default="cpu",
        help="Device for the smoke check. Default cpu; auto chooses cuda only when available.",
    )
    parser.add_argument("--beam-size", type=int, default=3, help="Beam size for the tiny translation check.")
    parser.add_argument("--max-seq-len", type=int, default=8, help="Maximum generated sequence length; must be at least 3.")
    parser.add_argument("--seed", type=int, default=7, help="Torch random seed for deterministic tiny weights.")
    parser.add_argument(
        "--skip-batch-assertion-check",
        action="store_true",
        help="Do not verify that translate_sentence rejects batch sizes larger than one.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        parser.error(f"--repo-root does not exist: {repo_root}")
    if args.max_seq_len < 3:
        parser.error("--max-seq-len must be at least 3 for the original Translator loop")
    if args.beam_size < 1:
        parser.error("--beam-size must be positive")

    # Tiny vocab layout mirrors transformer.Constants token semantics.
    pad_idx = 0
    unk_idx = 1
    bos_idx = 2
    eos_idx = 3
    vocab_size = 9
    if args.beam_size > vocab_size:
        parser.error(f"--beam-size must be <= tiny target vocab size ({vocab_size})")

    sys.path.insert(0, str(repo_root))

    try:
        import torch
        from transformer.Models import Transformer
        from transformer.Translator import Translator
    except Exception as exc:  # pragma: no cover - reports user environment issue
        print(f"ERROR: failed to import repository Transformer/Translator: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    if args.device == "auto":
        device_name = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device_name = args.device
    if device_name == "cuda" and not torch.cuda.is_available():
        print("ERROR: CUDA was requested but torch.cuda.is_available() is false", file=sys.stderr)
        return 2
    device = torch.device(device_name)

    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)

    errors: list[str] = []
    result: dict[str, object] = {
        "repo_root": str(repo_root),
        "device": str(device),
        "beam_size": args.beam_size,
        "max_seq_len": args.max_seq_len,
        "seed": args.seed,
        "pad_idx": pad_idx,
        "unk_idx": unk_idx,
        "bos_idx": bos_idx,
        "eos_idx": eos_idx,
        "prediction_ids": None,
        "batch_assertion_checked": not args.skip_batch_assertion_check,
        "batch_assertion_ok": None,
    }

    try:
        model = Transformer(
            n_src_vocab=vocab_size,
            n_trg_vocab=vocab_size,
            src_pad_idx=pad_idx,
            trg_pad_idx=pad_idx,
            d_word_vec=8,
            d_model=8,
            d_inner=16,
            n_layers=1,
            n_head=2,
            d_k=4,
            d_v=4,
            dropout=0.0,
            n_position=max(12, args.max_seq_len + 4),
            trg_emb_prj_weight_sharing=True,
            emb_src_trg_weight_sharing=True,
            scale_emb_or_prj="prj",
        ).to(device)
        translator = Translator(
            model=model,
            beam_size=args.beam_size,
            max_seq_len=args.max_seq_len,
            src_pad_idx=pad_idx,
            trg_pad_idx=pad_idx,
            trg_bos_idx=bos_idx,
            trg_eos_idx=eos_idx,
        ).to(device)

        src_seq = torch.tensor([[4, 5, 6, pad_idx]], dtype=torch.long, device=device)
        pred_ids = translator.translate_sentence(src_seq)
        result["prediction_ids"] = pred_ids

        if not isinstance(pred_ids, list):
            errors.append(f"translate_sentence returned {type(pred_ids).__name__}, expected list")
        elif not pred_ids:
            errors.append("translate_sentence returned an empty list")
        else:
            if pred_ids[0] != bos_idx:
                errors.append(f"first generated id should be BOS {bos_idx}, got {pred_ids[0]}")
            if len(pred_ids) > args.max_seq_len:
                errors.append(f"prediction length {len(pred_ids)} exceeds max_seq_len {args.max_seq_len}")
            bad_ids = [idx for idx in pred_ids if not isinstance(idx, int) or idx < 0 or idx >= vocab_size]
            if bad_ids:
                errors.append(f"prediction contains ids outside tiny vocab: {bad_ids}")

        if not args.skip_batch_assertion_check:
            try:
                translator.translate_sentence(torch.tensor([[4, 5], [6, pad_idx]], dtype=torch.long, device=device))
                result["batch_assertion_ok"] = False
                errors.append("translate_sentence accepted batch size two; expected AssertionError")
            except AssertionError:
                result["batch_assertion_ok"] = True

    except Exception as exc:  # pragma: no cover - reports user environment/runtime issue
        errors.append(f"smoke check failed with {type(exc).__name__}: {exc}")

    result["errors"] = errors
    result["status"] = "OK" if not errors else "FAILED"

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("attention-is-all-you-need-pytorch translation smoke check")
        for key in ["device", "beam_size", "max_seq_len", "seed", "prediction_ids", "batch_assertion_ok"]:
            print(f"{key}: {result.get(key)}")
        for error in errors:
            print(f"ERROR: {error}")
        print("status:", result["status"])

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
