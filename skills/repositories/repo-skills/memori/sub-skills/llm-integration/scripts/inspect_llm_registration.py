#!/usr/bin/env python3
"""Inspect the installed Memori LLM registration surface without calling a provider."""

from __future__ import annotations

import inspect
import json
from importlib import util


def _has(module_name: str) -> bool:
    return util.find_spec(module_name) is not None


def main() -> None:
    from memori import LlmRegistry

    payload = {
        "register_signature": str(inspect.signature(LlmRegistry.register)),
        "optional_sdks": {
            "openai": _has("openai"),
            "anthropic": _has("anthropic"),
            "google.genai": _has("google.genai"),
            "langchain": _has("langchain"),
            "langchain_openai": _has("langchain_openai"),
            "agno": _has("agno"),
            "pydantic_ai": _has("pydantic_ai"),
            "litellm": _has("litellm"),
            "xai_sdk": _has("xai_sdk"),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
