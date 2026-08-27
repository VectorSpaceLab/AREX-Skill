#!/usr/bin/env python
"""List known LMFlow conversation templates.

This helper prints the bundled template names from the installed package when
possible and falls back to a static list if the package cannot be imported.
"""

from __future__ import annotations

import argparse
from typing import Iterable

FALLBACK_TEMPLATES = [
    "chatglm3",
    "chatml",
    "deepseek",
    "deepseek_v2",
    "deepseek_v3",
    "deepseek_r1",
    "deepseek_r1_distill",
    "disable",
    "empty",
    "empty_no_special_tokens",
    "gemma",
    "hymba",
    "internlm2",
    "llama2",
    "llama3",
    "llama3_for_tool",
    "phi3",
    "qwen2",
    "qwen2_for_tool",
    "qwen2_5",
    "qwen2_5_1m",
    "qwen2_5_math",
    "qwen_qwq",
    "qwen3",
    "yi",
    "yi1_5",
    "zephyr",
]


def print_items(items: Iterable[str]) -> None:
    for item in sorted(items):
        print(item)


def main() -> int:
    parser = argparse.ArgumentParser(description="List LMFlow conversation templates.")
    parser.add_argument("--installed-only", action="store_true", help="Print only templates exposed by installed lmflow.")
    args = parser.parse_args()

    try:
        from lmflow.utils.conversation_template import PRESET_TEMPLATES

        print_items(PRESET_TEMPLATES.keys())
        if args.installed_only:
            return 0
    except Exception:  # noqa: BLE001
        if args.installed_only:
            return 1
        print_items(FALLBACK_TEMPLATES)
        return 0

    print("--- fallback-known-templates ---")
    print_items(FALLBACK_TEMPLATES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
