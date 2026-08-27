#!/usr/bin/env python3
"""Build a safe HunyuanImage-3.0 vLLM request payload.

This script mirrors the inspected request-shape logic from
vllm_infer/openai_client.py, but it stops before any network request or image
post-processing.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

DEFAULT_PROMPT = (
    "Generate an image: In a colosseum, a woman and a bear engage in combat, "
    "illuminated by torchlight. Rendered in 3D style."
)
DEFAULT_MODEL = "vllm_hunyuan_image3"
DEFAULT_MAX_TOKENS = 256
DEFAULT_TEMPERATURE = 0

TEMPLATES_PRETRAIN = {
    "image": (
        "{% for message in messages %}"
        "{% if message['role'] == 'user' %}"
        "<|startoftext|>{{ message['content'] }}"
        "{% endif %}"
        "{% endfor %}"
    ),
    "auto": (
        "{% for message in messages %}"
        "{% if message['role'] == 'user' %}"
        "<|startoftext|>{{ message['content'] }}<boi><image_shape_1024>"
        "{% endif %}"
        "{% endfor %}"
    ),
}


def default(value, fallback):
    return value if value is not None else fallback


def build_payload(args):
    if args.sequence_template != "pretrain":
        raise NotImplementedError(
            "The inspected source build_payload path only implements the "
            "pretrain template. The safe bundled payload builder does not "
            "synthesize an instruct request shape."
        )

    if args.bot_task not in TEMPLATES_PRETRAIN:
        raise NotImplementedError(
            "The safe bundled payload builder only verifies the image and auto "
            "request shapes. The source help advertises think/recaption, but "
            "those labels are not part of this verified request contract."
        )

    chat_template = TEMPLATES_PRETRAIN[args.bot_task]
    task_extra_kwargs = {
        "diff_infer_steps": args.diff_infer_steps,
        "use_system_prompt": args.use_system_prompt,
        "bot_task": args.bot_task,
    }

    if args.bot_task == "image":
        task_extra_kwargs["image_size"] = (
            f"{default(args.height, 1024)}x{default(args.width, 1024)}"
        )

    max_tokens = args.max_tokens
    if args.bot_task in {"image", "auto"}:
        max_tokens = 1

    payload = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": ""},
            {"role": "user", "content": args.prompt},
        ],
        "max_completion_tokens": max_tokens,
        "temperature": args.temperature,
        "seed": default(args.seed, random.randint(1, 10_000_000)),
        "chat_template": chat_template,
        "task_type": "hunyuan_image3",
        "task_extra_kwargs": task_extra_kwargs,
    }
    return payload


def parse_args():
    parser = argparse.ArgumentParser(
        description="Render a safe vLLM payload for HunyuanImage-3.0"
    )
    parser.add_argument(
        "--sequence-template",
        choices=["pretrain", "instruct"],
        default="pretrain",
        help="Sequence template family. Only the verified pretrain request shape is bundled.",
    )
    parser.add_argument(
        "--bot-task",
        choices=["image", "auto", "think", "recaption"],
        default="image",
        help=(
            "Task label used by the client payload. The safe bundled contract "
            "covers image and auto request shapes."
        ),
    )
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="User prompt")
    parser.add_argument("--width", type=int, help="Image width")
    parser.add_argument("--height", type=int, help="Image height")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument(
        "--diff-infer-steps",
        type=int,
        default=50,
        help="Number of inference steps",
    )
    parser.add_argument(
        "--use-system-prompt",
        type=str,
        default="None",
        choices=[
            "None",
            "dynamic",
            "en_vanilla",
            "en_recaption",
            "en_think_recaption",
            "custom",
        ],
        help="System prompt routing flag mirrored from the inspected client",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model alias")
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help="Maximum completion tokens before task-specific overrides",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help="Sampling temperature",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the rendered JSON payload",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the payload JSON",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    payload = build_payload(args)
    indent = 2 if args.pretty or args.output else None
    rendered = json.dumps(payload, ensure_ascii=False, indent=indent, sort_keys=False)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

    print(rendered)


if __name__ == "__main__":
    main()
