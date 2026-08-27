#!/usr/bin/env python3
"""Safe LaVague context/retriever import and template probe.

Default behavior is intentionally local-only: patch likely network helpers,
import selected LaVague modules, inspect constructor/function signatures, and
report credential-variable presence without printing secret values. The script
never instantiates provider contexts, launches browsers, starts servers, or
calls model/retriever APIs.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import inspect
import os
import sys
import textwrap
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ProbeTarget:
    key: str
    label: str
    dist: str | None
    module: str
    attributes: tuple[str, ...]
    required_env: tuple[str, ...] = ()
    optional_env: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


CONTEXT_TARGETS: dict[str, ProbeTarget] = {
    "openai": ProbeTarget(
        key="openai",
        label="OpenAI context",
        dist="lavague-contexts-openai",
        module="lavague.contexts.openai",
        attributes=("OpenaiContext",),
        required_env=("OPENAI_API_KEY",),
        notes=(
            "Installed signature uses OpenAI for llm, mm_llm, embedding, and extraction_llm.",
            "Pass embedding= explicitly if you need a smaller or non-default embedding model.",
        ),
    ),
    "azure-openai": ProbeTarget(
        key="azure-openai",
        label="Azure OpenAI context",
        dist="lavague-contexts-openai",
        module="lavague.contexts.openai",
        attributes=("AzureOpenaiContext",),
        required_env=(
            "AZURE_OPENAI_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT",
        ),
        optional_env=("AZURE_API_VERSION",),
        notes=(
            "embedding_deployment is required by the installed constructor.",
            "Pass real llm/mm_llm model names explicitly; do not rely on deployment defaults.",
        ),
    ),
    "anthropic": ProbeTarget(
        key="anthropic",
        label="Anthropic context",
        dist="lavague-contexts-anthropic",
        module="lavague.contexts.anthropic",
        attributes=("AnthropicContext",),
        required_env=("ANTHROPIC_API_KEY", "OPENAI_API_KEY"),
        notes=("Default embedding is OpenAI, so OPENAI_API_KEY is required unless you build a custom Context.",),
    ),
    "gemini": ProbeTarget(
        key="gemini",
        label="Gemini context",
        dist="lavague-contexts-gemini",
        module="lavague.contexts.gemini",
        attributes=("GeminiContext",),
        required_env=("GOOGLE_API_KEY",),
        notes=("GeminiContext supplies llm, mm_llm, and embedding from Gemini models.",),
    ),
    "fireworks": ProbeTarget(
        key="fireworks",
        label="Fireworks context",
        dist="lavague-contexts-fireworks",
        module="lavague.contexts.fireworks",
        attributes=("FireworksContext",),
        required_env=("FIREWORKS_API_KEY", "OPENAI_API_KEY"),
        notes=("Default mm_llm is OpenAI gpt-4o, so OPENAI_API_KEY is required unless replaced.",),
    ),
    "cache": ProbeTarget(
        key="cache",
        label="Cache context",
        dist="lavague-contexts-cache",
        module="lavague.contexts.cache",
        attributes=("ContextCache",),
        notes=(
            "Bare ContextCache has no provider-key requirement but writes prompt stores in the working directory by default.",
            "ContextCache.default() and ContextCache.from_context(...) may call fallback providers on cache misses.",
        ),
    ),
}

RETRIEVER_TARGETS: dict[str, ProbeTarget] = {
    "basic": ProbeTarget(
        key="basic",
        label="Basic/core retrievers",
        dist="lavague-core",
        module="lavague.core.retrievers",
        attributes=(
            "InteractiveXPathRetriever",
            "SyntaxicRetriever",
            "XPathedChunkRetriever",
            "get_trivial_retriever",
        ),
        notes=("Driver-backed retrievers are not instantiated by this probe.",),
    ),
    "pipeline": ProbeTarget(
        key="pipeline",
        label="Retriever pipeline",
        dist="lavague-core",
        module="lavague.core.retrievers",
        attributes=(
            "RetrieversPipeline",
            "InteractiveXPathRetriever",
            "FromXPathNodesExpansionRetriever",
            "SemanticRetriever",
            "SyntaxicRetriever",
            "XPathedChunkRetriever",
            "get_default_retriever",
        ),
        notes=("Default pipeline uses the selected embedding for SemanticRetriever.",),
    ),
    "cohere": ProbeTarget(
        key="cohere",
        label="Cohere rerank retriever",
        dist="lavague-retriever-cohere",
        module="lavague.retrievers.cohere",
        attributes=("CohereRetriever",),
        required_env=("COHERE_API_KEY",),
        notes=("Safe mode inspects the signature only; live retrieval would call Cohere rerank.",),
    ),
}


def install_network_guards() -> None:
    """Best-effort guards against import-time network checks/downloads."""
    os.environ.setdefault("LAVAGUE_TELEMETRY", "NONE")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    try:
        import requests  # type: ignore

        def blocked_get(*_args, **_kwargs):
            raise RuntimeError("network disabled by lavague_context_retriever_probe safe mode")

        requests.get = blocked_get  # type: ignore[assignment]
    except Exception:
        pass

    try:
        import nltk  # type: ignore

        def blocked_download(*_args, **_kwargs):
            return False

        nltk.download = blocked_download  # type: ignore[assignment]
    except Exception:
        pass


def selected(keys: Sequence[str], value: str) -> list[str]:
    if value == "all":
        return list(keys)
    return [value]


def env_status(names: Iterable[str]) -> list[str]:
    lines = []
    for name in names:
        state = "set" if os.getenv(name) else "missing"
        lines.append(f"    - {name}: {state}")
    return lines


def dist_status(dist_name: str | None) -> str:
    if not dist_name:
        return "not checked"
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return "not installed"
    except Exception as exc:  # pragma: no cover - diagnostic fallback
        return f"unknown ({exc.__class__.__name__}: {exc})"


def safe_signature(obj) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # pragma: no cover - diagnostic fallback
        return f"<signature unavailable: {exc.__class__.__name__}: {exc}>"


def probe_target(target: ProbeTarget, show_env: bool = True) -> bool:
    """Print one target report. Return True if imports/signatures resolved."""
    print(f"\n## {target.label} ({target.key})")
    if target.dist:
        print(f"  distribution {target.dist}: {dist_status(target.dist)}")

    ok = True
    try:
        module = importlib.import_module(target.module)
        print(f"  import {target.module}: ok")
    except Exception as exc:
        ok = False
        print(f"  import {target.module}: MISSING/FAILED ({exc.__class__.__name__}: {exc})")
        module = None

    if module is not None:
        for attr in target.attributes:
            try:
                obj = getattr(module, attr)
                print(f"  signature {attr}{safe_signature(obj)}")
            except Exception as exc:
                ok = False
                print(f"  attribute {attr}: MISSING/FAILED ({exc.__class__.__name__}: {exc})")

    if show_env and (target.required_env or target.optional_env):
        if target.required_env:
            print("  required env vars:")
            print("\n".join(env_status(target.required_env)))
        if target.optional_env:
            print("  optional env vars:")
            print("\n".join(env_status(target.optional_env)))
    elif show_env:
        print("  required env vars: none for import/signature checks")

    for note in target.notes:
        print(f"  note: {note}")

    return ok


def context_template(context_key: str) -> str:
    templates = {
        "openai": """
            from lavague.contexts.openai import OpenaiContext

            context = OpenaiContext(
                llm="gpt-4o-mini",
                mm_llm="gpt-4o-mini",
                embedding="text-embedding-3-small",
            )
        """,
        "azure-openai": """
            from lavague.contexts.openai import AzureOpenaiContext

            context = AzureOpenaiContext(
                endpoint="<AZURE_OPENAI_ENDPOINT>",
                deployment="<chat-deployment>",
                embedding_deployment="<embedding-deployment>",
                llm="gpt-4o",
                mm_llm="gpt-4o",
                embedding="text-embedding-3-small",
            )
        """,
        "anthropic": """
            from lavague.contexts.anthropic import AnthropicContext

            context = AnthropicContext(
                llm="claude-3-5-sonnet-20240620",
                mm_llm="claude-3-5-sonnet-20240620",
                embedding="text-embedding-3-small",  # OpenAI embedding by default
            )
        """,
        "gemini": """
            from lavague.contexts.gemini import GeminiContext

            context = GeminiContext(
                llm="models/gemini-1.5-flash-latest",
                mm_llm="models/gemini-1.5-pro-latest",
                embedding="models/text-embedding-004",
            )
        """,
        "fireworks": """
            from lavague.contexts.fireworks import FireworksContext

            context = FireworksContext(
                llm="accounts/fireworks/models/llama-v3p1-70b-instruct",
                mm_llm="gpt-4o",  # OpenAI multimodal by default
                embedding="nomic-ai/nomic-embed-text-v1.5",
            )
        """,
        "cache": """
            from lavague.contexts.cache import ContextCache

            context = ContextCache()  # No provider fallback; cache misses return placeholders/mocks.
            # Or: context = ContextCache.from_context(provider_context)
        """,
    }
    return textwrap.dedent(templates[context_key]).strip()


def retriever_template(retriever_key: str) -> str:
    templates = {
        "basic": """
            from lavague.core.retrievers import InteractiveXPathRetriever, SyntaxicRetriever

            retriever = SyntaxicRetriever(top_k=5)  # no provider embedding required
            # For action use, a driver-backed first stage is usually needed:
            # retriever = InteractiveXPathRetriever(driver)
        """,
        "pipeline": """
            from lavague.core.retrievers import (
                InteractiveXPathRetriever,
                SyntaxicRetriever,
                XPathedChunkRetriever,
                RetrieversPipeline,
            )

            retriever = RetrieversPipeline(
                InteractiveXPathRetriever(driver),
                SyntaxicRetriever(top_k=5),
                XPathedChunkRetriever(),
            )
            action_engine = ActionEngine.from_context(
                context=context,
                driver=driver,
                retriever=retriever,
            )
        """,
        "cohere": """
            import os
            from lavague.retrievers.cohere import CohereRetriever

            retriever = CohereRetriever(
                cohere_model="rerank-english-v3.0",
                cohere_api_key=os.environ.get("COHERE_API_KEY"),
                top_k=5,
            )
            # Retrieval performs Cohere API calls; do not use unless provider calls are approved.
        """,
    }
    return textwrap.dedent(templates[retriever_key]).strip()


def print_templates(context_keys: Sequence[str], retriever_keys: Sequence[str]) -> None:
    print("\n# Templates (not executed)")
    for key in context_keys:
        print(f"\n## Context template: {key}\n")
        print(context_template(key))
    for key in retriever_keys:
        print(f"\n## Retriever template: {key}\n")
        print(retriever_template(key))


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely inspect LaVague provider context and retriever imports, "
            "signatures, and credential-variable presence without live calls."
        )
    )
    parser.add_argument(
        "--context",
        choices=(*CONTEXT_TARGETS.keys(), "all"),
        default="all",
        help="Context family to inspect (default: all).",
    )
    parser.add_argument(
        "--retriever",
        choices=(*RETRIEVER_TARGETS.keys(), "all"),
        default="all",
        help="Retriever family to inspect (default: all).",
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Show credential environment-variable presence. Env status is shown in the default report too.",
    )
    parser.add_argument(
        "--print-template",
        action="store_true",
        help="Print safe, non-executed construction templates for the selected context/retriever.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    install_network_guards()

    context_keys = selected(tuple(CONTEXT_TARGETS.keys()), args.context)
    retriever_keys = selected(tuple(RETRIEVER_TARGETS.keys()), args.retriever)

    print("# LaVague context/retriever safe probe")
    print("safe_mode: imports/signatures/env only; no provider calls; no browser launch")
    print("network_guards: requests.get and nltk.download patched best-effort during imports")

    all_ok = True
    for key in context_keys:
        all_ok = probe_target(CONTEXT_TARGETS[key], show_env=True) and all_ok
    for key in retriever_keys:
        all_ok = probe_target(RETRIEVER_TARGETS[key], show_env=True) and all_ok

    if args.print_template:
        print_templates(context_keys, retriever_keys)

    print("\n# Summary")
    print("imports_and_signatures:", "ok" if all_ok else "one_or_more_failed")
    print("missing credential variables are informational unless you intend to instantiate that provider")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
