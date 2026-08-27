#!/usr/bin/env python3
"""Build a safe Qwen inference checklist without loading or downloading a model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CHAT_HINTS = ("-Chat", "chat", "Chat")

def inspect_checkpoint(path: str) -> dict:
    p = Path(path).expanduser()
    out = {"path": str(p), "exists": p.exists(), "is_dir": p.is_dir(), "checks": []}
    if not p.is_dir():
        out["checks"].append({"status": "FAIL", "message": "checkpoint path is not a directory"})
        return out
    names = {x.name for x in p.iterdir()}
    for filename in ("config.json",):
        out["checks"].append({"status": "PASS" if filename in names else "FAIL", "message": f"{filename} present"})
    tokenizer_markers = ["tokenizer_config.json", "tokenizer.json", "qwen.tiktoken"]
    out["checks"].append({"status": "PASS" if any(x in names for x in tokenizer_markers) else "WARN", "message": "tokenizer marker present"})
    shard_count = len([x for x in names if x.startswith("pytorch_model") or x.startswith("model-") or x.endswith(".safetensors")])
    out["checks"].append({"status": "PASS" if shard_count else "WARN", "message": f"model shard/safetensors count: {shard_count}"})
    return out

def main() -> int:
    parser = argparse.ArgumentParser(description="Plan Qwen inference settings safely; no imports, downloads, or model loads.")
    parser.add_argument("--model", default="Qwen/Qwen-7B-Chat", help="Model id or human-readable checkpoint name.")
    parser.add_argument("--local-checkpoint", help="Optional local checkpoint directory to inspect.")
    parser.add_argument("--backend", choices=["auto", "cpu", "cuda", "dashscope", "modelscope", "vllm"], default="auto")
    parser.add_argument("--precision", choices=["auto", "bf16", "fp16", "fp32", "int4", "int8"], default="auto")
    parser.add_argument("--task", choices=["chat", "completion", "batch-chat"], default="chat")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    plan = {
        "model": args.model,
        "task": args.task,
        "backend": args.backend,
        "precision": args.precision,
        "warnings": [],
        "required_choices": ["trust_remote_code must be accepted for historical Qwen checkpoints"],
    }
    is_chat = any(h in args.model for h in CHAT_HINTS)
    if args.task == "chat" and not is_chat:
        plan["warnings"].append("chat task requested but model name does not look like a Qwen chat checkpoint")
    if args.backend == "cpu":
        plan["warnings"].append("CPU inference is compatible but expected to be very slow")
    if args.backend in {"dashscope", "modelscope"}:
        plan["warnings"].append(f"{args.backend} may require network access and account/service availability")
    if args.precision in {"int4", "int8"}:
        plan["warnings"].append("quantized checkpoints require a compatible AutoGPTQ/torch/CUDA/Transformers stack")
    if args.task == "batch-chat":
        plan["required_choices"].extend(["use left padding", "set a pad token distinct from EOS", "set generation_config.pad_token_id"])
    if args.local_checkpoint:
        plan["checkpoint"] = inspect_checkpoint(args.local_checkpoint)

    if args.as_json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(json.dumps(plan, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
