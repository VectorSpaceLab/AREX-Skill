#!/usr/bin/env python3
"""Parse tiny Khoj content fixtures without database writes.

The helper prefers Khoj parser static methods when the package is installed. If
Django/Khoj parser imports are unavailable, it falls back to a small built-in
parser for Markdown, Org, and plaintext fixtures so future agents can still
inspect entry shape safely.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BUILTIN_FIXTURES = {
    "markdown": ("fixture.md", "# Project Alpha\nStatus update\n## Risks\nBudget risk\n"),
    "org": ("fixture.org", "* Project Alpha\nStatus update\n** TODO Follow up\nBudget risk\n"),
    "plaintext": ("fixture.txt", "Project Alpha status update\nBudget risk\n"),
}


@dataclass
class SimpleEntry:
    raw: str
    compiled: str
    heading: str
    file: str
    uri: str
    corpus_id: str | None = None
    parser: str = "fallback"


def ensure_import_path() -> None:
    """Allow use from an editable checkout without hard-coding machine paths."""
    cwd_src = Path.cwd() / "src"
    if cwd_src.exists() and str(cwd_src) not in sys.path:
        sys.path.insert(0, str(cwd_src))


def setup_django_if_needed() -> None:
    """Initialize Django only if parser imports require configured settings."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "khoj.app.settings")
    import django
    from django.apps import apps

    if not apps.ready:
        django.setup()


def import_parsers() -> tuple[Any, Any, Any, Any] | None:
    ensure_import_path()
    try:
        from khoj.processor.content.markdown.markdown_to_entries import MarkdownToEntries
        from khoj.processor.content.org_mode.org_to_entries import OrgToEntries
        from khoj.processor.content.plaintext.plaintext_to_entries import PlaintextToEntries
        from khoj.processor.content.text_to_entries import TextToEntries

        return MarkdownToEntries, OrgToEntries, PlaintextToEntries, TextToEntries
    except Exception:
        try:
            setup_django_if_needed()
            from khoj.processor.content.markdown.markdown_to_entries import MarkdownToEntries
            from khoj.processor.content.org_mode.org_to_entries import OrgToEntries
            from khoj.processor.content.plaintext.plaintext_to_entries import PlaintextToEntries
            from khoj.processor.content.text_to_entries import TextToEntries

            return MarkdownToEntries, OrgToEntries, PlaintextToEntries, TextToEntries
        except Exception:
            return None


def entry_to_dict(entry: Any) -> dict[str, Any]:
    return {
        "raw": entry.raw,
        "compiled": entry.compiled,
        "heading": entry.heading,
        "file": entry.file,
        "uri": entry.uri,
        "corpus_id": str(entry.corpus_id) if getattr(entry, "corpus_id", None) else None,
        "parser": getattr(entry, "parser", "khoj"),
    }


def read_content(args: argparse.Namespace) -> tuple[str, str]:
    if args.text is not None and args.file is not None:
        raise SystemExit("Use only one of --text or --file.")

    if args.file is not None:
        file_path = Path(args.file)
        return args.name or str(file_path), file_path.read_text(encoding=args.encoding)

    if args.text is not None:
        default_name, _ = BUILTIN_FIXTURES[args.type]
        return args.name or default_name, args.text

    default_name, default_text = BUILTIN_FIXTURES[args.type]
    return args.name or default_name, default_text


def split_markdown_sections(content: str) -> list[tuple[str, str, int]]:
    sections: list[tuple[str, str, int]] = []
    current: list[str] = []
    start_line = 1
    current_heading = ""
    for line_number, line in enumerate(content.splitlines(), start=1):
        if re.match(r"^#+\s+", line) and current:
            sections.append((current_heading, "\n".join(current).strip(), start_line))
            current = []
            start_line = line_number
        if re.match(r"^#+\s+", line):
            current_heading = line.strip()
        current.append(line)
    if current:
        sections.append((current_heading, "\n".join(current).strip(), start_line))
    return [(heading, raw, line) for heading, raw, line in sections if raw]


