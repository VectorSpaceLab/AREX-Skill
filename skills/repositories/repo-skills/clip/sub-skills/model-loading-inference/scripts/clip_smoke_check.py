#!/usr/bin/env python3
"""No-download CLIP import, model-list, tokenizer, and API smoke check."""

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


def _stringify_dtype(dtype: Any) -> str:
    return str(dtype).replace("torch.", "")


def run_smoke_check(sample_texts: List[str], context_length: int, truncate: bool) -> Dict[str, Any]:
    try:
        import clip
        import torch
    except Exception as exc:  # pragma: no cover - environment-specific error path
        return {
            "ok": False,
            "stage": "import",
            "error": f"{type(exc).__name__}: {exc}",
        }

    result: Dict[str, Any] = {
        "ok": True,
        "stage": "complete",
        "clip_file": getattr(clip, "__file__", None),
        "torch_version": getattr(torch, "__version__", None),
        "cuda_available": bool(torch.cuda.is_available()),
    }

    try:
        available_models = list(clip.available_models())
        tokens = clip.tokenize(sample_texts, context_length=context_length, truncate=truncate)
        load_signature = str(inspect.signature(clip.load))
        tokenize_signature = str(inspect.signature(clip.tokenize))
        missing_models = [model for model in EXPECTED_MODELS if model not in available_models]
    except Exception as exc:
        result.update(
            {
                "ok": False,
                "stage": "api_probe",
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        return result

    result.update(
        {
            "available_models": available_models,
            "expected_models_present": not missing_models,
            "missing_expected_models": missing_models,
            "token_shape": list(tokens.shape),
            "token_dtype": _stringify_dtype(tokens.dtype),
            "load_signature": load_signature,
            "tokenize_signature": tokenize_signature,
            "downloads_attempted": False,
        }
    )

    expected_shape = [len(sample_texts), context_length]
    if list(tokens.shape) != expected_shape:
        result.update(
            {
                "ok": False,
                "stage": "token_shape",
                "error": f"expected token shape {expected_shape}, got {list(tokens.shape)}",
            }
        )

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate CLIP import, available model names, tokenizer output, and public signatures "
            "without calling clip.load or downloading checkpoints."
        )
    )
    parser.add_argument(
        "--texts",
        default="a diagram,a dog",
        help="Comma-separated sample texts to tokenize. Default: %(default)s",
    )
    parser.add_argument(
        "--context-length",
        type=int,
        default=77,
        help="Tokenizer context length. CLIP models use 77 by default.",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Allow tokenizer truncation for overlong sample text.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sample_texts = [text.strip() for text in args.texts.split(",") if text.strip()]
    if not sample_texts:
        print("At least one non-empty sample text is required.", file=sys.stderr)
        return 2

    result = run_smoke_check(sample_texts, args.context_length, args.truncate)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = "PASS" if result.get("ok") else "FAIL"
        print(f"CLIP smoke check: {status}")
        if result.get("ok"):
            print(f"Models: {', '.join(result['available_models'])}")
            print(f"Token shape: {result['token_shape']} dtype={result['token_dtype']}")
            print("Downloads attempted: false")
        else:
            print(f"Stage: {result.get('stage')}")
            print(f"Error: {result.get('error')}")

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
