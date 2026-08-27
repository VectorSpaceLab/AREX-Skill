#!/usr/bin/env python3
"""Static checker for TTS adapter contracts.

Heuristic only:
- parses the adapter file with AST
- never imports the adapter module
- never instantiates a model or runs inference
- warns about missing adapter class names, contract attributes, and method shapes
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

REGISTER_DECORATOR = "register_tts_adapter"
ADAPTER_BASE_NAMES = {"TTSModelAdapter", "ARTTSAdapter", "DiffusionTTSAdapter"}
COMMON_METHODS = (
    "normalize",
    "validate",
    "build",
    "apply_sampling_overrides",
    "matches",
    "stage_serves_speech",
    "extra_body_params",
)


@dataclass(slots=True)
class ClassSummary:
    node: ast.ClassDef
    decorators: set[str]
    bases: set[str]
    methods: dict[str, ast.AST]
    class_attrs: set[str]


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return dotted_name(node.func)
    return None


def decorator_name(node: ast.AST) -> str | None:
    name = dotted_name(node)
    if name is None:
        return None
    return name.rsplit(".", 1)[-1]


def collect_class_summary(node: ast.ClassDef) -> ClassSummary:
    decorators = {name for dec in node.decorator_list if (name := decorator_name(dec))}
    bases = {name.rsplit(".", 1)[-1] for base in node.bases if (name := dotted_name(base))}
    methods: dict[str, ast.AST] = {}
    class_attrs: set[str] = set()

    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods[item.name] = item
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    class_attrs.add(target.id)
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            class_attrs.add(item.target.id)

    return ClassSummary(
        node=node,
        decorators=decorators,
        bases=bases,
        methods=methods,
        class_attrs=class_attrs,
    )


def method_decorators(node: ast.AST) -> set[str]:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return set()
    return {name for dec in node.decorator_list if (name := decorator_name(dec))}


def gather_effective_contract(
    summary: ClassSummary,
    class_map: dict[str, ClassSummary],
    stack: set[str] | None = None,
) -> tuple[dict[str, ast.AST], set[str]]:
    stack = set() if stack is None else set(stack)
    if summary.node.name in stack:
        return {}, set()
    stack.add(summary.node.name)

    methods: dict[str, ast.AST] = {}
    class_attrs: set[str] = set()
    for base_name in sorted(summary.bases):
        base = class_map.get(base_name)
        if base is None:
            continue
        inherited_methods, inherited_attrs = gather_effective_contract(base, class_map, stack)
        methods.update(inherited_methods)
        class_attrs.update(inherited_attrs)

    methods.update(summary.methods)
    class_attrs.update(summary.class_attrs)
    return methods, class_attrs


def warn(path: Path, lineno: int, message: str) -> None:
    print(f"{path}:{lineno}: warning: {message}", file=sys.stderr)


def info(path: Path, lineno: int, message: str) -> None:
    print(f"{path}:{lineno}: {message}")


def choose_targets(classes: list[ClassSummary], class_name: str | None) -> tuple[list[ClassSummary], bool]:
    class_map = {summary.node.name: summary for summary in classes}
    if class_name is not None:
        summary = class_map.get(class_name)
        if summary is None:
            return [], False
        return [summary], False

    decorated = [summary for summary in classes if REGISTER_DECORATOR in summary.decorators]
    if decorated:
        return decorated, True

    fallback = [
        summary
        for summary in classes
        if summary.node.name.endswith("Adapter") or bool(summary.bases & ADAPTER_BASE_NAMES)
    ]
    return fallback, False


def inspect_class(path: Path, summary: ClassSummary, class_map: dict[str, ClassSummary]) -> None:
    effective_methods, effective_attrs = gather_effective_contract(summary, class_map)
    direct_methods = sorted(summary.methods)
    bases_text = ",".join(sorted(summary.bases)) or "-"
    methods_text = ",".join(direct_methods) or "-"
    info(
        path,
        summary.node.lineno,
        f"{summary.node.name}: bases={bases_text} methods={methods_text}",
    )

    if "name" not in effective_attrs:
        warn(path, summary.node.lineno, f"{summary.node.name} has no obvious class-level 'name' attribute")
    if "stage_keys" not in effective_attrs:
        warn(path, summary.node.lineno, f"{summary.node.name} has no obvious class-level 'stage_keys' attribute")

    build_node = effective_methods.get("build")
    if build_node is None:
        warn(
            path,
            summary.node.lineno,
            f"{summary.node.name} does not define build(); adapter contract usually expects async build",
        )
    elif not isinstance(build_node, ast.AsyncFunctionDef):
        warn(path, build_node.lineno, f"{summary.node.name}.build should usually be async def")

    for method_name in COMMON_METHODS:
        node = effective_methods.get(method_name)
        if node is None:
            continue
        decorators = method_decorators(node)
        if method_name in {"matches", "stage_serves_speech", "extra_body_params"} and "classmethod" not in decorators:
            warn(
                path,
                node.lineno,
                f"{summary.node.name}.{method_name} is usually a @classmethod in adapter contracts",
            )
        if method_name in {"normalize", "validate", "apply_sampling_overrides"} and decorators & {
            "classmethod",
            "staticmethod",
        }:
            bad_decorator = sorted(decorators & {"classmethod", "staticmethod"})[0]
            warn(
                path,
                node.lineno,
                f"{summary.node.name}.{method_name} is usually an instance method, not {bad_decorator}",
            )

    common_present = [name for name in COMMON_METHODS if name in effective_methods]
    if common_present:
        info(path, summary.node.lineno, f"{summary.node.name}: common hooks present -> {', '.join(common_present)}")
    else:
        warn(
            path,
            summary.node.lineno,
            f"{summary.node.name} exposes none of the common adapter hooks listed in the heuristic",
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Static, import-free checker for TTS adapter contract drift.")
    parser.add_argument("--adapter-file", required=True, help="Path to the adapter Python file to inspect")
    parser.add_argument(
        "--class-name",
        help=(
            "Optional class name to target inside the adapter file; when omitted, "
            "registered adapter classes are checked."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    adapter_path = Path(args.adapter_file)
    if not adapter_path.is_file():
        print(f"check_tts_adapter_contract: file not found: {adapter_path}", file=sys.stderr)
        return 1

    try:
        tree = ast.parse(adapter_path.read_text(encoding="utf-8"), filename=str(adapter_path))
    except SyntaxError as exc:
        print(f"check_tts_adapter_contract: syntax error in {adapter_path}: {exc}", file=sys.stderr)
        return 1

    classes = [collect_class_summary(node) for node in tree.body if isinstance(node, ast.ClassDef)]
    class_map = {summary.node.name: summary for summary in classes}
    if not classes:
        print(f"check_tts_adapter_contract: no top-level classes found in {adapter_path}", file=sys.stderr)
        return 1

    targets, found_registered = choose_targets(classes, args.class_name)
    if args.class_name is not None and not targets:
        print(
            f"check_tts_adapter_contract: class {args.class_name!r} not found in {adapter_path}",
            file=sys.stderr,
        )
        return 1
    if not targets:
        print(
            f"check_tts_adapter_contract: no registered or adapter-like class found in {adapter_path}",
            file=sys.stderr,
        )
        return 1
    if not found_registered and args.class_name is None:
        print(
            f"check_tts_adapter_contract: no @register_tts_adapter decorator found in {adapter_path}; "
            "using class-name heuristics",
            file=sys.stderr,
        )

    for summary in targets:
        inspect_class(adapter_path, summary, class_map)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
