#!/usr/bin/env python3
"""Run tiny deterministic training helper checks for attention-is-all-you-need-pytorch.

This imports source from an explicit --repo-root, constructs a tiny Transformer,
checks train.py loss helpers, and verifies the ScheduledOptim learning-rate
update. It does not load user data, write checkpoints, or start epoch training.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tiny deterministic smoke check for train.py helpers, Transformer forward, and ScheduledOptim.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", required=True, type=Path, help="Repository checkout containing train.py and transformer/.")
    parser.add_argument("--device", choices=["cpu", "cuda", "auto"], default="cpu", help="Device for tiny tensor checks. Use cpu for safest behavior.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable lines.")
    return parser.parse_args()


def import_repo(repo_root: Path):
    root = repo_root.expanduser().resolve()
    if not (root / "train.py").is_file() or not (root / "transformer" / "Models.py").is_file():
        raise SystemExit("ERROR: --repo-root must contain train.py and transformer/Models.py.")
    sys.path.insert(0, str(root))
    try:
        import torch  # noqa: F401
        import train  # noqa: F401
        from transformer.Models import Transformer  # noqa: F401
        from transformer.Optim import ScheduledOptim  # noqa: F401
    except Exception as exc:  # pragma: no cover - exact dependency errors vary by environment
        raise SystemExit(
            "ERROR: failed to import training sources. Use a legacy-compatible environment "
            "with PyTorch, torchtext.data.Field, dill, NumPy, and tqdm. Original error: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    import torch
    import train
    from transformer.Models import Transformer
    from transformer.Optim import ScheduledOptim

    return torch, train, Transformer, ScheduledOptim


def choose_device(torch, requested: str):
    if requested == "cpu":
        return torch.device("cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise SystemExit("ERROR: --device cuda requested, but torch.cuda.is_available() is False.")
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def run_checks(torch, train, Transformer, ScheduledOptim, device) -> Dict[str, Any]:
    torch.manual_seed(7)

    # Loss/performance helpers: 6 token positions, two pads ignored.
    pred = torch.tensor(
        [
            [0.1, 3.0, 0.2, 0.0, -0.1],
            [0.0, 0.1, 2.5, 0.2, -0.3],
            [4.0, 0.0, 0.0, 0.0, 0.0],
            [0.2, 0.1, 0.0, 2.1, -0.2],
            [0.1, 0.0, 0.1, 0.2, 2.2],
            [3.0, 0.1, 0.0, 0.0, 0.0],
        ],
        dtype=torch.float32,
        device=device,
    )
    gold = torch.tensor([[1, 2, 0], [3, 4, 0]], dtype=torch.long, device=device)
    plain_loss, n_correct, n_word = train.cal_performance(pred, gold, trg_pad_idx=0, smoothing=False)
    smooth_loss = train.cal_loss(pred, gold, trg_pad_idx=0, smoothing=True)
    if n_word != 4:
        raise AssertionError(f"expected 4 non-pad words, got {n_word}")
    if n_correct != 4:
        raise AssertionError(f"expected 4 correct predictions, got {n_correct}")
    if not (torch.isfinite(plain_loss) and torch.isfinite(smooth_loss)):
        raise AssertionError("loss values must be finite")

    # patch_src/patch_trg operate on torchtext-style time-major batches.
    time_major_src = torch.tensor([[1, 2], [3, 0], [4, 0]], dtype=torch.long, device=device)
    patched_src = train.patch_src(time_major_src, pad_idx=0)
    time_major_trg = torch.tensor([[1, 1], [2, 3], [4, 0], [0, 0]], dtype=torch.long, device=device)
    patched_trg, shifted_gold = train.patch_trg(time_major_trg, pad_idx=0)
    if tuple(patched_src.shape) != (2, 3):
        raise AssertionError(f"patch_src shape mismatch: {tuple(patched_src.shape)}")
    if tuple(patched_trg.shape) != (2, 3) or tuple(shifted_gold.shape) != (6,):
        raise AssertionError("patch_trg shape mismatch")

    # Tiny Transformer forward and one scheduled optimizer step.
    model = Transformer(
        n_src_vocab=11,
        n_trg_vocab=11,
        src_pad_idx=0,
        trg_pad_idx=0,
        d_word_vec=8,
        d_model=8,
        d_inner=16,
        n_layers=1,
        n_head=2,
        d_k=4,
        d_v=4,
        dropout=0.0,
        n_position=10,
        trg_emb_prj_weight_sharing=True,
        emb_src_trg_weight_sharing=True,
        scale_emb_or_prj="prj",
    ).to(device)
    model.train()
    src_seq = torch.tensor([[1, 2, 0, 0], [3, 4, 5, 0]], dtype=torch.long, device=device)
    trg_seq = torch.tensor([[1, 6, 7], [1, 8, 0]], dtype=torch.long, device=device)
    logits = model(src_seq, trg_seq)
    if tuple(logits.shape) != (6, 11):
        raise AssertionError(f"Transformer output shape mismatch: {tuple(logits.shape)}")
    tiny_gold = torch.tensor([[6, 7, 0], [8, 0, 0]], dtype=torch.long, device=device)
    tiny_loss = train.cal_loss(logits, tiny_gold, trg_pad_idx=0, smoothing=True)
    optimizer = torch.optim.Adam(model.parameters(), betas=(0.9, 0.98), eps=1e-9)
    scheduled = ScheduledOptim(optimizer, lr_mul=2.0, d_model=8, n_warmup_steps=4)
    scheduled.zero_grad()
    tiny_loss.backward()
    scheduled.step_and_update_lr()
    first_lr = optimizer.param_groups[0]["lr"]
    expected_lr = 2.0 * (8 ** -0.5) * min(1 ** -0.5, 1 * (4 ** -1.5))
    if not math.isclose(first_lr, expected_lr, rel_tol=1e-7, abs_tol=1e-10):
        raise AssertionError(f"ScheduledOptim lr mismatch: got {first_lr}, expected {expected_lr}")

    return {
        "status": "passed",
        "device": str(device),
        "loss_helpers": {
            "plain_loss": float(plain_loss.detach().cpu()),
            "smooth_loss": float(smooth_loss.detach().cpu()),
            "n_correct": int(n_correct),
            "n_word": int(n_word),
        },
        "patch_shapes": {
            "src": list(patched_src.shape),
            "trg": list(patched_trg.shape),
            "gold": list(shifted_gold.shape),
        },
        "transformer_forward_shape": list(logits.shape),
        "scheduled_optim": {
            "n_steps": scheduled.n_steps,
            "first_lr": first_lr,
            "expected_first_lr": expected_lr,
        },
    }


def main() -> int:
    args = parse_args()
    torch, train, Transformer, ScheduledOptim = import_repo(args.repo_root)
    device = choose_device(torch, args.device)
    result = run_checks(torch, train, Transformer, ScheduledOptim, device)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("training smoke check passed")
        print(f"device: {result['device']}")
        print(
            "loss helpers: "
            f"n_word={result['loss_helpers']['n_word']} "
            f"n_correct={result['loss_helpers']['n_correct']} "
            f"plain_loss={result['loss_helpers']['plain_loss']:.6f} "
            f"smooth_loss={result['loss_helpers']['smooth_loss']:.6f}"
        )
        print(
            "patch shapes: "
            f"src={result['patch_shapes']['src']} "
            f"trg={result['patch_shapes']['trg']} "
            f"gold={result['patch_shapes']['gold']}"
        )
        print(f"tiny Transformer forward shape: {result['transformer_forward_shape']}")
        print(
            "ScheduledOptim first lr: "
            f"{result['scheduled_optim']['first_lr']:.10f} "
            f"(n_steps={result['scheduled_optim']['n_steps']})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
