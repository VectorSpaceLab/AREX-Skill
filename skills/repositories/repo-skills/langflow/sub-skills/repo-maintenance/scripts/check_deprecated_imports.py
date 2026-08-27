#!/usr/bin/env python3
"""Static checker for deprecated LangChain import paths in Langflow code.

The checker is intentionally self-contained and uses only the Python standard
library. By default, run it from a Langflow repository root and it scans common
component and bundle roots when they exist. You can also pass explicit files or
directories.

Exit codes:
    0: no deprecated imports found
    1: deprecated imports found
    2: usage, I/O, or parse error
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


@dataclass(frozen=True)
class DeprecatedPattern:
    """One deprecated module prefix and its suggested replacement."""

    old: str
    new: str
    note: str = ""


@dataclass(frozen=True)
class Finding:
    """One deprecated import occurrence."""

    path: Path
    line: int
    column: int
    module: str
    replacement: str
    import_kind: str
    note: str


DEFAULT_PATTERNS = (
    DeprecatedPattern("langchain.embeddings.base", "langchain_core.embeddings"),
    DeprecatedPattern("langchain.llms.base", "langchain_core.language_models.llms"),
    DeprecatedPattern("langchain.chat_models.base", "langchain_core.language_models.chat_models"),
    DeprecatedPattern("langchain.schema", "langchain_core.messages", "Verify non-message symbols before replacing."),
    DeprecatedPattern("langchain.vectorstores", "langchain_community.vectorstores"),
    DeprecatedPattern("langchain.document_loaders", "langchain_community.document_loaders"),
    DeprecatedPattern("langchain.text_splitter", "langchain_text_splitters"),
)

DEFAULT_ROOTS = (
    Path("src/lfx/src/lfx/components"),
    Path("src/bundles"),
    Path("src/backend/base/langflow/components"),
)

IGNORED_DIR_NAMES = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__", "node_modules"}


class CheckError(RuntimeError):
    """A recoverable checker error that should produce exit code 2."""


def parse_extra_pattern(raw: str) -> DeprecatedPattern:
    """Parse OLD=NEW or OLD=NEW::NOTE into a pattern."""
    old, sep, rest = raw.partition("=")
    if not sep or not old.strip() or not rest.strip():
        msg = f"Invalid --pattern {raw!r}; expected OLD=NEW or OLD=NEW::NOTE."
        raise CheckError(msg)
    new, _, note = rest.partition("::")
    return DeprecatedPattern(old.strip(), new.strip(), note.strip())


def discover_default_targets(cwd: Path) -> list[Path]:
    """Return default scan roots that exist under cwd."""
    return [cwd / root for root in DEFAULT_ROOTS if (cwd / root).exists()]


def iter_python_files(targets: list[Path]) -> list[Path]:
    """Return sorted Python files from explicit file/directory targets."""
    files: set[Path] = set()
    missing: list[Path] = []
    for target in targets:
        if not target.exists():
            missing.append(target)
            continue
        if target.is_file():
            if target.suffix == ".py":
                files.add(target)
            continue
        for candidate in target.rglob("*.py"):
            if any(part in IGNORED_DIR_NAMES for part in candidate.parts):
                continue
            if candidate.name.startswith("."):
                continue
            files.add(candidate)
    if missing:
        missing_list = "\n".join(f"  - {path}" for path in missing)
        msg = f"Target path does not exist:\n{missing_list}"
        raise CheckError(msg)
    return sorted(files)


def relative_display(path: Path, cwd: Path) -> str:
    """Return a stable path display without machine-specific absolute prefixes."""
    try:
        return path.resolve().relative_to(cwd.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def match_pattern(module: str, patterns: tuple[DeprecatedPattern, ...]) -> DeprecatedPattern | None:
    """Return the matching pattern for a module, if any."""
    for pattern in patterns:
        if module == pattern.old or module.startswith(f"{pattern.old}."):
            return pattern
    return None


def scan_file(path: Path, patterns: tuple[DeprecatedPattern, ...]) -> tuple[list[Finding], str | None]:
    """Scan a Python file and return findings plus an optional parse warning."""
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CheckError(f"Could not read {path}: {exc}") from exc

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        warning = f"Could not parse {path}: {exc.msg} at line {exc.lineno}"
        return [], warning

    findings: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            pattern = match_pattern(module, patterns)
            if pattern is not None:
                findings.append(
                    Finding(
                        path=path,
                        line=node.lineno,
                        column=node.col_offset + 1,
                        module=module,
                        replacement=pattern.new,
                        import_kind="from",
                        note=pattern.note,
                    )
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                pattern = match_pattern(alias.name, patterns)
                if pattern is not None:
                    findings.append(
                        Finding(
                            path=path,
                            line=node.lineno,
                            column=node.col_offset + 1,
                            module=alias.name,
                            replacement=pattern.new,
                            import_kind="import",
                            note=pattern.note,
                        )
                    )
    return findings, None


def format_text(finding: Finding, cwd: Path) -> str:
    """Format a finding for terminal output."""
    location = f"{relative_display(finding.path, cwd)}:{finding.line}:{finding.column}"
    note = f" ({finding.note})" if finding.note else ""
    return f"{location}: deprecated {finding.import_kind} '{finding.module}' -> use '{finding.replacement}'{note}"


def format_github(finding: Finding, cwd: Path) -> str:
    """Format a finding as a GitHub Actions annotation."""
    path = relative_display(finding.path, cwd)
    message = f"deprecated {finding.import_kind} '{finding.module}' -> use '{finding.replacement}'"
    if finding.note:
        message = f"{message} ({finding.note})"
    return f"::error file={path},line={finding.line},col={finding.column}::{message}"


def print_report(
    findings: list[Finding],
    warnings: list[str],
    *,
    cwd: Path,
    output_format: str,
    stdout: TextIO,
    stderr: TextIO,
) -> None:
    """Print scan warnings and findings."""
    for warning in warnings:
        print(f"warning: {warning}", file=stderr)

    if not findings:
        print("No deprecated LangChain imports found.", file=stdout)
        return

    print(f"Found {len(findings)} deprecated LangChain import(s):", file=stderr)
    formatter = format_github if output_format == "github" else format_text
    for finding in findings:
        print(formatter(finding, cwd), file=stderr)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Check Python files for deprecated LangChain import paths used by Langflow components and bundles.",
    )
    parser.add_argument(
        "targets",
        nargs="*",
        type=Path,
        help="Files or directories to scan. Defaults to common Langflow component and bundle roots when present.",
    )
    parser.add_argument(
        "--pattern",
        action="append",
        default=[],
        metavar="OLD=NEW",
        help="Additional deprecated module prefix and replacement. Use OLD=NEW::NOTE to append a note.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "github"),
        default="text",
        help="Output format for findings (default: text).",
    )
    parser.add_argument(
        "--fail-on-parse-warning",
        action="store_true",
        help="Return exit code 2 if any Python file cannot be parsed. By default parse warnings are non-fatal.",
    )
    parser.add_argument(
        "--list-patterns",
        action="store_true",
        help="Print the deprecated import patterns and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the checker."""
    parser = build_parser()
    args = parser.parse_args(argv)
    cwd = Path.cwd()

    try:
        extra_patterns = tuple(parse_extra_pattern(raw) for raw in args.pattern)
        patterns = (*DEFAULT_PATTERNS, *extra_patterns)

        if args.list_patterns:
            for pattern in patterns:
                note = f" # {pattern.note}" if pattern.note else ""
                print(f"{pattern.old} -> {pattern.new}{note}")
            return 0

        targets = [target if target.is_absolute() else cwd / target for target in args.targets]
        if not targets:
            targets = discover_default_targets(cwd)
        if not targets:
            defaults = ", ".join(root.as_posix() for root in DEFAULT_ROOTS)
            raise CheckError(
                "No scan targets were provided and no default Langflow component roots exist. "
                f"Run from a Langflow repo root or pass explicit targets. Defaults: {defaults}"
            )

        files = iter_python_files(targets)
        findings: list[Finding] = []
        warnings: list[str] = []
        for file_path in files:
            file_findings, warning = scan_file(file_path, patterns)
            findings.extend(file_findings)
            if warning:
                warnings.append(warning)

        print_report(findings, warnings, cwd=cwd, output_format=args.format, stdout=sys.stdout, stderr=sys.stderr)
        if warnings and args.fail_on_parse_warning:
            return 2
        return 1 if findings else 0
    except CheckError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
