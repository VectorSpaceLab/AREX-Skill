#!/usr/bin/env python3
"""Report which FT-Agent settings are present without exposing secret values."""

from __future__ import annotations

import json
import os


KEYS = (
    "BACKEND",
    "CHAT_MODEL",
    "OPENAI_API_KEY",
    "OPENAI_API_BASE",
    "EMBEDDING_MODEL",
    "FT_FILE_PATH",
    "FT_Coder_CoSTEER_env_type",
    "FT_TARGET_BENCHMARK",
    "FT_BENCHMARK_DESCRIPTION",
    "FT_BASE_MODEL",
    "FT_UPPER_DATA_SIZE_LIMIT",
    "FT_API_MAX_WORKERS",
    "FT_STRONG_MODELS",
    "FT_WEAK_MODELS",
    "HF_TOKEN",
)


def main() -> int:
    result = {key: bool(os.environ.get(key)) for key in KEYS}
    print(json.dumps(result, indent=2))
    required = ("BACKEND", "CHAT_MODEL", "FT_FILE_PATH", "FT_BASE_MODEL")
    return 0 if all(result[key] for key in required) else 2


if __name__ == "__main__":
    raise SystemExit(main())
