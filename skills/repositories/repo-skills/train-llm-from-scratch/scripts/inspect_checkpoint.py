#!/usr/bin/env python3
"""Inspect a train-llm-from-scratch checkpoint without constructing a model.

Reports top-level keys, stored config fields, likely stage, tensor-key prefixes,
and common backbone/head key counts. This is read-only and does not load tensors
onto CUDA.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def tensor_shape(value) -> list[int] | None:
    shape = getattr(value, "shape", None)
    if shape is None:
        return None
    try:
        return [int(x) for x in shape]
    except Exception:  # noqa: BLE001
        return None


def inspect(path: Path, max_keys: int) -> dict:
    if not path.exists():
        raise SystemExit(f"checkpoint not found: {path}")
    try:
        import torch
    except ModuleNotFoundError as exc:
        raise SystemExit("torch is required to inspect checkpoints") from exc

    ckpt = torch.load(str(path), map_location="cpu", weights_only=False)
    if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
        state = ckpt.get("model_state_dict") or {}
        payload_kind = "training-checkpoint"
    elif isinstance(ckpt, dict):
        state = ckpt
        payload_kind = "state-dict-or-legacy-dict"
    else:
        state = {}
        payload_kind = type(ckpt).__name__

    keys = list(state.keys()) if isinstance(state, dict) else []
    prefixes = Counter(k.split(".", 1)[0] for k in keys)
    cfg = ckpt.get("cfg") if isinstance(ckpt, dict) else None
    legacy_config = ckpt.get("config") if isinstance(ckpt, dict) else None

    tensor_samples = []
    for key in keys[:max_keys]:
        shape = tensor_shape(state[key])
        tensor_samples.append({"key": key, "shape": shape})

    backbone_indicators = {
        "token_embed": sum("token_embed" in k for k in keys),
        "position_embed": sum("position_embed" in k for k in keys),
        "attn_blocks": sum("attn_blocks" in k for k in keys),
        "lm_head": sum("lm_head" in k for k in keys),
        "reward_head": sum("reward_head" in k for k in keys),
        "value_head": sum("value_head" in k for k in keys),
        "module_prefix": sum(k.startswith("module.") for k in keys),
        "transformer_prefix": sum(k.startswith("transformer.") or k.startswith("module.transformer.") for k in keys),
    }

    return {
        "path": str(path),
        "payload_kind": payload_kind,
        "top_level_keys": list(ckpt.keys()) if isinstance(ckpt, dict) else [],
        "stage": ckpt.get("stage") if isinstance(ckpt, dict) else None,
        "step": ckpt.get("step") if isinstance(ckpt, dict) else None,
        "is_final": ckpt.get("is_final") if isinstance(ckpt, dict) else None,
        "cfg": cfg,
        "legacy_config": legacy_config,
        "state_key_count": len(keys),
        "state_prefix_counts": dict(prefixes.most_common()),
        "backbone_indicators": backbone_indicators,
        "tensor_samples": tensor_samples,
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Read-only checkpoint inspector for train-llm-from-scratch.")
    p.add_argument("checkpoint", help="checkpoint .pt file to inspect")
    p.add_argument("--max-keys", type=int, default=20, help="number of state keys to sample")
    p.add_argument("--json", action="store_true", help="emit JSON")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    info = inspect(Path(args.checkpoint), args.max_keys)
    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True, default=str))
    else:
        print(f"path: {info['path']}")
        print(f"payload_kind: {info['payload_kind']}")
        print(f"stage: {info['stage']} | step: {info['step']} | is_final: {info['is_final']}")
        print(f"top_level_keys: {info['top_level_keys']}")
        cfg = info.get("cfg") or info.get("legacy_config") or {}
        if cfg:
            print("config summary:")
            for key in ["vocab_size", "context_length", "n_embed", "n_head", "n_blocks", "device", "amp_dtype"]:
                if isinstance(cfg, dict) and key in cfg:
                    print(f"  {key}: {cfg[key]}")
        print(f"state_key_count: {info['state_key_count']}")
        print("backbone_indicators:")
        for key, value in info["backbone_indicators"].items():
            print(f"  {key}: {value}")
        print("sample tensor keys:")
        for row in info["tensor_samples"]:
            print(f"  {row['key']}: {row['shape']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
