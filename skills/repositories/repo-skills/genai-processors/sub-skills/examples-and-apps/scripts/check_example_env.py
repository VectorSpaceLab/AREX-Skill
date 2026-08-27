#!/usr/bin/env python3
"""Print safe readiness signals for GenAI Processors example apps.

The script does not run examples, call models, open devices, fetch URLs, or start
a WebSocket server. It reports whether common environment variables are present
without printing secret values, and import-checks supporting modules.
"""

from __future__ import annotations

import importlib
import os

ENV_VARS = [
    "GOOGLE_API_KEY",
    "GOOGLE_PROJECT_ID",
    "OPENROUTER_API_KEY",
]

SUPPORT_MODULES = [
    "genai_processors.dev.live_server",
    "genai_processors.dev.trace_file",
    "genai_processors.core.text",
    "genai_processors.core.genai_model",
    "genai_processors.core.live_model",
    "genai_processors.core.realtime",
    "genai_processors.core.function_calling",
    "genai_processors.core.pdf",
    "genai_processors.core.audio_io",
    "genai_processors.core.video",
    "genai_processors.core.speech_to_text",
    "genai_processors.core.text_to_speech",
    "genai_processors.core.vad",
    "genai_processors.core.ollama_model",
    "genai_processors.core.adk",
    "genai_processors.contrib.langchain_model",
    "genai_processors.mcp",
]


def main() -> int:
  for name in ENV_VARS:
    print(f"ENV {name}: {'set' if os.environ.get(name) else 'missing'}")

  failures: list[str] = []
  for module_name in SUPPORT_MODULES:
    try:
      importlib.import_module(module_name)
      print(f"OK import {module_name}")
    except Exception as exc:  # pylint: disable=broad-except
      failures.append(f"{module_name}: {type(exc).__name__}: {exc}")
      print(f"FAIL import {module_name}: {type(exc).__name__}: {exc}")

  if failures:
    print("Failures:")
    for failure in failures:
      print(f"- {failure}")
    return 1
  print("examples-and-apps readiness check OK")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
