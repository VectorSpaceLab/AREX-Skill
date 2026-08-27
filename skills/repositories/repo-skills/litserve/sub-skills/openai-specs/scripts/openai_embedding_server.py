#!/usr/bin/env python3
"""Safe LitServe OpenAIEmbeddingSpec embeddings example.

Run:
    python openai_embedding_server.py --port 8000

OpenAI client:
    from openai import OpenAI
    client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="lit")
    response = client.embeddings.create(
        model="lit",
        input="A beautiful sunset over the beach.",
        encoding_format="float",
    )

The server is deterministic and has no model dependency. It returns one
768-dimensional float vector per text input.
"""

from __future__ import annotations

import argparse
import hashlib
from typing import Any

import litserve as ls
from litserve import OpenAIEmbeddingSpec

DEFAULT_DIMENSIONS = 768


def _normalise_embedding_items(inputs: Any) -> list[Any]:
    """Normalize common OpenAI embedding inputs to a list of embedding items.

    The demo intentionally focuses on string and list[str] inputs. Token-list
    inputs are accepted as opaque items so the response still has one vector per
    item for the common OpenAI request shapes.
    """
    if isinstance(inputs, str):
        return [inputs]
    if isinstance(inputs, list):
        if not inputs:
            return [""]
        if all(isinstance(item, int) for item in inputs):
            return [inputs]
        return inputs
    return [inputs]


def _stable_embedding(item: Any, dimensions: int = DEFAULT_DIMENSIONS) -> list[float]:
    """Create a deterministic pseudo-embedding in [0, 1]."""
    data = repr(item).encode("utf-8")
    digest = hashlib.sha256(data).digest()
    values = []
    for index in range(dimensions):
        byte = digest[index % len(digest)]
        # Center approximately around zero while keeping float JSON output.
        values.append(round((byte / 255.0) * 2.0 - 1.0, 6))
    return values


def _token_count(item: Any) -> int:
    if isinstance(item, str):
        return max(1, len(item.split()))
    if isinstance(item, list):
        return max(1, len(item))
    return 1


class DemoOpenAIEmbeddingAPI(ls.LitAPI):
    """Deterministic embeddings API for OpenAIEmbeddingSpec shape validation."""

    def setup(self, device: str) -> None:
        self.device = device

    def predict(self, inputs: Any) -> dict[str, Any]:
        # OpenAIEmbeddingSpec rejects generator-based predict methods. Return a
        # complete value that encode_response can pass through.
        items = _normalise_embedding_items(inputs)
        embeddings = [_stable_embedding(item) for item in items]
        prompt_tokens = sum(_token_count(item) for item in items)
        return {
            "embeddings": embeddings,
            "prompt_tokens": prompt_tokens,
            "total_tokens": prompt_tokens,
        }

    def encode_response(self, output: dict[str, Any]) -> dict[str, Any]:
        # Must return a dict with an `embeddings` key; do not yield here.
        return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a LitServe OpenAIEmbeddingSpec demo server.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--log-level", default="info")
    parser.add_argument(
        "--max-batch-size",
        default=1,
        type=int,
        help=(
            "Server dynamic batching size. Keep this at 1 when clients send "
            "input lists; use >1 only when each client request sends one input."
        ),
    )
    parser.add_argument("--batch-timeout", default=0.0, type=float)
    args = parser.parse_args()

    api = DemoOpenAIEmbeddingAPI(
        max_batch_size=args.max_batch_size,
        batch_timeout=args.batch_timeout,
        spec=OpenAIEmbeddingSpec(),
    )
    server = ls.LitServer(api)
    server.run(host=args.host, port=args.port, log_level=args.log_level)


if __name__ == "__main__":
    main()
