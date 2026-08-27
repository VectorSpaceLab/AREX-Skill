#!/usr/bin/env python3
"""Build a validated RAG-Retrieval embedding training launch command."""

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
    parser.add_argument("--config", required=True, help="Working training_embedding.yaml or distill_embedding.yaml")
    parser.add_argument("--backend", choices=["fsdp", "deepspeed"], default="fsdp", help="Distributed launch config family")
    parser.add_argument("--accelerate-config", help="Override accelerate config path")
    parser.add_argument("--devices", default="0,1", help="CUDA_VISIBLE_DEVICES value for the printed command")
    parser.add_argument("--json", action="store_true", help="Print a JSON object instead of shell text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = skill_root()
    config = Path(args.config).expanduser().resolve()

    if args.checkout:
        checkout = Path(args.checkout).expanduser().resolve()
        train_dir = checkout / "rag_retrieval" / "train" / "embedding"
        if args.accelerate_config:
            accelerate_config = Path(args.accelerate_config).expanduser().resolve()
        elif args.backend == "fsdp":
            accelerate_config = checkout / "config" / "default_fsdp.yaml"
        else:
            accelerate_config = checkout / "config" / "deepspeed" / "deepspeed_zero2.yaml"
        source = "external-checkout"
    else:
        train_dir = Path(__file__).resolve().parent / "training_bundle"
        if args.accelerate_config:
            accelerate_config = Path(args.accelerate_config).expanduser().resolve()
        elif args.backend == "fsdp":
            accelerate_config = root / "scripts" / "accelerate_configs" / "default_fsdp.yaml"
        else:
            accelerate_config = root / "scripts" / "accelerate_configs" / "deepspeed" / "deepspeed_zero2.yaml"
        source = "bundled-skill-copy"

    entrypoint = train_dir / "train_embedding.py"
    errors = []
    for label, path in (
        ("training directory", train_dir),
        ("entrypoint", entrypoint),
        ("working config", config),
        ("accelerate config", accelerate_config),
    ):
        if not path.exists():
            errors.append(f"Missing {label}: {path}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 2

    command = (
        f"cd {quote(train_dir)} && "
        f"CUDA_VISIBLE_DEVICES={quote(args.devices)} accelerate launch "
        f"--config_file {quote(accelerate_config)} "
        f"{quote(entrypoint.name)} --config {quote(config)}"
    )
    payload = {
        "ok": True,
        "source": source,
        "training_directory": str(train_dir),
        "entrypoint": entrypoint.name,
        "working_config": str(config),
        "accelerate_config": str(accelerate_config),
        "devices": args.devices,
        "command": command,
        "note": "Review the command, run a small foreground smoke job first, and add nohup/log redirection only after paths and imports resolve.",
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(command)
        print("\n# " + payload["note"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
