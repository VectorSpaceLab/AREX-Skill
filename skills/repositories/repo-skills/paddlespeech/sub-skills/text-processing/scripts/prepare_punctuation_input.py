#!/usr/bin/env python3
"""Preview PaddleSpeech punctuation input cleaning."""
from __future__ import annotations

import argparse
import re


def clean_text(text: str) -> str:
    text = text.lower()
    return re.sub(r"[^A-Za-z0-9\u4e00-\u9fa5]", "", text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean/validate text before paddlespeech text --task punc")
    parser.add_argument("--text", required=True)
    parser.add_argument("--print-command", action="store_true")
    args = parser.parse_args()
    cleaned = clean_text(args.text)
    print(f"cleaned={cleaned}")
    if not cleaned:
        print("ERROR: cleaned text is empty; punctuation executor will reject this input")
        return 1
    if args.print_command:
        print(f"paddlespeech text --task punc --input {cleaned}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
