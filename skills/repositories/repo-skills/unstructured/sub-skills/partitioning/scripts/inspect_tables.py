#!/usr/bin/env python3
"""Extract Table element metadata.text_as_html values from unstructured JSON."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


_STYLE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; }}
table {{ border-collapse: collapse; margin-bottom: 1rem; }}
th, td {{ border: 1px solid #777; padding: 0.4rem 0.6rem; vertical-align: top; }}
caption {{ font-weight: bold; margin-bottom: 0.5rem; }}
.meta {{ color: #555; font-size: 0.9rem; margin-bottom: 1rem; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def _load_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    payload = json.loads(text)
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict) and isinstance(payload.get("elements"), list):
        records = payload["elements"]
    else:
        raise ValueError("Expected a JSON array of element objects or an object with an elements array.")
    if not all(isinstance(record, dict) for record in records):
        raise ValueError("Element JSON must contain objects.")
    return records


def _table_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        if record.get("type") != "Table":
            continue
        metadata = record.get("metadata") or {}
        text_as_html = metadata.get("text_as_html")
        if not text_as_html:
            continue
        tables.append(
            {
                "source_index": index,
                "page_number": metadata.get("page_number"),
                "text": record.get("text", ""),
                "html": str(text_as_html),
            }
        )
    return tables


def _add_table_borders(table_html: str) -> str:
    if re.search(r"<table\b[^>]*\bclass=", table_html, flags=re.IGNORECASE):
        return table_html
    return re.sub(
        r"<table\b([^>]*)>",
        lambda match: f"<table class=\"extracted-table\"{match.group(1)}>",
        table_html,
        count=1,
        flags=re.IGNORECASE,
    )


def _pretty_breaks(table_html: str) -> str:
    return re.sub(r">\s*<", ">\n<", table_html.strip())


def _render_table_document(table: dict[str, Any], title: str) -> str:
    page = table.get("page_number")
    meta_bits = [f"source element index: {table['source_index']}"]
    if page is not None:
        meta_bits.append(f"page: {page}")
    text_preview = str(table.get("text") or "")[:300]
    body = [f"<h1>{html.escape(title)}</h1>"]
    body.append(f"<div class=\"meta\">{html.escape(' | '.join(meta_bits))}</div>")
    if text_preview:
        body.append(f"<p><strong>Text preview:</strong> {html.escape(text_preview)}</p>")
    body.append(_pretty_breaks(_add_table_borders(str(table["html"]))))
    return _STYLE.format(title=html.escape(title), body="\n".join(body))


def _render_index(tables: list[dict[str, Any]], output_files: list[Path], title: str) -> str:
    rows = []
    for table, output_file in zip(tables, output_files):
        page = table.get("page_number") or ""
        text_preview = html.escape(str(table.get("text") or "")[:120])
        rows.append(
            "<tr>"
            f"<td>{table['source_index']}</td>"
            f"<td>{html.escape(str(page))}</td>"
            f"<td><a href=\"{html.escape(output_file.name)}\">{html.escape(output_file.name)}</a></td>"
            f"<td>{text_preview}</td>"
            "</tr>"
        )
    body = (
        f"<h1>{html.escape(title)}</h1>"
        "<table><thead><tr><th>Element index</th><th>Page</th><th>File</th><th>Text preview</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )
    return _STYLE.format(title=html.escape(title), body=body)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract Table metadata.text_as_html from unstructured element JSON into HTML files.",
    )
    parser.add_argument("json_file", help="Path to elements JSON produced from unstructured elements.")
    parser.add_argument("--out-dir", default="tables-out", help="Directory for generated HTML files.")
    parser.add_argument("--prefix", help="Output filename prefix; defaults to input filename stem.")
    parser.add_argument("--index", action="store_true", help="Write an index.html linking all extracted tables.")
    parser.add_argument("--fail-if-none", action="store_true", help="Exit non-zero when no table HTML is found.")
    parser.add_argument("--stdout", action="store_true", help="Print extracted HTML fragments to stdout instead of writing files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    json_path = Path(args.json_file)
    try:
        records = _load_records(json_path)
        tables = _table_records(records)
    except Exception as exc:  # noqa: BLE001 - diagnostic CLI should report parse errors directly.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not tables:
        print("No Table elements with metadata.text_as_html found.", file=sys.stderr)
        return 1 if args.fail_if_none else 0

    if args.stdout:
        for table in tables:
            print(_pretty_breaks(str(table["html"])))
            print()
        return 0

    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix or json_path.stem
    output_files: list[Path] = []

    for number, table in enumerate(tables, start=1):
        output_file = output_dir / f"{prefix}-table-{number:03d}.html"
        title = f"{prefix} table {number}"
        output_file.write_text(_render_table_document(table, title), encoding="utf-8")
        output_files.append(output_file)
        print(output_file)

    if args.index:
        index_file = output_dir / "index.html"
        index_file.write_text(_render_index(tables, output_files, f"{prefix} tables"), encoding="utf-8")
        print(index_file)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
