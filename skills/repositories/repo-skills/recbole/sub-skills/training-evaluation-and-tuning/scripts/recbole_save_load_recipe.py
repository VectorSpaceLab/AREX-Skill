#!/usr/bin/env python3
"""RecBole checkpoint load and case-study recipe helper.

By default this script validates a checkpoint path and prints the public API
sequence. If --topk and --users are supplied, it loads the checkpoint with
RecBole and executes full_sort_topk for those users.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _friendly_import():
    try:
        from recbole.quick_start import load_data_and_model
        from recbole.utils.case_study import full_sort_scores, full_sort_topk
    except ImportError as exc:  # pragma: no cover - environment dependent
        message = (
            "Unable to import RecBole load/case-study APIs. Install RecBole "
            "in the active Python environment before executing top-k scoring. "
            f"Original import error: {exc}"
        )
        raise SystemExit(message) from exc
    return load_data_and_model, full_sort_scores, full_sort_topk


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if hasattr(obj, "detach"):
        try:
            return obj.detach().cpu().tolist()
        except Exception:
            pass
    if hasattr(obj, "cpu"):
        try:
            return obj.cpu().tolist()
        except Exception:
            pass
    if hasattr(obj, "tolist"):
        try:
            return obj.tolist()
        except Exception:
            pass
    if hasattr(obj, "item"):
        try:
            return obj.item()
        except Exception:
            pass
    return obj


def _split_csv(text: str | None) -> list[str]:
    if not text:
        return []
    return [piece.strip() for piece in text.split(",") if piece.strip()]


def recipe_text(model_file: str) -> str:
    return f'''# RecBole save/load and case-study sequence
from recbole.quick_start import load_data_and_model
from recbole.utils.case_study import full_sort_scores, full_sort_topk

config, model, dataset, train_data, valid_data, test_data = load_data_and_model(
    model_file={model_file!r},
)

# External user tokens must exist in this dataset.
uid_series = dataset.token2id(dataset.uid_field, ["196", "186"])

# Top-k scores and internal item ids.
topk_scores, topk_iids = full_sort_topk(
    uid_series,
    model,
    test_data,
    k=10,
    device=config["device"],
)
external_items = dataset.id2token(dataset.iid_field, topk_iids.cpu())

# Full score matrix; can be large for big item catalogs.
scores = full_sort_scores(uid_series, model, test_data, device=config["device"])
'''


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a RecBole checkpoint path, print the load/case-study API "
            "sequence, and optionally execute top-k scoring."
        )
    )
    parser.add_argument("--model-file", "--model_file", help="Path to a RecBole saved model checkpoint (*.pth)")
    parser.add_argument("--topk", type=int, default=None, help="Execute full_sort_topk with this k")
    parser.add_argument("--users", default=None, help="Comma-separated external user tokens for --topk, e.g. 196,186")
    parser.add_argument(
        "--device",
        default="config",
        choices=["config", "cpu", "cuda"],
        help="Device passed to case-study helpers; default uses config['device']",
    )
    parser.add_argument(
        "--print-full-scores-shape",
        "--print_full_scores_shape",
        action="store_true",
        help="Also compute full_sort_scores and print its shape; can be expensive on large item catalogs",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    if not args.model_file:
        print(recipe_text("./checkpoints/BPR-example.pth"))
        print("Provide --model-file to validate a real checkpoint path.")
        return 0

    model_path = Path(args.model_file).expanduser()
    if not model_path.is_file():
        raise SystemExit(f"Checkpoint file does not exist: {model_path}")

    resolved = str(model_path.resolve())
    print(f"Checkpoint exists: {resolved}")
    print(recipe_text(resolved))

    if args.topk is None:
        print("No scoring executed. Add --topk K --users user1,user2 to run full_sort_topk.")
        return 0
    if args.topk < 1:
        raise SystemExit("--topk must be >= 1")
    users = _split_csv(args.users)
    if not users:
        raise SystemExit("--topk requires --users with comma-separated external user tokens")

    load_data_and_model, full_sort_scores, full_sort_topk = _friendly_import()

    config, model, dataset, train_data, valid_data, test_data = load_data_and_model(model_file=resolved)

    if args.device == "config":
        device = config["device"]
    else:
        try:
            import torch
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise SystemExit(f"PyTorch is required to choose --device {args.device}: {exc}") from exc
        device = torch.device(args.device)
        model = model.to(device)

    uid_series = dataset.token2id(dataset.uid_field, users)
    topk_scores, topk_iids = full_sort_topk(uid_series, model, test_data, k=args.topk, device=device)
    external_items = dataset.id2token(dataset.iid_field, topk_iids.cpu())

    output: dict[str, Any] = {
        "users": users,
        "internal_user_ids": _jsonable(uid_series),
        "topk": args.topk,
        "topk_scores": _jsonable(topk_scores),
        "topk_internal_item_ids": _jsonable(topk_iids),
        "topk_external_items": _jsonable(external_items),
    }

    if args.print_full_scores_shape:
        scores = full_sort_scores(uid_series, model, test_data, device=device)
        output["full_scores_shape"] = list(scores.shape)

    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
