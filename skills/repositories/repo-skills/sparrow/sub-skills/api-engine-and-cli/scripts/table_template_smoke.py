#!/usr/bin/env python3
"""Offline smoke check for Sparrow's generic table-template behavior.

This script uses an embedded HTML table fixture by default. It does not call a
Sparrow service, load models, or import source modules.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_TABLE_HTML = """
<table>
  <thead>
    <tr><th>Instrument Name</th><th>Valuation</th><th>Risk Category</th></tr>
  </thead>
  <tbody>
    <tr><td>Core EUR Govt Bond ETF</td><td>83488</td><td>low</td></tr>
    <tr><td>EUR Corp Bond 1-5YR ETF</td><td>213030</td><td></td></tr>
  </tbody>
</table>
""".strip()

DEFAULT_QUERY = json.dumps({
    'items': [{
        'instrument_name': 'str',
        'valuation': 'int',
        'risk_category': 'str or null',
    }]
})


@dataclass
class ParsedTable:
    headers: List[str]
    rows: List[List[str]]


class SimpleTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_cell_tag = ''
        self.current_cell_text: List[str] = []
        self.current_row: List[Tuple[str, str]] = []
        self.rows: List[List[Tuple[str, str]]] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        if tag == 'table':
            self.in_table = True
        elif self.in_table and tag == 'tr':
            self.in_row = True
            self.current_row = []
        elif self.in_row and tag in {'th', 'td'}:
            self.in_cell = True
            self.current_cell_tag = tag
            self.current_cell_text = []

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.current_cell_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {'th', 'td'} and self.in_cell:
            text = ' '.join(part.strip() for part in self.current_cell_text if part.strip())
            self.current_row.append((self.current_cell_tag, text))
            self.in_cell = False
            self.current_cell_tag = ''
            self.current_cell_text = []
        elif tag == 'tr' and self.in_row:
            if self.current_row:
                self.rows.append(self.current_row)
            self.in_row = False
            self.current_row = []
        elif tag == 'table':
            self.in_table = False


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_html_table(html_text: str) -> ParsedTable:
    parser = SimpleTableParser()
    parser.feed(html_text)
    if not parser.rows:
        return ParsedTable(headers=[], rows=[])

    first_row = parser.rows[0]
    first_row_has_header = any(tag == 'th' for tag, _ in first_row)
    if first_row_has_header:
        headers = [text or f'col{i + 1}' for i, (_, text) in enumerate(first_row)]
        data_rows = [[text for _, text in row] for row in parser.rows[1:]]
    else:
        headers = [f'col{i + 1}' for i in range(len(first_row))]
        data_rows = [[text for _, text in row] for row in parser.rows]

    return ParsedTable(headers=headers, rows=data_rows)


def find_best_column_match(query_field: str, headers: List[str]) -> Optional[int]:
    normalized_query = normalize_text(query_field.replace('_', ' '))
    query_words = set(normalized_query.split())
    best_score = 0.0
    best_idx: Optional[int] = None
    for idx, header in enumerate(headers):
        normalized_header = normalize_text(header)
        header_words = set(normalized_header.split())
        if normalized_query == normalized_header:
            return idx
        if normalized_query in normalized_header or normalized_header in normalized_query:
            score = 0.8
        elif query_words and header_words:
            score = len(query_words.intersection(header_words)) / max(len(query_words), len(header_words))
        else:
            score = 0.0
        if score > best_score and score > 0.5:
            best_score = score
            best_idx = idx
    return best_idx


def parse_query_fields(query_text: str) -> Optional[List[Dict[str, str]]]:
    if query_text.strip() == '*':
        return None
    query_data = json.loads(query_text)
    items_schema: Optional[List[Dict[str, str]]] = None
    if isinstance(query_data, dict) and 'items' in query_data:
        items_schema = query_data['items']
    elif isinstance(query_data, list) and query_data and isinstance(query_data[0], dict) and 'items' in query_data[0]:
        items_schema = query_data[0]['items']
    else:
        return []

    if not isinstance(items_schema, list) or not items_schema or not isinstance(items_schema[0], dict):
        return []
    return [{'name': key, 'type': str(value)} for key, value in items_schema[0].items()]


def convert_value(value: str, target_type: str) -> Any:
    target_type = target_type.lower().strip()
    is_nullable = 'or null' in target_type
    base_type = target_type.split()[0] if is_nullable else target_type
    stripped = value.strip()
    cleaned = re.sub(r"['’]", '', stripped)
    cleaned = re.sub(r'[^\d.-]', '', cleaned)

    if not stripped and is_nullable:
        return None
    if base_type == 'int':
        try:
            return int(float(cleaned)) if cleaned else (None if is_nullable else 0)
        except ValueError:
            return None if is_nullable else 0
    if base_type == 'float':
        try:
            return float(cleaned) if cleaned else (None if is_nullable else 0.0)
        except ValueError:
            return None if is_nullable else 0.0
    return stripped if stripped else (None if is_nullable else stripped)


def extract_generic(table: ParsedTable, query_text: str) -> Dict[str, List[Dict[str, Any]]]:
    if not table.headers:
        return {'items': []}
    fields = parse_query_fields(query_text)
    if fields is None:
        fields = [{'name': header, 'type': 'str'} for header in table.headers]
    if not fields:
        return {'items': []}

    field_to_col: Dict[str, Tuple[int, str]] = {}
    for field in fields:
        idx = find_best_column_match(field['name'], table.headers)
        if idx is not None:
            field_to_col[field['name']] = (idx, field['type'])

    items: List[Dict[str, Any]] = []
    for row in table.rows:
        item: Dict[str, Any] = {}
        for field in fields:
            match = field_to_col.get(field['name'])
            if match is None:
                item[field['name']] = None
                continue
            idx, target_type = match
            item[field['name']] = convert_value(row[idx] if idx < len(row) else '', target_type)
        items.append(item)
    return {'items': items}


def load_text(value: Optional[str], path: Optional[Path], default: str) -> str:
    if value is not None:
        return value
    if path is not None:
        return path.read_text(encoding='utf-8')
    return default


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Run an offline generic-table-template fixture smoke check.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--template', choices=['sparrow_generic_table', 'sparrow_invoice_table'], default='sparrow_generic_table', help='Template behavior to emulate.')
    parser.add_argument('--query', help='Table query JSON. Use * for auto-detect all columns.')
    parser.add_argument('--query-file', type=Path, help='File containing table query JSON.')
    parser.add_argument('--table-html', help='HTML table text. Uses embedded fixture when omitted.')
    parser.add_argument('--table-file', type=Path, help='File containing HTML table text.')
    parser.add_argument('--expect-items', type=int, help='Require this number of returned items.')
    parser.add_argument('--json', action='store_true', help='Emit only JSON output, without explanatory text.')
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    query_text = load_text(args.query, args.query_file, DEFAULT_QUERY)
    table_html = load_text(args.table_html, args.table_file, DEFAULT_TABLE_HTML)

    if args.template == 'sparrow_invoice_table':
        result: Dict[str, Any] = {}
        if not args.json:
            print('sparrow_invoice_table is a placeholder in the inspected implementation and returns {}.')
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if args.expect_items not in (None, 0):
            return 1
        return 0

    parsed_table = parse_html_table(table_html)
    try:
        result = extract_generic(parsed_table, query_text)
    except json.JSONDecodeError as exc:
        print(f'Invalid table query JSON: {exc}', file=sys.stderr)
        return 1

    item_count = len(result.get('items', []))
    if not args.json:
        print(f'headers: {parsed_table.headers}')
        print(f'rows: {len(parsed_table.rows)}')
        print(f'items: {item_count}')
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.expect_items is not None and item_count != args.expect_items:
        print(f'Expected {args.expect_items} items, got {item_count}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
