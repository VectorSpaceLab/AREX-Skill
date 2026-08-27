#!/usr/bin/env python3
"""Deterministic smoke checks for Haystack pipeline/component public APIs.

Run in any Python environment with `haystack-ai` installed:
    python pipeline_smoke_check.py
"""

from __future__ import annotations

import asyncio

from haystack import AsyncPipeline, Pipeline, SuperComponent, component
from haystack.core.errors import PipelineConnectError


@component
class Prefixer:
    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix

    @component.output_types(text=str)
    def run(self, text: str) -> dict[str, str]:
        return {"text": f"{self.prefix}{text}"}


@component
class Reverser:
    @component.output_types(reversed_text=str)
    def run(self, text: str) -> dict[str, str]:
        return {"reversed_text": text[::-1]}


@component
class AsyncEcho:
    @component.output_types(text=str)
    def run(self, text: str) -> dict[str, str]:
        return {"text": text}

    @component.output_types(text=str)
    async def run_async(self, text: str) -> dict[str, str]:
        await asyncio.sleep(0)
        return {"text": text}


def build_pipeline() -> Pipeline:
    pipe = Pipeline(metadata={"smoke": True}, max_runs_per_component=5)
    pipe.add_component("prefix", Prefixer("haystack:"))
    pipe.add_component("reverse", Reverser())
    pipe.connect("prefix.text", "reverse.text")
    return pipe


def check_sync_pipeline() -> None:
    pipe = build_pipeline()
    result = pipe.run({"prefix": {"text": "ok"}}, include_outputs_from={"prefix"})
    assert result["prefix"]["text"] == "haystack:ok"
    assert result["reverse"]["reversed_text"] == "ko:kcatsyah"
    assert "prefix" in pipe.inputs(include_components_with_connected_inputs=True)
    assert "reverse" in pipe.outputs()


def check_serialization() -> None:
    pipe = build_pipeline()
    serialized = pipe.dumps()
    loaded = Pipeline.loads(serialized)
    assert loaded == pipe
    result = loaded.run({"prefix": {"text": "yaml"}})
    assert result["reverse"]["reversed_text"] == "lmay:kcatsyah"


async def check_async_pipeline() -> None:
    pipe = AsyncPipeline(max_runs_per_component=5)
    pipe.add_component("echo", AsyncEcho())
    pipe.add_component("reverse", Reverser())
    pipe.connect("echo.text", "reverse.text")
    result = await pipe.run_async({"echo": {"text": "async"}}, include_outputs_from={"echo"}, concurrency_limit=2)
    assert result["echo"]["text"] == "async"
    assert result["reverse"]["reversed_text"] == "cnysa"


def check_super_component() -> None:
    inner = build_pipeline()
    wrapper = SuperComponent(
        pipeline=inner,
        input_mapping={"raw_text": ["prefix.text"]},
        output_mapping={"reverse.reversed_text": "final_text"},
    )
    result = wrapper.run(raw_text="wrap")
    assert result["final_text"] == "parw:kcatsyah"


def check_connection_validation() -> None:
    pipe = Pipeline()
    pipe.add_component("prefix", Prefixer())
    pipe.add_component("reverse", Reverser())
    try:
        pipe.connect("prefix.missing", "reverse.text")
    except PipelineConnectError as error:
        assert "does not exist" in str(error)
    else:
        raise AssertionError("Expected PipelineConnectError for a missing output socket")


def main() -> None:
    check_sync_pipeline()
    check_serialization()
    asyncio.run(check_async_pipeline())
    check_super_component()
    check_connection_validation()
    print("Haystack pipeline/component smoke checks passed")


if __name__ == "__main__":
    main()
