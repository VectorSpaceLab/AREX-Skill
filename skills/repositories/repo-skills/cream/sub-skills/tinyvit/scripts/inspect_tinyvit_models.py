#!/usr/bin/env python3
"""Inspect known TinyViT variants without importing the source checkout.

This helper prints the model metadata distilled from the repo docs and source
inspection. It does not instantiate the model code.
"""

from __future__ import annotations

import argparse
import json

VARIANTS = {
    "tiny_vit_5m_224": {"input_size": 224, "num_classes": 1000, "notes": "IN-1k and 22k-to-1k variants exist"},
    "tiny_vit_11m_224": {"input_size": 224, "num_classes": 1000, "notes": "IN-1k and 22k-to-1k variants exist"},
    "tiny_vit_21m_224": {"input_size": 224, "num_classes": 1000, "notes": "IN-1k and 22k-to-1k variants exist"},
    "tiny_vit_21m_384": {"input_size": 384, "num_classes": 1000, "notes": "higher-resolution finetuning variant"},
    "tiny_vit_21m_512": {"input_size": 512, "num_classes": 1000, "notes": "higher-resolution finetuning variant"},
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect TinyViT variant metadata")
    parser.add_argument("--variant", choices=sorted(VARIANTS.keys()), help="Variant to describe")
    parser.add_argument("--list", action="store_true", help="List all known variants")
    args = parser.parse_args()

    if args.list or not args.variant:
        print(json.dumps(VARIANTS, indent=2, sort_keys=True))
        return 0

    print(json.dumps({args.variant: VARIANTS[args.variant]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
