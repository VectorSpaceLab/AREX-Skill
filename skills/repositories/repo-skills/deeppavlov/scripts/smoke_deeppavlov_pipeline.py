#!/usr/bin/env python3
"""Run a tiny offline DeepPavlov pipeline smoke.

This helper uses only a minimal in-memory config and never downloads models,
datasets, or weights. It is useful for quick installation checks and for
showing the basic `build_model` contract without reopening the original repo.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from deeppavlov import build_model


TINY_CONFIG: dict[str, Any] = {
    "chainer": {
        "in": ["x"],
        "out": ["tokens"],
        "pipe": [
            {
                "class_name": "deeppavlov.models.preprocessors.str_lower:str_lower",
                "in": ["x"],
                "out": ["x_lower"],
            },
            {
                "class_name": "split_tokenizer",
                "in": ["x_lower"],
                "out": ["tokens"],
            },
        ],
    }
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny offline DeepPavlov smoke pipeline.")
    parser.add_argument("--text", default="Hello WORLD", help="Input text to feed through the smoke pipeline.")
    parser.add_argument("--json", action="store_true", help="Print a JSON summary instead of a plain result.")
    args = parser.parse_args()

    model = build_model(TINY_CONFIG)
    result = model([args.text])

    if args.json:
        print(json.dumps({"text": args.text, "result": result}, ensure_ascii=False, indent=2))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
