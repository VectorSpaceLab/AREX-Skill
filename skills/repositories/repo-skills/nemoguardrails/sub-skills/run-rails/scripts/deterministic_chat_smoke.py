#!/usr/bin/env python3
"""Deterministic no-provider chat smoke for NeMo Guardrails.

This helper exercises two public runtime surfaces without contacting live
providers:

- the `Guardrails` wrapper falling back to `LLMRails` when a custom `llm` is
  supplied, and
- the public `TestChat` harness streaming a scripted response.

It also patches the default embedding search path with a local deterministic
implementation so the smoke never tries to download FastEmbed or Hugging Face
assets.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import math
import re
import warnings
from contextlib import contextmanager
from typing import Any, Iterator, Optional


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _vectorize(text: str) -> list[float]:
    vector = [0.0] * 64
    tokens = _tokens(text)

    if not tokens:
        vector[0] = 1.0
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        vector[digest[0] % len(vector)] += 1.0 if digest[1] % 2 == 0 else -1.0

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        vector[0] = 1.0
        return vector

    return [value / norm for value in vector]


def _assistant_text(result: Any) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        content = result.get("content", "")
        return content if isinstance(content, str) else str(content)
    response = getattr(result, "response", None)
    if isinstance(response, str):
        return response
    if isinstance(response, list) and response:
        last = response[-1]
        if isinstance(last, dict):
            content = last.get("content", "")
            return content if isinstance(content, str) else str(content)
    return str(result)


async def _collect_stream_chunks(stream) -> list[str]:
    chunks: list[str] = []
    async for chunk in stream:
        chunks.append(str(chunk))
    return chunks


@contextmanager
def _patch_deterministic_embeddings() -> Iterator[None]:
    from nemoguardrails.embeddings.index import EmbeddingsIndex, IndexItem
    from nemoguardrails.rails.llm.config import EmbeddingsCacheConfig
    from nemoguardrails.rails.llm.llmrails import LLMRails

    class DeterministicEmbeddingSearchProvider(EmbeddingsIndex):
        def __init__(self, search_threshold: float = float("inf"), **kwargs):
            self.items: list[IndexItem] = []
            self.embeddings: list[list[float]] = []
            self.search_threshold = search_threshold
            self._cache_config = EmbeddingsCacheConfig()

        @property
        def embedding_size(self):
            return 64

        @property
        def cache_config(self):
            return self._cache_config

        async def _get_embeddings(self, texts: list[str]):
            return [_vectorize(text) for text in texts]

        async def add_item(self, item: IndexItem):
            self.items.append(item)
            self.embeddings.append(_vectorize(item.text))

        async def add_items(self, items: list[IndexItem]):
            self.items.extend(items)
            self.embeddings.extend(_vectorize(item.text) for item in items)

        async def search(self, text: str, max_results: int = 20, threshold: Optional[float] = None):
            if threshold is None:
                threshold = self.search_threshold

            text_embedding = _vectorize(text)
            scored_items = []

            for index, item in enumerate(self.items):
                score = sum(a * b for a, b in zip(text_embedding, self.embeddings[index], strict=True))
                if threshold == float("inf") or score >= threshold:
                    scored_items.append((score, index, item))

            scored_items.sort(key=lambda result: (-result[0], result[1]))
            return [item for _, _, item in scored_items[:max_results]]

    original = LLMRails._get_embeddings_search_provider_instance

    def patched(self, esp_config=None):
        if esp_config is None or getattr(esp_config, "name", None) == "default":
            parameters = getattr(esp_config, "parameters", {}) if esp_config is not None else {}
            return DeterministicEmbeddingSearchProvider(**parameters)
        return original(self, esp_config)

    LLMRails._get_embeddings_search_provider_instance = patched
    try:
        yield
    finally:
        LLMRails._get_embeddings_search_provider_instance = original


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    return parser


def run_smoke() -> dict[str, Any]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with _patch_deterministic_embeddings():
            logger = logging.getLogger("nemoguardrails.guardrails.guardrails")
            previous_level = logger.level
            logger.setLevel(logging.ERROR)
            try:
                from nemoguardrails import Guardrails, RailsConfig
                from nemoguardrails.testing import FakeLLMModel, TestChat

                config = RailsConfig.from_content(config={"models": []})

                guardrails = Guardrails(
                    config=config,
                    llm=FakeLLMModel(responses=["Guardrails hello", "unused"]),
                    use_iorails=True,
                    require_iorails=False,
                )
                generated = guardrails.generate(messages=[{"role": "user", "content": "Hello"}])
                generated_text = _assistant_text(generated)
                if generated_text != "Guardrails hello":
                    raise RuntimeError(f"Unexpected Guardrails output: {generated_text!r}")

                if guardrails.use_iorails_engine:
                    raise RuntimeError("Expected Guardrails to fall back to LLMRails for the fake-LLM smoke.")

                stream_chat = TestChat(config, llm_completions=["Streaming smoke output", "unused"], streaming=True)

                async def _run_stream() -> list[str]:
                    return await _collect_stream_chunks(
                        stream_chat.app.stream_async(messages=[{"role": "user", "content": "Hello"}])
                    )

                chunks = asyncio.run(_run_stream())
                stream_text = "".join(chunks)
                if stream_text != "Streaming smoke output":
                    raise RuntimeError(f"Unexpected streaming output: {stream_text!r}")

                return {
                    "guardrails": {
                        "engine": guardrails.rails_engine.__class__.__name__,
                        "use_iorails_engine": guardrails.use_iorails_engine,
                        "content": generated_text,
                    },
                    "stream": {
                        "chunk_count": len(chunks),
                        "chunks": chunks,
                        "content": stream_text,
                    },
                    "embedding_provider": "deterministic",
                }
            finally:
                logger.setLevel(previous_level)


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Guardrails engine: {result['guardrails']['engine']}")
        print(f"Fallback to LLMRails: {not result['guardrails']['use_iorails_engine']}")
        print(f"Generate smoke: {result['guardrails']['content']}")
        print(f"Stream smoke chunks: {result['stream']['chunk_count']}")
        print(f"Stream smoke text: {result['stream']['content']}")
        print("Deterministic embeddings: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
