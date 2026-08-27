#!/usr/bin/env python3
"""Statically check ZenML integration flavor files for unsafe imports."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

ALLOWED_THIRD_PARTY_ROOTS = {
    "pydantic",
    "typing_extensions",
    "yaml",
    "zenml",
}

IMPLEMENTATION_SEGMENTS = {
    "alerters",
    "annotators",
    "artifact_stores",
    "container_registries",
    "data_validators",
    "deployers",
    "experiment_trackers",
    "feature_stores",
    "image_builders",
    "log_stores",
    "materializers",
    "model_deployers",
    "model_registries",
    "orchestrators",
    "sandboxes",
    "service_connectors",
    "step_operators",
    "steps",
    "visualizers",
}


@dataclass(frozen=True)
class Finding:
    """One suspicious top-level import finding."""

    path: str
    line: int
    import_name: str
    reason: str
    guidance: str


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Scan ZenML integration flavor files for suspicious top-level "
            "optional SDK imports. The script uses Python AST only and does "
            "not import ZenML or integration packages."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help=(
            "Repository root, integrations directory, flavor directory, or "
            "individual Python flavor file. Defaults to the current directory."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    parser.add_argument(
        "--include-init",
        action="store_true",
        help="Also scan __init__.py files under flavor directories.",
    )
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Exit with status 1 when suspicious imports are found.",
    )
    return parser.parse_args(argv)


def iter_flavor_files(paths: Sequence[str], include_init: bool) -> list[Path]:
    """Resolve input paths to flavor Python files."""
    files: set[Path] = set()
    for raw_path in paths:
        path = Path(raw_path).resolve()
        if path.is_file() and path.suffix == ".py":
            files.add(path)
            continue

        candidate_roots = []
        if (path / "src" / "zenml" / "integrations").is_dir():
            candidate_roots.append(path / "src" / "zenml" / "integrations")
        if path.name == "integrations" and path.is_dir():
            candidate_roots.append(path)
        if path.name == "flavors" and path.is_dir():
            candidate_roots.append(path.parent.parent)

        for integrations_root in candidate_roots:
            files.update(integrations_root.glob("*/flavors/*.py"))

        if not candidate_roots and path.is_dir():
            files.update(path.glob("*/flavors/*.py"))
            files.update(path.glob("*.py"))

    resolved = [file for file in files if include_init or file.name != "__init__.py"]
    return sorted(resolved)


def is_type_checking_guard(node: ast.AST) -> bool:
    """Return whether an if node is guarded by TYPE_CHECKING."""
    if not isinstance(node, ast.If):
        return False
    test = node.test
    if isinstance(test, ast.Name):
        return test.id == "TYPE_CHECKING"
    if isinstance(test, ast.Attribute):
        return test.attr == "TYPE_CHECKING"
    return False


def top_level_imports(tree: ast.Module) -> Iterable[ast.Import | ast.ImportFrom]:
    """Yield imports that execute at module import time."""
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield node
        elif is_type_checking_guard(node):
            continue


def imported_names(node: ast.Import | ast.ImportFrom) -> list[str]:
    """Return display import names for an import node."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]

    prefix = "." * node.level
    module = node.module or ""
    if module:
        return [f"{prefix}{module}"]
    return [f"{prefix}{alias.name}" for alias in node.names]


def is_stdlib_root(root: str) -> bool:
    """Return whether an import root belongs to the Python standard library."""
    return root in getattr(sys, "stdlib_module_names", set())


def is_allowed_third_party(root: str) -> bool:
    """Return whether a non-stdlib root is safe for flavor modules."""
    return root in ALLOWED_THIRD_PARTY_ROOTS


def module_segments(import_name: str) -> list[str]:
    """Split a dotted import name into useful module segments."""
    return [segment for segment in import_name.lstrip(".").split(".") if segment]


def relative_import_reason(import_name: str, node: ast.ImportFrom) -> str | None:
    """Return a reason for suspicious relative imports."""
    segments = module_segments(import_name)
    if node.level <= 1:
        return None
    if segments and segments[0] in IMPLEMENTATION_SEGMENTS:
        return "relative import from an integration implementation package"
    imported_aliases = {alias.name for alias in node.names}
    if imported_aliases & IMPLEMENTATION_SEGMENTS:
        return "relative import of an integration implementation package"
    return None


def absolute_import_reason(import_name: str) -> str | None:
    """Return a reason for suspicious absolute imports."""
    segments = module_segments(import_name)
    if not segments:
        return None

    root = segments[0]
    if root == "zenml":
        if len(segments) >= 4 and segments[1] == "integrations":
            if any(segment in IMPLEMENTATION_SEGMENTS for segment in segments[3:]):
                return "top-level import from an integration implementation package"
        return None

    if is_stdlib_root(root) or is_allowed_third_party(root):
        return None

    return "top-level third-party import in a flavor file"


def scan_file(path: Path) -> list[Finding]:
    """Scan one flavor file for suspicious imports."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [
            Finding(
                path=str(path),
                line=exc.lineno or 1,
                import_name="<syntax-error>",
                reason=f"could not parse file: {exc.msg}",
                guidance="Fix syntax before rerunning the static import check.",
            )
        ]

    findings: list[Finding] = []
    for node in top_level_imports(tree):
        for import_name in imported_names(node):
            reason = None
            if isinstance(node, ast.ImportFrom) and node.level:
                reason = relative_import_reason(import_name, node)
            else:
                reason = absolute_import_reason(import_name)

            if not reason:
                continue

            findings.append(
                Finding(
                    path=str(path),
                    line=node.lineno,
                    import_name=import_name,
                    reason=reason,
                    guidance=(
                        "Move optional SDK or implementation imports into the "
                        "implementation_class property, a method body, or a "
                        "TYPE_CHECKING block. Keep flavor config fields typed "
                        "with stdlib, Pydantic, or ZenML core types."
                    ),
                )
            )
    return findings


def print_text(files: Sequence[Path], findings: Sequence[Finding]) -> None:
    """Print a human-readable report."""
    print(f"Scanned {len(files)} flavor file(s).")
    if not findings:
        print("No suspicious top-level flavor imports found.")
        return

    print(f"Found {len(findings)} suspicious import(s):")
    for finding in findings:
        print(
            f"- {finding.path}:{finding.line}: {finding.import_name} "
            f"({finding.reason})"
        )
        print(f"  Guidance: {finding.guidance}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the static import checker."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    files = iter_flavor_files(args.paths, include_init=args.include_init)
    findings = [finding for file in files for finding in scan_file(file)]

    if args.format == "json":
        print(
            json.dumps(
                {
                    "scanned_files": [str(file) for file in files],
                    "findings": [asdict(finding) for finding in findings],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print_text(files, findings)

    if findings and args.fail_on_findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
