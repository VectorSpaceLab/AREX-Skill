#!/usr/bin/env python3
"""Check a FlashRAG Python environment without loading models or launching services.

Example:
  python skills/flashrag/scripts/check_flashrag_environment.py --json
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys
from typing import Any

CORE_IMPORTS = ["flashrag"]
RUNTIME_HINTS = {
    "yaml": "PyYAML is needed for Config YAML files.",
    "numpy": "NumPy is used by datasets, metrics, and pipelines.",
    "torch": "Torch is used by most model-backed components.",
    "transformers": "Transformers is used by HF generators, prompts, retrievers, refiners, and metrics.",
    "tqdm": "tqdm is imported by generator/judger flows.",
    "requests": "requests is used by retrieval and remote/model utilities.",
}
OPTIONAL_HINTS = {
    "faiss": "Dense retrieval indexes need a compatible Faiss CPU/GPU package.",
    "bm25s": "BM25s is the lightweight BM25 backend.",
    "pyserini": "Pyserini BM25 requires Pyserini and Java.",
    "sentence_transformers": "Sentence Transformers supports selected dense retriever workflows.",
    "vllm": "vLLM generation needs a compatible PyTorch/CUDA stack.",
    "openai": "OpenAI generation or judge-style calls need the OpenAI client and credentials.",
    "tiktoken": "OpenAI token counting and token metrics may need tiktoken.",
    "streamlit": "Some UI deployments use Streamlit-style dependencies.",
    "gradio": "FlashRAG UI dependencies may include Gradio.",
    "qwen_vl_utils": "Qwen-VL multimodal generation needs Qwen VL utilities.",
}


def check_import(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {"name": name, "ok": True, "module": getattr(module, "__name__", name)}
    except Exception as exc:  # noqa: BLE001 - diagnostics should report any import failure
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def dist_version() -> dict[str, Any]:
    for dist_name in ("flashrag_dev", "flashrag-dev"):
        try:
            return {"ok": True, "distribution": dist_name, "version": metadata.version(dist_name)}
        except metadata.PackageNotFoundError:
            continue
    return {"ok": False, "error": "No distribution metadata for flashrag_dev or flashrag-dev"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check FlashRAG imports and optional dependency availability.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--include-optional", action="store_true", help="Check optional workflow dependencies too.")
    args = parser.parse_args()

    checks = {
        "python": sys.version.split()[0],
        "distribution": dist_version(),
        "core_imports": [check_import(name) for name in CORE_IMPORTS],
        "runtime_hints": {name: {**check_import(name), "hint": hint} for name, hint in RUNTIME_HINTS.items()},
        "optional_hints": {},
    }
    if args.include_optional:
        checks["optional_hints"] = {name: {**check_import(name), "hint": hint} for name, hint in OPTIONAL_HINTS.items()}

    if args.json:
        print(json.dumps(checks, indent=2, sort_keys=True))
    else:
        print(f"Python: {checks['python']}")
        dist = checks["distribution"]
        print(f"Distribution: {'OK ' + dist['distribution'] + ' ' + dist['version'] if dist['ok'] else 'MISSING - ' + dist['error']}")
        for section in ("core_imports", "runtime_hints", "optional_hints"):
            values = checks[section]
            if isinstance(values, dict):
                iterable = values.values()
            else:
                iterable = values
            for item in iterable:
                status = "OK" if item["ok"] else "MISSING"
                hint = f" - {item.get('hint', '')}" if not item["ok"] and item.get("hint") else ""
                print(f"{item['name']}: {status}{hint}")

    required_ok = checks["distribution"]["ok"] and all(item["ok"] for item in checks["core_imports"])
    return 0 if required_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
