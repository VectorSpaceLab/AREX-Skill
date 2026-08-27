#!/usr/bin/env python3
"""Validate Agriculture_KnowledgeGraph relation-extraction dataset schemas.

This checker is intentionally TensorFlow-free. It validates small TSV/JSON
fixtures and generated preprocessing files before the PCNN data loader is used.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from typing import Any, Dict, Iterable, List, Optional, Tuple


class Report:
    def __init__(self, max_errors: int = 50) -> None:
        self.max_errors = max_errors
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checked: List[str] = []

    def check(self, label: str) -> None:
        self.checked.append(label)

    def error(self, message: str) -> None:
        if len(self.errors) < self.max_errors:
            self.errors.append(message)
        elif len(self.errors) == self.max_errors:
            self.errors.append("maximum error display limit reached; additional errors suppressed")

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors

    def emit(self) -> None:
        for label in self.checked:
            print(f"[CHECKED] {label}")
        for warning in self.warnings:
            print(f"[WARN] {warning}", file=sys.stderr)
        for error in self.errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        if self.ok:
            print(f"[OK] {len(self.checked)} input group(s) checked; {len(self.warnings)} warning(s)")
        else:
            print(f"[FAIL] {len(self.errors)} error(s), {len(self.warnings)} warning(s)", file=sys.stderr)


def read_json(path: str, report: Report) -> Any:
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except FileNotFoundError:
        report.error(f"{path}: file does not exist")
    except json.JSONDecodeError as exc:
        report.error(f"{path}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}")
    except OSError as exc:
        report.error(f"{path}: cannot read file: {exc}")
    return None


def is_int_like(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("-"):
            stripped = stripped[1:]
        return stripped.isdigit()
    return False


def to_int(value: Any) -> Optional[int]:
    if not is_int_like(value):
        return None
    return int(value)


def strip_wrapping_quotes(text: str) -> str:
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1]
    return text


def valid_non_bool_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_id_mapping(
    path: str,
    value: Any,
    report: Report,
    label: str,
    require_na_zero: bool = False,
) -> Optional[Dict[str, int]]:
    if value is None:
        return None
    report.check(f"{label}: {path}")
    if not isinstance(value, dict):
        report.error(f"{path}: expected JSON object mapping strings to integer ids")
        return None

    seen_ids: Dict[int, str] = {}
    parsed: Dict[str, int] = {}
    for key, raw_id in value.items():
        if not isinstance(key, str) or not key.strip():
            report.error(f"{path}: mapping key {key!r} must be a non-empty string")
            continue
        if not valid_non_bool_int(raw_id):
            report.error(f"{path}: id for {key!r} must be a non-negative integer, got {raw_id!r}")
            continue
        if raw_id in seen_ids:
            report.error(f"{path}: duplicate id {raw_id} for {key!r} and {seen_ids[raw_id]!r}")
        seen_ids[raw_id] = key
        parsed[key] = raw_id

    if require_na_zero:
        if parsed.get("NA") != 0:
            report.error(f"{path}: rel2id must contain 'NA': 0 for the PCNN evaluation assumptions")

    if parsed:
        expected = set(range(len(parsed)))
        actual = set(parsed.values())
        if expected != actual:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            report.warn(
                f"{path}: ids are not contiguous 0..{len(parsed) - 1}; "
                f"missing={missing[:8]} extra={extra[:8]}"
            )
    return parsed


def looks_like_header(fields: List[str]) -> bool:
    normalized = [field.strip().lower().replace("_", "") for field in fields]
    first_names = {"entity1pos", "headpos", "entity1position", "entity1index"}
    relation_names = {"relation", "rel"}
    return bool(normalized and normalized[0] in first_names and normalized[-1] in relation_names)


def check_alignment(
    path: str,
    location: str,
    sentence: str,
    pos_raw: Any,
    word: str,
    report: Report,
    allow_position_mismatch: bool,
) -> None:
    pos = to_int(pos_raw)
    if pos is None:
        report.error(f"{path}:{location}: position {pos_raw!r} is not an integer")
        return
    if pos < 0:
        report.error(f"{path}:{location}: position {pos} is negative")
        return
    clean_sentence = strip_wrapping_quotes(sentence)
    if pos > len(clean_sentence):
        report.error(
            f"{path}:{location}: position {pos} is beyond sentence length {len(clean_sentence)}"
        )
        return
    if word and not clean_sentence.startswith(word, pos):
        message = (
            f"{path}:{location}: word {word!r} does not start at character offset {pos} "
            f"in sentence {clean_sentence!r}"
        )
        if allow_position_mismatch:
            report.warn(message)
        else:
            report.error(message)


def validate_training_tsv(
    path: str,
    report: Report,
    rel2id: Optional[Dict[str, int]],
    allow_unknown_relations: bool,
    allow_position_mismatch: bool,
) -> None:
    report.check(f"training TSV: {path}")
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            data_lines = 0
            for line_no, raw_line in enumerate(handle, start=1):
                line = raw_line.rstrip("\n\r")
                if not line:
                    report.warn(f"{path}:{line_no}: blank line skipped")
                    continue
                fields = line.split("\t")
                if line_no == 1 and looks_like_header(fields):
                    report.warn(
                        f"{path}:{line_no}: header row detected; remove it before running preprocessing.py datasetjson"
                    )
                    continue
                if len(fields) != 6:
                    report.error(f"{path}:{line_no}: expected 6 tab-separated fields, got {len(fields)}")
                    continue
                head_pos, head, tail_pos, tail, sentence, relation = fields
                data_lines += 1
                if not head.strip():
                    report.error(f"{path}:{line_no}: entity1/head is empty")
                if not tail.strip():
                    report.error(f"{path}:{line_no}: entity2/tail is empty")
                if not sentence.strip():
                    report.error(f"{path}:{line_no}: sentence is empty")
                relation = relation.strip()
                if not relation:
                    report.error(f"{path}:{line_no}: relation is empty")
                elif rel2id is not None and relation not in rel2id and not allow_unknown_relations:
                    report.error(f"{path}:{line_no}: relation {relation!r} is not present in rel2id")
                check_alignment(path, str(line_no), sentence, head_pos, head, report, allow_position_mismatch)
                check_alignment(path, str(line_no), sentence, tail_pos, tail, report, allow_position_mismatch)
                if head.strip() == tail.strip():
                    report.warn(f"{path}:{line_no}: head and tail entity text are identical")
            if data_lines == 0:
                report.warn(f"{path}: no data rows found")
    except FileNotFoundError:
        report.error(f"{path}: file does not exist")
    except OSError as exc:
        report.error(f"{path}: cannot read file: {exc}")


def validate_dataset_json(
    path: str,
    value: Any,
    report: Report,
    rel2id: Optional[Dict[str, int]],
    entity2id: Optional[Dict[str, int]],
    allow_unknown_relations: bool,
    allow_position_mismatch: bool,
) -> None:
    if value is None:
        return
    report.check(f"dataset JSON: {path}")
    if not isinstance(value, list):
        report.error(f"{path}: expected a JSON list of relation instances")
        return
    if not value:
        report.warn(f"{path}: dataset list is empty")
        return

    for idx, record in enumerate(value):
        loc = f"item {idx}"
        if not isinstance(record, dict):
            report.error(f"{path}:{loc}: expected object, got {type(record).__name__}")
            continue
        for key in ("head", "tail", "relation", "sentence"):
            if key not in record:
                report.error(f"{path}:{loc}: missing key {key!r}")
        sentence = record.get("sentence")
        if not isinstance(sentence, str) or not sentence.strip():
            report.error(f"{path}:{loc}: sentence must be a non-empty string")
            sentence = ""
        relation = record.get("relation")
        if not isinstance(relation, str) or not relation.strip():
            report.error(f"{path}:{loc}: relation must be a non-empty string")
        elif rel2id is not None and relation not in rel2id and not allow_unknown_relations:
            report.error(f"{path}:{loc}: relation {relation!r} is not present in rel2id")

        for role in ("head", "tail"):
            endpoint = record.get(role)
            if not isinstance(endpoint, dict):
                report.error(f"{path}:{loc}: {role} must be an object")
                continue
            for key in ("pos", "word", "id"):
                if key not in endpoint:
                    report.error(f"{path}:{loc}: {role} missing key {key!r}")
            word = endpoint.get("word")
            pos = endpoint.get("pos")
            ent_id = endpoint.get("id")
            if not isinstance(word, str) or not word.strip():
                report.error(f"{path}:{loc}: {role}.word must be a non-empty string")
                word = ""
            if not is_int_like(pos):
                report.error(f"{path}:{loc}: {role}.pos must be integer-like, got {pos!r}")
            elif sentence:
                check_alignment(
                    path,
                    f"{loc} {role}",
                    sentence,
                    pos,
                    word,
                    report,
                    allow_position_mismatch,
                )
            if not is_int_like(ent_id):
                report.error(f"{path}:{loc}: {role}.id must be integer-like, got {ent_id!r}")
            elif entity2id is not None and isinstance(word, str) and word in entity2id:
                expected = str(entity2id[word])
                if str(ent_id) != expected:
                    report.error(
                        f"{path}:{loc}: {role}.id {ent_id!r} does not match entity2id[{word!r}]={expected!r}"
                    )
            elif entity2id is not None and isinstance(word, str) and word:
                report.warn(f"{path}:{loc}: {role}.word {word!r} is absent from entity2id")


def validate_word2vec_json(path: str, value: Any, report: Report) -> None:
    if value is None:
        return
    report.check(f"word2vec JSON: {path}")
    if not isinstance(value, list):
        report.error(f"{path}: expected a JSON list of {'{word, vec}'} objects")
        return
    if not value:
        report.warn(f"{path}: word vector list is empty")
        return
    expected_dim: Optional[int] = None
    seen_words = set()
    for idx, item in enumerate(value):
        loc = f"item {idx}"
        if not isinstance(item, dict):
            report.error(f"{path}:{loc}: expected object")
            continue
        word = item.get("word")
        vec = item.get("vec")
        if not isinstance(word, str) or not word:
            report.error(f"{path}:{loc}: word must be a non-empty string")
        elif word in seen_words:
            report.warn(f"{path}:{loc}: duplicate word {word!r}")
        else:
            seen_words.add(word)
        if not isinstance(vec, list) or not vec:
            report.error(f"{path}:{loc}: vec must be a non-empty list")
            continue
        if expected_dim is None:
            expected_dim = len(vec)
        elif len(vec) != expected_dim:
            report.error(f"{path}:{loc}: vec length {len(vec)} differs from expected {expected_dim}")
        for dim, raw in enumerate(vec[: min(len(vec), 8)]):
            try:
                float(raw)
            except (TypeError, ValueError):
                report.error(f"{path}:{loc}: vec[{dim}]={raw!r} is not numeric")
                break


def write_json(path: str, value: Any) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def run_self_test(args: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory(prefix="relation-schema-check-") as tmp:
        tsv = os.path.join(tmp, "training.tsv")
        rel = os.path.join(tmp, "rel2id.json")
        ent = os.path.join(tmp, "entity2id.json")
        dataset = os.path.join(tmp, "dataset.json")
        wordvec = os.path.join(tmp, "word2vec.json")
        with open(tsv, "w", encoding="utf-8") as handle:
            handle.write("0\t小麦\t3\t植物\t小麦是植物。\tinstance of\n")
            handle.write("0\t玉米\t3\t作物\t玉米是作物。\tsubclass of\n")
        write_json(rel, {"NA": 0, "instance of": 1, "subclass of": 2})
        write_json(ent, {"小麦": 0, "植物": 1, "玉米": 2, "作物": 3})
        write_json(
            dataset,
            [
                {
                    "head": {"pos": "0", "word": "小麦", "id": "0"},
                    "relation": "instance of",
                    "sentence": "小麦是植物。",
                    "tail": {"pos": "3", "word": "植物", "id": "1"},
                }
            ],
        )
        write_json(
            wordvec,
            [
                {"word": "小麦", "vec": ["0.1", "0.2"]},
                {"word": "植物", "vec": ["0.0", "0.3"]},
            ],
        )
        args.training_tsv = tsv
        args.rel2id = rel
        args.entity2id = ent
        args.dataset_json = dataset
        args.word2vec_json = wordvec
        print(f"[SELF-TEST] validating generated tiny fixtures in {tmp}")
        return run_validation(args)


def run_validation(args: argparse.Namespace) -> int:
    report = Report(max_errors=args.max_errors)

    rel2id: Optional[Dict[str, int]] = None
    entity2id: Optional[Dict[str, int]] = None

    if args.rel2id:
        rel2id = validate_id_mapping(
            args.rel2id,
            read_json(args.rel2id, report),
            report,
            "rel2id",
            require_na_zero=not args.no_require_na,
        )
    if args.entity2id:
        entity2id = validate_id_mapping(
            args.entity2id,
            read_json(args.entity2id, report),
            report,
            "entity2id",
            require_na_zero=False,
        )
    if args.training_tsv:
        validate_training_tsv(
            args.training_tsv,
            report,
            rel2id,
            allow_unknown_relations=args.allow_unknown_relations,
            allow_position_mismatch=args.allow_position_mismatch,
        )
    if args.dataset_json:
        validate_dataset_json(
            args.dataset_json,
            read_json(args.dataset_json, report),
            report,
            rel2id,
            entity2id,
            allow_unknown_relations=args.allow_unknown_relations,
            allow_position_mismatch=args.allow_position_mismatch,
        )
    if args.word2vec_json:
        validate_word2vec_json(args.word2vec_json, read_json(args.word2vec_json, report), report)

    if not report.checked:
        report.error("no inputs were provided")

    if args.summary_json:
        summary = {
            "ok": report.ok,
            "checked": report.checked,
            "warnings": report.warnings,
            "errors": report.errors,
        }
        with open(args.summary_json, "w", encoding="utf-8") as handle:
            json.dump(summary, handle, ensure_ascii=False, indent=2)

    report.emit()
    return 0 if report.ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate relation extraction training TSV, rel2id, entity2id, dataset JSON, "
            "and optional word-vector JSON schemas without TensorFlow."
        )
    )
    parser.add_argument("--training-tsv", help="Six-column TSV: head_pos, head, tail_pos, tail, sentence, relation")
    parser.add_argument("--rel2id", help="JSON object mapping relation labels to integer ids")
    parser.add_argument("--entity2id", help="JSON object mapping entity text to integer ids")
    parser.add_argument("--dataset-json", help="JSON list with head/tail/relation/sentence records")
    parser.add_argument("--word2vec-json", help="Optional JSON list of {'word', 'vec'} objects")
    parser.add_argument("--allow-unknown-relations", action="store_true", help="Warn less strictly when TSV/dataset relation labels are absent from rel2id")
    parser.add_argument("--allow-position-mismatch", action="store_true", help="Report entity-position mismatches as warnings instead of errors")
    parser.add_argument("--no-require-na", action="store_true", help="Do not require rel2id to contain NA mapped to 0")
    parser.add_argument("--max-errors", type=int, default=50, help="Maximum number of errors to display before suppressing extras")
    parser.add_argument("--summary-json", help="Optional path to write machine-readable validation summary")
    parser.add_argument("--self-test", action="store_true", help="Run built-in tiny fixture validation and exit")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test(args)
    if not any([args.training_tsv, args.rel2id, args.entity2id, args.dataset_json, args.word2vec_json]):
        parser.error("provide at least one input file or use --self-test")
    return run_validation(args)


if __name__ == "__main__":
    sys.exit(main())
