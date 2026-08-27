#!/usr/bin/env python3
"""Service-free AdalFlow Generator/Embedder smoke test with a fake ModelClient.

This script intentionally performs no network calls and requires no API keys. It
checks that the installed AdalFlow package can orchestrate:

- Generator prompt rendering
- ModelClient input-to-api-kwargs conversion
- GeneratorOutput parsing through JsonParser
- async Generator.acall
- Embedder and BatchEmbedder output parsing
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from typing import Any, Dict, List, Optional

try:
    from adalflow.core.embedder import BatchEmbedder, Embedder
    from adalflow.core.generator import Generator
    from adalflow.core.model_client import ModelClient
    from adalflow.core.string_parser import JsonParser
    from adalflow.core.types import (
        EmbedderOutput,
        Embedding,
        GeneratorOutput,
        ModelType,
        Usage,
    )
except ImportError as exc:  # pragma: no cover - runtime diagnostic path
    raise SystemExit(
        "Unable to import AdalFlow generator APIs. Install AdalFlow and its "
        "required lightweight model-client dependencies, including the OpenAI "
        "SDK used by current generator streaming types, then rerun this script."
    ) from exc


class FakeModelClient(ModelClient):
    """Deterministic fake client implementing the AdalFlow ModelClient protocol."""

    def __init__(self) -> None:
        super().__init__()
        self.sync_client = self.init_sync_client()
        self.async_client = self.init_async_client()
        self.calls: List[Dict[str, Any]] = []

    def init_sync_client(self) -> "FakeModelClient":
        return self

    def init_async_client(self) -> "FakeModelClient":
        return self

    def convert_inputs_to_api_kwargs(
        self,
        input: Optional[Any] = None,
        model_kwargs: Dict[str, Any] = {},
        model_type: ModelType = ModelType.UNDEFINED,
    ) -> Dict[str, Any]:
        api_kwargs = dict(model_kwargs)
        api_kwargs.update(
            {
                "input": input,
                "model_type": model_type.name,
            }
        )
        return api_kwargs

    def call(
        self,
        api_kwargs: Dict[str, Any] = {},
        model_type: ModelType = ModelType.UNDEFINED,
    ) -> Dict[str, Any]:
        self.calls.append({"mode": "sync", "model_type": model_type.name, **api_kwargs})
        if model_type == ModelType.EMBEDDER:
            inputs = api_kwargs.get("input", [])
            if isinstance(inputs, str):
                inputs = [inputs]
            return {
                "model": api_kwargs.get("model", "fake-embedding"),
                "input": inputs,
                "embeddings": [self._embed_text(text, idx) for idx, text in enumerate(inputs)],
            }
        return {
            "text": json.dumps(
                {
                    "answer": "fake-ok",
                    "model": api_kwargs.get("model", "fake-llm"),
                    "input_seen": api_kwargs.get("input"),
                    "model_type": model_type.name,
                },
                sort_keys=True,
            )
        }

    async def acall(
        self,
        api_kwargs: Dict[str, Any] = {},
        model_type: ModelType = ModelType.UNDEFINED,
    ) -> Dict[str, Any]:
        self.calls.append({"mode": "async", "model_type": model_type.name, **api_kwargs})
        return self.call(api_kwargs=api_kwargs, model_type=model_type)

    def parse_chat_completion(self, completion: Dict[str, Any]) -> GeneratorOutput:
        return GeneratorOutput(raw_response=completion["text"])

    def parse_embedding_response(self, response: Dict[str, Any]) -> EmbedderOutput:
        embeddings = [
            Embedding(embedding=item["embedding"], index=item["index"])
            for item in response["embeddings"]
        ]
        token_count = sum(len(text.split()) for text in response.get("input", []))
        return EmbedderOutput(
            data=embeddings,
            model=response.get("model"),
            usage=Usage(prompt_tokens=token_count, total_tokens=token_count),
        )

    def track_completion_usage(self, *args: Any, **kwargs: Any) -> None:
        return None

    def list_models(self) -> List[str]:
        return ["fake-llm", "fake-embedding"]

    @staticmethod
    def _embed_text(text: str, index: int) -> Dict[str, Any]:
        length = float(len(text))
        words = float(len(text.split()))
        checksum = float(sum(ord(ch) for ch in text) % 97)
        return {"embedding": [length, words, checksum], "index": index}


async def _check_async_generator(generator: Generator) -> None:
    output = await generator.acall(prompt_kwargs={"question": "async path"}, use_cache=False)
    assert isinstance(output, GeneratorOutput)
    assert output.error is None, output.error
    assert output.data["answer"] == "fake-ok"
    assert "async path" in output.data["input_seen"]


def main() -> None:
    client = FakeModelClient()

    with tempfile.TemporaryDirectory(prefix="adalflow-fake-client-") as cache_dir:
        generator = Generator(
            model_client=client,
            model_kwargs={"model": "fake-llm", "temperature": 0},
            model_type=ModelType.LLM,
            template="Answer as JSON for question: {{ question }}",
            output_processors=JsonParser(),
            cache_path=cache_dir,
            use_cache=False,
        )

        prompt = generator.get_prompt(question="2 + 2")
        assert "2 + 2" in prompt

        output = generator.call(prompt_kwargs={"question": "2 + 2"}, id="sync-case")
        assert isinstance(output, GeneratorOutput)
        assert output.id == "sync-case"
        assert output.error is None, output.error
        assert output.data["answer"] == "fake-ok"
        assert output.data["model"] == "fake-llm"
        assert output.data["model_type"] == "LLM"
        assert "2 + 2" in output.input

        asyncio.run(_check_async_generator(generator))

        embedder = Embedder(
            model_client=client,
            model_kwargs={"model": "fake-embedding"},
        )
        embedding_output = embedder.call(["alpha beta", "gamma"])
        assert isinstance(embedding_output, EmbedderOutput)
        assert embedding_output.error is None, embedding_output.error
        assert embedding_output.length == 2
        assert embedding_output.embedding_dim == 3
        assert embedding_output.input == ["alpha beta", "gamma"]

        batch_embedder = BatchEmbedder(embedder=embedder, batch_size=1)
        batches = batch_embedder.call(["one", "two three"])
        assert len(batches) == 2
        assert all(batch.length == 1 for batch in batches)

    print(
        "adalflow generator fake-client smoke passed: "
        "sync, async, JsonParser, Embedder, and BatchEmbedder"
    )


if __name__ == "__main__":
    main()
