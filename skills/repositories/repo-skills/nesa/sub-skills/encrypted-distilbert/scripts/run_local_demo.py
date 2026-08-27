#!/usr/bin/env python3
"""Run a promptable Nesa-style encrypted DistilBERT sentiment demo.

The script is standalone: pass either a local model directory or a Hugging Face
model id. It intentionally does not import the original Nesa repository checkout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt is not None:
        return args.prompt
    if args.prompt_file is not None:
        return Path(args.prompt_file).read_text(encoding="utf-8").strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    raise SystemExit("Provide --prompt, --prompt-file, or pipe prompt text on stdin.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run encrypted DistilBERT sentiment inference with a local path or HF model id.")
    parser.add_argument("--model", required=True, help="Local model directory or Hugging Face model id.")
    parser.add_argument("--prompt", help="Prompt text to classify.")
    parser.add_argument("--prompt-file", help="Read prompt text from this UTF-8 file.")
    parser.add_argument("--local-files-only", action="store_true", help="Do not download from Hugging Face; require local/cache files.")
    parser.add_argument("--trust-remote-code", action="store_true", help="Pass trust_remote_code=True. Use only for trusted model repos.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of readable text.")
    args = parser.parse_args()

    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        raise SystemExit(f"Missing runtime dependency: {type(exc).__name__}: {exc}") from exc

    prompt = read_prompt(args)
    model_ref = args.model
    model_path = Path(model_ref).expanduser()
    load_ref = str(model_path.resolve()) if model_path.exists() else model_ref

    tokenizer = AutoTokenizer.from_pretrained(
        load_ref,
        local_files_only=args.local_files_only,
        trust_remote_code=args.trust_remote_code,
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        load_ref,
        local_files_only=args.local_files_only,
        trust_remote_code=args.trust_remote_code,
    )

    encoded = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        logits = model(**encoded).logits
    probs = torch.nn.functional.softmax(logits, dim=-1)[0].tolist()
    id2label = getattr(model.config, "id2label", {}) or {i: str(i) for i in range(len(probs))}
    scores = {str(id2label.get(i, i)): float(prob) for i, prob in enumerate(probs)}
    top_label = max(scores, key=scores.get)

    result = {
        "model": model_ref,
        "prompt_length_chars": len(prompt),
        "encrypted_input_ids": encoded["input_ids"][0].tolist(),
        "scores": scores,
        "top_label": top_label,
        "top_score": scores[top_label],
        "local_files_only": args.local_files_only,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("[Client] Plaintext prompt was tokenized locally.")
        print(f"Prompt characters: {result['prompt_length_chars']}")
        print("\n[Server simulation] Encrypted token IDs visible to the model host:")
        print(result["encrypted_input_ids"])
        print("\n[Client] Classification probabilities from model config labels:")
        for label, score in sorted(scores.items(), key=lambda item: item[1], reverse=True):
            marker = " <- top" if label == top_label else ""
            print(f"{label}: {score:.6f}{marker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
