#!/usr/bin/env python3
"""Safely preflight a custom MergeKit method with Python's AST parser.

This helper never imports the candidate module, MergeKit, PyTorch, or optional
evolution packages. It checks decorator/task shape and, when requested, the
static import or registry anchor. It does not execute a merge or prove tensor
semantics.

Examples:
  python scripts/check_extension_registration.py --api decorator \
      --module path/to/method.py --import-anchor path/to/package_init.py
  python scripts/check_extension_registration.py --api class \
      --module path/to/method.py --registry path/to/registry.py
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import sys
from dataclasses import dataclass, field
from typing import Iterable, Optional


@dataclass
class Finding:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    names: list[str] = field(default_factory=list)


def dotted(node: ast.AST | None) -> str:
    if node is None:
        return ""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def string_value(node: ast.AST | None) -> Optional[str]:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def subscript_parts(node: ast.AST | None) -> tuple[str, list[ast.AST]]:
    if not isinstance(node, ast.Subscript):
        return "", []
    value = dotted(node.value)
    slice_node = node.slice
    if isinstance(slice_node, ast.Tuple):
        return value, list(slice_node.elts)
    return value, [slice_node]


def is_list_of_torch_tensor(annotation: ast.AST | None) -> bool:
    container, args = subscript_parts(annotation)
    return container in {"List", "list", "typing.List"} and len(args) == 1 and dotted(args[0]) in {
        "torch.Tensor",
        "Tensor",
    }


def decorator_call(node: ast.AST) -> tuple[Optional[str], bool]:
    """Return the declared merge name and whether this is @merge_method."""
    call = node.func if isinstance(node, ast.Call) else node
    name = dotted(call)
    if name not in {"merge_method", "easy_define.merge_method"}:
        return None, False
    if not isinstance(node, ast.Call):
        return None, True
    declared = None
    if node.args:
        declared = string_value(node.args[0])
    for keyword in node.keywords:
        if keyword.arg == "name":
            declared = string_value(keyword.value)
    return declared, True


def class_method_names(node: ast.ClassDef) -> set[str]:
    return {
        item.name
        for item in node.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def inspect_candidate(path: pathlib.Path, api: str) -> Finding:
    finding = Finding()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        finding.errors.append(f"cannot parse candidate {path}: {exc}")
        return finding

    if api in {"auto", "decorator"}:
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            declared = None
            seen_decorator = False
            for decorator in node.decorator_list:
                maybe_name, is_merge = decorator_call(decorator)
                if is_merge:
                    seen_decorator = True
                    declared = maybe_name or declared
            if not seen_decorator:
                continue
            if not declared:
                finding.errors.append(
                    f"{path}:{node.lineno}: @merge_method needs a string name"
                )
            else:
                finding.names.append(declared)
            args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            tensors = next((arg for arg in args if arg.arg == "tensors"), None)
            if tensors is None:
                finding.errors.append(
                    f"{path}:{node.lineno}: decorated function lacks tensors parameter"
                )
            elif not is_list_of_torch_tensor(tensors.annotation):
                finding.errors.append(
                    f"{path}:{node.lineno}: tensors must be annotated List[torch.Tensor]"
                )
            for arg in args:
                if arg.arg in {"tensors", "base_tensor", "output_weight", "base_model"}:
                    continue
                if arg.annotation is None:
                    finding.errors.append(
                        f"{path}:{node.lineno}: parameter {arg.arg!r} lacks an annotation"
                    )
        if api == "decorator" and not finding.names:
            finding.errors.append("no @merge_method function found")

    if api in {"auto", "class"}:
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = {dotted(base) for base in node.bases}
            if "MergeMethod" not in bases and "merge_methods.base.MergeMethod" not in bases:
                continue
            finding.names.append(node.name)
            methods = class_method_names(node)
            for required in ("name", "make_task"):
                if required not in methods:
                    finding.errors.append(
                        f"{path}:{node.lineno}: MergeMethod {node.name} lacks {required}()"
                    )
        if api == "class" and not finding.names:
            finding.errors.append("no class extending MergeMethod found")

    if len(finding.names) != len(set(finding.names)):
        finding.errors.append("candidate declares duplicate method/class names")
    return finding


def assigned_list(tree: ast.AST, variable: str) -> Iterable[ast.AST]:
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(isinstance(target, ast.Name) and target.id == variable for target in targets):
            value = node.value
            if isinstance(value, (ast.List, ast.Tuple)):
                yield from value.elts


def check_import_anchor(path: pathlib.Path, candidate: pathlib.Path, names: list[str]) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        return [f"cannot parse import anchor {path}: {exc}"]
    candidate_stem = candidate.stem
    imported = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = imported or any(alias.name.rsplit(".", 1)[-1] == candidate_stem for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported = imported or any(alias.name in names or alias.name == "*" for alias in node.names)
    return [] if imported else [
        f"{path} has no static import of {candidate_stem}; decorator registration will not run"
    ]


def check_registry(path: pathlib.Path, names: list[str]) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        return [f"cannot parse registry {path}: {exc}"]
    registered = set()
    for element in assigned_list(tree, "STATIC_MERGE_METHODS"):
        if isinstance(element, ast.Call):
            called = dotted(element.func)
            if called:
                registered.add(called.rsplit(".", 1)[-1])
    missing = [name for name in names if name not in registered]
    if missing:
        return [
            "class method(s) are not instantiated in STATIC_MERGE_METHODS: "
            + ", ".join(missing)
        ]
    return []


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AST-only, non-executing MergeKit extension registration check."
    )
    parser.add_argument("--api", choices=("auto", "decorator", "class"), default="auto")
    parser.add_argument("--module", type=pathlib.Path, required=True)
    parser.add_argument(
        "--import-anchor",
        type=pathlib.Path,
        help="Import file required for decorator registration",
    )
    parser.add_argument(
        "--registry",
        type=pathlib.Path,
        help="Registry file containing STATIC_MERGE_METHODS for class registration",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    finding = inspect_candidate(args.module, args.api)
    if args.api == "decorator" and args.import_anchor and finding.names:
        finding.errors.extend(check_import_anchor(args.import_anchor, args.module, finding.names))
    if args.api == "class" and not args.registry:
        finding.warnings.append("no --registry supplied; static registration was not checked")
    elif args.api == "class" and args.registry:
        finding.errors.extend(check_registry(args.registry, finding.names))

    for message in finding.errors:
        print(f"ERROR: {message}", file=sys.stderr)
    for message in finding.warnings:
        print(f"WARNING: {message}", file=sys.stderr)
    if not finding.errors:
        names = ", ".join(finding.names) if finding.names else "none"
        print(f"OK: candidate parsed; discovered {names}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
