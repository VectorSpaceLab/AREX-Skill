#!/usr/bin/env python3
"""Statically inspect ControlNet Gradio app scripts without importing them."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

APP_GLOB = "gradio_*2image*.py"
SIDE_EFFECT_CALLS = {
    "launch",
    "create_model",
    "load_state_dict",
    "DDIMSampler",
    "CannyDetector",
    "MLSDdetector",
    "HEDdetector",
    "OpenposeDetector",
    "UniformerDetector",
    "MidasDetector",
}


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def literal_or_source(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        return ast.unparse(node)


def signature_for(function: ast.FunctionDef) -> str:
    parts: list[str] = []
    defaults = [None] * (len(function.args.args) - len(function.args.defaults)) + list(function.args.defaults)
    for arg, default in zip(function.args.args, defaults):
        text = arg.arg
        if default is not None:
            text += f"={ast.unparse(default)}"
        parts.append(text)
    return f"{function.name}({', '.join(parts)})"


def collect_string_refs(tree: ast.AST) -> list[str]:
    refs: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            normalized = value[2:] if value.startswith("./") else value
            if normalized.startswith("models/") or normalized.startswith("annotator/ckpts/"):
                refs.add(normalized)
            elif "control_sd15" in value or "cldm_v15" in value:
                refs.add(normalized)
    return sorted(refs)


def collect_top_level_calls(tree: ast.Module) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for statement in tree.body:
        for node in ast.walk(statement):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node is not statement:
                continue
            if isinstance(node, ast.Call):
                name = dotted_name(node.func)
                short_name = name.rsplit(".", 1)[-1] if name else None
                if short_name in SIDE_EFFECT_CALLS:
                    calls.append({"name": name, "line": getattr(node, "lineno", None)})
    return calls


def collect_gradio_controls(tree: ast.AST) -> list[dict[str, Any]]:
    controls: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if dotted_name(node.func.value) != "gr":
            continue
        if node.func.attr not in {"Image", "Textbox", "Slider", "Checkbox", "Number", "Button"}:
            continue
        item: dict[str, Any] = {"kind": node.func.attr, "line": getattr(node, "lineno", None)}
        for keyword in node.keywords:
            if keyword.arg in {"label", "minimum", "maximum", "value", "step", "source", "type", "tool", "randomize"}:
                item[keyword.arg] = literal_or_source(keyword.value)
        controls.append(item)
    return controls


def inspect_file(path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    signatures = [signature_for(function) for function in functions if function.name in {"process", "create_canvas"}]
    return {
        "file": path.name,
        "signatures": signatures,
        "model_or_checkpoint_refs": collect_string_refs(tree),
        "gradio_controls": collect_gradio_controls(tree),
        "top_level_side_effect_calls": collect_top_level_calls(tree),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Statically list process signatures, Gradio controls, and model/checkpoint references from ControlNet gradio_*2image*.py files."
    )
    parser.add_argument("--repo-root", type=Path, required=True, help="Path to a ControlNet source checkout to inspect.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.expanduser().resolve()
    if not repo_root.is_dir():
        raise SystemExit(f"repo root does not exist or is not a directory: {repo_root}")

    paths = sorted(repo_root.glob(APP_GLOB))
    if not paths:
        raise SystemExit(f"no {APP_GLOB} files found under: {repo_root}")

    results = [inspect_file(path) for path in paths]
    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
        return 0

    for result in results:
        print(f"## {result['file']}")
        for signature in result["signatures"]:
            print(f"signature: {signature}")
        refs = result["model_or_checkpoint_refs"]
        print("model/checkpoint refs: " + (", ".join(refs) if refs else "none found"))
        side_effects = result["top_level_side_effect_calls"]
        if side_effects:
            calls = ", ".join(f"{item['name']}@{item['line']}" for item in side_effects)
            print(f"top-level side effects: {calls}")
        controls = result["gradio_controls"]
        if controls:
            print("controls:")
            for control in controls:
                label = control.get("label", control.get("kind"))
                details = []
                for key in ("value", "minimum", "maximum", "step", "source", "type", "tool", "randomize"):
                    if key in control:
                        details.append(f"{key}={control[key]!r}")
                suffix = f" ({', '.join(details)})" if details else ""
                print(f"  - {control['kind']}: {label}{suffix}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
