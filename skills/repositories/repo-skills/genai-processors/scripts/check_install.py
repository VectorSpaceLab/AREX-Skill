#!/usr/bin/env python3
"""Safe install smoke check for GenAI Processors.

This script performs import-level and tiny in-process checks only. It does not
call remote models, access credentials, open audio/video devices, fetch URLs, or
start servers.
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import AsyncIterable
import importlib
import sys

from genai_processors import content_api
from genai_processors import processor

CORE_MODULES = [
    "genai_processors",
    "genai_processors.content_api",
    "genai_processors.processor",
    "genai_processors.streams",
    "genai_processors.switch",
    "genai_processors.cache",
    "genai_processors.sql_cache",
    "genai_processors.core.genai_model",
    "genai_processors.core.live_model",
    "genai_processors.core.realtime",
    "genai_processors.core.function_calling",
    "genai_processors.core.text",
    "genai_processors.core.preamble",
    "genai_processors.core.jinja_template",
    "genai_processors.core.constrained_decoding",
]

OPTIONAL_MODULES = [
    "genai_processors.core.audio_io",
    "genai_processors.core.video",
    "genai_processors.core.pdf",
    "genai_processors.core.speech_to_text",
    "genai_processors.core.text_to_speech",
    "genai_processors.core.vad",
    "genai_processors.core.web",
    "genai_processors.core.github",
    "genai_processors.core.drive",
    "genai_processors.core.ollama_model",
    "genai_processors.core.transformers_model",
    "genai_processors.core.adk",
    "genai_processors.contrib.langchain_model",
    "genai_processors.contrib.openrouter_model",
    "genai_processors.mcp",
]


@processor.processor_function
async def _echo(
    content: processor.ProcessorStream,
) -> AsyncIterable[content_api.ProcessorPartTypes]:
  async for part in content:
    yield part


async def _run_core_smoke() -> None:
  result = await _echo(["hello", " ", content_api.ProcessorPart("world")]).text()
  if result != "hello world":
    raise AssertionError(f"processor echo smoke returned {result!r}")


def _import_modules(modules: list[str]) -> list[tuple[str, str]]:
  failures: list[tuple[str, str]] = []
  for module in modules:
    try:
      importlib.import_module(module)
      print(f"OK import {module}")
    except Exception as exc:  # pylint: disable=broad-except
      failures.append((module, f"{type(exc).__name__}: {exc}"))
      print(f"FAIL import {module}: {type(exc).__name__}: {exc}")
  return failures


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
      "--optional",
      action="store_true",
      help="also check optional multimodal/contrib/backend imports",
  )
  args = parser.parse_args()

  failures = _import_modules(CORE_MODULES)
  asyncio.run(_run_core_smoke())
  print("OK processor echo smoke")

  if args.optional:
    failures.extend(_import_modules(OPTIONAL_MODULES))

  if failures:
    print("\nFailures:", file=sys.stderr)
    for module, message in failures:
      print(f"- {module}: {message}", file=sys.stderr)
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
