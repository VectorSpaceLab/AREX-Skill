#!/usr/bin/env python3
"""Create simple DeepKE-LLM instruction JSONL records from common IE/KG labels.

This standalone helper mirrors the public contract of DeepKE's instruction data:
records contain ``task``, ``source``, ``instruction`` (a JSON string with an
instruction, schema, and input), and, for train mode, ``output``. It intentionally
avoids model calls, negative sampling, hard-negative clustering, and imports from
the DeepKE source checkout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence

INSTRUCTIONS = {
    ("NER", "en"): "You are an expert in named entity recognition. Extract entities that match the schema from the input. Return an empty list for labels that do not appear. Respond as a JSON string.",
    ("NER", "zh"): "你是命名实体识别专家。请从输入中抽取符合 schema 的实体；不存在的类型返回空列表。请用 JSON 字符串回答。",
    ("RE", "en"): "You are an expert in relation extraction. Extract head-tail entity pairs for each relation in the schema from the input. Return an empty list for absent relations. Respond as a JSON string.",
    ("RE", "zh"): "你是关系抽取专家。请从输入中为 schema 中的每个关系抽取头实体和尾实体；不存在的关系返回空列表。请用 JSON 字符串回答。",
    ("SPO", "en"): "You are an expert in subject-predicate-object extraction. Extract triples whose predicate matches the schema. Respond as a JSON string.",
    ("SPO", "zh"): "你是主谓宾三元组抽取专家。请抽取谓词符合 schema 的三元组。请用 JSON 字符串回答。",
    ("KG", "en"): "You are an expert in knowledge graph construction. Extract relation triples that match the schema from the input. Respond as a JSON string.",
    ("KG", "zh"): "你是知识图谱构建专家。请从输入中抽取符合 schema 的关系三元组。请用 JSON 字符串回答。",
    ("EE", "en"): "You are an expert in event extraction. Extract events and arguments that match the schema from the input. Respond as a JSON string.",
    ("EE", "zh"): "你是事件抽取专家。请从输入中抽取符合 schema 的事件及论元。请用 JSON 字符串回答。",
    ("EET", "en"): "You are an expert in event trigger extraction. Extract triggers that match the schema from the input. Respond as a JSON string.",
    ("EET", "zh"): "你是事件触发词抽取专家。请从输入中抽取符合 schema 的触发词。请用 JSON 字符串回答。",
    ("EEA", "en"): "You are an expert in event argument extraction. Extract event arguments that match the schema from the input. Respond as a JSON string.",
    ("EEA", "zh"): "你是事件论元抽取专家。请从输入中抽取符合 schema 的事件论元。请用 JSON 字符串回答。",
}

TEXT_KEYS = ("text", "input", "sentence", "content", "document")
NER_KEYS = ("entities", "entity", "ner")
REL_KEYS = ("relations", "relation", "spo", "kg", "triples")
EVENT_KEYS = ("events", "event", "event_list")


class ConvertError(Exception):
    """Raised for invalid records or conversion options."""


def load_json_records(path: Path) -> List[Dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        return []
    if text[0] == "[":
        data = json.loads(text)
        if not isinstance(data, list):
            raise ConvertError("top-level JSON array expected")
        records = data
    elif text[0] == "{" and "\n" not in text:
        records = [json.loads(text)]
    else:
        records = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ConvertError(f"line {line_no}: invalid JSONL row: {exc}") from exc
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ConvertError(f"record {index} is {type(record).__name__}, expected object")
    return records  # type: ignore[return-value]


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [value]


def unique_preserve(values: Iterable[Any]) -> List[str]:
    seen = set()
    out: List[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def first_value(record: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in record:
            return record[key]
    return None


def nested_value(obj: Any, keys: Sequence[str]) -> Any:
    if isinstance(obj, Mapping):
        for key in keys:
            if key in obj:
                return obj[key]
    return None


def infer_text(record: Mapping[str, Any], index: int) -> str:
    value = first_value(record, TEXT_KEYS)
    if value is None:
        raise ConvertError(f"record {index}: missing text/input field")
    if not isinstance(value, str):
        value = str(value)
    if not value.strip():
        raise ConvertError(f"record {index}: input text is empty")
    return value


def infer_schema(record: Mapping[str, Any], task: str, schema_field: str | None) -> List[str]:
    if schema_field and schema_field in record:
        return unique_preserve(as_list(record[schema_field]))
    if "schema" in record:
        return unique_preserve(as_list(record["schema"]))
    labels: List[Any] = []
    if task == "NER":
        for ent in as_list(first_value(record, NER_KEYS)):
            labels.append(nested_value(ent, ("type", "label", "entity_type", "tag")))
    elif task in {"RE", "SPO", "KG"}:
        for rel in as_list(first_value(record, REL_KEYS)):
            if isinstance(rel, (list, tuple)) and len(rel) >= 3:
                labels.append(rel[1])
            else:
                labels.append(nested_value(rel, ("relation", "predicate", "label", "type")))
    else:
        for event in as_list(first_value(record, EVENT_KEYS)):
            labels.append(nested_value(event, ("event_type", "type", "label")))
    return unique_preserve(labels)


def ner_output(record: Mapping[str, Any], schema: Sequence[str]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {label: [] for label in schema}
    for ent in as_list(first_value(record, NER_KEYS)):
        if not isinstance(ent, Mapping):
            continue
        label = nested_value(ent, ("type", "label", "entity_type", "tag"))
        text = nested_value(ent, ("text", "word", "entity", "name"))
        if label is None or text is None:
            continue
        out.setdefault(str(label), []).append(str(text))
    return out


def relation_output(record: Mapping[str, Any], schema: Sequence[str]) -> Dict[str, List[List[str]]]:
    out: Dict[str, List[List[str]]] = {label: [] for label in schema}
    for rel in as_list(first_value(record, REL_KEYS)):
        head = relation = tail = None
        if isinstance(rel, (list, tuple)) and len(rel) >= 3:
            head, relation, tail = rel[0], rel[1], rel[2]
        elif isinstance(rel, Mapping):
            head = nested_value(rel, ("head", "subject", "subj", "h"))
            relation = nested_value(rel, ("relation", "predicate", "label", "type", "rel"))
            tail = nested_value(rel, ("tail", "object", "obj", "t"))
        if head is None or relation is None or tail is None:
            continue
        out.setdefault(str(relation), []).append([str(head), str(tail)])
    return out


def event_output(record: Mapping[str, Any]) -> Any:
    events = first_value(record, EVENT_KEYS)
    return [] if events is None else events


def build_output(record: Mapping[str, Any], task: str, schema: Sequence[str], output_from_field: str | None) -> str:
    if output_from_field:
        if output_from_field not in record:
            raise ConvertError(f"record with text {str(first_value(record, TEXT_KEYS))[:40]!r}: missing output field {output_from_field!r}")
        value = record[output_from_field]
    elif "output" in record:
        value = record["output"]
    elif task == "NER":
        value = ner_output(record, schema)
    elif task in {"RE", "SPO", "KG"}:
        value = relation_output(record, schema)
    else:
        value = event_output(record)
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def make_instruction(task: str, language: str, schema: Sequence[str], text: str) -> str:
    prompt = INSTRUCTIONS.get((task, language)) or INSTRUCTIONS.get((task, "en")) or INSTRUCTIONS[("KG", "en")]
    return json.dumps({"instruction": prompt, "schema": list(schema), "input": text}, ensure_ascii=False)


def convert(records: Sequence[Dict[str, Any]], args: argparse.Namespace) -> List[Dict[str, Any]]:
    explicit_schema = unique_preserve(as_list(args.schema)) if args.schema else None
    out: List[Dict[str, Any]] = []
    for index, record in enumerate(records):
        text = infer_text(record, index)
        schema = explicit_schema or infer_schema(record, args.task, args.schema_field)
        if not schema:
            raise ConvertError(f"record {index}: schema is empty; supply --schema, --schema-field, or labels that expose schema names")
        item: MutableMapping[str, Any] = {
            "task": args.task,
            "source": args.source,
            "instruction": make_instruction(args.task, args.language, schema, text),
        }
        if args.id_field and args.id_field in record:
            item["id"] = record[args.id_field]
        elif "id" in record:
            item["id"] = record["id"]
        if args.mode == "train":
            item["output"] = build_output(record, args.task, schema, args.output_from_field)
        elif args.include_label:
            item["label"] = build_output(record, args.task, schema, args.output_from_field)
        out.append(dict(item))
    return out


def write_records(records: Sequence[Dict[str, Any]], path: Path, *, json_array: bool, pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if json_array:
        path.write_text(json.dumps(records, ensure_ascii=False, indent=2 if pretty else None) + "\n", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert common IE/KG JSONL records to DeepKE-LLM-style instruction records without model calls.")
    parser.add_argument("--input", required=True, help="input JSONL, JSON array, or single JSON object")
    parser.add_argument("--output", required=True, help="output instruction file")
    parser.add_argument("--task", choices=["NER", "RE", "EE", "EET", "EEA", "SPO", "KG"], required=True)
    parser.add_argument("--language", choices=["zh", "en"], default="en")
    parser.add_argument("--source", default="custom", help="source dataset name to write into each record")
    parser.add_argument("--mode", choices=["train", "test"], default="train")
    parser.add_argument("--schema", help="comma-separated schema labels to use for every record")
    parser.add_argument("--schema-field", help="record field containing schema labels; defaults to 'schema' when present")
    parser.add_argument("--output-from-field", help="copy/serialize this record field as output/label instead of inferring labels")
    parser.add_argument("--id-field", help="record field to copy as id; defaults to existing 'id' when present")
    parser.add_argument("--include-label", action="store_true", help="in test mode, include a label field when labels are available")
    parser.add_argument("--json-array", action="store_true", help="write one JSON array instead of JSONL")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON arrays")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        records = load_json_records(Path(args.input))
        converted = convert(records, args)
        write_records(converted, Path(args.output), json_array=args.json_array, pretty=args.pretty)
        print(f"wrote {len(converted)} instruction record(s) to {args.output}")
    except (OSError, json.JSONDecodeError, ConvertError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
