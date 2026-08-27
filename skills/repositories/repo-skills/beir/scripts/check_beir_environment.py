#!/usr/bin/env python3
"""Inspect BEIR core and optional runtime dependencies without external services.

Example:
    python scripts/check_beir_environment.py
    python scripts/check_beir_environment.py --json
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import importlib.util
import json
import os
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def package_version(dist_name: str) -> str | None:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None


def module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def check_core_imports() -> list[Check]:
    modules = [
        "beir",
        "beir.datasets.data_loader",
        "beir.retrieval.evaluation",
        "beir.retrieval.search.dense.exact_search",
        "beir.reranking.rerank",
        "beir.generation.generate",
        "beir.retrieval.train",
    ]
    checks: list[Check] = []
    for module_name in modules:
        try:
            __import__(module_name)
            checks.append(Check(module_name, True, "import ok"))
        except Exception as exc:  # noqa: BLE001 - diagnostic script should report any import failure
            checks.append(Check(module_name, False, f"{type(exc).__name__}: {exc}"))
    return checks


def check_optional() -> list[Check]:
    optional_modules = {
        "faiss": "FAISS dense index workflows",
        "elasticsearch": "BM25 Python client; still requires a running service",
        "cohere": "Cohere API embeddings; still requires credentials/network",
        "voyageai": "Voyage API embeddings; still requires credentials/network",
        "vllm": "VLLM embedding workflows; usually GPU/model-cache heavy",
        "peft": "LoRA/PEFT workflows",
        "llm2vec": "LLM2Vec workflows",
        "nltk": "TILDE generation helpers and stopword resources",
    }
    checks = [
        Check(module, module_available(module), purpose)
        for module, purpose in optional_modules.items()
    ]

    try:
        import torch

        cuda_available = bool(torch.cuda.is_available())
        checks.append(Check("torch", True, f"version={torch.__version__}; cuda_available={cuda_available}"))
    except Exception as exc:  # noqa: BLE001
        checks.append(Check("torch", False, f"{type(exc).__name__}: {exc}"))

    for env_var in ["COHERE_API_KEY", "VOYAGE_API_KEY"]:
        checks.append(Check(env_var, bool(os.environ.get(env_var)), "environment variable present"))

    return checks


def build_report() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "distributions": {
            name: package_version(name)
            for name in [
                "beir",
                "sentence-transformers",
                "transformers",
                "torch",
                "datasets",
                "pytrec-eval-terrier",
                "elasticsearch",
            ]
        },
        "core": [asdict(check) for check in check_core_imports()],
        "optional": [asdict(check) for check in check_optional()],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect BEIR core and optional dependencies without network calls.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print("Distributions:")
        for name, version in report["distributions"].items():
            print(f"  {name}: {version or 'not installed'}")
        print("Core imports:")
        for check in report["core"]:
            status = "ok" if check["ok"] else "missing/error"
            print(f"  {status:13} {check['name']} - {check['detail']}")
        print("Optional signals:")
        for check in report["optional"]:
            status = "ok" if check["ok"] else "not detected"
            print(f"  {status:13} {check['name']} - {check['detail']}")

    return 0 if all(check["ok"] for check in report["core"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
