#!/usr/bin/env python3
"""Inspect MOSS runtime classes without loading checkpoints.

The script adds an optional source checkout to sys.path, imports the MOSS config,
tokenizer, and model classes, instantiates a tiny MossForCausalLM from a small
configuration, and optionally performs a tiny CUDA tensor check. It never calls
from_pretrained and never downloads model files.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def add_repo_root(repo_root: Optional[str]) -> None:
    if repo_root:
        sys.path.insert(0, str(Path(repo_root).expanduser().resolve()))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check MOSS model-runtime imports, signatures, and optional CUDA.")
    parser.add_argument("--repo-root", help="Optional MOSS source checkout root to import local models/ modules.")
    parser.add_argument("--cuda", action="store_true", help="Also require torch CUDA availability and a tiny tensor allocation.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    add_repo_root(args.repo_root)
    report: Dict[str, Any] = {"ok": True, "imports": {}, "checks": {}, "warnings": []}

    try:
        config_mod = importlib.import_module("models.configuration_moss")
        modeling_mod = importlib.import_module("models.modeling_moss")
        tokenizer_mod = importlib.import_module("models.tokenization_moss")
        report["imports"] = {
            "MossConfig": getattr(config_mod, "__file__", None),
            "MossForCausalLM": getattr(modeling_mod, "__file__", None),
            "MossTokenizer": getattr(tokenizer_mod, "__file__", None),
        }
    except Exception as exc:
        report["ok"] = False
        report["error"] = f"import failure: {type(exc).__name__}: {exc}"
        print(json.dumps(report, indent=2, sort_keys=True) if args.json else report["error"])
        return 2

    MossConfig = config_mod.MossConfig
    MossForCausalLM = modeling_mod.MossForCausalLM
    MossTokenizer = tokenizer_mod.MossTokenizer

    cfg = MossConfig()
    report["checks"]["config_defaults"] = {
        "model_type": MossConfig.model_type,
        "vocab_size": cfg.vocab_size,
        "n_positions": cfg.n_positions,
        "n_ctx": cfg.n_ctx,
        "n_embd": cfg.n_embd,
        "n_layer": cfg.n_layer,
        "n_head": cfg.n_head,
        "rotary_dim": cfg.rotary_dim,
        "bos_token_id": cfg.bos_token_id,
        "eos_token_id": cfg.eos_token_id,
        "wbits": getattr(cfg, "wbits", None),
        "groupsize": getattr(cfg, "groupsize", None),
    }
    report["checks"]["tokenizer_model_input_names"] = list(MossTokenizer.model_input_names)
    report["checks"]["model_forward_signature"] = str(inspect.signature(MossForCausalLM.forward))

    try:
        tiny_cfg = MossConfig(vocab_size=128, n_positions=16, n_ctx=16, n_embd=16, n_layer=1, n_head=1, rotary_dim=8, n_inner=32)
        tiny_model = MossForCausalLM(tiny_cfg)
        report["checks"]["tiny_model_param_count"] = sum(param.numel() for param in tiny_model.parameters())
    except Exception as exc:
        report["ok"] = False
        report["checks"]["tiny_model_error"] = f"{type(exc).__name__}: {exc}"

    try:
        import torch
        cuda = {
            "torch_version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
            "cuda_version": getattr(torch.version, "cuda", None),
        }
        if torch.cuda.is_available():
            x = torch.ones(2, device="cuda")
            cuda["cuda_tensor_sum"] = float(x.sum().item())
            cuda["device_name"] = torch.cuda.get_device_name(0)
        if args.cuda and not cuda["cuda_available"]:
            report["ok"] = False
            cuda["required_but_unavailable"] = True
        report["checks"]["cuda"] = cuda
    except Exception as exc:
        if args.cuda:
            report["ok"] = False
        report["checks"]["cuda_error"] = f"{type(exc).__name__}: {exc}"

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("MOSS model runtime:", "PASS" if report["ok"] else "FAIL")
        print(json.dumps(report["checks"], indent=2, sort_keys=True))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
