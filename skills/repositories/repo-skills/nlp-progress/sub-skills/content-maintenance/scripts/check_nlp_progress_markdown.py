#!/usr/bin/env python3
"""Validate NLP-progress Markdown result tables and inline links.

This helper is intentionally lightweight and standard-library only. It is meant
for content-maintenance checks before handing off Markdown edits, not for the
structured JSON export workflow.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, List, NamedTuple, Sequence, Tuple


class Diagnostic(NamedTuple):
    path: str
    line: int
    severity: str
    message: str


INLINE_LINK_RE = re.compile(r"!?\[([^\]\n]*)\]\(([^)\n]*)\)")
SEPARATOR_CELL_RE = re.compile(r":?-{3,}:?")
METRIC_HINTS = (
    "score",
    "f1",
    "accuracy",
    "acc",
    "bleu",
    "rouge",
    "meteor",
    "em",
    "las",
    "uas",
    "wer",
    "cer",
    "error",
    "perplexity",
    "loss",
    "mrr",
    "map",
    "precision",
    "recall",
    "micro",
    "macro",
    "test",
    "dev",
    "validation",
    "challenge",
    "code",
)


def split_table_row(line: str) -> List[str]:
    """Split a Markdown pipe row while honoring escaped literal pipes."""
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|") and not text.endswith(r"\|"):
        text = text[:-1]

    cells: List[str] = []
    buf: List[str] = []
    escaped = False
    for char in text:
        if char == "|" and not escaped:
            cells.append("".join(buf).strip())
            buf = []
            escaped = False
            continue
        buf.append(char)
        if char == "\\" and not escaped:
            escaped = True
        else:
            escaped = False
    cells.append("".join(buf).strip())
    return cells


def is_table_line(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith("|") and stripped.count("|") >= 2


def is_separator_line(line: str) -> bool:
    if not is_table_line(line):
        return False
    cells = split_table_row(line)
    non_empty = [cell.strip() for cell in cells if cell.strip()]
    if not non_empty:
        return False
    return all(SEPARATOR_CELL_RE.fullmatch(cell.strip()) for cell in non_empty)


def find_tables(lines: Sequence[str]) -> Iterable[List[Tuple[int, str]]]:
    i = 0
    while i < len(lines) - 1:
        if is_table_line(lines[i]) and is_separator_line(lines[i + 1]):
            table: List[Tuple[int, str]] = []
            while i < len(lines) and is_table_line(lines[i]):
                table.append((i + 1, lines[i].rstrip("\n")))
                i += 1
            yield table
        else:
            i += 1


def normalize_header(cell: str) -> str:
    cell = re.sub(r"<[^>]+>", "", cell)
    cell = cell.replace("**", "").replace("__", "").replace("*", "").replace("`", "")
    cell = cell.replace("&nbsp;", " ")
    return re.sub(r"[^a-z0-9@]+", "", cell.lower())


def normalize_row_key(cells: Sequence[str]) -> Tuple[str, ...]:
    normalized: List[str] = []
    for cell in cells:
        collapsed = re.sub(r"\s+", " ", cell.strip().lower())
        normalized.append(collapsed)
    return tuple(normalized)


def has_model_header(headers: Sequence[str]) -> bool:
    return any(header == "model" for header in headers)


def has_paper_header(headers: Sequence[str]) -> bool:
    return any("paper" in header for header in headers)


def has_code_header(headers: Sequence[str]) -> bool:
    return any(header == "code" for header in headers)


def looks_like_result_table(headers: Sequence[str]) -> bool:
    if has_model_header(headers):
        return True
    if has_paper_header(headers):
        return any(any(hint in header for hint in METRIC_HINTS) for header in headers)
    return False


def analyze_table(path: Path, table: Sequence[Tuple[int, str]]) -> List[Diagnostic]:
    diagnostics: List[Diagnostic] = []
    header_line_no, header_line = table[0]
    headers_raw = split_table_row(header_line)
    headers = [normalize_header(cell) for cell in headers_raw]
    result_like = looks_like_result_table(headers)

    if not result_like:
        return diagnostics

    if not has_model_header(headers):
        diagnostics.append(
            Diagnostic(
                str(path),
                header_line_no,
                "ERROR",
                "result-like table header is missing required 'Model' column",
            )
        )
    if not has_paper_header(headers):
        diagnostics.append(
            Diagnostic(
                str(path),
                header_line_no,
                "ERROR",
                "result table header is missing required 'Paper' or 'Paper / Source' column",
            )
        )
    if not has_code_header(headers):
        diagnostics.append(
            Diagnostic(
                str(path),
                header_line_no,
                "WARN",
                "result table has no 'Code' column; legacy tables may omit it, but new tables should include it when possible",
            )
        )

    expected_cells = len(headers_raw)
    seen_rows = {}
    for line_no, row in table[2:]:
        cells = split_table_row(row)
        if not any(cell.strip() for cell in cells):
            continue
        if len(cells) != expected_cells:
            diagnostics.append(
                Diagnostic(
                    str(path),
                    line_no,
                    "WARN",
                    "table row has %d cells but header has %d; check missing cells, extra pipes, or unescaped literal pipes"
                    % (len(cells), expected_cells),
                )
            )
        key = normalize_row_key(cells)
        if key in seen_rows:
            diagnostics.append(
                Diagnostic(
                    str(path),
                    line_no,
                    "WARN",
                    "possible duplicate result row; first identical row appears at line %d" % seen_rows[key],
                )
            )
        else:
            seen_rows[key] = line_no

    return diagnostics


def strip_inline_code_spans(line: str) -> str:
    """Remove simple inline-code spans before Markdown-link linting."""
    return re.sub(r"`+[^`]*`+", "", line)


def analyze_links(path: Path, lines: Sequence[str]) -> List[Diagnostic]:
    diagnostics: List[Diagnostic] = []
    in_fenced_code = False
    fence_marker = ""
    for line_no, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fenced_code:
                in_fenced_code = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fenced_code = False
                fence_marker = ""
            continue
        if in_fenced_code:
            continue

        scan_line = strip_inline_code_spans(line)
        for match in INLINE_LINK_RE.finditer(scan_line):
            label = match.group(1).strip()
            target = match.group(2).strip()
            if not label:
                diagnostics.append(
                    Diagnostic(str(path), line_no, "ERROR", "Markdown link has an empty label")
                )
            if not target:
                diagnostics.append(
                    Diagnostic(str(path), line_no, "ERROR", "Markdown link has an empty URL")
                )

        search_from = 0
        while True:
            marker = scan_line.find("](", search_from)
            if marker == -1:
                break
            opening = scan_line.rfind("[", 0, marker)
            closing = scan_line.find(")", marker + 2)
            if opening == -1:
                diagnostics.append(
                    Diagnostic(str(path), line_no, "ERROR", "found '](' without a matching '['")
                )
            elif closing == -1:
                diagnostics.append(
                    Diagnostic(
                        str(path),
                        line_no,
                        "ERROR",
                        "malformed Markdown link is missing a closing ')'",
                    )
                )
            search_from = marker + 2
    return diagnostics


def analyze_file(path: Path) -> List[Diagnostic]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    diagnostics: List[Diagnostic] = []
    diagnostics.extend(analyze_links(path, lines))
    for table in find_tables(lines):
        diagnostics.extend(analyze_table(path, table))
    return diagnostics


def collect_paths(arguments: Sequence[str]) -> Tuple[List[Path], List[str]]:
    files: List[Path] = []
    errors: List[str] = []
    for arg in arguments:
        path = Path(arg)
        if not path.exists():
            errors.append("path does not exist: %s" % arg)
            continue
        if path.is_dir():
            files.extend(sorted(p for p in path.rglob("*.md") if p.is_file()))
        else:
            files.append(path)
    unique: List[Path] = []
    seen = set()
    for path in files:
        key = str(path)
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique, errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check NLP-progress Markdown files for result-table required columns "
            "and malformed inline Markdown links."
        )
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Markdown files or directories to check. Directories are searched recursively for *.md files.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings, such as missing Code columns or duplicate rows, as fatal.",
    )
    return parser


def main(argv: Sequence[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    files, path_errors = collect_paths(args.paths)
    diagnostics: List[Diagnostic] = []
    for message in path_errors:
        diagnostics.append(Diagnostic("<input>", 0, "ERROR", message))

    if not files and not path_errors:
        diagnostics.append(Diagnostic("<input>", 0, "ERROR", "no Markdown files found"))

    for path in files:
        diagnostics.extend(analyze_file(path))

    diagnostics.sort(key=lambda d: (d.path, d.line, d.severity, d.message))
    for diagnostic in diagnostics:
        line = diagnostic.line if diagnostic.line else 1
        print("%s:%d: %s: %s" % (diagnostic.path, line, diagnostic.severity.lower(), diagnostic.message))

    errors = sum(1 for diagnostic in diagnostics if diagnostic.severity == "ERROR")
    warnings = sum(1 for diagnostic in diagnostics if diagnostic.severity == "WARN")
    checked = len(files)

    if diagnostics:
        print(
            "Checked %d file(s): %d error(s), %d warning(s)%s."
            % (checked, errors, warnings, " (strict mode)" if args.strict else "")
        )
    else:
        print("OK: checked %d file(s); no errors or warnings." % checked)

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
