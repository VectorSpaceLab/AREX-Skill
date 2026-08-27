#!/usr/bin/env python3
"""Safe optional dependency probe for Chonkie embeddings/genies.

Default behavior is import-spec and distribution metadata inspection only. It does
not instantiate provider clients, load model weights, download models, or call
external APIs. Use --instantiate-safe for a small no-network contract check that
only constructs local dummy classes and AutoEmbeddings' empty factory object.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import importlib.util as importutil
import json
import os
import platform
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ModuleStatus:
    module: str
    installed: bool
    error: str | None = None


@dataclass
class DistributionStatus:
    distribution: str
    version: str | None
    installed: bool


MODULES: dict[str, list[str]] = {
    "base": ["chonkie", "chonkie_core", "numpy", "tokie", "tenacity", "httpx"],
    "semantic/model2vec": ["model2vec", "tokenizers"],
    "sentence-transformers/late": ["sentence_transformers", "tokenizers", "accelerate"],
    "neural": ["transformers", "torch"],
    "catsu-provider-embeddings": ["catsu"],
    "litellm-embeddings": ["litellm", "tiktoken", "tokenizers"],
    "openai-genie-family": ["openai", "pydantic"],
    "azure-openai": ["openai", "azure.identity", "tiktoken", "pydantic"],
    "gemini": ["google.genai", "pydantic"],
    "groq-genie": ["groq", "pydantic"],
    "cerebras-genie": ["cerebras.cloud.sdk", "pydantic"],
    "legacy-provider-sdks": ["cohere", "voyageai"],
}

DISTRIBUTIONS = [
    "chonkie",
    "chonkie-core",
    "numpy",
    "tokie",
    "tenacity",
    "httpx",
    "model2vec",
    "tokenizers",
    "sentence-transformers",
    "accelerate",
    "transformers",
    "torch",
    "catsu",
    "litellm",
    "tiktoken",
    "openai",
    "azure-identity",
    "google-genai",
    "pydantic",
    "groq",
    "cerebras-cloud-sdk",
    "cohere",
    "voyageai",
]

CREDENTIAL_ENV_VARS = [
    "OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "COHERE_API_KEY",
    "JINA_API_KEY",
    "VOYAGE_API_KEY",
    "VOYAGEAI_API_KEY",
    "GROQ_API_KEY",
    "CEREBRAS_API_KEY",
    "CHONKIE_API_KEY",
]


def safe_find_spec(module: str) -> ModuleStatus:
    try:
        found = importutil.find_spec(module) is not None
        return ModuleStatus(module=module, installed=found)
    except Exception as exc:  # parent namespace import errors can surface here
        return ModuleStatus(module=module, installed=False, error=f"{type(exc).__name__}: {exc}")


def distribution_status(name: str) -> DistributionStatus:
    try:
        return DistributionStatus(distribution=name, version=metadata.version(name), installed=True)
    except metadata.PackageNotFoundError:
        return DistributionStatus(distribution=name, version=None, installed=False)


def summarize_groups(module_status: dict[str, ModuleStatus]) -> dict[str, dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for group, modules in MODULES.items():
        missing = [m for m in modules if not module_status[m].installed]
        errors = {m: module_status[m].error for m in modules if module_status[m].error}
        groups[group] = {
            "modules": modules,
            "looks_installed": not missing,
            "missing_modules": missing,
            "spec_errors": errors,
        }
    return groups


def credential_presence() -> dict[str, bool]:
    # Report presence only; never print secret values.
    return {name: bool(os.environ.get(name)) for name in CREDENTIAL_ENV_VARS}


def safe_instantiation_checks() -> dict[str, Any]:
    """Run no-network constructor/contract checks only.

    This intentionally avoids Model2Vec, SentenceTransformer, provider embeddings,
    provider genies, SemanticChunker, LateChunker, NeuralChunker, and the default
    SlumberChunker because those can require model loads, credentials, or network.
    """

    checks: dict[str, Any] = {}
    if safe_find_spec("chonkie").installed is False:
        checks["status"] = "skipped"
        checks["reason"] = "The chonkie import package is not visible to this Python interpreter."
        return checks

    try:
        import numpy as np
        from chonkie.embeddings import AutoEmbeddings
        from chonkie.embeddings.base import BaseEmbeddings
        from chonkie.genie import BaseGenie

        class TinyTokenizer:
            def count_tokens(self, text: str) -> int:
                return len(text.split()) if text else 0

            def count_tokens_batch(self, texts: list[str]) -> list[int]:
                return [self.count_tokens(text) for text in texts]

        class ZeroEmbeddings(BaseEmbeddings):
            @property
            def dimension(self) -> int:
                return 1

            def embed(self, text: str) -> np.ndarray:
                return np.zeros(1, dtype=np.float32)

            def get_tokenizer(self) -> TinyTokenizer:
                return TinyTokenizer()

        class FixedGenie(BaseGenie):
            def generate(self, prompt: str) -> str:
                return "1"

        auto = AutoEmbeddings()
        emb = ZeroEmbeddings()
        genie = FixedGenie()
        checks["AutoEmbeddings_constructor"] = type(auto).__name__
        checks["BaseEmbeddings_dummy_dimension"] = emb.dimension
        checks["BaseEmbeddings_dummy_batch_len"] = len(emb.embed_batch(["alpha", "beta"]))
        checks["BaseEmbeddings_dummy_call_shape"] = list(emb("alpha").shape)
        checks["BaseGenie_dummy_generate"] = genie.generate("split?")
        checks["BaseGenie_dummy_batch"] = genie.generate_batch(["a", "b"])
        checks["status"] = "ok"
    except Exception as exc:
        checks["status"] = "failed"
        checks["error"] = f"{type(exc).__name__}: {exc}"
    return checks


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    all_modules = sorted({module for modules in MODULES.values() for module in modules})
    module_status = {module: safe_find_spec(module) for module in all_modules}
    dist_status = {dist: distribution_status(dist) for dist in DISTRIBUTIONS}

    report: dict[str, Any] = {
        "probe": "chonkie embeddings/generative optional dependency probe",
        "safe_no_network_default": True,
        "python": {
            "version": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "module_groups": summarize_groups(module_status),
        "modules": {name: asdict(status) for name, status in module_status.items()},
        "distributions": {name: asdict(status) for name, status in dist_status.items()},
        "credential_env_present": credential_presence(),
        "notes": [
            "Presence of a module does not prove model weights, credentials, quotas, endpoints, or live API access.",
            "Provider embedding wrappers for OpenAI/Gemini/Jina/Cohere/Voyage use Catsu in Chonkie 1.7.0.",
            "Unknown LiteLLM embedding dimensions may trigger a live test embedding unless dimension is supplied by the caller.",
            "CHONKIE_API_KEY is for Chonkie Cloud/API, not third-party embedding or genie providers.",
        ],
    }
    if args.instantiate_safe:
        report["safe_instantiation_checks"] = safe_instantiation_checks()
    return report


def print_text(report: dict[str, Any]) -> None:
    print(report["probe"])
    print(f"Python: {report['python']['version']} ({report['python']['implementation']})")
    print("\nOptional module groups:")
    for group, info in report["module_groups"].items():
        marker = "ok" if info["looks_installed"] else "missing"
        missing = ", ".join(info["missing_modules"]) if info["missing_modules"] else "none"
        print(f"- {group}: {marker}; missing: {missing}")
        if info["spec_errors"]:
            for module, error in info["spec_errors"].items():
                print(f"  spec error {module}: {error}")

    print("\nInstalled distributions:")
    for name, info in report["distributions"].items():
        if info["installed"]:
            print(f"- {name}: {info['version']}")

    print("\nCredential environment variables present (values hidden):")
    for name, present in report["credential_env_present"].items():
        print(f"- {name}: {'set' if present else 'not set'}")

    if "safe_instantiation_checks" in report:
        print("\nSafe no-network instantiation checks:")
        for name, value in report["safe_instantiation_checks"].items():
            print(f"- {name}: {value}")

    print("\nNotes:")
    for note in report["notes"]:
        print(f"- {note}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect Chonkie embedding/genie optional dependencies without network calls. "
            "By default this only checks import specs, package metadata, and credential variable presence."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text report.",
    )
    parser.add_argument(
        "--instantiate-safe",
        action="store_true",
        help=(
            "Also run small no-network checks using AutoEmbeddings' empty constructor and local "
            "dummy BaseEmbeddings/BaseGenie subclasses. Does not load real models or providers."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
