#!/usr/bin/env python3
"""Statically inspect Krita AI Diffusion custom ComfyUI workflow JSON files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PLACEHOLDERS = {
    "ETN_KritaCanvas",
    "ETN_KritaOutput",
    "ETN_KritaImageLayer",
    "ETN_KritaMaskLayer",
    "ETN_KritaStyle",
    "ETN_KritaStyleAndPrompt",
    "ETN_KritaSelection",
    "ETN_Parameter",
}

PARAM_TYPES = {
    "number (integer)": "number_int",
    "number": "number_float",
    "toggle": "toggle",
    "text": "text",
    "prompt (positive)": "prompt_positive",
    "prompt (negative)": "prompt_negative",
    "choice": "choice",
    "auto": "auto",
}


def load_graph(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "nodes" in data and isinstance(data["nodes"], list):
        # UI-format workflow.
        graph = {}
        for node in data["nodes"]:
            node_id = str(node.get("id"))
            graph[node_id] = {
                "class_type": node.get("type"),
                "inputs": {inp.get("name", f"input_{i}"): inp.get("link") for i, inp in enumerate(node.get("inputs", []))},
                "_meta": {"title": node.get("title") or node.get("type")},
            }
        return graph
    if isinstance(data, dict):
        return data
    raise ValueError("workflow JSON root must be an object")


def split_order(text: str) -> tuple[int, str]:
    if ". " in text:
        prefix, rest = text.split(". ", 1)
        if prefix.isdigit():
            return int(prefix), rest.strip()
    return 0, text


def split_name(name: str) -> tuple[str, str, int, int]:
    group, display = ("", name.rsplit("/", 1)[0]) if False else ("", name)
    if "/" in name:
        group, display = name.rsplit("/", 1)
    group_order, group_name = split_order(group)
    display_order, display_name = split_order(display)
    return group_name, display_name, group_order, display_order


def param_from_node(node_id: str, node: dict[str, Any]) -> dict[str, Any] | None:
    node_type = node.get("class_type")
    inputs = node.get("inputs", {}) or {}
    if node_type == "ETN_KritaStyle":
        name = inputs.get("name", "Style")
        kind = "style"
    elif node_type == "ETN_KritaImageLayer":
        name = inputs.get("name", "Image")
        kind = "image_layer"
    elif node_type == "ETN_KritaMaskLayer":
        name = inputs.get("name", "Mask")
        kind = "mask_layer"
    elif node_type == "ETN_Parameter":
        name = inputs.get("name", "Parameter")
        raw_type = inputs.get("type", "")
        kind = PARAM_TYPES.get(raw_type, f"unsupported:{raw_type}")
        if kind == "auto":
            return None
    else:
        return None
    group, display, group_order, display_order = split_name(str(name))
    return {
        "node": node_id,
        "kind": kind,
        "name": name,
        "display": display,
        "group": group,
        "group_order": group_order,
        "display_order": display_order,
        "default": inputs.get("default"),
        "min": inputs.get("min"),
        "max": inputs.get("max"),
    }


def inspect(path: Path) -> dict[str, Any]:
    graph = load_graph(path)
    warnings = []
    placeholders = []
    params = []
    outputs = []
    links = 0
    style_prompt_count = 0

    for node_id, node in graph.items():
        if not isinstance(node, dict):
            warnings.append(f"node {node_id} is not an object")
            continue
        node_type = node.get("class_type")
        inputs = node.get("inputs", {}) or {}
        for value in inputs.values():
            if isinstance(value, list) and len(value) == 2:
                links += 1
        if node_type in PLACEHOLDERS:
            placeholders.append({"node": node_id, "type": node_type, "inputs": inputs})
        if node_type == "ETN_KritaStyleAndPrompt":
            style_prompt_count += 1
        if node_type == "ETN_KritaOutput":
            outputs.append({"node": node_id, "inputs": inputs})
        param = param_from_node(str(node_id), node)
        if param:
            params.append(param)

    if style_prompt_count > 1:
        warnings.append("Workflow contains multiple 'Krita Style & Prompt' nodes, but only one is allowed.")
    for param in params:
        if str(param["kind"]).startswith("unsupported:"):
            warnings.append(f"Unsupported parameter type for node {param['node']}: {param['kind'].split(':', 1)[1]}")

    params.sort(key=lambda p: (p["group_order"], p["group"], p["display_order"], p["display"]))
    grouped: dict[str, list[str]] = {}
    for p in params:
        grouped.setdefault(p["group"] or "<ungrouped>", []).append(p["display"])

    return {
        "workflow": str(path),
        "node_count": len(graph),
        "placeholders": placeholders,
        "parameters": params,
        "grouped_order": grouped,
        "outputs": outputs,
        "link_count": links,
        "warnings": warnings,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Statically inspect a Krita AI Diffusion custom workflow JSON file.")
    parser.add_argument("workflow", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    info = inspect(args.workflow)
    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True))
        return 0

    print(f"Workflow: {info['workflow']}")
    print(f"Node count: {info['node_count']}")
    print("\nKrita placeholders:")
    for item in info["placeholders"]:
        print(f"  - #{item['node']} {item['type']} inputs={json.dumps(item['inputs'], sort_keys=True)}")
    if not info["placeholders"]:
        print("  none detected")
    print("\nParameters:")
    for i, param in enumerate(info["parameters"], 1):
        group = f"; group='{param['group']}'" if param["group"] else ""
        print(f"  - {i}. #{param['node']} '{param['name']}'; kind={param['kind']}; display='{param['display']}'{group}; default={param['default']!r}; range=({param['min']}, {param['max']})")
    if not info["parameters"]:
        print("  none detected")
    print("\nGrouped order:")
    for group, names in info["grouped_order"].items():
        print(f"  - {group}: {', '.join(names)}")
    if not info["grouped_order"]:
        print("  none")
    print("\nOutputs:")
    for item in info["outputs"]:
        print(f"  - #{item['node']} inputs={json.dumps(item['inputs'], sort_keys=True)}")
    if not info["outputs"]:
        print("  none detected")
    print(f"\nLinks: {info['link_count']} edges")
    print("\nWarnings:")
    if info["warnings"]:
        for warning in info["warnings"]:
            print(f"  - {warning}")
    else:
        print("  - none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
