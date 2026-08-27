#!/usr/bin/env python3
"""Preview Nesa/text-generation-webui Hugging Face model naming without downloading."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

BASE = "https://huggingface.co"
BRANCH_RE = re.compile(r"^[a-zA-Z0-9._-]+$")


def sanitize_model_and_branch(model: str, branch: str | None) -> tuple[str, str]:
    model = model.strip()
    if model.endswith("/"):
        model = model[:-1]
    if model.startswith(BASE + "/"):
        model = model[len(BASE) + 1 :]
    parts = model.split(":")
    model = parts[0]
    if len(parts) > 1:
        branch = parts[1]
    branch = branch or "main"
    if not BRANCH_RE.match(branch):
        raise ValueError("Invalid branch name. Use only letters, digits, period, underscore, and dash.")
    if "/" not in model:
        raise ValueError("Model should usually be a Hugging Face repo id like namespace/model.")
    return model, branch


def output_folder(model: str, branch: str, *, is_lora: bool, is_llamacpp: bool, model_dir: str | None) -> str:
    base = Path(model_dir or ("loras" if is_lora else "models"))
    if is_llamacpp:
        return str(base)
    folder = "_".join(model.split("/")[-2:])
    if branch != "main":
        folder += f"_{branch}"
    return str(base / folder)


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview model/branch normalization and output folder; no network calls.")
    parser.add_argument("model", help="Hugging Face repo id, URL, or repo:branch.")
    parser.add_argument("--branch", help="Branch override unless model includes ':branch'.")
    parser.add_argument("--model-dir", help="Base output directory for models.")
    parser.add_argument("--lora", action="store_true", help="Plan as a LoRA output.")
    parser.add_argument("--llamacpp", action="store_true", help="Plan as a direct GGUF/llama.cpp output.")
    parser.add_argument("--specific-file", help="Record a specific requested file name in output.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    model, branch = sanitize_model_and_branch(args.model, args.branch)
    result = {
        "input_model": args.model,
        "normalized_model": model,
        "branch": branch,
        "specific_file": args.specific_file,
        "output_folder": output_folder(model, branch, is_lora=args.lora, is_llamacpp=args.llamacpp, model_dir=args.model_dir),
        "network_calls": False,
        "download_started": False,
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
