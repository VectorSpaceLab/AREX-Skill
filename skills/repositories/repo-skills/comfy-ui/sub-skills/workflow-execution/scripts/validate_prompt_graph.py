#!/usr/bin/env python3
"""Validate ComfyUI API prompt graph structure without importing ComfyUI.

This checker catches JSON shape, prompt-vs-UI-workflow confusion, malformed
[node_id, output_index] links, missing class_type/inputs, unresolved references,
and likely missing output nodes. It intentionally does not validate node-specific
schemas, installed custom nodes, model names, or runtime backend availability.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LIKELY_OUTPUT_CLASS_PATTERNS = (
    "save",
    "preview",
    "display",
    "output",
    "writer",
    "export",
)
PLACEHOLDER_RE = re.compile(r"(<[^>]+>|\$\{[^}]+\}|\{\{[^}]+\}\}|__[^_]+__)")


@dataclass
class Finding:
    level: str
    path: str
    message: str


class Collector:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def error(self, path: str, message: str) -> None:
        self.findings.append(Finding("ERROR", path, message))

    def warn(self, path: str, message: str) -> None:
        self.findings.append(Finding("WARN", path, message))

    def info(self, path: str, message: str) -> None:
        self.findings.append(Finding("INFO", path, message))

    @property
    def has_errors(self) -> bool:
        return any(finding.level == "ERROR" for finding in self.findings)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_node_object(value: Any) -> bool:
    return isinstance(value, dict) and ("class_type" in value or "inputs" in value)


def looks_like_prompt(value: Any) -> bool:
    return isinstance(value, dict) and bool(value) and all(is_node_object(node) for node in value.values())


def looks_like_ui_workflow(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("nodes"), list)
        and ("links" in value or "version" in value or "groups" in value or "config" in value)
    )


def extract_prompt(document: Any, collector: Collector, allow_ui_workflow: bool) -> tuple[dict[str, Any] | None, str]:
    if looks_like_prompt(document):
        return document, "$"

    if isinstance(document, dict) and "prompt" in document:
        prompt = document["prompt"]
        if looks_like_prompt(prompt) or isinstance(prompt, dict):
            return prompt, "$.prompt"
        collector.error("$.prompt", "prompt wrapper exists but prompt is not an object")
        return None, "$.prompt"

    if looks_like_ui_workflow(document):
        message = "file looks like a UI workflow export, not API prompt JSON"
        if allow_ui_workflow:
            collector.warn("$", message)
            return None, "$"
        collector.error("$", message + "; export/convert to API format before POSTing")
        return None, "$"

    if isinstance(document, dict):
        collector.error("$", "JSON object does not look like a ComfyUI API prompt or prompt wrapper")
    else:
        collector.error("$", "top-level JSON must be an object")
    return None, "$"


def is_link(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[1], int)
        and not isinstance(value[1], bool)
        and isinstance(value[0], (str, int))
    )


def maybe_bad_link(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 2 and isinstance(value[0], (str, int)) and not is_link(value)


def walk_values(value: Any, path: str):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk_values(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_values(child, f"{path}[{index}]")


def validate_prompt(prompt: dict[str, Any], base_path: str, collector: Collector, allow_templates: bool) -> None:
    if not prompt:
        collector.error(base_path, "prompt object is empty")
        return

    node_ids = {str(node_id) for node_id in prompt.keys()}
    output_like_nodes: list[str] = []
    referenced_nodes: set[str] = set()

    for raw_node_id, node in prompt.items():
        node_id = str(raw_node_id)
        node_path = f"{base_path}.{node_id}"

        if not isinstance(raw_node_id, str):
            collector.warn(node_path, "node id key is not a string after JSON parsing; treat ids as strings")

        if not isinstance(node, dict):
            collector.error(node_path, "node value must be an object")
            continue

        class_type = node.get("class_type")
        if not isinstance(class_type, str) or not class_type.strip():
            collector.error(f"{node_path}.class_type", "class_type must be a non-empty string")
        else:
            lowered = class_type.lower()
            if any(pattern in lowered for pattern in LIKELY_OUTPUT_CLASS_PATTERNS):
                output_like_nodes.append(node_id)

        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            collector.error(f"{node_path}.inputs", "inputs must be an object")
            continue

        for input_name, input_value in inputs.items():
            input_path = f"{node_path}.inputs.{input_name}"
            if is_link(input_value):
                upstream_id = str(input_value[0])
                output_index = input_value[1]
                referenced_nodes.add(upstream_id)
                if upstream_id not in node_ids:
                    collector.error(input_path, f"link references missing upstream node {upstream_id!r}")
                if output_index < 0:
                    collector.error(input_path, "link output_index must be >= 0")
            elif maybe_bad_link(input_value):
                collector.error(input_path, "value looks like a link but is not [node_id, integer_output_index]")

            if allow_templates:
                for value_path, nested_value in walk_values(input_value, input_path):
                    if isinstance(nested_value, str) and PLACEHOLDER_RE.search(nested_value):
                        collector.info(value_path, "template placeholder detected; replace before live execution")

    if not output_like_nodes:
        collector.warn(base_path, "no likely output node found; confirm partial execution target or add Save/Preview/Output node")

    terminal_nodes = sorted(node_ids - referenced_nodes)
    if terminal_nodes:
        collector.info(base_path, f"terminal nodes not consumed by other nodes: {', '.join(terminal_nodes[:12])}{' ...' if len(terminal_nodes) > 12 else ''}")


def print_findings(path: Path, collector: Collector) -> None:
    if not collector.findings:
        print(f"{path}: OK")
        return
    for finding in collector.findings:
        print(f"{path}: {finding.level}: {finding.path}: {finding.message}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate ComfyUI API prompt JSON structure without importing ComfyUI.",
    )
    parser.add_argument("files", nargs="+", type=Path, help="JSON prompt, prompt wrapper, or workflow/template files")
    parser.add_argument(
        "--allow-ui-workflow",
        action="store_true",
        help="treat UI workflow exports as warnings instead of errors",
    )
    parser.add_argument(
        "--allow-templates",
        action="store_true",
        help="report placeholder strings as info instead of treating templates as ready-to-run prompts",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    exit_code = 0

    for file_path in args.files:
        collector = Collector()
        try:
            document = load_json(file_path)
        except FileNotFoundError:
            print(f"{file_path}: ERROR: file not found", file=sys.stderr)
            exit_code = 2
            continue
        except json.JSONDecodeError as exc:
            print(f"{file_path}: ERROR: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
            exit_code = 2
            continue

        prompt, base_path = extract_prompt(document, collector, args.allow_ui_workflow)
        if prompt is not None:
            validate_prompt(prompt, base_path, collector, args.allow_templates)

        print_findings(file_path, collector)
        if collector.has_errors:
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
