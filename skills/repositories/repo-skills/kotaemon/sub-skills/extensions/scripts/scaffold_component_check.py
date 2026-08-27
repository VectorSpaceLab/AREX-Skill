#!/usr/bin/env python3
"""Static compatibility checker for Kotaemon/ktem extension files or templates.

The checker intentionally avoids importing target code. It parses Python with
`ast` and scans packaging/config text so it is safe to run on untrusted drafts.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Finding:
    level: str
    message: str
    path: Path | None = None

    def render(self) -> str:
        prefix = self.level.upper()
        if self.path:
            return f"[{prefix}] {self.path}: {self.message}"
        return f"[{prefix}] {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Statically check a Kotaemon/ktem component file or template directory."
    )
    parser.add_argument(
        "--path",
        required=True,
        type=Path,
        help="Python file or project/template directory to inspect.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures.",
    )
    return parser.parse_args()


def base_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = base_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Subscript):
        return base_name(node.value)
    return ""


def function_names(class_node: ast.ClassDef) -> set[str]:
    return {item.name for item in class_node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))}


def class_has_base(class_node: ast.ClassDef, expected: tuple[str, ...]) -> bool:
    names = {base_name(base).split(".")[-1] for base in class_node.bases}
    return any(name in names for name in expected)


def check_python_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as exc:
        return [Finding("error", f"Python syntax error: {exc}", path)]

    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    component_classes = [cls for cls in classes if class_has_base(cls, ("BaseComponent",))]
    index_classes = [cls for cls in classes if class_has_base(cls, ("BaseIndex", "BaseFileIndexIndexing", "BaseFileIndexRetriever"))]
    page_classes = [cls for cls in classes if class_has_base(cls, ("BasePage",))]

    if not classes:
        findings.append(Finding("warning", "No top-level classes found; extension modules usually expose classes.", path))

    for cls in component_classes:
        methods = function_names(cls)
        if "run" not in methods:
            findings.append(Finding("error", f"BaseComponent subclass `{cls.name}` is missing run(...).", path))
        annotated = [item for item in cls.body if isinstance(item, ast.AnnAssign)]
        if not annotated:
            findings.append(Finding("warning", f"Component `{cls.name}` has no annotated params or nodes.", path))

    for cls in index_classes:
        methods = function_names(cls)
        base_names = {base_name(base).split(".")[-1] for base in cls.bases}
        if "BaseFileIndexIndexing" in base_names:
            for required in ("run", "get_pipeline"):
                if required not in methods:
                    findings.append(Finding("error", f"Indexing pipeline `{cls.name}` is missing {required}(...).", path))
        if "BaseFileIndexRetriever" in base_names:
            for required in ("run", "get_pipeline"):
                if required not in methods:
                    findings.append(Finding("error", f"Retriever pipeline `{cls.name}` is missing {required}(...).", path))
        if "BaseIndex" in base_names:
            for required in ("on_start", "get_indexing_pipeline", "get_retriever_pipelines"):
                if required not in methods:
                    findings.append(Finding("warning", f"BaseIndex `{cls.name}` does not define {required}(...); inherited behavior must be intentional.", path))

    for cls in page_classes:
        methods = function_names(cls)
        if not ({"on_building_ui", "as_gradio_component"} & methods):
            findings.append(Finding("warning", f"BasePage `{cls.name}` has no UI-building method override.", path))

    if not (component_classes or index_classes or page_classes):
        findings.append(
            Finding(
                "warning",
                "No BaseComponent/BaseIndex/BaseFileIndex/BasePage subclasses found; verify this file is an extension entry point or helper.",
                path,
            )
        )

    dotted_literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and "." in node.value:
            if any(token in node.value for token in ("KH_", "FILE_INDEX", "ktem.", "kotaemon.")):
                dotted_literals.append(node.value)
    if dotted_literals:
        findings.append(Finding("info", f"Review dotted/import-like strings: {', '.join(sorted(set(dotted_literals))[:6])}", path))

    return findings


def iter_python_files(path: Path) -> list[Path]:
    if path.is_file() and path.suffix == ".py":
        return [path]
    if path.is_dir():
        ignored = {".git", "__pycache__", ".venv", "venv", "build", "dist"}
        files = []
        for child in path.rglob("*.py"):
            if any(part in ignored for part in child.parts):
                continue
            files.append(child)
        return sorted(files)
    return []


def check_template_dir(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not path.is_dir():
        return findings

    has_packaging = any((path / name).exists() for name in ("setup.py", "pyproject.toml", "setup.cfg"))
    if not has_packaging:
        findings.append(Finding("warning", "No setup.py, pyproject.toml, or setup.cfg found at template root.", path))

    package_dirs = [child for child in path.iterdir() if child.is_dir() and (child / "__init__.py").exists()]
    cookiecutter_dirs = [child for child in path.rglob("__init__.py") if "{{" in str(child)]
    if not package_dirs and not cookiecutter_dirs:
        findings.append(Finding("warning", "No obvious Python package directory with __init__.py found.", path))

    if (path / "cookiecutter.json").exists():
        findings.append(Finding("info", "Cookiecutter template detected; run checks on a generated project too.", path))

    text = "\n".join(
        file.read_text(encoding="utf-8", errors="replace")[:20000]
        for file in path.rglob("*.py")
        if file.is_file()
    )
    if "flowsettings" in text or "FILE_INDEX_" in text or "KH_REASONINGS" in text:
        findings.append(Finding("info", "Flowsettings registration hints found; verify dotted paths after installation.", path))

    return findings


def main() -> int:
    args = parse_args()
    target = args.path.expanduser().resolve()
    findings: list[Finding] = []

    if not target.exists():
        findings.append(Finding("error", "Path does not exist.", target))
    else:
        findings.extend(check_template_dir(target))
        py_files = iter_python_files(target)
        if not py_files:
            findings.append(Finding("warning", "No Python files found to inspect.", target))
        for file in py_files:
            findings.extend(check_python_file(file))

    for finding in findings:
        print(finding.render())

    has_error = any(f.level == "error" for f in findings)
    has_warning = any(f.level == "warning" for f in findings)
    if has_error or (args.strict and has_warning):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
