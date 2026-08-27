#!/usr/bin/env python3
"""Inspect a Hugging Face Qwen3 config for nano-vLLM compatibility.

This helper reads configuration only; it does not load model weights or
construct nano-vLLM runners. Use it before selecting tensor_parallel_size or
attempting a new checkpoint.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PACKED_MODULES_MAPPING = {
    "q_proj": ("qkv_proj", "q"),
    "k_proj": ("qkv_proj", "k"),
    "v_proj": ("qkv_proj", "v"),
    "gate_proj": ("gate_up_proj", 0),
    "up_proj": ("gate_up_proj", 1),
}


def load_config(args: argparse.Namespace) -> Any:
    from transformers import AutoConfig

    source = args.model_dir or args.model_config
    if not source:
        raise SystemExit("provide --model-dir or --model-config")
    path = Path(source).expanduser()
    if args.model_config and path.is_file():
        source = str(path.parent)
    elif path.exists():
        source = str(path)
    return AutoConfig.from_pretrained(source, local_files_only=True, trust_remote_code=False)


def get_int(config: Any, name: str, fallback: int | None = None) -> int | None:
    value = getattr(config, name, fallback)
    return int(value) if value is not None else None


def add_div_check(checks: list[dict[str, Any]], name: str, value: int | None, tp: int, required: bool = True) -> None:
    if value is None:
        checks.append({"field": name, "ok": not required, "value": None, "message": "missing" if required else "missing optional"})
        return
    ok = value % tp == 0
    checks.append({"field": name, "ok": ok, "value": value, "tensor_parallel_size": tp, "message": "divisible" if ok else f"{value} is not divisible by {tp}"})


def inspect(config: Any, tp: int) -> dict[str, Any]:
    num_heads = get_int(config, "num_attention_heads")
    num_kv_heads = get_int(config, "num_key_value_heads", num_heads)
    hidden_size = get_int(config, "hidden_size")
    intermediate_size = get_int(config, "intermediate_size")
    vocab_size = get_int(config, "vocab_size")
    head_dim = get_int(config, "head_dim") or (hidden_size // num_heads if hidden_size and num_heads else None)
    model_type = getattr(config, "model_type", None)
    architectures = getattr(config, "architectures", None)
    hidden_act = getattr(config, "hidden_act", None)

    checks: list[dict[str, Any]] = []
    checks.append({"field": "model_type", "ok": model_type == "qwen3", "value": model_type, "message": "expected qwen3"})
    if architectures:
        checks.append({"field": "architectures", "ok": any("Qwen3" in str(item) for item in architectures), "value": architectures, "message": "should name Qwen3 architecture"})
    add_div_check(checks, "num_attention_heads", num_heads, tp)
    add_div_check(checks, "num_key_value_heads", num_kv_heads, tp)
    add_div_check(checks, "vocab_size", vocab_size, tp)
    add_div_check(checks, "hidden_size", hidden_size, tp)
    add_div_check(checks, "intermediate_size", intermediate_size, tp)
    if num_heads and hidden_size and head_dim:
        checks.append({"field": "head_dim", "ok": head_dim * num_heads == hidden_size, "value": head_dim, "message": "head_dim*num_heads should equal hidden_size"})
    checks.append({"field": "hidden_act", "ok": hidden_act == "silu", "value": hidden_act, "message": "Qwen3MLP asserts silu"})

    return {
        "model_type": model_type,
        "architectures": architectures,
        "tensor_parallel_size": tp,
        "dimensions": {
            "num_attention_heads": num_heads,
            "num_key_value_heads": num_kv_heads,
            "hidden_size": hidden_size,
            "intermediate_size": intermediate_size,
            "vocab_size": vocab_size,
            "head_dim": head_dim,
            "max_position_embeddings": get_int(config, "max_position_embeddings"),
            "tie_word_embeddings": bool(getattr(config, "tie_word_embeddings", False)),
            "attention_bias": getattr(config, "attention_bias", None),
            "dtype": str(getattr(config, "torch_dtype", getattr(config, "dtype", None))),
        },
        "packed_modules_mapping": PACKED_MODULES_MAPPING,
        "checks": checks,
        "ok": all(item["ok"] for item in checks),
    }


def print_text(report: dict[str, Any]) -> None:
    print("nano-vLLM Qwen3 contract inspection")
    print(f"model_type: {report['model_type']}")
    print(f"tensor_parallel_size: {report['tensor_parallel_size']}")
    print("dimensions:")
    for key, value in report["dimensions"].items():
        print(f"  {key}: {value}")
    print("checks:")
    for item in report["checks"]:
        status = "OK" if item["ok"] else "FAIL"
        print(f"  {status} {item['field']}: {item.get('message')} (value={item.get('value')})")
    print("packed module mapping:")
    for source, target in report["packed_modules_mapping"].items():
        print(f"  {source} -> {target[0]} shard {target[1]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Qwen3 config assumptions for nano-vLLM without loading weights.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--model-dir", help="Local Hugging Face model directory containing config.json.")
    group.add_argument("--model-config", help="Path to a config.json file or directory containing one.")
    parser.add_argument("--tensor-parallel-size", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not (1 <= args.tensor_parallel_size <= 8):
        parser.error("--tensor-parallel-size must be between 1 and 8")

    config = load_config(args)
    report = inspect(config, args.tensor_parallel_size)
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
