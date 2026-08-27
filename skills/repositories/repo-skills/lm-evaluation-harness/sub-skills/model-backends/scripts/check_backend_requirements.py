#!/usr/bin/env python3
"""Check LM Evaluation Harness backend registry aliases and likely extras.

This script is safe for lightweight diagnostics: it imports the registry and
optionally materializes selected aliases, but it never downloads models or starts
an evaluation run.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import sys
from dataclasses import dataclass
from typing import Iterable


KNOWN_EXTRAS = {
    "api": ["requests", "aiohttp", "tenacity", "tqdm", "tiktoken"],
    "hf": ["transformers", "torch", "accelerate", "peft"],
    "vllm": ["vllm"],
    "gptq": ["auto_gptq"],
    "gptqmodel": ["gptqmodel"],
    "ipex": ["optimum.intel"],
    "ibm_watsonx_ai": ["ibm_watsonx_ai", "dotenv"],
    "litellm": ["litellm", "aiohttp", "requests", "tenacity", "tqdm"],
    "optimum": ["optimum", "openvino"],
    "habana": ["optimum.habana"],
}

BACKEND_EXTRAS = {
    "anthropic-chat": ["api"],
    "anthropic-chat-completions": ["api"],
    "anthropic-completions": ["api"],
    "ggml": [],
    "gguf": [],
    "habana": ["habana"],
    "hf": ["hf"],
    "hf-audiolm-qwen": ["hf"],
    "hf-auto": ["hf"],
    "hf-mistral3": ["hf"],
    "hf-multimodal": ["hf"],
    "huggingface": ["hf"],
    "ipex": ["ipex"],
    "litellm": ["litellm"],
    "litellm-chat": ["litellm"],
    "litellm-chat-completions": ["litellm"],
    "local-chat-completions": ["api"],
    "local-completions": ["api"],
    "openai-chat-completions": ["api"],
    "openai-completions": ["api"],
    "openvino": ["optimum"],
    "sglang": [],
    "sglang-generate": ["api"],
    "textsynth": ["api"],
    "vllm": ["vllm"],
    "vllm-vlm": ["vllm"],
    "watsonx_llm": ["ibm_watsonx_ai"],
    "winml": [],
}


@dataclass
class BackendReport:
    backend: str
    registered: bool
    extras: list[str]
    missing_packages: list[str]
    materialized: bool | None
    target: str | None
    error: str | None


def package_available(name: str) -> bool:
    root = name.split(".", 1)[0]
    return importlib.util.find_spec(root) is not None


def missing_for_extras(extras: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for extra in extras:
        for package in KNOWN_EXTRAS.get(extra, []):
            if not package_available(package):
                missing.append(package)
    return sorted(set(missing))


def load_registry():
    try:
        import lm_eval.models  # noqa: F401 - populates lazy model registry
        from lm_eval.api.registry import MODEL_REGISTRY, get_model
    except ModuleNotFoundError as exc:
        if exc.name == "lm_eval":
            raise RuntimeError(
                "Could not import lm_eval. Run this script in an environment where "
                "the lm_eval package is installed, or from a checkout with the "
                "repository root on PYTHONPATH."
            ) from exc
        raise

    return MODEL_REGISTRY, get_model


def target_for(registry, backend: str) -> str | None:
    try:
        value = dict(registry.items())[backend]
    except Exception:
        return None
    if isinstance(value, str):
        return value
    return f"{value.__module__}:{getattr(value, '__name__', type(value).__name__)}"


def inspect_backend(backend: str, materialize: bool) -> BackendReport:
    registry, get_model = load_registry()
    registered = backend in registry
    extras = BACKEND_EXTRAS.get(backend, [])
    missing = missing_for_extras(extras)
    target = target_for(registry, backend) if registered else None
    materialized = None
    error = None
    if registered and materialize:
        try:
            model_class = get_model(backend)
            materialized = True
            target = f"{model_class.__module__}:{model_class.__name__}"
        except Exception as exc:  # noqa: BLE001 - diagnostic tool reports all failures
            materialized = False
            error = f"{type(exc).__name__}: {exc}"
    return BackendReport(
        backend=backend,
        registered=registered,
        extras=extras,
        missing_packages=missing,
        materialized=materialized,
        target=target,
        error=error,
    )


def list_registered() -> list[str]:
    registry, _ = load_registry()
    return sorted(registry.keys())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check lm_eval backend aliases, expected extras, and optional imports."
    )
    parser.add_argument(
        "--backend",
        action="append",
        default=[],
        help="Backend alias to inspect. May be passed multiple times.",
    )
    parser.add_argument(
        "--materialize",
        action="store_true",
        help="Call lm_eval.api.registry.get_model for selected aliases to import concrete classes.",
    )
    parser.add_argument(
        "--list-known",
        action="store_true",
        help="List known backend-to-extra mappings bundled with this script.",
    )
    parser.add_argument(
        "--list-registered",
        action="store_true",
        help="List model aliases currently registered by lm_eval.models.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    args = parser.parse_args(argv)

    payload: dict[str, object] = {}
    if args.list_known:
        payload["known_extras"] = KNOWN_EXTRAS
        payload["backend_extras"] = BACKEND_EXTRAS
    try:
        if args.list_registered:
            payload["registered"] = list_registered()
        if args.backend:
            payload["reports"] = [
                inspect_backend(backend, args.materialize).__dict__
                for backend in args.backend
            ]
    except RuntimeError as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1

    if not payload:
        parser.print_help()
        return 0

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if "known_extras" in payload:
            print("Known extras:")
            for extra, packages in sorted(KNOWN_EXTRAS.items()):
                print(f"  {extra}: {', '.join(packages) or '(no package map)'}")
            print("\nKnown backend mappings:")
            for backend, extras in sorted(BACKEND_EXTRAS.items()):
                print(f"  {backend}: {', '.join(extras) or '(external/base/unknown)'}")
        if "registered" in payload:
            print("Registered aliases:")
            for alias in payload["registered"]:
                print(f"  {alias}")
        if "reports" in payload:
            print("Backend reports:")
            for report in payload["reports"]:
                print(f"  {report['backend']}:")
                print(f"    registered: {report['registered']}")
                print(f"    target: {report['target']}")
                print(f"    extras: {', '.join(report['extras']) or '(none mapped)'}")
                print(
                    f"    missing_packages: {', '.join(report['missing_packages']) or '(none detected)'}"
                )
                print(f"    materialized: {report['materialized']}")
                if report["error"]:
                    print(f"    error: {report['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