def split_org_sections(content: str) -> list[tuple[str, str, int]]:
    sections: list[tuple[str, str, int]] = []
    current: list[str] = []
    start_line = 1
    current_heading = ""
    for line_number, line in enumerate(content.splitlines(), start=1):
        if re.match(r"^\*+\s+", line) and current:
            sections.append((current_heading, "\n".join(current).strip(), start_line))
            current = []
            start_line = line_number
        if re.match(r"^\*+\s+", line):
            current_heading = line.strip()
        current.append(line)
    if current:
        sections.append((current_heading, "\n".join(current).strip(), start_line))
    return [(heading, raw, line) for heading, raw, line in sections if raw]


def fallback_parse(args: argparse.Namespace) -> list[SimpleEntry]:
    name, content = read_content(args)
    corpus_id = str(uuid.uuid4())
    if args.type == "markdown":
        sections = split_markdown_sections(content) or [("", content.strip(), 1)]
        return [
            SimpleEntry(
                raw=raw,
                compiled=f"# {name}\n{raw}",
                heading=f"# {name}\n#{heading}" if heading else f"# {name}",
                file=name,
                uri=f"file://{name}#line={line}",
                corpus_id=corpus_id,
            )
            for heading, raw, line in sections
        ]
    if args.type == "org":
        sections = split_org_sections(content) or [("", content.strip(), 1)]
        return [
            SimpleEntry(
                raw=raw,
                compiled=f"* {name}\n{raw}",
                heading=f"* {name}\n{heading}" if heading else f"* {name}",
                file=name,
                uri=f"file://{name}#line={line}",
                corpus_id=corpus_id,
            )
            for heading, raw, line in sections
        ]
    return [
        SimpleEntry(
            raw=content,
            compiled=f"# {name}\n{content}",
            heading=f"# {name}",
            file=name,
            uri=f"file://{name}",
            corpus_id=corpus_id,
        )
    ]


def parse_entries(args: argparse.Namespace) -> tuple[list[Any], str]:
    parser_modules = import_parsers()
    if parser_modules is None:
        if args.require_khoj:
            raise SystemExit("Khoj parser imports failed; rerun in an installed Khoj environment or omit --require-khoj.")
        return fallback_parse(args), "fallback"

    MarkdownToEntries, OrgToEntries, PlaintextToEntries, TextToEntries = parser_modules
    name, content = read_content(args)

    if args.type == "markdown":
        _, entries = MarkdownToEntries.extract_markdown_entries({name: content}, max_tokens=args.max_tokens)
        raw_is_compiled = False
    elif args.type == "org":
        _, entries = OrgToEntries.extract_org_entries(
            {name: content},
            index_heading_entries=args.index_heading_entries,
            max_tokens=args.max_tokens,
        )
        raw_is_compiled = False
    else:
        _, entries = PlaintextToEntries.extract_plaintext_entries({name: content})
        raw_is_compiled = True

    if not args.no_split:
        entries = TextToEntries.split_entries_by_max_tokens(
            entries,
            max_tokens=args.max_tokens,
            raw_is_compiled=raw_is_compiled,
        )
    return entries, "khoj"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse tiny Markdown, Org, or plaintext content into Khoj-like JSON entries without DB writes.",
    )
    parser.add_argument("--type", choices=sorted(BUILTIN_FIXTURES), default="markdown", help="Content parser to use.")
    parser.add_argument("--text", help="Inline fixture text. If omitted with --file, a tiny built-in fixture is used.")
    parser.add_argument("--file", help="Path to a small local text fixture to parse.")
    parser.add_argument("--name", help="Logical filename for returned entries. Defaults to --file or a fixture name.")
    parser.add_argument("--encoding", default="utf-8", help="Encoding for --file input. Default: utf-8.")
    parser.add_argument("--max-tokens", type=int, default=256, help="Token limit used for extraction/splitting. Default: 256.")
    parser.add_argument("--no-split", action="store_true", help="Show parser extraction output before TextToEntries chunking.")
    parser.add_argument(
        "--index-heading-entries",
        action="store_true",
        help="For Org only, include heading-only entries when using real Khoj parser methods.",
    )
    parser.add_argument("--require-khoj", action="store_true", help="Fail instead of using the built-in fallback parser.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.max_tokens < 1:
        parser.error("--max-tokens must be at least 1")

    entries, parser_name = parse_entries(args)
    payload = {
        "parser": parser_name,
        "entries": [entry_to_dict(entry) for entry in entries],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
