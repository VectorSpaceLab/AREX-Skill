#!/usr/bin/env python3
"""Inspect MAGI-1 ComfyUI workflow JSON files without importing ComfyUI.

The helper understands common ComfyUI UI workflow JSON files and prompt/API-style
JSON dictionaries. It prints MAGI node classes, display/title hints, linked inputs,
widget values, and obvious placeholder strings that should be reassigned before
queueing a workflow.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


MAGI_CLASSES = {
    "MagiImageLoader",
    "MagiVideoLoader",
    "MagiPromptLoader",
    "MagiTextEncoder",
    "MagiProcess",
    "MagiSaveVideo",
}

DISPLAY_NAMES = {
    "MagiImageLoader": "Load Image",
    "MagiVideoLoader": "Load Video",
    "MagiPromptLoader": "Load Prompt",
    "MagiTextEncoder": "T5 Text Encoder",
    "MagiProcess": "Process with MAGI",
    "MagiSaveVideo": "Save Video",
}

WIDGET_NAMES = {
    "MagiPromptLoader": ["prompt"],
    "MagiTextEncoder": ["prompt", "t5_pretrained_path", "t5_device"],
    "MagiImageLoader": ["image_path", "upload_kind"],
    "MagiVideoLoader": ["video_path", "upload_kind"],
    "MagiProcess": [
        "task_mode",
        "config_path",
        "image_path",
        "magi_seed",
        "video_size_h",
        "video_size_w",
        "num_frames",
        "num_steps",
        "fps",
    ],
    "MagiSaveVideo": ["output_path", "fps"],
}

PLACEHOLDER_MARKERS = (
    "/path/to/",
    "path/to/",
    "your/",
    "undefined",
    "example.png",
    "The text to be encoded.",
)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_magi_class(class_name: str | None) -> bool:
    return bool(class_name and (class_name in MAGI_CLASSES or class_name.startswith("Magi")))


def string_flag(value: str) -> str:
    lowered = value.strip().lower()
    flags: list[str] = []
    if value == "":
        flags.append("empty")
    if any(marker.lower() in lowered for marker in PLACEHOLDER_MARKERS):
        flags.append("placeholder")
    if value.startswith("/"):
        flags.append("absolute")
    return f" [{' '.join(flags)}]" if flags else ""


def format_value(value: Any) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False) + string_flag(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return repr(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def title_for(class_name: str, node: dict[str, Any]) -> str:
    direct_title = node.get("title")
    properties = node.get("properties") if isinstance(node.get("properties"), dict) else {}
    meta = node.get("_meta") if isinstance(node.get("_meta"), dict) else {}
    return (
        direct_title
        or properties.get("title")
        or meta.get("title")
        or DISPLAY_NAMES.get(class_name)
        or properties.get("Node name for S&R")
        or ""
    )


def iter_ui_nodes(data: dict[str, Any]) -> Iterable[dict[str, Any]]:
    nodes = data.get("nodes")
    if isinstance(nodes, list):
        for node in nodes:
            if isinstance(node, dict):
                class_name = node.get("type") or node.get("class_type")
                if is_magi_class(class_name):
                    yield node


def iter_prompt_nodes(data: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for node_id, node in data.items():
        if not isinstance(node, dict):
            continue
        class_name = node.get("class_type") or node.get("type")
        if is_magi_class(class_name):
            copied = dict(node)
            copied.setdefault("id", node_id)
            yield copied


def print_ui_node(node: dict[str, Any]) -> None:
    class_name = str(node.get("type") or node.get("class_type"))
    node_id = node.get("id", "?")
    title = title_for(class_name, node)
    print(f"  - id={node_id} class={class_name} title={title or '-'}")

    inputs = node.get("inputs")
    if isinstance(inputs, list) and inputs:
        linked = []
        for item in inputs:
            if not isinstance(item, dict):
                continue
            link = item.get("link")
            name = item.get("name", "?")
            type_name = item.get("type", "?")
            if link is not None:
                linked.append(f"{name}:{type_name}<=link {link}")
        if linked:
            print("    linked inputs: " + ", ".join(linked))

    widgets = node.get("widgets_values")
    if isinstance(widgets, list):
        names = WIDGET_NAMES.get(class_name, [])
        if widgets:
            print("    widgets:")
        for index, value in enumerate(widgets):
            name = names[index] if index < len(names) else f"widget_{index}"
            print(f"      {name}: {format_value(value)}")


def print_prompt_node(node: dict[str, Any]) -> None:
    class_name = str(node.get("class_type") or node.get("type"))
    node_id = node.get("id", "?")
    title = title_for(class_name, node)
    print(f"  - id={node_id} class={class_name} title={title or '-'}")

    inputs = node.get("inputs")
    if isinstance(inputs, dict) and inputs:
        print("    inputs:")
        for name, value in inputs.items():
            linked = isinstance(value, list) and len(value) >= 2 and isinstance(value[0], (str, int))
            suffix = " [link]" if linked else ""
            print(f"      {name}: {format_value(value)}{suffix}")


def inspect_file(path: Path) -> int:
    try:
        data = load_json(path)
    except Exception as exc:  # noqa: BLE001 - CLI helper should report parse/read failures clearly.
        print(f"{path}: ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"File: {path}")
    if not isinstance(data, dict):
        print("  No MAGI nodes found: top-level JSON is not an object.")
        return 0

    ui_nodes = list(iter_ui_nodes(data))
    if ui_nodes:
        print(f"  Format: ComfyUI workflow graph; MAGI nodes: {len(ui_nodes)}")
        for node in ui_nodes:
            print_ui_node(node)
        return 0

    prompt_nodes = list(iter_prompt_nodes(data))
    if prompt_nodes:
        print(f"  Format: ComfyUI prompt/API graph; MAGI nodes: {len(prompt_nodes)}")
        for node in prompt_nodes:
            print_prompt_node(node)
        return 0

    print("  No MAGI nodes found.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect MAGI-1 ComfyUI workflow JSON files without importing ComfyUI.",
    )
    parser.add_argument(
        "workflow_json",
        nargs="+",
        type=Path,
        help="One or more ComfyUI workflow JSON files to inspect.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    status = 0
    for index, path in enumerate(args.workflow_json):
        if index:
            print()
        status = max(status, inspect_file(path))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
