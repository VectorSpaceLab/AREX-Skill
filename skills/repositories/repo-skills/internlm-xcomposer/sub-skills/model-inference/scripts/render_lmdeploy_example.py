#!/usr/bin/env python3
"""Render a safe InternLM-XComposer LMDeploy example or serving plan.

This helper is stdlib-only. It does not import lmdeploy, torch, or any model
checkpoint. It only renders text that a user can copy into a prepared runtime.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import List, Sequence

FP16_MODEL_ID = "internlm/internlm-xcomposer2d5-7b"
AWQ_MODEL_ID = "internlm/internlm-xcomposer2d5-7b-4bit"


@dataclass
class ValidationResult:
    ok: bool
    messages: List[str]


def choose_model_id(quantization: str, model_id: str) -> str:
    if model_id:
        return model_id
    return AWQ_MODEL_ID if quantization == "awq" else FP16_MODEL_ID


def validate(args: argparse.Namespace, model_id: str) -> ValidationResult:
    messages: List[str] = []
    ok = True

    if not (0.0 < args.cache_max_entry_count <= 1.0):
        ok = False
        messages.append("cache-max-entry-count must be in (0, 1]")
    if args.tp < 1:
        ok = False
        messages.append("tp must be at least 1")
    if args.session_len < 1:
        ok = False
        messages.append("session-len must be positive")
    if args.max_new_tokens < 1:
        ok = False
        messages.append("max-new-tokens must be positive")
    if args.quantization == "awq" and not model_id.endswith("-4bit"):
        messages.append("awq mode is usually paired with a -4bit checkpoint; check the model id before execution")
    if args.mode in {"offline", "both"} and not args.image:
        messages.append("no image provided; the rendered offline snippet will use a default example image placeholder")

    return ValidationResult(ok=ok, messages=messages)


def offline_snippet(args: argparse.Namespace, model_id: str) -> str:
    image_path = args.image or "/data/dubai.png"
    engine_config = (
        f"TurbomindEngineConfig(model_format='awq', cache_max_entry_count={args.cache_max_entry_count})"
        if args.quantization == "awq"
        else f"TurbomindEngineConfig(cache_max_entry_count={args.cache_max_entry_count})"
    )
    return dedent(
        f"""
        from lmdeploy import pipeline, TurbomindEngineConfig
        from lmdeploy.vl import load_image

        engine_config = {engine_config}
        pipe = pipeline({model_id!r}, backend_config=engine_config)
        image = load_image({image_path!r})
        response = pipe(({args.prompt!r}, image))
        print(response.text)
        """
    ).strip() + "\n"


def server_command(args: argparse.Namespace, model_id: str) -> str:
    parts = [
        "lmdeploy",
        "serve",
        "api_server",
        model_id,
        f"--tp {args.tp}",
        f"--session-len {args.session_len}",
        f"--cache-max-entry-count {args.cache_max_entry_count}",
    ]
    if args.quantization == "awq":
        parts.append("--model-format awq")
    return " ".join(parts)


def render_markdown(args: argparse.Namespace, model_id: str, result: ValidationResult) -> str:
    lines = [
        "# Rendered InternLM-XComposer LMDeploy plan",
        "",
        f"- mode: `{args.mode}`",
        f"- quantization: `{args.quantization}`",
        f"- model id: `{model_id}`",
        f"- image: `{args.image or '/data/dubai.png'}`",
        f"- prompt: `{args.prompt}`",
        f"- tp: `{args.tp}`",
        f"- session-len: `{args.session_len}`",
        f"- cache-max-entry-count: `{args.cache_max_entry_count}`",
        f"- validation: `{ 'ok' if result.ok else 'failed' }`",
        "",
    ]
    if result.messages:
        lines.append("## Validation notes")
        lines.append("")
        for msg in result.messages:
            lines.append(f"- {msg}")
        lines.append("")
    if args.mode in {"offline", "both"}:
        lines.append("## Offline pipeline")
        lines.append("")
        lines.append("```python")
        lines.append(offline_snippet(args, model_id).rstrip())
        lines.append("```")
        lines.append("")
    if args.mode in {"server", "both"}:
        lines.append("## API server")
        lines.append("")
        lines.append("```bash")
        lines.append(server_command(args, model_id))
        lines.append("```")
        lines.append("")
        lines.append("Confirm the exact CLI flags with `lmdeploy serve api_server -h` in the target runtime.")
    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a safe InternLM-XComposer LMDeploy example or serving plan.")
    parser.add_argument("--mode", choices=["offline", "server", "both"], default="offline")
    parser.add_argument("--quantization", choices=["fp16", "awq"], default="fp16")
    parser.add_argument("--model-id", default="", help="Optional explicit model id or local path.")
    parser.add_argument("--prompt", default="describe this image")
    parser.add_argument("--image", default="", help="Image path for offline VLM examples.")
    parser.add_argument("--tp", type=int, default=1)
    parser.add_argument("--session-len", type=int, default=32768)
    parser.add_argument("--cache-max-entry-count", type=float, default=0.1)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--format", choices=["python", "markdown"], default="python")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--output", default="-", help="Write rendered output to this file, or '-' for stdout.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    model_id = choose_model_id(args.quantization, args.model_id)
    result = validate(args, model_id)

    if args.validate_only:
        text = "\n".join(["OK" if result.ok else "FAILED", *result.messages])
    elif args.format == "markdown":
        text = render_markdown(args, model_id, result)
    else:
        if args.mode == "offline":
            text = offline_snippet(args, model_id)
        elif args.mode == "server":
            text = server_command(args, model_id) + "\n"
        else:
            text = render_markdown(args, model_id, result)

    if args.output == "-":
        sys.stdout.write(text)
    else:
        Path(args.output).expanduser().write_text(text, encoding="utf-8")
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
