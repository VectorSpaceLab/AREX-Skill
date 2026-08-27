#!/usr/bin/env python3
"""Export table summaries and CSV-like files from DoclingDocument JSON."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass
class ExportedTable:
    index: int
    rows: list[list[str]]
    source: str

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        return max((len(row) for row in self.rows), default=0)


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        raise SystemExit(f"Input JSON not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Input is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit("Expected a DoclingDocument JSON object at the top level.")
    return data


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        for key in ("text", "orig", "value", "content", "label"):
            if key in value and value[key] is not None:
                return stringify(value[key])
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, list):
        return " ".join(stringify(item) for item in value if item is not None).strip()
    return str(value)


def rows_from_grid(data: Any) -> list[list[str]]:
    if not isinstance(data, list):
        return []
    if all(isinstance(row, list) for row in data):
        return [[stringify(cell) for cell in row] for row in data]
    return []


def rows_from_table_cells(table: dict[str, Any]) -> list[list[str]]:
    table_data = table.get("data")
    if not isinstance(table_data, dict):
        table_data = table

    grid = rows_from_grid(table_data.get("grid"))
    if grid:
        return grid

    cells = table_data.get("table_cells") or table_data.get("cells")
    if not isinstance(cells, list):
        return []

    placed_cells: list[tuple[int, int, str]] = []
    max_row = -1
    max_col = -1
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        row = first_int(cell, ("start_row_offset_idx", "row_header_index", "row", "row_idx"))
        col = first_int(cell, ("start_col_offset_idx", "col_header_index", "col", "col_idx"))
        if row is None or col is None:
            continue
        text = stringify(cell.get("text") or cell.get("content") or cell.get("value"))
        placed_cells.append((row, col, text))
        max_row = max(max_row, row)
        max_col = max(max_col, col)

    if max_row < 0 or max_col < 0:
        return []

    rows = [["" for _ in range(max_col + 1)] for _ in range(max_row + 1)]
    for row, col, text in placed_cells:
        rows[row][col] = text
    return rows


def first_int(mapping: dict[str, Any], keys: Iterable[str]) -> int | None:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def collect_tables_raw(data: dict[str, Any]) -> list[ExportedTable]:
    tables = data.get("tables")
    if not isinstance(tables, list):
        return []

    exported: list[ExportedTable] = []
    for index, table in enumerate(tables, start=1):
        if not isinstance(table, dict):
            continue
        rows = rows_from_table_cells(table)
        if not rows:
            text = stringify(table.get("text") or table.get("caption") or table.get("label"))
            rows = [[text]] if text else []
        exported.append(ExportedTable(index=index, rows=rows, source="raw-json"))
    return exported


def collect_tables_docling(json_path: Path) -> list[ExportedTable]:
    try:
        from docling_core.types.doc import DoclingDocument
    except Exception:
        return []

    try:
        doc = DoclingDocument.load_from_json(json_path)
    except Exception:
        try:
            data = load_json(json_path)
            doc = DoclingDocument.model_validate(data)
        except Exception:
            return []

    exported: list[ExportedTable] = []
    for index, table in enumerate(getattr(doc, "tables", []), start=1):
        try:
            dataframe = table.export_to_dataframe(doc=doc)
            rows = [list(map(str, dataframe.columns.tolist()))]
            rows.extend(
                [stringify(value) for value in record]
                for record in dataframe.astype(object).values.tolist()
            )
            exported.append(ExportedTable(index=index, rows=rows, source="docling-core"))
        except Exception:
            continue
    return exported


def write_table_csv(table: ExportedTable, output_dir: Path, prefix: str) -> Path:
    output_path = output_dir / f"{prefix}-table-{table.index}.csv"
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(table.rows)
    return output_path


def write_summary(tables: list[ExportedTable], output_dir: Path, prefix: str) -> Path:
    summary_path = output_dir / f"{prefix}-tables-summary.json"
    payload = [
        {
            "table_index": table.index,
            "rows": table.row_count,
            "columns": table.column_count,
            "source": table.source,
        }
        for table in tables
    ]
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read DoclingDocument JSON and emit table summaries plus CSV-like files. "
            "Uses docling-core validation when available and falls back to raw JSON parsing."
        )
    )
    parser.add_argument("json_path", type=Path, help="Path to DoclingDocument JSON.")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("docling-tables"),
        help="Directory for CSV and summary outputs. Default: docling-tables",
    )
    parser.add_argument(
        "--prefix",
        help="Output filename prefix. Default: input JSON stem.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Write only the JSON summary and skip CSV files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    json_path = args.json_path.expanduser()
    data = load_json(json_path)

    tables = collect_tables_docling(json_path)
    if not tables:
        tables = collect_tables_raw(data)

    if not tables:
        print("No tables found in the Docling JSON.", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix or json_path.stem
    summary_path = write_summary(tables, args.output_dir, prefix)

    csv_paths: list[Path] = []
    if not args.summary_only:
        for table in tables:
            if table.rows:
                csv_paths.append(write_table_csv(table, args.output_dir, prefix))

    print(f"Found {len(tables)} table(s).")
    print(f"Summary: {summary_path}")
    for path in csv_paths:
        print(f"CSV: {path}")
    if not csv_paths and not args.summary_only:
        print("Tables were present but no row grids could be written.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
