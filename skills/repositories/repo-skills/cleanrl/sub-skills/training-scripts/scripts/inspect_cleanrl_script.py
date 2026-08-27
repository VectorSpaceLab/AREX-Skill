#!/usr/bin/env python3
"""Inspect CleanRL training script arguments without importing the script.

The helper parses Python source with ast and summarizes dataclass Args defaults
or argparse add_argument calls. It intentionally avoids importing CleanRL,
Gym, JAX, EnvPool, MuJoCo, Procgen, PettingZoo, IsaacGym, or other optional
runtime packages.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


def unparse(node: ast.AST | None) -> str:
    if node is None:
        return "None"
    try:
        return ast.unparse(node)
    except Exception:
        return type(node).__name__


def literal_or_source(node: ast.AST | None) -> Any:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        return unparse(node)


def docstring_after(statements: list[ast.stmt], index: int) -> str | None:
    if index + 1 >= len(statements):
        return None
    next_node = statements[index + 1]
    if isinstance(next_node, ast.Expr) and isinstance(next_node.value, ast.Constant):
        if isinstance(next_node.value.value, str):
            return next_node.value.value.strip()
    return None


def is_args_class(node: ast.ClassDef) -> bool:
    if node.name == "Args":
        return True
    return any(
        isinstance(deco, ast.Name) and deco.id == "dataclass"
        or isinstance(deco, ast.Attribute) and deco.attr == "dataclass"
        for deco in node.decorator_list
    ) and node.name.lower() == "args"


def inspect_dataclass_args(tree: ast.Module) -> list[dict[str, Any]]:
    args: list[dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or not is_args_class(node):
            continue
        for index, statement in enumerate(node.body):
            name = None
            annotation = None
            default = None
            if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                name = statement.target.id
                annotation = unparse(statement.annotation)
                default = literal_or_source(statement.value)
            elif isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
                name = statement.targets[0].id
                default = literal_or_source(statement.value)
            if name:
                args.append(
                    {
                        "name": name,
                        "flag": "--" + name.replace("_", "-"),
                        "annotation": annotation,
                        "default": default,
                        "help": docstring_after(node.body, index),
                        "source": "dataclass",
                    }
                )
    return args


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{call_name(node.value)}.{node.attr}"
    return ""


def inspect_argparse_args(tree: ast.Module) -> list[dict[str, Any]]:
    args: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not call_name(node.func).endswith("add_argument"):
            continue
        flags = [literal_or_source(arg) for arg in node.args if isinstance(literal_or_source(arg), str)]
        kwargs = {kw.arg: literal_or_source(kw.value) for kw in node.keywords if kw.arg}
        primary_flag = next((flag for flag in flags if isinstance(flag, str) and flag.startswith("--")), None)
        if not primary_flag:
            continue
        name = primary_flag.lstrip("-").replace("-", "_")
        args.append(
            {
                "name": name,
                "flag": primary_flag,
                "aliases": flags,
                "annotation": kwargs.get("type"),
                "default": kwargs.get("default"),
                "help": kwargs.get("help"),
                "source": "argparse",
            }
        )
    return args


def inspect_script(path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    args = inspect_dataclass_args(tree)
    argparse_args = inspect_argparse_args(tree)
    if argparse_args:
        args.extend(argparse_args)

    classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
    functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    return {
        "script": str(path),
        "argument_style": "argparse" if argparse_args and not inspect_dataclass_args(tree) else "tyro/dataclass" if args else "unknown",
        "args_count": len(args),
        "args": args,
        "classes": classes,
        "functions": functions,
        "imports": sorted({item for item in imports if item}),
    }


def render_markdown(data: dict[str, Any]) -> str:
    lines = [f"# {data['script']}", ""]
    lines.append(f"- Argument style: `{data['argument_style']}`")
    lines.append(f"- Args discovered: `{data['args_count']}`")
    if data.get("classes"):
        lines.append(f"- Classes: `{', '.join(data['classes'])}`")
    if data.get("functions"):
        lines.append(f"- Functions: `{', '.join(data['functions'])}`")
    lines.append("")
    lines.append("| Flag | Default | Help |")
    lines.append("| --- | --- | --- |")
    for item in data["args"]:
        default = str(item.get("default", ""))
        help_text = str(item.get("help") or "").replace("\n", " ")
        lines.append(f"| `{item['flag']}` | `{default}` | {help_text} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect CleanRL script Args without importing optional dependencies.")
    parser.add_argument("script", type=Path, help="Path to a CleanRL Python script")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format")
    parser.add_argument("--only-common", action="store_true", help="Only print commonly adjusted training flags")
    args = parser.parse_args()

    data = inspect_script(args.script)
    if args.only_common:
        common = {
            "exp_name",
            "seed",
            "cuda",
            "track",
            "wandb_project_name",
            "wandb_entity",
            "capture_video",
            "capture_video",
            "save_model",
            "upload_model",
            "hf_entity",
            "env_id",
            "total_timesteps",
            "num_envs",
            "num_steps",
            "num_minibatches",
            "learning_starts",
            "buffer_size",
            "batch_size",
        }
        data["args"] = [item for item in data["args"] if item["name"] in common]
        data["args_count"] = len(data["args"])

    if args.format == "markdown":
        print(render_markdown(data), end="")
    else:
        print(json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
