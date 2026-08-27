#!/usr/bin/env python3
"""Flag CUDA/Triton-only pytest skip conditions missing pytest.mark.gpu.

The script is standalone and scans only files or directories explicitly passed on
the command line. It is conservative: review findings manually when a custom skip
variable is shared by both CPU and GPU tests.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


GPU_TRIGGER_FRAGMENTS: tuple[str, ...] = (
    "torch.cuda",
    "cuda.is_available",
    "cuda.device_count",
    "_has_cuda",
    "has_cuda",
    "_has_triton",
    "has_triton",
    "requires_cuda",
    "cuda_required",
    "triton",
)


@dataclass(frozen=True)
class Issue:
    """One marker-policy issue."""

    path: str
    line: int
    node_type: str
    name: str
    message: str
    condition: str


@dataclass(frozen=True)
class MarkerSummary:
    """GPU and CUDA-skip markers found on a node."""

    has_gpu: bool
    cuda_skip_conditions: tuple[tuple[int, str], ...]


class MarkerChecker(ast.NodeVisitor):
    """AST visitor that checks module, class, and function pytest markers."""

    def __init__(self, path: Path, source: str) -> None:
        self.path = path
        self.source = source
        self.issues: list[Issue] = []
        self.module_summary = _module_marker_summary(source, ast.parse(source, filename=str(path)))
        self._gpu_scope_stack: list[bool] = [self.module_summary.has_gpu]

    def check_module(self) -> None:
        if self.module_summary.cuda_skip_conditions and not self.module_summary.has_gpu:
            for line, condition in self.module_summary.cuda_skip_conditions:
                self.issues.append(
                    Issue(
                        path=str(self.path),
                        line=line,
                        node_type="module",
                        name="pytestmark",
                        message="CUDA/Triton module-level skipif is missing pytest.mark.gpu",
                        condition=condition,
                    )
                )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        summary = _decorator_marker_summary(node.decorator_list, self.source)
        inherited_gpu = any(self._gpu_scope_stack)
        if summary.cuda_skip_conditions and not (summary.has_gpu or inherited_gpu):
            for line, condition in summary.cuda_skip_conditions:
                self.issues.append(
                    Issue(
                        path=str(self.path),
                        line=line,
                        node_type="class",
                        name=node.name,
                        message="CUDA/Triton class skipif is missing pytest.mark.gpu",
                        condition=condition,
                    )
                )
        self._gpu_scope_stack.append(summary.has_gpu or inherited_gpu)
        self.generic_visit(node)
        self._gpu_scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if not _could_be_pytest_test(node):
            return
        summary = _decorator_marker_summary(node.decorator_list, self.source)
        inherited_gpu = any(self._gpu_scope_stack)
        if summary.cuda_skip_conditions and not (summary.has_gpu or inherited_gpu):
            for line, condition in summary.cuda_skip_conditions:
                self.issues.append(
                    Issue(
                        path=str(self.path),
                        line=line,
                        node_type="function",
                        name=node.name,
                        message="CUDA/Triton test skipif is missing pytest.mark.gpu",
                        condition=condition,
                    )
                )
        self.generic_visit(node)


def _could_be_pytest_test(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return node.name.startswith("test_")


def _iter_python_files(paths: Iterable[Path]) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    errors: list[str] = []
    for path in paths:
        if not path.exists():
            errors.append(f"{path}: path does not exist")
            continue
        if path.is_dir():
            files.extend(sorted(child for child in path.rglob("*.py") if child.is_file()))
        elif path.suffix == ".py":
            files.append(path)
        else:
            errors.append(f"{path}: not a Python file or directory")
    return files, errors


def _node_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return _node_name(node.func)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _node_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
        return node.attr
    if isinstance(node, ast.Subscript):
        return _node_name(node.value)
    return None


def _is_gpu_mark(node: ast.AST) -> bool:
    name = _node_name(node)
    return name in {"pytest.mark.gpu", "mark.gpu"} or bool(name and name.endswith(".mark.gpu"))


def _is_skipif_mark(node: ast.AST) -> bool:
    name = _node_name(node)
    return name in {"pytest.mark.skipif", "mark.skipif"} or bool(
        name and name.endswith(".mark.skipif")
    )


def _source_segment(source: str, node: ast.AST) -> str:
    segment = ast.get_source_segment(source, node)
    if segment is not None:
        return " ".join(segment.split())
    return ast.dump(node, include_attributes=False)


def _condition_from_skipif(decorator: ast.AST, source: str) -> str | None:
    if not isinstance(decorator, ast.Call):
        return None
    if not _is_skipif_mark(decorator.func):
        return None
    if not decorator.args:
        return ""
    return _source_segment(source, decorator.args[0])


def _condition_is_cuda_only(condition: str) -> bool:
    lowered = condition.lower()
    return any(fragment.lower() in lowered for fragment in GPU_TRIGGER_FRAGMENTS)


def _flatten_marker_nodes(value: ast.AST) -> list[ast.AST]:
    if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
        nodes: list[ast.AST] = []
        for elt in value.elts:
            nodes.extend(_flatten_marker_nodes(elt))
        return nodes
    return [value]


def _decorator_marker_summary(decorators: Iterable[ast.expr], source: str) -> MarkerSummary:
    has_gpu = False
    cuda_skip_conditions: list[tuple[int, str]] = []
    for decorator in decorators:
        if _is_gpu_mark(decorator):
            has_gpu = True
        condition = _condition_from_skipif(decorator, source)
        if condition is not None and _condition_is_cuda_only(condition):
            cuda_skip_conditions.append((getattr(decorator, "lineno", 1), condition))
    return MarkerSummary(has_gpu=has_gpu, cuda_skip_conditions=tuple(cuda_skip_conditions))


def _module_marker_summary(source: str, tree: ast.Module) -> MarkerSummary:
    has_gpu = False
    cuda_skip_conditions: list[tuple[int, str]] = []
    for statement in tree.body:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        targets: list[ast.expr]
        if isinstance(statement, ast.Assign):
            targets = list(statement.targets)
            value = statement.value
        else:
            targets = [statement.target]
            value = statement.value
        if value is None:
            continue
        if not any(isinstance(target, ast.Name) and target.id == "pytestmark" for target in targets):
            continue
        for marker in _flatten_marker_nodes(value):
            if _is_gpu_mark(marker):
                has_gpu = True
            condition = _condition_from_skipif(marker, source)
            if condition is not None and _condition_is_cuda_only(condition):
                cuda_skip_conditions.append((getattr(marker, "lineno", 1), condition))
    return MarkerSummary(has_gpu=has_gpu, cuda_skip_conditions=tuple(cuda_skip_conditions))


def check_file(path: Path) -> tuple[list[Issue], str | None]:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [], f"{path}: could not decode as UTF-8: {exc}"
    except OSError as exc:
        return [], f"{path}: could not read file: {exc}"

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [], f"{path}:{exc.lineno}: syntax error: {exc.msg}"

    checker = MarkerChecker(path, source)
    checker.check_module()
    checker.visit(tree)
    return checker.issues, None


def _issue_to_dict(issue: Issue) -> dict[str, object]:
    return {
        "path": issue.path,
        "line": issue.line,
        "node_type": issue.node_type,
        "name": issue.name,
        "message": issue.message,
        "condition": issue.condition,
    }


def _print_text(issues: list[Issue], errors: list[str]) -> None:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if not issues:
        if not errors:
            print("OK: no CUDA/Triton skipif markers missing pytest.mark.gpu were found.")
        return
    for issue in issues:
        print(
            f"{issue.path}:{issue.line}: {issue.message} "
            f"({issue.node_type} {issue.name}; condition: {issue.condition})"
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check CUDA/Triton pytest skipif markers for missing pytest.mark.gpu."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="Python test files or directories to scan.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    files, errors = _iter_python_files(args.paths)
    issues: list[Issue] = []

    for file_path in files:
        file_issues, error = check_file(file_path)
        issues.extend(file_issues)
        if error is not None:
            errors.append(error)

    if args.json:
        payload = {
            "issues": [_issue_to_dict(issue) for issue in issues],
            "errors": errors,
            "scanned_files": [str(path) for path in files],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_text(issues, errors)

    if errors:
        return 2
    if issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
