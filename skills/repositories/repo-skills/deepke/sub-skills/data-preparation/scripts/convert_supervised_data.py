#!/usr/bin/env python3
"""Standalone DeepKE supervised-data converters.

Generated helper for the DeepKE data-preparation skill. It adapts the small
format-conversion behavior DeepKE users need without importing DeepKE or reading
from any source checkout.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple
import xml.etree.ElementTree as ET

XML_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}

Span = Tuple[int, int, str]


class ConversionError(ValueError):
    """User-facing conversion failure."""


def read_json_records(path: Path, *, json_lines: bool = False, encoding: str = "utf-8") -> List[Dict[str, Any]]:
    try:
        text = path.read_text(encoding=encoding)
    except OSError as exc:
        raise ConversionError(f"cannot read {path}: {exc}") from exc

    try:
        if json_lines:
            records: List[Dict[str, Any]] = []
            for line_no, line in enumerate(text.splitlines(), 1):
                line = line.strip()
                if not line:
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ConversionError(f"JSONL line {line_no} is {type(value).__name__}, expected object")
                records.append(value)
            return records
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConversionError(f"invalid JSON in {path}: line {exc.lineno} column {exc.colno}: {exc.msg}") from exc

    if isinstance(value, list):
        if not all(isinstance(item, dict) for item in value):
            raise ConversionError("JSON array must contain objects")
        return list(value)
    if isinstance(value, dict):
        # Accept a single doccano-style export record for convenience.
        return [value]
    raise ConversionError(f"top-level JSON must be an object or array, got {type(value).__name__}")


def ensure_parent(path: Path) -> None:
    if path.parent and str(path.parent) != ".":
        path.parent.mkdir(parents=True, exist_ok=True)


def json_scalar_for_csv(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ordered_fieldnames(records: Sequence[Dict[str, Any]]) -> List[str]:
    seen = set()
    fields: List[str] = []
    for record in records:
        for key in record.keys():
            if key not in seen:
                seen.add(key)
                fields.append(str(key))
    if not fields:
        raise ConversionError("no fields found in input records")
    return fields


def convert_json2csv(args: argparse.Namespace) -> None:
    records = read_json_records(Path(args.input), json_lines=args.json_lines, encoding=args.encoding)
    if not records:
        raise ConversionError("input JSON contains no records")
    fields = ordered_fieldnames(records)
    out = Path(args.output)
    ensure_parent(out)
    with out.open("w", encoding=args.encoding, newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: json_scalar_for_csv(record.get(field)) for field in fields})
    print(f"wrote {len(records)} rows to {out}")


def col_ref_to_index(ref: str) -> int:
    match = re.match(r"([A-Z]+)", ref.upper())
    if not match:
        return 0
    value = 0
    for char in match.group(1):
        value = value * 26 + (ord(char) - ord("A") + 1)
    return value - 1


def read_shared_strings(zf: zipfile.ZipFile) -> List[str]:
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    strings: List[str] = []
    for si in root.findall("main:si", XML_NS):
        pieces: List[str] = []
        for text_node in si.findall(".//main:t", XML_NS):
            pieces.append(text_node.text or "")
        strings.append("".join(pieces))
    return strings


def workbook_sheet_path(zf: zipfile.ZipFile, sheet_index: int) -> str:
    fallback = f"xl/worksheets/sheet{sheet_index + 1}.xml"
    try:
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    except KeyError:
        if fallback in zf.namelist():
            return fallback
        raise ConversionError("xlsx is missing workbook metadata and the expected worksheet file")

    sheets = workbook.findall("main:sheets/main:sheet", XML_NS)
    if sheet_index < 0 or sheet_index >= len(sheets):
        raise ConversionError(f"sheet index {sheet_index} is out of range for {len(sheets)} sheet(s)")
    rel_id = sheets[sheet_index].attrib.get(f"{{{XML_NS['rel']}}}id")
    if not rel_id:
        return fallback

    for rel in rels.findall("pkgrel:Relationship", XML_NS):
        if rel.attrib.get("Id") == rel_id:
            target = rel.attrib.get("Target", "")
            if target.startswith("/"):
                return target.lstrip("/")
            if target.startswith("xl/"):
                return target
            return "xl/" + target
    return fallback


def cell_text(cell: ET.Element, shared_strings: Sequence[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(t.text or "" for t in cell.findall(".//main:t", XML_NS))
    value_node = cell.find("main:v", XML_NS)
    if value_node is None or value_node.text is None:
        return ""
    raw = value_node.text
    if cell_type == "s":
        try:
            return shared_strings[int(raw)]
        except (ValueError, IndexError):
            raise ConversionError(f"invalid shared-string index {raw!r}")
    if cell_type == "b":
        return "TRUE" if raw == "1" else "FALSE"
    return raw


def read_xlsx_rows(path: Path, *, sheet_index: int = 0) -> List[List[str]]:
    try:
        with zipfile.ZipFile(path) as zf:
            shared = read_shared_strings(zf)
            sheet_path = workbook_sheet_path(zf, sheet_index)
            try:
                root = ET.fromstring(zf.read(sheet_path))
            except KeyError as exc:
                raise ConversionError(f"xlsx is missing worksheet {sheet_path}") from exc
            rows: List[List[str]] = []
            for row in root.findall(".//main:sheetData/main:row", XML_NS):
                values: List[str] = []
                for cell in row.findall("main:c", XML_NS):
                    ref = cell.attrib.get("r", "")
                    index = col_ref_to_index(ref) if ref else len(values)
                    while len(values) < index:
                        values.append("")
                    values.append(cell_text(cell, shared))
                rows.append(values)
            return rows
    except zipfile.BadZipFile as exc:
        raise ConversionError(f"{path} is not a valid .xlsx file") from exc


def convert_xlsx2csv(args: argparse.Namespace) -> None:
    rows = read_xlsx_rows(Path(args.input), sheet_index=args.sheet_index)
    rows = [row for row in rows if any(cell != "" for cell in row)]
    if not rows:
        raise ConversionError("xlsx worksheet has no nonempty rows")
    header = [str(cell).strip() for cell in rows[0]]
    if not any(header):
        raise ConversionError("xlsx first row must contain column headers")
    # Fill blank headers with stable generated names instead of silently dropping cells.
    header = [name if name else f"column_{i + 1}" for i, name in enumerate(header)]
    width = len(header)
    out = Path(args.output)
    ensure_parent(out)
    with out.open("w", encoding=args.encoding, newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for row in rows[1:]:
            padded = list(row[:width]) + [""] * max(0, width - len(row))
            writer.writerow(padded)
    print(f"wrote {max(0, len(rows) - 1)} rows to {out}")


def normalize_doccano_label(label_item: Any, *, context: str) -> Dict[str, Any]:
    """Normalize doccano sequence-labeling exports into entity dictionaries.

    Doccano versions and export settings vary. Some write `entities` objects with
    `start_offset`/`end_offset`; others write `label` or `labels` rows like
    `[start, end, label]` or dictionaries with `start`, `end`, and `label`.
    """
    if isinstance(label_item, dict):
        label = label_item.get("label", label_item.get("type", label_item.get("tag")))
        start = label_item.get("start_offset", label_item.get("start"))
        end = label_item.get("end_offset", label_item.get("end"))
        return {"label": label, "start_offset": start, "end_offset": end, "text": label_item.get("text")}
    if isinstance(label_item, (list, tuple)) and len(label_item) >= 3:
        start, end, label = label_item[0], label_item[1], label_item[2]
        return {"label": label, "start_offset": start, "end_offset": end}
    raise ConversionError(f"{context}: doccano label entry must be an object or [start, end, label] list")


def text_and_entities(record: Dict[str, Any], input_format: str) -> Tuple[str, List[Dict[str, Any]]]:
    if input_format == "doccano" or (input_format == "auto" and "text" in record):
        text = record.get("text")
    else:
        text = record.get("sentence", record.get("text"))
    if not isinstance(text, str):
        raise ConversionError("NER record is missing string field 'sentence' or 'text'")
    entities = record.get("entities")
    if entities is None and (input_format == "doccano" or "label" in record or "labels" in record):
        raw_labels = record.get("label", record.get("labels", []))
        if raw_labels is None:
            raw_labels = []
        if not isinstance(raw_labels, list):
            raise ConversionError("doccano record field 'label'/'labels' must be a list")
        entities = [normalize_doccano_label(item, context="doccano label") for item in raw_labels]
    if entities is None:
        entities = []
    if not isinstance(entities, list):
        raise ConversionError("NER record field 'entities' must be a list")
    return text, entities


def add_span(spans: List[Span], start: int, end: int, label: str, text: str, *, context: str) -> None:
    if not label:
        raise ConversionError(f"{context}: entity label is empty")
    if start < 0 or end < start or end > len(text):
        raise ConversionError(f"{context}: span ({start}, {end}) is outside text length {len(text)}")
    if start == end:
        return
    spans.append((start, end, label))


def spans_from_entities(text: str, entities: Sequence[Dict[str, Any]], *, context: str) -> List[Span]:
    spans: List[Span] = []
    for ent_index, entity in enumerate(entities):
        if not isinstance(entity, dict):
            raise ConversionError(f"{context}: entity {ent_index} is not an object")
        label = str(entity.get("label", "")).strip()
        has_offsets = "start_offset" in entity or "end_offset" in entity or "start" in entity or "end" in entity
        if has_offsets:
            try:
                start = int(entity.get("start_offset", entity.get("start")))
                end = int(entity.get("end_offset", entity.get("end")))
            except (TypeError, ValueError) as exc:
                raise ConversionError(f"{context}: entity {ent_index} has non-integer offsets") from exc
            surface = entity.get("word", entity.get("text"))
            if isinstance(surface, str) and surface and text[start:end] != surface:
                raise ConversionError(
                    f"{context}: offset text {text[start:end]!r} does not match entity surface {surface!r}"
                )
            add_span(spans, start, end, label, text, context=f"{context}: entity {ent_index}")
            continue

        word = entity.get("word", entity.get("text"))
        if not isinstance(word, str) or not word:
            raise ConversionError(f"{context}: entity {ent_index} needs offsets or a nonempty 'word'/'text'")
        pos = 0
        found = False
        while True:
            idx = text.find(word, pos)
            if idx < 0:
                break
            add_span(spans, idx, idx + len(word), label, text, context=f"{context}: entity {ent_index}")
            found = True
            pos = idx + max(1, len(word))
        if not found:
            raise ConversionError(f"{context}: entity surface {word!r} was not found in text")
    return spans


def validate_no_overlap(spans: Sequence[Span], *, context: str) -> None:
    ordered = sorted(spans, key=lambda s: (s[0], s[1]))
    for prev, cur in zip(ordered, ordered[1:]):
        if cur[0] < prev[1]:
            raise ConversionError(f"{context}: overlapping spans {prev} and {cur} cannot be represented as simple BIO")


def char_units(text: str) -> List[Tuple[str, int, int]]:
    return [(ch, i, i + 1) for i, ch in enumerate(text) if ch not in "\r\n"]


def token_units(text: str) -> List[Tuple[str, int, int]]:
    # Words/numbers plus individual punctuation. This keeps English multi-word entity BIO usable.
    return [(m.group(0), m.start(), m.end()) for m in re.finditer(r"\w+|[^\w\s]", text, flags=re.UNICODE)]


def labels_for_units(units: Sequence[Tuple[str, int, int]], spans: Sequence[Span]) -> List[str]:
    labels: List[str] = []
    for _, start, end in units:
        label = "O"
        for span_start, span_end, span_label in spans:
            if end <= span_start or start >= span_end:
                continue
            prefix = "B" if start == span_start else "I"
            label = f"{prefix}-{span_label}"
            break
        labels.append(label)
    return labels


def write_ner_txt(samples: Sequence[Tuple[str, List[Span]]], out: Path, *, unit: str, encoding: str) -> None:
    ensure_parent(out)
    with out.open("w", encoding=encoding, newline="\n") as fh:
        for sample_index, (text, spans) in enumerate(samples):
            validate_no_overlap(spans, context=f"sample {sample_index}")
            units = token_units(text) if unit == "token" else char_units(text)
            labels = labels_for_units(units, spans)
            for (piece, _, _), label in zip(units, labels):
                fh.write(f"{piece} {label}\n")
            if sample_index != len(samples) - 1:
                fh.write("\n")


def convert_json2txt(args: argparse.Namespace) -> None:
    records = read_json_records(Path(args.input), json_lines=args.json_lines, encoding=args.encoding)
    if not records:
        raise ConversionError("input JSON contains no NER records")
    samples: List[Tuple[str, List[Span]]] = []
    for idx, record in enumerate(records):
        text, entities = text_and_entities(record, args.input_format)
        spans = spans_from_entities(text, entities, context=f"record {idx}")
        samples.append((text, spans))
    write_ner_txt(samples, Path(args.output), unit=args.unit, encoding=args.encoding)
    print(f"wrote {len(samples)} NER sample(s) to {args.output}")


def docx_paragraphs(path: Path) -> List[str]:
    try:
        with zipfile.ZipFile(path) as zf:
            try:
                xml = zf.read("word/document.xml")
            except KeyError as exc:
                raise ConversionError("docx is missing word/document.xml") from exc
    except zipfile.BadZipFile as exc:
        raise ConversionError(f"{path} is not a valid .docx file") from exc
    root = ET.fromstring(xml)
    paragraphs: List[str] = []
    for para in root.findall(".//w:p", XML_NS):
        pieces: List[str] = []
        for node in para.iter():
            if node.tag == f"{{{XML_NS['w']}}}t" and node.text:
                pieces.append(node.text)
            elif node.tag == f"{{{XML_NS['w']}}}tab":
                pieces.append("\t")
        text = "".join(pieces).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def samples_from_docx(path: Path) -> List[Tuple[str, List[Span]]]:
    paragraphs = docx_paragraphs(path)
    samples: List[Tuple[str, List[Dict[str, Any]]]] = []
    current_text: str | None = None
    current_entities: List[Dict[str, Any]] = []

    def flush() -> None:
        nonlocal current_text, current_entities
        if current_text is not None:
            samples.append((current_text, current_entities))
        current_text = None
        current_entities = []

    sentence_re = re.compile(r"^Sentence\s*[:：]\s*(.*)$", re.IGNORECASE)
    label_re = re.compile(r"^([^:：]+)[:：](.*)$")
    for para_index, paragraph in enumerate(paragraphs):
        sentence_match = sentence_re.match(paragraph)
        if sentence_match:
            flush()
            current_text = sentence_match.group(1).strip()
            if not current_text:
                raise ConversionError(f"paragraph {para_index}: sentence text is empty")
            continue
        label_match = label_re.match(paragraph)
        if label_match:
            if current_text is None:
                raise ConversionError(f"paragraph {para_index}: label paragraph appears before any Sentence paragraph")
            label = label_match.group(1).strip()
            words = [item.strip() for item in re.split(r"[,，]", label_match.group(2)) if item.strip()]
            for word in words:
                current_entities.append({"word": word, "label": label})
            continue
        raise ConversionError(f"paragraph {para_index}: expected 'Sentence:<text>' or 'LABEL:entity1,entity2'")
    flush()

    if not samples:
        raise ConversionError("docx contained no Sentence paragraphs")
    converted: List[Tuple[str, List[Span]]] = []
    for idx, (text, entities) in enumerate(samples):
        converted.append((text, spans_from_entities(text, entities, context=f"docx sentence {idx}")))
    return converted


def convert_docx2txt(args: argparse.Namespace) -> None:
    samples = samples_from_docx(Path(args.input))
    write_ner_txt(samples, Path(args.output), unit=args.unit, encoding=args.encoding)
    print(f"wrote {len(samples)} NER sample(s) to {args.output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert supervised DeepKE NER/RE/AE data without importing DeepKE.",
    )
    parser.add_argument("--encoding", default="utf-8", help="text encoding for JSON/CSV/TXT files (default: utf-8)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("json2csv", help="convert JSON array/JSONL objects to CSV for RE or AE tabular data")
    p.add_argument("input", help="input .json or .jsonl file")
    p.add_argument("output", help="output .csv file")
    p.add_argument("--json-lines", action="store_true", help="read one JSON object per nonempty line")
    p.set_defaults(func=convert_json2csv)

    p = sub.add_parser("xlsx2csv", help="convert the first worksheet of an .xlsx file to CSV")
    p.add_argument("input", help="input .xlsx file")
    p.add_argument("output", help="output .csv file")
    p.add_argument("--sheet-index", type=int, default=0, help="zero-based worksheet index (default: 0)")
    p.set_defaults(func=convert_xlsx2csv)

    p = sub.add_parser("json2txt", help="convert DeepKE-style or doccano-style NER JSON to BIO text")
    p.add_argument("input", help="input .json or .jsonl file")
    p.add_argument("output", help="output BIO .txt file")
    p.add_argument("--json-lines", action="store_true", help="read one JSON object per nonempty line")
    p.add_argument("--input-format", choices=["auto", "deepke", "doccano"], default="auto", help="NER JSON schema hint")
    p.add_argument("--unit", choices=["char", "token"], default="char", help="BIO output unit (default: char)")
    p.set_defaults(func=convert_json2txt)

    p = sub.add_parser("docx2txt", help="convert paragraph-form NER .docx annotations to BIO text")
    p.add_argument("input", help="input .docx file")
    p.add_argument("output", help="output BIO .txt file")
    p.add_argument("--unit", choices=["char", "token"], default="char", help="BIO output unit (default: char)")
    p.set_defaults(func=convert_docx2txt)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except ConversionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
