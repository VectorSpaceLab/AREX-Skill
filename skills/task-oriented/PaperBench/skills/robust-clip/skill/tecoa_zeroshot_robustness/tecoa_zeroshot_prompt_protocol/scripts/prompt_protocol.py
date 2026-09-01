#!/usr/bin/env python3
"""Deterministic CLIP-style prompt construction for TeCoA recovery."""

from __future__ import annotations

import argparse
import json
import re
from string import Formatter
from typing import Iterable


def normalize_label(label: str) -> str:
    value = str(label).strip().replace("_", " ")
    value = re.sub(r"\s+", " ", value)
    if not value:
        raise ValueError("labels must not contain empty values")
    return value


def _replacement_field_count(template: str) -> int:
    count = 0
    for _, field_name, _, _ in Formatter().parse(template):
        if field_name is not None:
            count += 1
    return count


def build_prompts(labels: Iterable[str], template: str = "a photo of a {}") -> dict:
    labels = list(labels)
    if not labels:
        raise ValueError("labels must be a non-empty sequence")
    if _replacement_field_count(template) != 1:
        raise ValueError("template must contain exactly one replacement field")
    normalized = [normalize_label(label) for label in labels]
    prompts = [template.format(label) for label in normalized]
    return {
        "prompts": prompts,
        "mapping": [
            {"index": index, "label": label, "normalized_label": norm, "prompt": prompt}
            for index, (label, norm, prompt) in enumerate(zip(labels, normalized, prompts))
        ],
        "metadata": {
            "template": template,
            "count": len(prompts),
            "normalization": ["strip", "underscore_to_space", "collapse_spaces"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", required=True, help="JSON list of labels or comma-separated labels")
    parser.add_argument("--template", default="a photo of a {}")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()
    try:
        labels = json.loads(args.labels)
        if not isinstance(labels, list):
            raise ValueError
    except Exception:
        labels = [part for part in args.labels.split(",")]
    payload = build_prompts(labels, args.template)
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
