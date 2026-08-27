#!/usr/bin/env python3
"""Generate Cosmos prompt text from a JSON template file."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate prompts for Cosmos-based visual augmentation.")
    parser.add_argument("--templates_path", type=Path, required=True, help="JSON file containing prompt templates.")
    parser.add_argument("--num_prompts", type=int, default=1, help="Number of prompts to generate.")
    parser.add_argument(
        "--output_path",
        type=Path,
        default=Path("prompts.txt"),
        help="Output file for the generated prompts.",
    )
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed for reproducible prompts.")
    return parser.parse_args()


def generate_prompt(templates_path: Path) -> str:
    """Generate one prompt by sampling a phrase from each non-empty template section."""
    try:
        templates = json.loads(templates_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Prompt templates file not found: {templates_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in prompt templates file: {templates_path}") from exc

    prompt_parts: list[str] = []
    for section_options in templates.values():
        if not isinstance(section_options, list) or not section_options:
            continue
        prompt_parts.append(random.choice(section_options))
    return " ".join(prompt_parts)


def main() -> int:
    args = parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    prompts = [generate_prompt(args.templates_path) for _ in range(args.num_prompts)]
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text("\n".join(prompts) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
