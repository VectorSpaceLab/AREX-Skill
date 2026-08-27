#!/usr/bin/env python3
"""Validate HunyuanImage-3.0 prompt-mode combinations.

This helper is intentionally self-contained. It does not import the source
checkout, load model weights, or call Tencent Cloud.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from typing import Any, Optional

LOCAL_CLI_SYSTEM_PROMPTS = {
    "None",
    "dynamic",
    "en_vanilla",
    "en_recaption",
    "en_think_recaption",
    "en_unified",
    "custom",
}

MODEL_API_SYSTEM_PROMPTS = LOCAL_CLI_SYSTEM_PROMPTS
VLLM_SYSTEM_PROMPTS = {
    "None",
    "dynamic",
    "en_vanilla",
    "en_recaption",
    "en_think_recaption",
    "custom",
}

LOCAL_CLI_BOT_TASKS = {"image", "auto", "recaption", "think_recaption"}
MODEL_API_BOT_TASKS = {"image", "auto", "think", "recaption", "think_recaption", "img_ratio"}
VLLM_BOT_TASKS = {"image", "auto", "think", "recaption"}

DYNAMIC_MAP = {
    "image": "en_vanilla",
    "recaption": "en_recaption",
    "think": "en_think_recaption",
}

PE_PROMPTS = {"universal", "text_rendering"}


@dataclass
class Finding:
    level: str
    message: str


@dataclass
class Result:
    surface: str
    use_system_prompt: str
    bot_task: str
    image_size: str
    rewrite: bool
    sys_deepseek_prompt: Optional[str]
    image_count: int
    resolved_system_prompt: str
    findings: list[Finding]


def parse_image_list(value: Optional[str]) -> tuple[list[str], bool]:
    if value is None:
        return [], False
    raw = [item.strip() for item in value.split(",")]
    has_empty = any(item == "" for item in raw)
    items = [item for item in raw if item]
    return items, has_empty


def validate_image_size(value: str) -> Optional[str]:
    if value == "auto":
        return None
    if re.fullmatch(r"\d+x\d+", value):
        return None
    if re.fullmatch(r"\d+:\d+", value):
        return None
    return (
        "image_size must be 'auto', 'HxW', or 'W:H'. "
        "The source implementation treats the colon form as width:height."
    )


def surface_tables(surface: str) -> tuple[set[str], set[str]]:
    if surface == "local-cli":
        return LOCAL_CLI_SYSTEM_PROMPTS, LOCAL_CLI_BOT_TASKS
    if surface == "model-api":
        return MODEL_API_SYSTEM_PROMPTS, MODEL_API_BOT_TASKS
    if surface == "vllm-client":
        return VLLM_SYSTEM_PROMPTS, VLLM_BOT_TASKS
    raise ValueError(f"Unknown surface: {surface}")


def resolve_system_prompt(use_system_prompt: str, bot_task: str, custom_prompt: str) -> tuple[str, Optional[str]]:
    if use_system_prompt == "None":
        return "<none>", None
    if use_system_prompt == "en_unified":
        return "unified multimodal prompt", "en_unified"
    if use_system_prompt == "en_vanilla":
        return "vanilla image prompt", "en_vanilla"
    if use_system_prompt == "en_recaption":
        return "recaption prompt", "en_recaption"
    if use_system_prompt == "en_think_recaption":
        return "think+recaption prompt", "en_think_recaption"
    if use_system_prompt == "custom":
        return (custom_prompt or "").strip() or "<empty custom prompt>", "custom"
    if use_system_prompt == "dynamic":
        mapped = DYNAMIC_MAP.get(bot_task)
        if mapped is not None:
            return f"dynamic -> {mapped}", mapped
        return (custom_prompt or "").strip() or "<unmapped dynamic prompt>", None
    return "<unsupported>", None


def add_finding(findings: list[Finding], level: str, message: str) -> None:
    findings.append(Finding(level=level, message=message))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate HunyuanImage-3.0 prompt and image conditioning combinations"
    )
    parser.add_argument("--surface", choices=["local-cli", "model-api", "vllm-client"], default="local-cli")
    parser.add_argument("--use-system-prompt", default="None")
    parser.add_argument("--bot-task", default="image")
    parser.add_argument("--system-prompt", default="")
    parser.add_argument("--rewrite", action="store_true")
    parser.add_argument("--sys-deepseek-prompt", choices=sorted(PE_PROMPTS), default="universal")
    parser.add_argument("--image", default=None, help="Single path or comma-separated image list")
    parser.add_argument("--image-size", default="auto")
    parser.add_argument("--checkpoint-kind", choices=["base", "instruct", "distil", "unknown"], default="unknown")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    findings: list[Finding] = []
    allowed_system_prompts, allowed_bot_tasks = surface_tables(args.surface)

    if args.use_system_prompt not in allowed_system_prompts:
        add_finding(
            findings,
            "error",
            f"{args.surface} does not support use_system_prompt={args.use_system_prompt!r}."
        )

    if args.bot_task not in allowed_bot_tasks:
        add_finding(
            findings,
            "error",
            f"{args.surface} does not support bot_task={args.bot_task!r}."
        )

    if args.use_system_prompt == "custom" and not args.system_prompt.strip():
        add_finding(findings, "error", "custom mode requires a non-empty --system-prompt.")

    if args.use_system_prompt == "dynamic" and args.bot_task not in DYNAMIC_MAP:
        add_finding(
            findings,
            "error",
            "dynamic mode only maps image, recaption, and internal think; "
            "use en_unified or an explicit preset for think_recaption."
        )

    size_error = validate_image_size(args.image_size)
    if size_error:
        add_finding(findings, "error", size_error)

    image_items, has_empty = parse_image_list(args.image)
    image_count = len(image_items)
    if has_empty:
        add_finding(findings, "warning", "empty items were removed from the comma-separated --image list.")
    if image_count > 3:
        add_finding(
            findings,
            "warning",
            "README examples verify up to 3 reference images; more than 3 is unverified in this skill."
        )
    if image_count > 0 and "," in (args.image or "") and args.surface == "local-cli":
        add_finding(
            findings,
            "info",
            f"parsed {image_count} reference image(s) in CLI order; keep prompt labels aligned as 图1/图2/图3."
        )

    if args.rewrite:
        if not os.getenv("DEEPSEEK_KEY_ID") or not os.getenv("DEEPSEEK_KEY_SECRET"):
            add_finding(
                findings,
                "error",
                "rewrite requires DEEPSEEK_KEY_ID and DEEPSEEK_KEY_SECRET; do not silent-fallback."
            )
        add_finding(
            findings,
            "error",
            "the current run_image_gen.py snapshot references args.sys_deepseek_prompt without registering the argument."
        )
        if args.sys_deepseek_prompt not in PE_PROMPTS:
            add_finding(findings, "error", f"unsupported DeepSeek PE prompt: {args.sys_deepseek_prompt!r}.")

    if args.checkpoint_kind == "base" and args.rewrite:
        add_finding(
            findings,
            "warning",
            "the base checkpoint relies on external PE rewriting in the repo docs; instruct-style self-rewrite is not the same path."
        )

    resolved_text, resolved_key = resolve_system_prompt(
        args.use_system_prompt,
        args.bot_task,
        args.system_prompt,
    )

    if args.use_system_prompt == "dynamic" and resolved_key is None:
        add_finding(
            findings,
            "warning",
            "dynamic fell back to the custom prompt string or empty text because no explicit mapping exists for this bot_task."
        )

    if args.surface == "vllm-client" and args.use_system_prompt == "en_unified":
        add_finding(findings, "error", "vLLM client snapshot does not list en_unified as an allowed preset.")

    if args.surface == "vllm-client" and args.bot_task == "think_recaption":
        add_finding(findings, "error", "vLLM client snapshot uses think, not think_recaption.")

    if args.checkpoint_kind in {"instruct", "distil"} and args.bot_task == "image" and image_count > 0:
        add_finding(
            findings,
            "info",
            "for instruct checkpoints with references, think_recaption plus en_unified is usually the safer editing path."
        )

    if args.checkpoint_kind == "base" and args.bot_task in {"recaption", "think_recaption"}:
        add_finding(
            findings,
            "warning",
            "the base checkpoint docs emphasize manual prompting or external PE rewrite; test recaption flows carefully."
        )

    result = Result(
        surface=args.surface,
        use_system_prompt=args.use_system_prompt,
        bot_task=args.bot_task,
        image_size=args.image_size,
        rewrite=args.rewrite,
        sys_deepseek_prompt=args.sys_deepseek_prompt if args.rewrite else None,
        image_count=image_count,
        resolved_system_prompt=resolved_text,
        findings=findings,
    )

    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print(f"surface: {result.surface}")
        print(f"use_system_prompt: {result.use_system_prompt}")
        print(f"bot_task: {result.bot_task}")
        print(f"image_size: {result.image_size}")
        print(f"rewrite: {result.rewrite}")
        if result.sys_deepseek_prompt is not None:
            print(f"sys_deepseek_prompt: {result.sys_deepseek_prompt}")
        print(f"image_count: {result.image_count}")
        print(f"resolved_system_prompt: {result.resolved_system_prompt}")
        print("findings:")
        for finding in result.findings:
            print(f"  - {finding.level.upper()}: {finding.message}")

    has_error = any(item.level == "error" for item in findings)
    return 2 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
