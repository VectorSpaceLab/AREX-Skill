#!/usr/bin/env python3
"""Inspect OpenAssistant inference model configs without starting services.

Examples:
  python scripts/check_inference_config.py --repo-root /path/to/Open-Assistant --list
  python scripts/check_inference_config.py --repo-root /path/to/Open-Assistant --model-config _lorem --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect OpenAssistant inference model configs safely.")
    parser.add_argument("--repo-root", required=True, type=Path, help="Open-Assistant checkout to inspect.")
    parser.add_argument("--model-config", default="_lorem", help="MODEL_CONFIG_NAME to inspect.")
    parser.add_argument("--list", action="store_true", help="List available config names.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser.parse_args()


def add_repo_paths(repo_root: Path) -> None:
    for rel in ("oasst-shared", "inference/worker"):
        path = repo_root / rel
        if path.exists():
            sys.path.insert(0, str(path))


def estimate_params_b(name: str, model_id: str) -> float | None:
    text = f"{name} {model_id}"
    match = re.search(r"(\d+(?:\.\d+)?)\s*[bB]", text)
    if not match:
        return None
    return float(match.group(1))


def memory_estimate_gb(name: str, cfg: Any) -> float | None:
    params = estimate_params_b(name, cfg.model_id)
    if params is None:
        return None
    return round(params * (1.25 if cfg.quantized or name.endswith("q") else 2.5), 2)


def config_to_dict(name: str, cfg: Any) -> dict[str, Any]:
    return {
        "name": name,
        "model_id": cfg.model_id,
        "max_input_length": cfg.max_input_length,
        "max_total_length": cfg.max_total_length,
        "quantized": cfg.quantized,
        "is_lorem": cfg.is_lorem,
        "is_llama": cfg.is_llama,
        "compat_hash": cfg.compat_hash,
        "estimated_min_gpu_memory_gb": memory_estimate_gb(name, cfg),
    }


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    if not repo_root.is_dir():
        print(f"error: repo root not found: {repo_root}", file=sys.stderr)
        return 2
    add_repo_paths(repo_root)

    try:
        from oasst_shared import model_configs
        from oasst_shared.schemas import inference
    except Exception as exc:
        print(f"error: could not import inference shared modules: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    names = sorted(model_configs.MODEL_CONFIGS)
    if args.list:
        output = {"inference_protocol_version": inference.INFERENCE_PROTOCOL_VERSION, "model_configs": names}
        if args.json:
            print(json.dumps(output, indent=2))
        else:
            print(f"Inference protocol version: {inference.INFERENCE_PROTOCOL_VERSION}")
            for name in names:
                print(name)
        return 0

    cfg = model_configs.MODEL_CONFIGS.get(args.model_config)
    if cfg is None:
        print(f"error: unknown model config: {args.model_config}", file=sys.stderr)
        print("hint: pass --list to view available names", file=sys.stderr)
        return 2

    result = {
        "inference_protocol_version": inference.INFERENCE_PROTOCOL_VERSION,
        "selected": config_to_dict(args.model_config, cfg),
        "safe_smoke_guidance": "Use _lorem for no-download CPU protocol checks; real configs may require model downloads and GPU memory.",
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        selected = result["selected"]
        assert isinstance(selected, dict)
        print(f"Inference protocol version: {result['inference_protocol_version']}")
        for key, value in selected.items():
            print(f"{key}: {value}")
        print(result["safe_smoke_guidance"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
