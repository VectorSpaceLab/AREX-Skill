#!/usr/bin/env python3
"""Safe import smoke for GenAI Processors multimodal I/O modules."""

from __future__ import annotations

import importlib

MODULES = [
    "genai_processors.core.audio",
    "genai_processors.core.audio_io",
    "genai_processors.core.rate_limit_audio",
    "genai_processors.core.speech_to_text",
    "genai_processors.core.text_to_speech",
    "genai_processors.core.vad",
    "genai_processors.core.video",
    "genai_processors.core.pdf",
    "genai_processors.core.text",
    "genai_processors.core.web",
    "genai_processors.core.github",
    "genai_processors.core.drive",
    "genai_processors.core.filesystem",
    "genai_processors.core.event_detection",
    "genai_processors.core.timestamp",
    "genai_processors.core.window",
]


def main() -> int:
  failures: list[str] = []
  for module_name in MODULES:
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
  print("multimodal-i-o smoke OK")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
