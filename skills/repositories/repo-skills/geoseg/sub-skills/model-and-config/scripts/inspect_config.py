#!/usr/bin/env python3
"""Safely inspect a GeoSeg Python config without importing or executing it.

The repository's normal py2cfg loader imports a config and therefore may create
an external-data dataset, instantiate a model, load pretrained weights, and
construct optimizers. This helper only reads source text and parses its AST.
It is intentionally stdlib-only and works with the documented Python 3.8.
"""
from __future__ import print_function

import argparse
import ast
import json
import sys
from pathlib import Path


PATH_WORDS = (
    "path", "root", "dir", "file", "weight", "checkpoint", "ckpt",
    "data", "log", "output", "image", "mask",
)
RISK_CALLS = {
    "py2cfg", "py2dict", "DataLoader", "LoveDATrainDataset",
    "LoveDATestDataset", "PotsdamDataset", "VaihingenDataset",
    "UAVIDDataset", "UNetFormer", "dcswin_small", "dcswin_base",
    "dcswin_tiny", "ft_unetformer", "PyramidMamba", "EfficientPyramidMamba",
    "torch.load", "create_model", "AdamW", "Lookahead",
}


def source_segment(source, node):
    """Return a compact source expression on Python 3.8+ without execution."""
    try:
        segment = ast.get_source_segment(source, node)
    except (AttributeError, TypeError):
        segment = None
    if segment:
        return " ".join(segment.strip().split())
    return "<{}>".format(type(node).__name__)


def dotted_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return "{}.{}".format(parent, node.attr) if parent else node.attr
    return None


def literal_value(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None


def assignment_names(target):
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        names = []
        for item in target.elts:
            names.extend(assignment_names(item))
        return names
    return []


def call_names(tree):
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = dotted_name(node.func)
            if name:
                calls.append({
                    "name": name,
                    "line": getattr(node, "lineno", None),
                    "expression": source_segment(_SOURCE, node),
                    "risk": name in RISK_CALLS or name.rsplit(".", 1)[-1] in RISK_CALLS,
                })
    return calls


def path_reason(name, value):
    lowered = "{} {}".format(name, value).lower()
    if "pretrain" in lowered or "weight" in lowered or "checkpoint" in lowered or "ckpt" in lowered:
        return "checkpoint or pretrained-weight dependency"
    if "data" in lowered or "root" in lowered or "image" in lowered or "mask" in lowered:
        return "dataset/data-layout dependency"
    if "log" in lowered or "output" in lowered:
        return "output/log destination"
    return "path-like config value"


def inspect_config(path):
    global _SOURCE
    path = Path(path)
    if path.suffix != ".py":
        raise ValueError("config must have a .py suffix: {}".format(path))
    if not path.is_file():
        raise FileNotFoundError("config does not exist: {}".format(path))
    _SOURCE = path.read_text(encoding="utf-8")
    tree = ast.parse(_SOURCE, filename=str(path))

    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append("from {}".format(node.module or "."))

    assignments = []
    string_paths = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            continue
        if isinstance(node, ast.Assign):
            targets = []
            for target in node.targets:
                targets.extend(assignment_names(target))
            value_node = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = assignment_names(node.target)
            value_node = node.value
        else:
            targets = assignment_names(node.target)
            value_node = node.value
        expression = source_segment(_SOURCE, value_node) if value_node else None
        value = literal_value(value_node) if value_node else None
        assignments.append({
            "names": targets,
            "line": getattr(node, "lineno", None),
            "expression": expression,
            "literal": value,
        })
        if isinstance(value, str):
            for name in targets:
                if any(word in (name + " " + value).lower() for word in PATH_WORDS):
                    string_paths.append({
                        "name": name,
                        "line": getattr(node, "lineno", None),
                        "value": value,
                        "reason": path_reason(name, value),
                    })

    # Also report path-like literals nested in calls and formatted assignments,
    # such as data_root='data/...', weights_path='model_weights/...'.format(...),
    # and weight_path='pretrain_weights/...'.  This remains static: no values
    # are resolved and no call is executed.
    parents = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    seen_paths = {(item["line"], item["name"], item["value"]) for item in string_paths}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        value = node.value
        owner = parents.get(node)
        owner_name = None
        while owner is not None:
            if isinstance(owner, ast.keyword):
                owner_name = owner.arg
                break
            if isinstance(owner, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = []
                if isinstance(owner, ast.Assign):
                    for target in owner.targets:
                        targets.extend(assignment_names(target))
                else:
                    targets = assignment_names(owner.target)
                owner_name = targets[0] if targets else None
                break
            owner = parents.get(owner)
        display_name = owner_name or "<literal>"
        signal = (
            "/" in value or "\\\\" in value or
            value.endswith((".pth", ".pt", ".ckpt")) or
            any(word in (display_name + " " + value).lower() for word in PATH_WORDS)
        )
        key = (getattr(node, "lineno", None), display_name, value)
        if signal and key not in seen_paths:
            string_paths.append({
                "name": display_name,
                "line": getattr(node, "lineno", None),
                "value": value,
                "reason": path_reason(display_name, value),
            })
            seen_paths.add(key)

    calls = call_names(tree)
    risks = []
    if any("geoseg.datasets" in item for item in imports):
        risks.append("dataset module import may enumerate external files")
    if any(call["name"].rsplit(".", 1)[-1] in ("torch.load", "load") for call in calls):
        risks.append("config contains a checkpoint-load call")
    if any(call["name"].rsplit(".", 1)[-1] in ("UNetFormer", "dcswin_small", "dcswin_base", "dcswin_tiny", "ft_unetformer", "PyramidMamba", "EfficientPyramidMamba") for call in calls):
        risks.append("config constructs a model and may trigger timm/optional-weight access")
    if any("mamba" in item.lower() for item in imports + [call["name"] for call in calls]):
        risks.append("PyramidMamba/mamba_ssm is an optional dependency")

    return {
        "config": str(path),
        "mode": "static-ast; no imports or execution",
        "imports": imports,
        "assignments": assignments,
        "calls": calls,
        "required_paths": string_paths,
        "risk_flags": risks,
        "next_step": "Review paths and prerequisites before using tools.cfg.py2cfg.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Report GeoSeg config assignments and dependencies without importing it."
    )
    parser.add_argument("config", type=Path, help="Python config file")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    try:
        report = inspect_config(args.config)
    except (OSError, SyntaxError, ValueError) as exc:
        print("inspect_config: {}".format(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
        return 0
    print("Config: {}".format(report["config"]))
    print("Mode: {}".format(report["mode"]))
    print("Imports:")
    for item in report["imports"]:
        print("  - {}".format(item))
    print("Assignments:")
    for item in report["assignments"]:
        names = ", ".join(item["names"]) or "<unknown>"
        print("  - line {}: {} = {}".format(item["line"], names, item["expression"]))
    print("Calls with runtime implications:")
    for item in report["calls"]:
        if item["risk"]:
            print("  - line {}: {}".format(item["line"], item["expression"]))
    print("Required/path-like values:")
    for item in report["required_paths"]:
        print("  - {} (line {}): {} [{}]".format(item["name"], item["line"], item["value"], item["reason"]))
    print("Risk flags:")
    for item in report["risk_flags"]:
        print("  - {}".format(item))
    print(report["next_step"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
