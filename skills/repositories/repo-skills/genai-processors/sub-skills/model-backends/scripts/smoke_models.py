#!/usr/bin/env python3
"""Safe model-wrapper smoke check for GenAI Processors.

This imports model wrappers and prints constructor signatures. It does not call
remote APIs, start local services, load HuggingFace weights, or open MCP
sessions.
"""

from __future__ import annotations

import importlib
import inspect

MODULES = [
    "genai_processors.core.genai_model",
    "genai_processors.core.live_model",
    "genai_processors.core.realtime",
    "genai_processors.core.function_calling",
    "genai_processors.core.ollama_model",
    "genai_processors.core.transformers_model",
    "genai_processors.core.adk",
    "genai_processors.contrib.langchain_model",
    "genai_processors.contrib.openrouter_model",
    "genai_processors.mcp",
]

SIGNATURES = [
    ("genai_processors.core.genai_model", "GenaiModel"),
    ("genai_processors.core.live_model", "LiveProcessor"),
    ("genai_processors.core.realtime", "LiveProcessor"),
    ("genai_processors.core.function_calling", "FunctionCalling"),
    ("genai_processors.core.ollama_model", "OllamaModel"),
    ("genai_processors.core.transformers_model", "TransformersModel"),
    ("genai_processors.contrib.langchain_model", "LangChainModel"),
    ("genai_processors.contrib.openrouter_model", "OpenRouterModel"),
]


def main() -> int:
  failures: list[str] = []
  for module_name in MODULES:
    try:
      importlib.import_module(module_name)
      print(f"OK import {module_name}")
    except Exception as exc:  # pylint: disable=broad-except
      failures.append(f"{module_name}: {type(exc).__name__}: {exc}")

  for module_name, attr in SIGNATURES:
    try:
      obj = getattr(importlib.import_module(module_name), attr)
      print(f"{attr}: {inspect.signature(obj.__init__)}")
    except Exception as exc:  # pylint: disable=broad-except
      failures.append(f"signature {module_name}.{attr}: {type(exc).__name__}: {exc}")

  if failures:
    print("Failures:")
    for failure in failures:
      print(f"- {failure}")
    return 1
  print("model-backends smoke OK")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
