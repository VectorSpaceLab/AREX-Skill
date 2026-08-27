#!/usr/bin/env python3
"""Create a safe inference config for RWKV-LM demos.

The script records the checkpoint, tokenizer, mode, prompt, and sampling
parameters in JSON so future agents can reproduce the request without relying on
hard-coded demo paths.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True, help="Path to the model checkpoint")
    parser.add_argument("--tokenizer", required=True, help="Tokenizer identifier or file path")
    parser.add_argument("--mode", choices=["gpt", "rnn", "fast"], required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=0)
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    config = {
        "checkpoint": args.checkpoint,
        "tokenizer": args.tokenizer,
        "mode": args.mode,
        "prompt": args.prompt,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "top_k": args.top_k,
        "max_new_tokens": args.max_new_tokens,
        "seed": args.seed,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
