#!/usr/bin/env python3
"""Inspect Kotaemon RAG core components with safe AST fallback.

The script first tries lightweight imports for selected modules so it can report
runtime signatures. If imports fail because optional provider/app dependencies are
missing, it falls back to parsing source with ast and reports the import error.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable

DEFAULT_MODULES = [
    "kotaemon.base.schema",
    "kotaemon.base.component",
    "kotaemon.indices.base",
    "kotaemon.indices.vectorindex",
    "kotaemon.indices.qa.citation",
    "kotaemon.indices.qa.citation_qa",
    "kotaemon.indices.qa.citation_qa_inline",
    "kotaemon.indices.qa.format_context",
    "kotaemon.indices.rankings.base",
    "kotaemon.indices.rankings.llm",
    "kotaemon.indices.rankings.llm_scoring",
    "kotaemon.llms.base",
    "kotaemon.llms.cot",
    "kotaemon.llms.branching",
    "kotaemon.llms.linear",
    "kotaemon.llms.prompts.base",
    "kotaemon.llms.prompts.template",
    "kotaemon.embeddings.base",
    "kotaemon.storages.docstores.base",
    "kotaemon.storages.docstores.in_memory",
    "kotaemon.storages.vectorstores.base",
    "kotaemon.storages.vectorstores.in_memory",
]

PUBLIC_DUNDER_METHODS = {"__call__", "__init__", "__iter__", "__next__"}


@dataclass
class FunctionInfo:
    name: str
    signature: str | None = None
    decorators: list[str] = field(default_factory=list)
    doc: str | None = None


@dataclass
class ClassInfo:
    name: str
    bases: list[str] = field(default_factory=list)
    methods: list[FunctionInfo] = field(default_factory=list)
    class_attributes: list[str] = field(default_factory=list)
    doc: str | None = None


@dataclass
class ModuleReport:
    module: str
    discovery_mode: str
    source_path: str | None = None
    import_error: str | None = None
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)


def is_public(name: str) -> bool:
    return not name.startswith("_") or name in PUBLIC_DUNDER_METHODS


def first_doc_line(doc: str | None) -> str | None:
    if not doc:
        return None
    for line in doc.strip().splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def safe_signature(obj: Any) -> str | None:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return None


def module_to_relative_path(module_name: str) -> Path:
    return Path(*module_name.split(".")).with_suffix(".py")


def find_package_root(repo_root: Path) -> Path:
    candidates = [
        repo_root / "libs" / "kotaemon",
        repo_root / "libs" / "kotaemon" / "kotaemon",
        repo_root,
    ]
    for candidate in candidates:
        if (candidate / "kotaemon").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not find kotaemon package root. Expected repo_root/libs/kotaemon/kotaemon."
    )


def source_path_for_module(repo_root: Path, module_name: str) -> Path | None:
    package_root = find_package_root(repo_root)
    path = package_root / module_to_relative_path(module_name)
    if path.exists():
        return path
    package_dir = package_root / Path(*module_name.split("."))
    init_path = package_dir / "__init__.py"
    if init_path.exists():
        return init_path
    return None


def add_repo_to_sys_path(repo_root: Path) -> None:
    paths = [repo_root / "libs" / "kotaemon", repo_root / "libs" / "ktem", repo_root]
    for path in reversed(paths):
        if path.exists():
            path_string = str(path)
            if path_string not in sys.path:
                sys.path.insert(0, path_string)


def inspect_imported_module(module_name: str, module: ModuleType) -> ModuleReport:
    source_path = None
    try:
        source_path = inspect.getsourcefile(module) or inspect.getfile(module)
    except TypeError:
        source_path = None

    report = ModuleReport(
        module=module_name,
        discovery_mode="import",
        source_path=source_path,
    )

    for name, obj in sorted(vars(module).items()):
        if not is_public(name):
            continue
        if inspect.isclass(obj) and getattr(obj, "__module__", None) == module.__name__:
            methods = []
            class_attributes = []
            for attr_name, attr_obj in sorted(vars(obj).items()):
                if not is_public(attr_name):
                    continue
                raw_obj = attr_obj
                if isinstance(attr_obj, (staticmethod, classmethod)):
                    raw_obj = attr_obj.__func__
                if inspect.isfunction(raw_obj):
                    methods.append(
                        FunctionInfo(
                            name=attr_name,
                            signature=safe_signature(raw_obj),
                            doc=first_doc_line(inspect.getdoc(raw_obj)),
                        )
                    )
                elif not inspect.isclass(raw_obj):
                    class_attributes.append(attr_name)

            report.classes.append(
                ClassInfo(
                    name=name,
                    bases=[base.__name__ for base in obj.__bases__],
                    methods=methods,
                    class_attributes=class_attributes,
                    doc=first_doc_line(inspect.getdoc(obj)),
                )
            )
        elif inspect.isfunction(obj) and getattr(obj, "__module__", None) == module.__name__:
            report.functions.append(
                FunctionInfo(
                    name=name,
                    signature=safe_signature(obj),
                    doc=first_doc_line(inspect.getdoc(obj)),
                )
            )

    return report


def decorator_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = decorator_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return decorator_name(node.func)
    return ""


def expr_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = expr_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Subscript):
        return expr_name(node.value)
    if isinstance(node, ast.Call):
        return expr_name(node.func)
    if isinstance(node, ast.Constant):
        return repr(node.value)
    return type(node).__name__


def ast_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    try:
        args = []
        posonly = getattr(node.args, "posonlyargs", [])
        positional = list(posonly) + list(node.args.args)
        defaults_offset = len(positional) - len(node.args.defaults)
        for idx, arg in enumerate(positional):
            text = arg.arg
            if arg.annotation is not None:
                text += f": {ast.unparse(arg.annotation)}"
            if idx >= defaults_offset:
                text += " = ..."
            args.append(text)
        if node.args.vararg:
            text = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation is not None:
                text += f": {ast.unparse(node.args.vararg.annotation)}"
            args.append(text)
        elif node.args.kwonlyargs:
            args.append("*")
        for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
            text = arg.arg
            if arg.annotation is not None:
                text += f": {ast.unparse(arg.annotation)}"
            if default is not None:
                text += " = ..."
            args.append(text)
        if node.args.kwarg:
            text = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation is not None:
                text += f": {ast.unparse(node.args.kwarg.annotation)}"
            args.append(text)
        signature = f"({', '.join(args)})"
        if node.returns is not None:
            signature += f" -> {ast.unparse(node.returns)}"
        return signature
    except Exception:
        return "(...)"


def inspect_ast_module(module_name: str, source_path: Path, import_error: str | None) -> ModuleReport:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    report = ModuleReport(
        module=module_name,
        discovery_mode="ast",
        source_path=str(source_path),
        import_error=import_error,
    )

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and is_public(node.name):
            methods = []
            class_attributes = []
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public(child.name):
                    methods.append(
                        FunctionInfo(
                            name=child.name,
                            signature=ast_signature(child),
                            decorators=[decorator_name(d) for d in child.decorator_list if decorator_name(d)],
                            doc=first_doc_line(ast.get_docstring(child)),
                        )
                    )
                elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name) and is_public(child.target.id):
                    class_attributes.append(child.target.id)
                elif isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name) and is_public(target.id):
                            class_attributes.append(target.id)
            report.classes.append(
                ClassInfo(
                    name=node.name,
                    bases=[expr_name(base) for base in node.bases],
                    methods=methods,
                    class_attributes=sorted(set(class_attributes)),
                    doc=first_doc_line(ast.get_docstring(node)),
                )
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public(node.name):
            report.functions.append(
                FunctionInfo(
                    name=node.name,
                    signature=ast_signature(node),
                    decorators=[decorator_name(d) for d in node.decorator_list if decorator_name(d)],
                    doc=first_doc_line(ast.get_docstring(node)),
                )
            )

    return report


def inspect_module(repo_root: Path, module_name: str, import_mode: str) -> ModuleReport:
    source_path = source_path_for_module(repo_root, module_name)
    import_error = None

    if import_mode != "never":
        add_repo_to_sys_path(repo_root)
        try:
            module = importlib.import_module(module_name)
            return inspect_imported_module(module_name, module)
        except Exception as exc:  # noqa: BLE001 - explain and continue with AST fallback.
            import_error = f"{exc.__class__.__name__}: {exc}"
            if import_mode == "always":
                raise

    if source_path is None:
        return ModuleReport(
            module=module_name,
            discovery_mode="missing",
            import_error=import_error or "source file not found",
        )

    return inspect_ast_module(module_name, source_path, import_error)


def module_lines(report: ModuleReport) -> Iterable[str]:
    yield f"## {report.module}"
    yield f"mode: {report.discovery_mode}"
    if report.source_path:
        yield f"source: {report.source_path}"
    if report.import_error:
        yield f"import_error: {report.import_error}"
    if not report.classes and not report.functions:
        yield "public_api: none discovered"
        yield ""
        return
    if report.classes:
        yield "classes:"
        for cls in report.classes:
            bases = f" ({', '.join(cls.bases)})" if cls.bases else ""
            doc = f" - {cls.doc}" if cls.doc else ""
            yield f"  - {cls.name}{bases}{doc}"
            if cls.class_attributes:
                yield f"    attributes: {', '.join(cls.class_attributes)}"
            if cls.methods:
                yield "    methods:"
                for method in cls.methods:
                    signature = method.signature or "(...)"
                    doc_suffix = f" - {method.doc}" if method.doc else ""
                    decorators = f" [{', '.join(method.decorators)}]" if method.decorators else ""
                    yield f"      - {method.name}{signature}{decorators}{doc_suffix}"
    if report.functions:
        yield "functions:"
        for func in report.functions:
            signature = func.signature or "(...)"
            doc_suffix = f" - {func.doc}" if func.doc else ""
            decorators = f" [{', '.join(func.decorators)}]" if func.decorators else ""
            yield f"  - {func.name}{signature}{decorators}{doc_suffix}"
    yield ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Kotaemon RAG core classes/functions with AST fallback."
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Path to a Kotaemon repository checkout.",
    )
    parser.add_argument(
        "--module",
        action="append",
        dest="modules",
        help="Module to inspect. Repeat to override the default RAG-core module set.",
    )
    parser.add_argument(
        "--import-mode",
        choices=["auto", "always", "never"],
        default="auto",
        help="auto imports then falls back to AST; always raises import errors; never uses AST only.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of text.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"error: repo root does not exist: {repo_root}", file=sys.stderr)
        return 2

    modules = args.modules or DEFAULT_MODULES
    reports = [inspect_module(repo_root, module, args.import_mode) for module in modules]

    if args.json:
        print(json.dumps([asdict(report) for report in reports], indent=2, sort_keys=True))
    else:
        print("Kotaemon RAG core component inspection")
        print(f"repo_root: {repo_root}")
        print(f"import_mode: {args.import_mode}")
        print(
            "note: ast mode means import failed or was skipped; class/function discovery still uses source parsing."
        )
        print("")
        for report in reports:
            print("\n".join(module_lines(report)))

    missing = [report.module for report in reports if report.discovery_mode == "missing"]
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
