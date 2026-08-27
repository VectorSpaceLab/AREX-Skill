#!/usr/bin/env python3
"""Scan MaaNTE custom action/recognition registry consistency.

The script is static: it does not import action modules and therefore avoids
platform/audio/game side effects.

Example:
    python sub-skills/custom-actions/scripts/check_custom_action_registry.py --repo-root /path/to/MaaNTE
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any


def strip_jsonc(text: str) -> str:
    out: list[str] = []
    i = 0
    in_str = False
    esc = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def decorator_name(dec: ast.AST, attr: str) -> str | None:
    if not isinstance(dec, ast.Call):
        return None
    func = dec.func
    if not isinstance(func, ast.Attribute) or func.attr != attr:
        return None
    if not dec.args or not isinstance(dec.args[0], ast.Constant) or not isinstance(dec.args[0].value, str):
        return None
    return dec.args[0].value


def scan_python(action_dir: Path) -> dict[str, dict[str, str]]:
    actions: dict[str, dict[str, str]] = {}
    recognitions: dict[str, dict[str, str]] = {}
    for path in sorted(action_dir.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            actions[f"<syntax-error:{path}>"] = {"class": "", "file": str(path), "error": str(exc)}
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for dec in node.decorator_list:
                name = decorator_name(dec, "custom_action")
                if name:
                    actions[name] = {"class": node.name, "file": str(path)}
                name = decorator_name(dec, "custom_recognition")
                if name:
                    recognitions[name] = {"class": node.name, "file": str(path)}
    return {"actions": actions, "recognitions": recognitions}


def walk_values(value: Any):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k, v
            yield from walk_values(v)
    elif isinstance(value, list):
        for item in value:
            yield from walk_values(item)


def scan_pipeline(pipeline_dir: Path) -> dict[str, set[str]]:
    action_refs: set[str] = set()
    recognition_refs: set[str] = set()
    for path in sorted(pipeline_dir.rglob("*.json")):
        try:
            data = json.loads(strip_jsonc(path.read_text(encoding="utf-8")))
        except Exception:
            continue
        for key, val in walk_values(data):
            if key == "custom_action" and isinstance(val, str):
                action_refs.add(val)
            if key == "custom_recognition" and isinstance(val, str):
                recognition_refs.add(val)
    return {"actions": action_refs, "recognitions": recognition_refs}


def parse_all(repo_root: Path) -> dict[str, Any]:
    action_dir = repo_root / "agent" / "custom" / "action"
    pipeline_dir = repo_root / "assets" / "resource" / "base" / "pipeline"
    py = scan_python(action_dir)
    refs = scan_pipeline(pipeline_dir)
    missing_actions = sorted(refs["actions"] - set(py["actions"]))
    missing_recognitions = sorted(refs["recognitions"] - set(py["recognitions"]))
    unused_actions = sorted(set(py["actions"]) - refs["actions"])
    unused_recognitions = sorted(set(py["recognitions"]) - refs["recognitions"])
    init_path = action_dir / "__init__.py"
    init_text = init_path.read_text(encoding="utf-8") if init_path.exists() else ""
    missing_class_exports = []
    for name, meta in sorted({**py["actions"], **py["recognitions"]}.items()):
        cls = meta.get("class")
        if cls and cls not in init_text:
            missing_class_exports.append({"decorator": name, "class": cls, "file": meta.get("file")})
    return {
        "decorated_actions": py["actions"],
        "decorated_recognitions": py["recognitions"],
        "pipeline_action_refs": sorted(refs["actions"]),
        "pipeline_recognition_refs": sorted(refs["recognitions"]),
        "missing_actions": missing_actions,
        "missing_recognitions": missing_recognitions,
        "unused_actions": unused_actions,
        "unused_recognitions": unused_recognitions,
        "missing_class_exports": missing_class_exports,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = parse_all(args.repo_root.resolve())
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("Pipeline custom_action refs:", ", ".join(report["pipeline_action_refs"]) or "-")
        print("Pipeline custom_recognition refs:", ", ".join(report["pipeline_recognition_refs"]) or "-")
        for key in ["missing_actions", "missing_recognitions", "missing_class_exports"]:
            values = report[key]
            if values:
                print(f"{key}:")
                for item in values:
                    print(f"  - {item}")
        print(f"Decorated actions: {len(report['decorated_actions'])}; recognitions: {len(report['decorated_recognitions'])}")
    return 1 if report["missing_actions"] or report["missing_recognitions"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
