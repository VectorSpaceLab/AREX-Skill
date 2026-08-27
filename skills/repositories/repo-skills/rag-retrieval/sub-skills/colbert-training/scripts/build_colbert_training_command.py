#!/usr/bin/env python3
"""Build a validated RAG-Retrieval ColBERT training launch command."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path


def quote(value: object) -> str:
    return shlex.quote(str(value))


def skill_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", help="Optional external RAG-Retrieval source checkout; defaults to this skill's bundled training copy")
    parser.add_argument("--dataset", required=True, help="Triplet JSONL training data")
    parser.add_argument("--output-dir", required=True, help="Training output directory")
    parser.add_argument("--model-name-or-path", default="hfl/chinese-roberta-wwm-ext")
    parser.add_argument("--colbert-dim", type=int, default=768)
    parser.add_argument("--neg-nums", type=int, default=15)
    parser.add_argument("--query-max-len", type=int, default=128)
    parser.add_argument("--passage-max-len", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", default="5e-6")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=12)
    parser.add_argument("--temperature", default="0.02")
    parser.add_argument("--save-on-epoch-end", type=int, default=1)
    parser.add_argument("--log-with", default="wandb")
    parser.add_argument("--warmup-proportion", default="0.1")
    parser.add_argument("--accelerate-config", help="Override accelerate config path")
    parser.add_argument("--devices", default="0,1", help="CUDA_VISIBLE_DEVICES value for the printed command")
    parser.add_argument("--json", action="store_true", help="Print a JSON object instead of shell text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = skill_root()
    dataset = Path(args.dataset).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if args.checkout:
        checkout = Path(args.checkout).expanduser().resolve()
        train_dir = checkout / "rag_retrieval" / "train" / "colbert"
        if args.accelerate_config:
            accelerate_config = Path(args.accelerate_config).expanduser().resolve()
        elif "bge-m3" in args.model_name_or_path.lower() or "xlm" in args.model_name_or_path.lower():
            accelerate_config = checkout / "config" / "xlmroberta_default_config.yaml"
        else:
            accelerate_config = checkout / "config" / "default_fsdp.yaml"
        source = "external-checkout"
    else:
        train_dir = Path(__file__).resolve().parent / "training_bundle"
        if args.accelerate_config:
            accelerate_config = Path(args.accelerate_config).expanduser().resolve()
        elif "bge-m3" in args.model_name_or_path.lower() or "xlm" in args.model_name_or_path.lower():
            accelerate_config = root / "scripts" / "accelerate_configs" / "xlmroberta_default_config.yaml"
        else:
            accelerate_config = root / "scripts" / "accelerate_configs" / "default_fsdp.yaml"
        source = "bundled-skill-copy"

    entrypoint = train_dir / "train_colbert.py"
    errors = []
    for label, path in (
        ("training directory", train_dir),
        ("entrypoint", entrypoint),
        ("dataset", dataset),
        ("accelerate config", accelerate_config),
    ):
        if not path.exists():
            errors.append(f"Missing {label}: {path}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 2

    parts = [
        "cd", quote(train_dir), "&&", f"CUDA_VISIBLE_DEVICES={quote(args.devices)}", "accelerate", "launch",
        "--config_file", quote(accelerate_config), quote(entrypoint.name),
        "--model_name_or_path", quote(args.model_name_or_path),
        "--dataset", quote(dataset),
        "--output_dir", quote(output_dir),
        "--batch_size", str(args.batch_size),
        "--lr", quote(args.lr),
        "--epochs", str(args.epochs),
        "--save_on_epoch_end", str(args.save_on_epoch_end),
        "--gradient_accumulation_steps", str(args.gradient_accumulation_steps),
        "--temperature", quote(args.temperature),
        "--query_max_len", str(args.query_max_len),
        "--passage_max_len", str(args.passage_max_len),
        "--colbert_dim", str(args.colbert_dim),
        "--neg_nums", str(args.neg_nums),
        "--log_with", quote(args.log_with),
        "--warmup_proportion", quote(args.warmup_proportion),
    ]
    command = " ".join(parts)
    warnings = []
    if "bge-m3" in args.model_name_or_path.lower() and args.colbert_dim != 1024:
        warnings.append("BAAI/bge-m3 ColBERT commonly uses colbert_dim=1024; use 768 only when intentionally training a new projection size.")
    payload = {
        "ok": True,
        "source": source,
        "training_directory": str(train_dir),
        "entrypoint": entrypoint.name,
        "dataset": str(dataset),
        "output_dir": str(output_dir),
        "accelerate_config": str(accelerate_config),
        "command": command,
        "warnings": warnings,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(command)
        for warning in warnings:
            print("\n# Warning: " + warning)
    return 0


if __name__ == "__main__":
    sys.exit(main())
