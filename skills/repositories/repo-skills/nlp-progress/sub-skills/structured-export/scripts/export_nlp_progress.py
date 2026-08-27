#!/usr/bin/env python3
"""Export NLP-progress Markdown benchmark pages to structured JSON.

This is a self-contained, standard-library adaptation of the NLP-progress
Markdown-to-JSON exporter. It keeps the repository's heading/table assumptions,
adds deterministic directory traversal, validates input/output paths, reads and
writes UTF-8 explicitly, and sends diagnostics to stderr so JSON can be written
to stdout when requested with ``--output -``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

SOURCE_LINK = {
    "title": "NLP-progress",
    "url": "https://github.com/sebastianruder/NLP-progress",
}

MARKDOWN_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")


def warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def error(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)


def extract_markdown_links(markdown: str) -> List[Dict[str, str]]:
    """Extract Markdown links as {title, url} dictionaries."""
    links: List[Dict[str, str]] = []
    for title, url in MARKDOWN_LINK_RE.findall(markdown):
        links.append({"title": title.strip(), "url": url.strip()})
    return links


def extract_dataset_desc_links(desc: List[str]) -> List[Dict[str, str]]:
    """Extract all Markdown links from a dataset description."""
    return extract_markdown_links("".join(desc))


def sanitize_subdataset_name(name: str) -> str:
    """Sanitize automatically extracted subdataset names."""
    name = name.replace("**", "")
    if name.endswith(":"):
        name = name[:-1]
    return name.strip()


def extract_lines_before_tables(lines: List[str]) -> List[str]:
    """Return the last non-empty line before each Markdown table."""
    out: List[str] = []
    before: Optional[str] = None
    in_table = False

    for line in lines:
        if line.startswith("|") and not in_table:
            if before is not None:
                out.append(before)
            in_table = True
        elif in_table and not line.startswith("|"):
            in_table = False
            before = None
            if line.strip() != "":
                before = line.strip()
        elif line.strip() != "":
            before = line.strip()

    return out


def extract_title_and_link(markdown_link: str) -> Tuple[str, str]:
    """Extract title and URL from a single Markdown link string."""
    links = extract_markdown_links(markdown_link)
    if not links:
        return "", ""
    first = links[0]
    return first["title"], first["url"]


def extract_model_name_and_author(markdown_name: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract the model name and parenthesized author text, if present."""
    if " (" in markdown_name and ")" in markdown_name:
        model_name = markdown_name.split(" (")[0]
        model_authors = markdown_name.split(" (")[1].split(")")[0]
    elif "(" in markdown_name and ")" in markdown_name:
        model_name = None
        model_authors = markdown_name
    else:
        model_name = markdown_name
        model_authors = None
    return model_name, model_authors


