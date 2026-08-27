#!/usr/bin/env python3
"""Validate a CLIP runtime without downloading model checkpoints."""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from typing import Any, Dict, List

EXPECTED_MODELS = [
    "RN50",
    "RN101",
    "RN50x4",
    "RN50x16",
    "RN50x64",
    "ViT-B/32",
    "ViT-B/16",
    "ViT-L/14",
    "ViT-L/14@336px",
]


def split_texts(value: str) -> List[str]:
    return [text.strip() for text in value.split(",") if text.strip()]


def validate(texts: List[str], context_length: int, truncate: bool) -> Dict[str, Any]:
    result: Dict[str, Any] = {"downloads_attempted": False}
    try:
        import clip
        import torch
    except Exception as exc:  # pragma: no cover - environment-specific
        result.update({"ok": False, "stage": "import", "error": f"{type(exc).__name__}: {exc}"})
        return result

    try:
        models = list(clip.available_models())
        tokens = clip.tokenize(texts, context_length=context_length, truncate=truncate)
        missing = [model for model in EXPECTED_MODELS if model not in models]
        result.update(
            {
                "ok": not missing and list(tokens.shape) == [len(texts), context_length],
                "stage": "complete",
                "available_models": models,
                "missing_expected_models": missing,
                "token_shape": list(tokens.shape),
                "token_dtype": str(tokens.dtype).replace("torch.", ""),
                "load_signature": str(inspect.signature(clip.load)),
                "tokenize_signature": str(inspect.signature(clip.tokenize)),
                "torch_version": getattr(torch, "__version__", None),
                "cuda_available": bool(torch.cuda.is_available()),
            }
        )
    except Exception as exc:
        result.update({"ok": False, "stage": "api_probe", "error": f"{type(exc).__name__}: {exc}"})
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="No-download CLIP import/API/tokenizer validator.")
    parser.add_argument("--texts", default="a diagram,a dog", help="Comma-separated texts to tokenize.")
    parser.add_argument("--context-length", type=int, default=77, help="Tokenizer context length; released CLIP models use 77.")
    parser.add_argument("--truncate", action="store_true", help="Allow tokenizer truncation for overlong sample text.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    texts = split_texts(args.texts)
    if not texts:
        print("At least one non-empty text is required.", file=sys.stderr)
        return 2

    result = validate(texts, args.context_length, args.truncate)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result.get("ok"):
        print("CLIP runtime check: PASS")
        print("Models: " + ", ".join(result["available_models"]))
        print(f"Token shape: {result['token_shape']} dtype={result['token_dtype']}")
        print("Downloads attempted: false")
    else:
        print("CLIP runtime check: FAIL")
        print(f"Stage: {result.get('stage')}")
        print(f"Error: {result.get('error')}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
