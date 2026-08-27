#!/usr/bin/env python3
"""Inspect OpenCLIP checkpoint keys safely on CPU.

The default load path uses torch.load(weights_only=True). The script reports
nested payloads such as state_dict/state_dict_ema, common wrapper prefixes, and
optional missing/unexpected keys against a random uninitialized OpenCLIP model.
It never mutates the checkpoint and never downloads weights.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import torch


PREFIXES = ("module.", "_orig_mod.", "trainable_module.")
STATE_KEYS = ("state_dict", "state_dict_ema", "model", "module")


def is_tensor_mapping(value: Any) -> bool:
    return isinstance(value, Mapping) and bool(value) and all(torch.is_tensor(item) for item in value.values())


def safe_shape(value: Any) -> list[int] | str:
    if torch.is_tensor(value):
        return list(value.shape)
    return type(value).__name__


def load_checkpoint(path: Path, allow_unsafe_pickle: bool) -> Any:
    if path.suffix == ".safetensors":
        try:
            from safetensors.torch import load_file
        except ImportError as exc:
            raise SystemExit("Install safetensors to inspect .safetensors files.") from exc
        return load_file(str(path), device="cpu")
    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    except Exception as exc:
        if not allow_unsafe_pickle:
            raise SystemExit(
                "weights_only=True failed. Re-run only for a trusted checkpoint with "
                "--allow-unsafe-pickle if you accept arbitrary pickle execution risk. "
                f"Original error: {exc}"
            ) from exc
        return torch.load(path, map_location="cpu", weights_only=False)


def find_tensor_payloads(obj: Any) -> dict[str, Mapping[str, torch.Tensor]]:
    payloads: dict[str, Mapping[str, torch.Tensor]] = {}
    if is_tensor_mapping(obj):
        payloads["<root>"] = obj
    if isinstance(obj, Mapping):
        for key in STATE_KEYS:
            value = obj.get(key)
            if is_tensor_mapping(value):
                payloads[key] = value
        for key, value in obj.items():
            if key in payloads:
                continue
            if isinstance(key, str) and is_tensor_mapping(value):
                payloads[key] = value
    return payloads


def choose_payload(payloads: Mapping[str, Mapping[str, torch.Tensor]], prefer_ema: bool) -> tuple[str, Mapping[str, torch.Tensor]]:
    if prefer_ema and "state_dict_ema" in payloads:
        return "state_dict_ema", payloads["state_dict_ema"]
    if "state_dict" in payloads:
        return "state_dict", payloads["state_dict"]
    if "<root>" in payloads:
        return "<root>", payloads["<root>"]
    if payloads:
        name = next(iter(payloads))
        return name, payloads[name]
    raise SystemExit("No tensor state-dict-like payload found in checkpoint.")


def prefix_report(keys: list[str]) -> dict[str, Any]:
    counts = {prefix: sum(key.startswith(prefix) for key in keys) for prefix in PREFIXES}
    first_components = Counter(key.split(".", 1)[0] for key in keys)
    return {
        "total_keys": len(keys),
        "known_prefix_counts": counts,
        "top_first_components": first_components.most_common(20),
    }


def strip_prefixes(key: str, prefixes: tuple[str, ...]) -> str:
    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if key.startswith(prefix):
                key = key[len(prefix) :]
                changed = True
    return key


def summarize_payload(name: str, payload: Mapping[str, torch.Tensor], sample_count: int) -> dict[str, Any]:
    keys = list(payload.keys())
    dtype_counts = Counter(str(value.dtype) for value in payload.values() if torch.is_tensor(value))
    ndim_counts = Counter(int(value.ndim) for value in payload.values() if torch.is_tensor(value))
    return {
        "name": name,
        **prefix_report(keys),
        "dtype_counts": dtype_counts.most_common(),
        "ndim_counts": ndim_counts.most_common(),
        "sample_keys": [
            {"key": key, "shape": safe_shape(payload[key]), "dtype": str(payload[key].dtype)}
            for key in keys[:sample_count]
        ],
    }


def build_model_key_set(model_name: str, force_naflex_vision: bool) -> set[str]:
    import open_clip

    model = open_clip.create_model(
        model_name,
        pretrained=None,
        load_weights=False,
        pretrained_image=False,
        pretrained_text=False,
        force_naflex_vision=force_naflex_vision,
        device="cpu",
    )
    return set(model.state_dict().keys())


def compare_to_model(
    payload: Mapping[str, torch.Tensor],
    model_name: str,
    force_naflex_vision: bool,
    max_items: int,
) -> dict[str, Any]:
    model_keys = build_model_key_set(model_name, force_naflex_vision=force_naflex_vision)
    raw_keys = set(payload.keys())
    stripped_keys = {strip_prefixes(key, PREFIXES) for key in raw_keys}
    missing = sorted(model_keys - stripped_keys)
    unexpected = sorted(stripped_keys - model_keys)
    return {
        "model": model_name,
        "force_naflex_vision": force_naflex_vision,
        "model_key_count": len(model_keys),
        "checkpoint_key_count": len(raw_keys),
        "missing_count": len(missing),
        "unexpected_count": len(unexpected),
        "missing_sample": missing[:max_items],
        "unexpected_sample": unexpected[:max_items],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report OpenCLIP checkpoint state-dict key patterns safely.")
    parser.add_argument("checkpoint", type=Path, help="Local .pt/.pth/.bin/.safetensors checkpoint path.")
    parser.add_argument("--prefer-ema", action="store_true", help="Prefer state_dict_ema when present.")
    parser.add_argument(
        "--allow-unsafe-pickle",
        action="store_true",
        help="Allow torch.load(weights_only=False) only for trusted checkpoints when weights_only=True fails.",
    )
    parser.add_argument("--model", help="Optional OpenCLIP model name for random-model key comparison.")
    parser.add_argument(
        "--force-naflex-vision",
        action="store_true",
        help="Apply force_naflex_vision=True when constructing the optional comparison model.",
    )
    parser.add_argument("--max-sample-keys", type=int, default=12, help="Number of checkpoint keys to sample.")
    parser.add_argument("--max-missing", type=int, default=25, help="Number of missing/unexpected keys to sample.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.checkpoint.exists():
        raise SystemExit(f"Checkpoint not found: {args.checkpoint}")

    checkpoint = load_checkpoint(args.checkpoint, allow_unsafe_pickle=args.allow_unsafe_pickle)
    payloads = find_tensor_payloads(checkpoint)
    selected_name, selected_payload = choose_payload(payloads, prefer_ema=args.prefer_ema)

    top_level = {}
    if isinstance(checkpoint, Mapping):
        top_level = {str(key): type(value).__name__ for key, value in checkpoint.items() if key not in payloads}

    report: dict[str, Any] = {
        "checkpoint_name": args.checkpoint.name,
        "top_level_non_tensor_payloads": top_level,
        "available_tensor_payloads": [
            {"name": name, "num_keys": len(payload)} for name, payload in payloads.items()
        ],
        "selected_payload": summarize_payload(selected_name, selected_payload, args.max_sample_keys),
    }

    if args.model:
        try:
            report["model_key_comparison"] = compare_to_model(
                selected_payload,
                model_name=args.model,
                force_naflex_vision=args.force_naflex_vision,
                max_items=args.max_missing,
            )
        except Exception as exc:
            report["model_key_comparison_error"] = str(exc)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"checkpoint: {report['checkpoint_name']}")
        if top_level:
            print("top-level non-tensor payloads:")
            for key, value_type in top_level.items():
                print(f"  {key}: {value_type}")
        print("available tensor payloads:")
        for payload in report["available_tensor_payloads"]:
            marker = " *" if payload["name"] == selected_name else ""
            print(f"  {payload['name']}: {payload['num_keys']} keys{marker}")
        selected = report["selected_payload"]
        print(f"selected: {selected['name']} ({selected['total_keys']} keys)")
        print(f"known prefix counts: {selected['known_prefix_counts']}")
        print(f"top first components: {selected['top_first_components']}")
        print(f"dtype counts: {selected['dtype_counts']}")
        print("sample keys:")
        for item in selected["sample_keys"]:
            print(f"  {item['key']} shape={item['shape']} dtype={item['dtype']}")
        if "model_key_comparison" in report:
            comparison = report["model_key_comparison"]
            print("model key comparison:")
            for key in ("model", "force_naflex_vision", "missing_count", "unexpected_count"):
                print(f"  {key}: {comparison[key]}")
            print(f"  missing sample: {comparison['missing_sample']}")
            print(f"  unexpected sample: {comparison['unexpected_sample']}")
        if "model_key_comparison_error" in report:
            print(f"model key comparison error: {report['model_key_comparison_error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
