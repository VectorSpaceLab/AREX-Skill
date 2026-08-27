#!/usr/bin/env python3
"""Inventory NLP-progress Markdown headings and result-like tables.

Standard-library only and read-only. Pass any NLP-progress content root; the
script does not assume this skill is stored inside that checkout.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

LANGUAGES = (
    "english", "vietnamese", "hindi", "chinese", "french", "russian",
    "spanish", "portuguese", "korean", "nepali", "bengali", "persian",
    "turkish", "german", "arabic",
)
SUPPORT_DIRS = {".git", ".github", "_includes", "_layouts", "_site", "img", "images", "structured", "skills", "node_modules", "vendor"}
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)(?:\s+#+\s*)?$")
SEP_CELL_RE = re.compile(r":?-{3,}:?")
LINK_RE = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
TAG_RE = re.compile(r"<[^>]+>")
MODELISH = {"model", "models", "system", "systems", "method", "methods", "approach", "parser", "annotator"}
SOURCE = {"paper", "source", "reference", "citation"}
CODE = {"code", "github", "implementation", "webservice", "webservices"}
STRUCTURAL = {"dataset", "datasets", "data", "domain", "setting", "split", "note", "notes", "author", "authors"}
METRIC_HINTS = {
    "accuracy", "acc", "f1", "f1 score", "em", "exact match", "bleu", "rouge", "meteor",
    "perplexity", "ppl", "bpc", "bit per character", "bits per character", "smatch",
    "las", "uas", "error", "rmse", "score", "precision", "recall", "span", "nuclearity",
    "relation", "full", "test", "validation", "dev", "params", "parameters",
}


def clean(text: str) -> str:
    text = LINK_RE.sub(r"\1", text)
    text = TAG_RE.sub("", text)
    text = text.replace("`", "").replace("**", "").replace("__", "").replace("*", "")
    return html.unescape(text).strip()


def norm(text: str) -> str:
    text = clean(text).lower().replace("/", " ").replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]+", " ", text, flags=re.UNICODE)).strip()


def anchor(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", clean(text).lower(), flags=re.UNICODE)
    return re.sub(r"-+", "-", re.sub(r"\s+", "-", text.strip())).strip("-")


def row_cells(line: str) -> List[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def is_separator(line: str) -> bool:
    if "|" not in line or "-" not in line:
        return False
    cells = [cell for cell in row_cells(line) if cell.strip()]
    return bool(cells) and all(SEP_CELL_RE.fullmatch(cell.strip()) for cell in cells)


def has_term(value: str, terms: Iterable[str]) -> bool:
    words = set(value.split())
    for term in terms:
        t = norm(term)
        if t == value or (" " in t and t in value) or (" " not in t and t in words):
            return True
    return False


def headings(lines: Sequence[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for line_no, line in enumerate(lines, 1):
        match = HEADING_RE.match(line)
        if match:
            raw = match.group(2).strip()
            out.append({"line": line_no, "level": len(match.group(1)), "text": clean(raw), "anchor": anchor(raw)})
    return out


def context(heads: Sequence[Dict[str, Any]], line_no: int) -> List[Dict[str, Any]]:
    stack: List[Dict[str, Any]] = []
    for head in heads:
        if head["line"] >= line_no:
            break
        level = int(head["level"])
        stack = [item for item in stack if int(item["level"]) < level]
        stack.append(head)
    return [{"level": h["level"], "line": h["line"], "text": h["text"], "anchor": h["anchor"]} for h in stack]


def classify(header: Sequence[str]) -> Dict[str, Any]:
    model_cols: List[str] = []
    metric_cols: List[str] = []
    source_cols: List[str] = []
    code_cols: List[str] = []
    for raw in header:
        value = norm(raw)
        if not value:
            continue
        if has_term(value, MODELISH):
            model_cols.append(raw)
        elif has_term(value, SOURCE):
            source_cols.append(raw)
        elif has_term(value, CODE):
            code_cols.append(raw)
        elif has_term(value, METRIC_HINTS):
            metric_cols.append(raw)
        elif not has_term(value, STRUCTURAL):
            metric_cols.append(raw)
    result_like = bool(model_cols) and bool(metric_cols or source_cols or code_cols)
    notes: List[str] = []
    if result_like and not metric_cols:
        notes.append("model/source table has no obvious metric columns")
    if result_like and not source_cols:
        notes.append("result-like table has no obvious paper/source column")
    return {
        "result_like": result_like,
        "modelish_columns": model_cols,
        "metric_columns": metric_cols,
        "source_columns": source_cols,
        "code_columns": code_cols,
        "notes": notes,
    }


def tables(lines: Sequence[str], heads: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    i = 0
    while i < len(lines) - 1:
        if "|" not in lines[i] or not is_separator(lines[i + 1]):
            i += 1
            continue
        line_no = i + 1
        header = row_cells(lines[i])
        warnings: List[str] = []
        if len(row_cells(lines[i + 1])) != len(header):
            warnings.append("separator cell count differs from header cell count")
        row_count = 0
        j = i + 2
        while j < len(lines) and lines[j].strip() and "|" in lines[j] and not HEADING_RE.match(lines[j]):
            cells = row_cells(lines[j])
            row_count += 1
            if len(cells) != len(header):
                warnings.append(f"row at line {j + 1} has {len(cells)} cells; header has {len(header)}")
            j += 1
        info = classify(header)
        out.append({
            "line": line_no,
            "header": header,
            "row_count": row_count,
            "heading_context": context(heads, line_no),
            **info,
            "warnings": warnings,
        })
        i = max(j, i + 2)
    return out


def parse_file(path: Path, root: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    heads = headings(lines)
    tabs = tables(lines, heads)
    result_tabs = [tab for tab in tabs if tab["result_like"]]
    rel = path.relative_to(root).as_posix()
    return {
        "path": rel,
        "language": rel.split("/", 1)[0],
        "title": heads[0]["text"] if heads else None,
        "line_count": len(lines),
        "headings": heads,
        "table_counts": {
            "total": len(tabs),
            "result_like": len(result_tabs),
            "non_result_like": len(tabs) - len(result_tabs),
            "with_warnings": sum(1 for tab in tabs if tab["warnings"]),
        },
        "result_tables": result_tabs,
    }


def discover(root: Path, include_unlisted: bool) -> List[str]:
    langs = [name for name in LANGUAGES if (root / name).is_dir()]
    if include_unlisted:
        extras = []
        for child in root.iterdir():
            if child.is_dir() and child.name not in langs and child.name not in SUPPORT_DIRS and not child.name.startswith("."):
                if any(child.glob("*.md")):
                    extras.append(child.name)
        langs.extend(sorted(extras))
    return langs


def markdown_files(root: Path, langs: Sequence[str]) -> List[Path]:
    found: List[Path] = []
    for lang in langs:
        found.extend(sorted((root / lang).rglob("*.md")))
    return [path for path in found if not any(part.startswith(".") for part in path.relative_to(root).parts)]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inventory NLP-progress Markdown files under language directories and report headings plus result-like table counts as JSON."
    )
    parser.add_argument("content_root", nargs="?", default=".", help="NLP-progress content root containing README.md and language directories (default: current directory).")
    parser.add_argument("--language", action="append", help="Limit to a language directory; may be repeated, e.g. --language english --language chinese.")
    parser.add_argument("--all-markdown-dirs", action="store_true", help="Also include unlisted top-level Markdown directories that are not support directories.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON with two-space indentation.")
    args = parser.parse_args(argv)

    root_arg = args.content_root
    root = Path(root_arg).expanduser()
    if not root.exists():
        print(f"error: content root does not exist: {root_arg}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: content root is not a directory: {root_arg}", file=sys.stderr)
        return 2

    langs = discover(root, args.all_markdown_dirs)
    if args.language:
        missing = [lang for lang in args.language if not (root / lang).is_dir()]
        if missing:
            print("error: requested language directories not found: " + ", ".join(missing), file=sys.stderr)
            return 2
        langs = list(args.language)
    if not langs:
        print("error: no known language directories found; check the content root or pass --all-markdown-dirs", file=sys.stderr)
        return 2

    files = markdown_files(root, langs)
    if not files:
        print("error: no Markdown files found under selected language directories", file=sys.stderr)
        return 2
    parsed = [parse_file(path, root) for path in files]
    payload = {
        "schema_version": 1,
        "content_root_input": root_arg,
        "content_root_resolved": str(root.resolve()),
        "language_directories": langs,
        "summary": {
            "language_count": len(langs),
            "markdown_files": len(parsed),
            "headings": sum(len(item["headings"]) for item in parsed),
            "tables_total": sum(item["table_counts"]["total"] for item in parsed),
            "result_like_tables": sum(item["table_counts"]["result_like"] for item in parsed),
            "tables_with_warnings": sum(item["table_counts"]["with_warnings"] for item in parsed),
        },
        "files": parsed,
        "warnings": [] if (root / "README.md").is_file() else ["README.md not found at content root"],
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