def extract_paper_title_and_link(paper_markdown: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract the first paper title and URL from a table cell."""
    links = extract_markdown_links(paper_markdown)
    if len(links) > 1:
        warn(f"Found multiple paper references: `{paper_markdown}`, using only the first")
    if not links:
        return None, None
    first = links[0]
    return first["title"], first["url"]


def extract_code_links(code_markdown: str) -> List[Dict[str, str]]:
    """Extract all code implementation links from a table cell."""
    return extract_markdown_links(code_markdown)


def sanitized_header_columns(header_line: str) -> Tuple[List[str], List[str]]:
    header_columns = [column.strip() for column in header_line.split("|") if column.strip()]
    sanitized = [column.lower() for column in header_columns]
    sanitized = [re.sub(r" +", "", column).replace("**", "") for column in sanitized]
    return header_columns, sanitized


def extract_sota_table(table_lines: List[str]) -> Dict[str, object]:
    """Parse one SOTA table from Markdown table lines."""
    if not table_lines:
        return {}

    header = table_lines[0]
    header_columns, columns_sanitized = sanitized_header_columns(header)

    if "model" in columns_sanitized:
        model_index = columns_sanitized.index("model")
    else:
        error("Model name not found in this SOTA table, skipping")
        print("".join(table_lines), file=sys.stderr)
        return {}

    if "paper/source" in columns_sanitized:
        paper_index = columns_sanitized.index("paper/source")
    elif "paper" in columns_sanitized:
        paper_index = columns_sanitized.index("paper")
    else:
        error("Paper reference not found in this SOTA table, skipping")
        print("".join(table_lines), file=sys.stderr)
        return {}

    code_index: Optional[int]
    if "code" in columns_sanitized:
        code_index = columns_sanitized.index("code")
    else:
        code_index = None

    excluded_indices = {model_index, paper_index}
    if code_index is not None:
        excluded_indices.add(code_index)
    metric_indices = sorted(set(range(len(header_columns))) - excluded_indices)
    metric_names = [header_columns[index] for index in metric_indices]

    sota: Dict[str, object] = {"metrics": metric_names, "rows": []}
    rows: List[Dict[str, object]] = []
    min_columns = len(header_columns)

    for row in table_lines[2:]:
        row_columns = [column.strip() for column in row.split("|")][1:]
        if len(row_columns) < min_columns:
            warn(f"This row does not have enough columns, skipping: {row.rstrip()}")
            continue

        metrics = {
            metric_names[i]: row_columns[metric_indices[i]]
            for i in range(len(metric_indices))
        }
        paper_title, paper_link = extract_paper_title_and_link(row_columns[paper_index])
        model_name, _model_author = extract_model_name_and_author(row_columns[model_index])

        sota_row: Dict[str, object] = {
            "model_name": model_name,
            "metrics": metrics,
        }
        if paper_title is not None and paper_link is not None:
            sota_row["paper_title"] = paper_title
            sota_row["paper_url"] = paper_link
        if code_index is not None:
            sota_row["code_links"] = extract_code_links(row_columns[code_index])

        rows.append(sota_row)

    sota["rows"] = rows
    return sota


def handle_multiple_sota_table_exceptions(section: List[str], sota_tables: List[List[str]]) -> List[Dict[str, object]]:
    """Infer subdataset labels for a section containing multiple SOTA tables."""
    section_full = "".join(section).lower()
    subdatasets = [sanitize_subdataset_name(name) for name in extract_lines_before_tables(section)]

    if "hypernym discovery evaluation benchmark" in section_full:
        # The SemEval-2018 Hypernym Discovery section has a non-SOTA partition
        # table before the SOTA tables. Drop the partition-table label.
        subdatasets = subdatasets[1:]

    if len(subdatasets) != len(sota_tables):
        error(
            "Parsing the subdataset SOTA tables: inferred "
            f"{len(subdatasets)} labels for {len(sota_tables)} tables; skipping these subdatasets"
        )
        print("Inferred subdataset labels:", subdatasets, file=sys.stderr)
        print("SOTA table headers:", [table[0].rstrip() for table in sota_tables], file=sys.stderr)
        return []

    out: List[Dict[str, object]] = []
    for subdataset, table in zip(subdatasets, sota_tables):
        sota = extract_sota_table(table)
        if sota:
            out.append({"subdataset": subdataset, "sota": sota})
    return out


def get_line_no(sections: List[List[str]], section_index: int, section_line: int = 0) -> int:
    """Get the original line number for a section heading."""
    if section_index == 0:
        return 1 + section_line
    return sum(len(section) for section in sections[:section_index]) + 1 + section_index


def extract_dataset_desc_and_sota_table(markdown_lines: List[str]) -> Tuple[List[str], List[List[str]]]:
    """Split a section into description lines and SOTA table line groups."""
    desc: List[str] = []
    tables: List[List[str]] = []
    table: Optional[List[str]] = None
    in_table = False

    for line in markdown_lines:
        if line.startswith("|") and "model" in line.lower() and not in_table:
            table = [line]
            in_table = True
        elif in_table and line.startswith("|"):
            assert table is not None
            table.append(line)
        elif in_table and not line.startswith("|"):
            if table is not None:
                tables.append(table)
            table = None
            desc.append(line)
            in_table = False
        else:
            desc.append(line)

    if table is not None:
        tables.append(table)

    return desc, tables


def split_sections(markdown_lines: Iterable[str]) -> List[List[str]]:
    """Split Markdown into heading-led sections using column-0 # headings."""
    sections: List[List[str]] = []
    current: List[str] = []
    for line in markdown_lines:
        if line.startswith("#"):
            if current:
                sections.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append(current)
    return sections


def is_h1(header: str) -> bool:
    return header.startswith("#") and not header.startswith("##")


def is_h2(header: str) -> bool:
    return header.startswith("##") and not header.startswith("###")


def is_h3(header: str) -> bool:
    return header.startswith("###") and not header.startswith("####")


def is_h4(header: str) -> bool:
    return header.startswith("####") and not header.startswith("#####")


def parse_markdown_file(markdown_file: Path) -> List[Dict[str, object]]:
    """Parse a single NLP-progress Markdown file."""
    markdown_lines = markdown_file.read_text(encoding="utf-8").splitlines(keepends=True)
    sections = split_sections(markdown_lines)

    parsed_out: List[Dict[str, object]] = []
    task: Dict[str, object] = {}
    subtask: Optional[Dict[str, object]] = None
    dataset: Optional[Dict[str, object]] = None

    for section_index, section in enumerate(sections):
        header = section[0]

        if is_h1(header):
            if "task" in task:
                parsed_out.append(task)
                task = {}
            task["task"] = header[1:].strip()
            task["description"] = "".join(section[1:]).strip()
            subtask = None
            dataset = None

        if is_h2(header):
            if "task" not in task:
                error(
                    "Unexpected subtask without a parent task at "
                    f"{markdown_file}:#{get_line_no(sections, section_index)}"
                )

            task.setdefault("subtasks", [])
            subtask = {
                "task": header[2:].strip(),
                "description": "".join(section[1:]).strip(),
                "source_link": dict(SOURCE_LINK),
            }
            assert isinstance(task["subtasks"], list)
            task["subtasks"].append(subtask)
            dataset = None

        if is_h3(header) and "Table of content" not in header:
            if "task" not in task:
                error(
                    "Unexpected dataset without a parent task at "
                    f"{markdown_file}:#{get_line_no(sections, section_index)}"
                )

            dataset = {"dataset": header[3:].strip()}
            if subtask is not None:
                subtask.setdefault("datasets", [])
                assert isinstance(subtask["datasets"], list)
                subtask["datasets"].append(dataset)
            else:
                task.setdefault("datasets", [])
                assert isinstance(task["datasets"], list)
                task["datasets"].append(dataset)

            desc, tables = extract_dataset_desc_and_sota_table(section[1:])
            dataset["description"] = "".join(desc).strip()

            dataset_links = extract_dataset_desc_links(desc)
            if dataset_links:
                dataset["dataset_links"] = dataset_links

            if len(tables) > 1:
                subdatasets = handle_multiple_sota_table_exceptions(section, tables)
                if subdatasets:
                    dataset["subdatasets"] = subdatasets
            elif len(tables) == 1:
                sota = extract_sota_table(tables[0])
                if sota:
                    dataset["sota"] = sota

        if is_h4(header):
            if dataset is None:
                error(
                    "Unexpected subdataset without a parent dataset at "
                    f"{markdown_file}:#{get_line_no(sections, section_index)}"
                )
                continue

            desc, tables = extract_dataset_desc_and_sota_table(section[1:])
            if not tables:
                continue

            dataset.setdefault("subdatasets", [])
            assert isinstance(dataset["subdatasets"], list)
            subdataset_name = sanitize_subdataset_name(header[4:].strip())

            if len(tables) > 1:
                inferred = handle_multiple_sota_table_exceptions(section, tables)
                if inferred:
                    dataset["subdatasets"].extend(inferred)
            else:
                sota = extract_sota_table(tables[0])
                if sota:
                    dataset["subdatasets"].append({"subdataset": subdataset_name, "sota": sota})

    if task:
        task["source_link"] = dict(SOURCE_LINK)
        parsed_out.append(task)

    return parsed_out


def parse_markdown_directory(path: Path) -> List[Dict[str, object]]:
    """Parse all top-level .md files in a directory in deterministic order."""
    markdown_files = sorted(p for p in path.iterdir() if p.is_file() and p.name.endswith(".md"))
    if not markdown_files:
        warn(f"Directory has no top-level .md files and contributes no output: {path}")

    out: List[Dict[str, object]] = []
    for markdown_file in markdown_files:
        print(f"Processing `{markdown_file.name}`...", file=sys.stderr)
        out.extend(parse_markdown_file(markdown_file))
    return out


def validate_input_paths(raw_paths: Sequence[str], parser: argparse.ArgumentParser) -> List[Path]:
    paths: List[Path] = []
    for raw_path in raw_paths:
        path = Path(raw_path)
        if not path.exists():
            parser.error(f"input path does not exist: {raw_path}")
        if not path.is_file() and not path.is_dir():
            parser.error(f"input path is neither a file nor a directory: {raw_path}")
        paths.append(path)
    return paths


def validate_output_path(raw_output: str, parser: argparse.ArgumentParser) -> Optional[Path]:
    if raw_output == "-":
        return None
    output = Path(raw_output)
    parent = output.parent
    if str(parent) not in ("", ".") and not parent.exists():
        parser.error(f"output parent directory does not exist: {parent}")
    if output.exists() and output.is_dir():
        parser.error(f"output path is a directory, expected a JSON file path: {raw_output}")
    return output


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Parse NLP-progress Markdown task pages and export their tasks, "
            "datasets, SOTA tables, metrics, paper links, and code links to JSON."
        )
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=str,
        help=(
            "One or more Markdown files or directories to convert. Directories are "
            "scanned for top-level .md files only. CLI argument order is preserved."
        ),
    )
    parser.add_argument(
        "--output",
        default="structured.json",
        type=str,
        help=(
            "Output JSON file path. Defaults to structured.json. Use '-' to write "
            "JSON to stdout; diagnostics still go to stderr."
        ),
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    paths = validate_input_paths(args.paths, parser)
    output_path = validate_output_path(args.output, parser)

    out: List[Dict[str, object]] = []
    for path in paths:
        if path.is_dir():
            out.extend(parse_markdown_directory(path))
        else:
            out.extend(parse_markdown_file(path))

    if output_path is None:
        json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        with output_path.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(out, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
