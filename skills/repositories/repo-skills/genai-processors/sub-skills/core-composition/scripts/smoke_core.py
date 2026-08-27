#!/usr/bin/env python3
"""Safe smoke test for GenAI Processors core composition APIs."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterable

from genai_processors import content_api
from genai_processors import processor
from genai_processors import streams
from genai_processors import switch


@processor.processor_function
async def pass_text(content: processor.ProcessorStream) -> AsyncIterable[content_api.ProcessorPartTypes]:
  async for part in content:
    if content_api.is_text(part.mimetype):
      yield part


@processor.part_processor_function(match_fn=lambda part: content_api.is_text(part.mimetype))
async def upper(part: content_api.ProcessorPart) -> AsyncIterable[content_api.ProcessorPartTypes]:
  yield part.text.upper()


async def main() -> None:
  pipeline = pass_text + upper
  result = await pipeline(["hello", " ", content_api.ProcessorPart("world")]).text()
  assert result == "HELLO WORLD", result

  s1, s2 = streams.split(streams.stream_content(["a", "b"]), n=2)
  assert await streams.gather_stream(s1) == ["a", "b"]
  assert await streams.gather_stream(s2) == ["a", "b"]

  routed = switch.Switch(content_api.mime_type).default(processor.passthrough())
  routed_text = await routed("ok").text()
  assert routed_text == "ok", routed_text
  print("core-composition smoke OK")


if __name__ == "__main__":
  asyncio.run(main())
