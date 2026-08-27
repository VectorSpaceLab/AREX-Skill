#!/usr/bin/env python3
"""Check core sentence-transformers imports and API availability."""

from __future__ import annotations

import argparse
import inspect
import json


def main() -> int:
    parser = argparse.ArgumentParser(description="Check core sentence-transformers package imports and public API signatures.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of readable text.")
    args = parser.parse_args()

    import sentence_transformers
    from sentence_transformers import CrossEncoder, SentenceTransformer, SparseEncoder
    from sentence_transformers.backend import export_dynamic_quantized_onnx_model, export_optimized_onnx_model
    from sentence_transformers.util import cos_sim, semantic_search

    result = {
        "version": getattr(sentence_transformers, "__version__", "unknown"),
        "classes": [SentenceTransformer.__name__, CrossEncoder.__name__, SparseEncoder.__name__],
        "signatures": {
            "SentenceTransformer.encode": str(inspect.signature(SentenceTransformer.encode)),
            "CrossEncoder.rank": str(inspect.signature(CrossEncoder.rank)),
            "SparseEncoder.encode": str(inspect.signature(SparseEncoder.encode)),
            "semantic_search": str(inspect.signature(semantic_search)),
            "cos_sim": str(inspect.signature(cos_sim)),
            "export_optimized_onnx_model": str(inspect.signature(export_optimized_onnx_model)),
            "export_dynamic_quantized_onnx_model": str(inspect.signature(export_dynamic_quantized_onnx_model)),
        },
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"sentence-transformers version: {result['version']}")
        print("classes:", ", ".join(result["classes"]))
        for name, signature in result["signatures"].items():
            print(f"{name}{signature}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
