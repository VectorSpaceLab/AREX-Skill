#!/usr/bin/env python3
"""Run a tiny, CPU-safe loralib API smoke check.

Usage:
    python scripts/check_lora_core.py --json

The helper never downloads checkpoints or data. `--repo-root` is only useful
when inspecting an unpacked checkout before installing the package.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, help="Optional checkout to add to sys.path before import.")
    parser.add_argument("--json", action="store_true", help="Emit one JSON object instead of prose.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.repo_root:
        sys.path.insert(0, str(args.repo_root.expanduser().resolve()))

    try:
        import torch
        import loralib as lora
    except Exception as exc:  # pragma: no cover - diagnostic path
        message = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "hint": "Install a compatible PyTorch build and the loralib distribution before retrying.",
        }
        print(json.dumps(message) if args.json else f"ERROR: {message['error']}\n{message['hint']}")
        return 2

    try:
        linear = lora.Linear(4, 3, r=2, lora_alpha=4, lora_dropout=0.0)
        x = torch.randn(5, 4)
        train_shape = list(linear(x).shape)
        linear.eval()
        merged_after_eval = bool(linear.merged)
        eval_shape = list(linear(x).shape)
        linear.train()
        unmerged_after_train = not bool(linear.merged)

        embedding = lora.Embedding(10, 4, r=2)
        embedding_shape = list(embedding(torch.tensor([[1, 2, 3]])).shape)

        merged = lora.MergedLinear(4, 12, r=2, lora_alpha=4, enable_lora=[True, False, True])
        merged_shape = list(merged(torch.randn(2, 4)).shape)

        conv = lora.Conv2d(1, 2, kernel_size=3, r=1, padding=1)
        conv_shape = list(conv(torch.randn(1, 1, 4, 4)).shape)

        model = torch.nn.Sequential(lora.Linear(4, 4, r=2), torch.nn.Linear(4, 2))
        lora.mark_only_lora_as_trainable(model, bias="lora_only")
        trainable = [name for name, parameter in model.named_parameters() if parameter.requires_grad]
        state_keys = sorted(lora.lora_state_dict(model).keys())
        state_bias_keys = sorted(lora.lora_state_dict(model, bias="lora_only").keys())

        result = {
            "ok": True,
            "package": "loralib",
            "package_module_name": getattr(lora, "name", None),
            "torch_version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "shapes": {
                "linear_train": train_shape,
                "linear_eval": eval_shape,
                "embedding": embedding_shape,
                "merged_linear": merged_shape,
                "conv2d": conv_shape,
            },
            "merge_behavior": {
                "merged_after_eval": merged_after_eval,
                "unmerged_after_train": unmerged_after_train,
            },
            "trainable_parameters": trainable,
            "lora_state_keys": state_keys,
            "lora_state_keys_with_lora_only_bias": state_bias_keys,
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        result = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "hint": "Check the installed PyTorch version and the layer arguments; see core-lora-api references/troubleshooting.md.",
        }
        print(json.dumps(result) if args.json else f"ERROR: {result['error']}\n{result['hint']}")
        return 1

    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(f"loralib smoke: OK (torch {result['torch_version']}, CUDA={result['cuda_available']})")
        print(f"linear={train_shape}, embedding={embedding_shape}, merged_linear={merged_shape}, conv2d={conv_shape}")
        print(f"trainable={trainable}")
        print(f"lora_state_keys={state_keys}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
