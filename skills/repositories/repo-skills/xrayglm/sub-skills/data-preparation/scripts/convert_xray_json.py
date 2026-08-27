#!/usr/bin/env python3
"""Convert an OpenI-style annotation wrapper to records, caption JSON, or Markdown."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROMPT_VARIANTS = (
    "通过这张胸部X光影像可以诊断出什么？",
    "这张图片的背景里有什么内容？",
    "详细描述一下这张图片",
    "看看这张图片并描述你注意到的内容",
    "请提供图片的详细描述",
    "你能为我描述一下这张图片的内容吗？",
)
DEFAULT_TEMPLATE = "./data/Xray/{image_id}.png"


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise ValueError(f"input does not exist: {path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}")


def read_annotations(data: Any) -> list[dict[str, str]]:
    if not isinstance(data, dict) or not isinstance(data.get("annotations"), list):
        raise ValueError("input must be an object with an 'annotations' array")
    annotations: list[dict[str, str]] = []
    seen: dict[str, int] = {}
    for index, item in enumerate(data["annotations"]):
        if not isinstance(item, dict):
            raise ValueError(f"annotations[{index}] must be an object")
        image_id = item.get("image_id")
        caption = item.get("caption")
        if not isinstance(image_id, str) or not image_id.strip():
            raise ValueError(f"annotations[{index}].image_id must be a non-empty string")
        if not isinstance(caption, str) or not caption.strip():
            raise ValueError(f"annotations[{index}].caption must be a non-empty string")
        image_id = image_id.strip()
        if image_id in seen:
            raise ValueError(
                f"duplicate image_id {image_id!r} at annotations[{index}]; "
                f"first seen at annotations[{seen[image_id]}]"
            )
        seen[image_id] = index
        annotations.append({"image_id": image_id, "caption": caption})
    return annotations


def output_path_is_safe(input_path: Path, output_path: Path, force: bool) -> None:
    same = input_path.expanduser().resolve(strict=False) == output_path.expanduser().resolve(strict=False)
    if (output_path.exists() or same) and not force:
        if same:
            raise ValueError("output path equals input path; use --force to replace it")
        raise ValueError(f"output exists; refusing to overwrite without --force: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)


def write_output(input_path: Path, output_path: Path, value: Any, as_markdown: bool, force: bool) -> None:
    output_path_is_safe(input_path, output_path, force)
    try:
        if as_markdown:
            output_path.write_text(value, encoding="utf-8")
        else:
            output_path.write_text(
                json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
    except OSError as exc:
        raise ValueError(f"cannot write {output_path}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract OpenI captions locally; no downloading, translation, or credentials are used."
    )
    parser.add_argument("input", type=Path, help="OpenI-like JSON wrapper")
    parser.add_argument("output", type=Path, help="new JSON or Markdown output path")
    parser.add_argument(
        "--format", choices=("records", "captions", "markdown"), default="records",
        help="records = training schema; captions = image_id/caption JSON; markdown = caption document",
    )
    parser.add_argument("--prompt", default=None, help="explicit prompt for records format")
    parser.add_argument(
        "--prompt-index", type=int, choices=range(len(PROMPT_VARIANTS)), default=0,
        help="deterministic index into the six source Chinese prompts (default: 0)",
    )
    parser.add_argument(
        "--image-template", default=DEFAULT_TEMPLATE,
        help="records image path template containing {image_id}; default: ./data/Xray/{image_id}.png",
    )
    parser.add_argument("--force", action="store_true", help="allow replacing an existing output")
    args = parser.parse_args()

    prompt = args.prompt if args.prompt is not None else PROMPT_VARIANTS[args.prompt_index]
    if not isinstance(prompt, str) or not prompt.strip():
        parser.error("--prompt must be a non-empty string")
    if "{image_id}" not in args.image_template:
        parser.error("--image-template must contain {image_id}")

    try:
        data = load_json(args.input)
        annotations = read_annotations(data)  # validate before any output operation
        if args.format == "records":
            value = [
                {
                    "img": args.image_template.format(image_id=item["image_id"]),
                    "prompt": prompt,
                    "label": item["caption"],
                }
                for item in annotations
            ]
            write_output(args.input, args.output, value, False, args.force)
        elif args.format == "captions":
            value = annotations
            write_output(args.input, args.output, value, False, args.force)
        else:
            blocks = [f"## {item['image_id']}\n\n{item['caption']}" for item in annotations]
            markdown = "\n\n".join(blocks) + ("\n" if blocks else "")
            write_output(args.input, args.output, markdown, True, args.force)
    except (ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"WROTE {len(annotations)} item(s) as {args.format}: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
