#!/usr/bin/env python3
"""Check whether a draft robotics prompt resembles the PromptCraft-Robotics style.

This is a lightweight structural check, not a semantic validator.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RESPONSE_CUES = ["Question", "Code", "Reason", "Here's the code", "Here is the code", "This code", "Explanation"]
CODE_BLOCK_RE = re.compile(r"```.+?```", re.S)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="Markdown prompt to inspect")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if any required signal is missing")
    args = parser.parse_args(argv)

    try:
        text = args.file.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"missing file: {args.file}")
        return 1

    issues: list[str] = []
    if not CODE_BLOCK_RE.search(text):
        issues.append("missing fenced code block")
    if not any(cue in text for cue in RESPONSE_CUES):
        issues.append("missing repository-style response cues")

    print(f"Prompt example check: {args.file}")
    if issues:
        print("issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1 if args.strict else 0

    print("status: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
