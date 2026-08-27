#!/usr/bin/env python3
"""Validate SPLADE-style toy data layouts without importing SPLADE.

The validator accepts a dataset root containing files such as:
  full_collection/raw.tsv
  val_queries/raw.tsv
  qrel/qrel.json
  scores/toy.json
  scores/toy.pkl.gz
  triplets/raw.tsv

It reports schema errors and id-overlap warnings with conservative defaults.
"""

from __future__ import annotations

import argparse
import gzip
import json
import pickle
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


@dataclass
class CheckResult:
    path: str
    kind: str
    ok: bool
    count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sample_ids: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "kind": self.kind,
            "ok": self.ok,
            "count": self.count,
            "errors": self.errors,
            "warnings": self.warnings,
            "sample_ids": self.sample_ids,
        }


def normalize_id(value: Any) -> str:
    return str(value).strip()


def relpath(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def read_raw_tsv(path: Path, root: Path, kind: str, expected_fields: Optional[int] = None) -> Tuple[CheckResult, Set[str]]:
    result = CheckResult(path=relpath(path, root), kind=kind, ok=True)
    ids: Set[str] = set()
    if not path.exists():
        result.ok = False
        result.errors.append("missing file")
        return result, ids
    if not path.is_file():
        result.ok = False
        result.errors.append("not a file")
        return result, ids

    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                stripped = line.rstrip("\n")
                if not stripped.strip():
                    continue
                parts = stripped.split("\t")
                if expected_fields is not None and len(parts) != expected_fields:
                    result.errors.append(
                        f"line {line_no}: expected {expected_fields} tab-separated fields, found {len(parts)}"
                    )
                    continue
                if expected_fields is None and len(parts) < 2:
                    result.errors.append(f"line {line_no}: expected id<TAB>text with at least 2 fields")
                    continue
                first = normalize_id(parts[0])
                if not first:
                    result.errors.append(f"line {line_no}: empty first field")
                    continue
                if kind in {"collection", "queries"}:
                    if first in ids:
                        result.warnings.append(f"line {line_no}: duplicate id {first!r}")
                    ids.add(first)
                    if not "\t".join(parts[1:]).strip():
                        result.warnings.append(f"line {line_no}: empty text for id {first!r}")
                result.count += 1
    except UnicodeDecodeError as exc:
        result.errors.append(f"not valid UTF-8 text: {exc}")
    except OSError as exc:
        result.errors.append(f"could not read file: {exc}")

    result.ok = not result.errors
    result.sample_ids = sorted(ids)[:5]
    return result, ids


def load_json(path: Path, root: Path, kind: str) -> Tuple[CheckResult, Optional[Any]]:
    result = CheckResult(path=relpath(path, root), kind=kind, ok=True)
    if not path.exists():
        result.ok = False
        result.errors.append("missing file")
        return result, None
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:  # noqa: BLE001 - command-line validator should report any parse failure.
        result.ok = False
        result.errors.append(f"could not parse JSON: {exc}")
        return result, None
    return result, data


def validate_nested_numeric_mapping(
    path: Path,
    root: Path,
    kind: str,
    data: Any,
    value_name: str,
    require_positive: bool = False,
) -> Tuple[CheckResult, Dict[str, Dict[str, float]]]:
    result = CheckResult(path=relpath(path, root), kind=kind, ok=True)
    normalized: Dict[str, Dict[str, float]] = {}
    if not isinstance(data, Mapping):
        result.errors.append("top-level JSON value must be an object mapping qid to did-score objects")
        result.ok = False
        return result, normalized

    for qid, documents in data.items():
        qid_s = normalize_id(qid)
        if not qid_s:
            result.errors.append("empty qid key")
            continue
        if not isinstance(documents, Mapping):
            result.errors.append(f"qid {qid_s!r}: value must be an object mapping did to {value_name}")
            continue
        normalized[qid_s] = {}
        for did, value in documents.items():
            did_s = normalize_id(did)
            if not did_s:
                result.errors.append(f"qid {qid_s!r}: empty did key")
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                result.errors.append(f"qid {qid_s!r}, did {did_s!r}: {value_name} is not numeric")
                continue
            if require_positive and number < 1:
                result.warnings.append(f"qid {qid_s!r}, did {did_s!r}: relevance {number:g} is not positive")
            normalized[qid_s][did_s] = number
    result.count = sum(len(v) for v in normalized.values())
    result.sample_ids = sorted(normalized)[:5]
    result.ok = not result.errors
    return result, normalized


def validate_score_pickle(path: Path, root: Path) -> Tuple[CheckResult, Dict[str, Dict[str, float]]]:
    result = CheckResult(path=relpath(path, root), kind="score-pkl-gz", ok=True)
    normalized: Dict[str, Dict[str, float]] = {}
    if not path.exists():
        result.ok = False
        result.errors.append("missing file")
        return result, normalized
    try:
        with gzip.open(path, "rb") as handle:
            data = pickle.load(handle)
    except Exception as exc:  # noqa: BLE001 - command-line validator should report any load failure.
        result.ok = False
        result.errors.append(f"could not load gzip pickle: {exc}")
        return result, normalized
    nested_result, normalized = validate_nested_numeric_mapping(path, root, "score-pkl-gz", data, "score")
    result.errors.extend(nested_result.errors)
    result.warnings.extend(nested_result.warnings)
    result.count = nested_result.count
    result.sample_ids = nested_result.sample_ids
    result.ok = not result.errors
    return result, normalized


def check_qrel_overlap(
    qrels: Mapping[str, Mapping[str, float]],
    query_ids: Set[str],
    doc_ids: Set[str],
    result: CheckResult,
) -> None:
    if query_ids:
        missing_queries = sorted(qid for qid in qrels if qid not in query_ids)
        if missing_queries:
            result.warnings.append(
                f"{len(missing_queries)} qrel qids are absent from query raw.tsv; examples: {missing_queries[:5]}"
            )
    if doc_ids:
        missing_docs = sorted({did for docs in qrels.values() for did in docs if did not in doc_ids})
        if missing_docs:
            result.warnings.append(
                f"{len(missing_docs)} positive qrel dids are absent from document raw.tsv; examples: {missing_docs[:5]}"
            )


def check_score_overlap(
    scores: Mapping[str, Mapping[str, float]],
    qrels: Mapping[str, Mapping[str, float]],
    query_ids: Set[str],
    doc_ids: Set[str],
    result: CheckResult,
) -> None:
    if qrels:
        missing_score_qrels = sorted(qid for qid in qrels if qid not in scores)
        if missing_score_qrels:
            result.warnings.append(
                f"{len(missing_score_qrels)} qrel qids are absent from score file; examples: {missing_score_qrels[:5]}"
            )
        no_negative = []
        for qid, docs in scores.items():
            positives = set(qrels.get(qid, {}))
            candidates = set(docs)
            if positives and not (candidates - positives):
                no_negative.append(qid)
        if no_negative:
            result.warnings.append(
                f"{len(no_negative)} score qids have no non-positive negative candidates; examples: {no_negative[:5]}"
            )
    if query_ids:
        missing_queries = sorted(qid for qid in scores if qid not in query_ids)
        if missing_queries:
            result.warnings.append(
                f"{len(missing_queries)} score qids are absent from query raw.tsv; examples: {missing_queries[:5]}"
            )
    if doc_ids:
        missing_docs = sorted({did for docs in scores.values() for did in docs if did not in doc_ids})
        if missing_docs:
            result.warnings.append(
                f"{len(missing_docs)} score dids are absent from document raw.tsv; examples: {missing_docs[:5]}"
            )


def existing_or_default(root: Path, provided: Optional[str], default: str) -> Optional[Path]:
    if provided:
        return root / provided
    candidate = root / default
    return candidate if candidate.exists() else None


def add_missing(result_list: List[CheckResult], root: Path, path_text: str, kind: str, allow_missing: bool) -> None:
    result = CheckResult(path=path_text, kind=kind, ok=allow_missing)
    if allow_missing:
        result.warnings.append("missing optional file")
    else:
        result.errors.append("missing file")
    result_list.append(result)


def validate(args: argparse.Namespace) -> Tuple[bool, List[CheckResult]]:
    root = Path(args.root).expanduser().resolve()
    results: List[CheckResult] = []
    document_ids: Set[str] = set()
    query_ids: Set[str] = set()
    qrels: Dict[str, Dict[str, float]] = {}

    document_dirs = args.documents or ["full_collection", "val_collection"]
    query_dirs = args.queries or ["dev_queries", "val_queries"]

    for directory in document_dirs:
        raw_path = root / directory / "raw.tsv"
        if raw_path.exists() or args.documents:
            result, ids = read_raw_tsv(raw_path, root, "collection")
            results.append(result)
            document_ids.update(ids)
        elif not args.allow_missing:
            add_missing(results, root, f"{directory}/raw.tsv", "collection", args.allow_missing)

    for directory in query_dirs:
        raw_path = root / directory / "raw.tsv"
        if raw_path.exists() or args.queries:
            result, ids = read_raw_tsv(raw_path, root, "queries")
            results.append(result)
            query_ids.update(ids)
        elif not args.allow_missing:
            add_missing(results, root, f"{directory}/raw.tsv", "queries", args.allow_missing)

    triplet_path = existing_or_default(root, args.triplets, "triplets/raw.tsv")
    if triplet_path is not None:
        result, _ = read_raw_tsv(triplet_path, root, "triplets", expected_fields=3)
        results.append(result)
    elif args.triplets or not args.allow_missing:
        add_missing(results, root, args.triplets or "triplets/raw.tsv", "triplets", args.allow_missing)

    qrel_path = existing_or_default(root, args.qrels, "qrel/qrel.json")
    if qrel_path is not None:
        _, data = load_json(qrel_path, root, "qrels")
        if data is None:
            result = CheckResult(path=relpath(qrel_path, root), kind="qrels", ok=False, errors=["could not load qrel JSON"])
        else:
            result, qrels = validate_nested_numeric_mapping(
                qrel_path,
                root,
                "qrels",
                data,
                "relevance",
                require_positive=True,
            )
            check_qrel_overlap(qrels, query_ids, document_ids, result)
        results.append(result)
    elif args.qrels or not args.allow_missing:
        add_missing(results, root, args.qrels or "qrel/qrel.json", "qrels", args.allow_missing)

    score_paths: List[Path] = []
    if args.scores:
        score_paths = [root / item for item in args.scores]
    else:
        score_dir = root / "scores"
        if score_dir.exists():
            score_paths.extend(sorted(score_dir.glob("*.json")))
            score_paths.extend(sorted(score_dir.glob("*.pkl.gz")))

    if score_paths:
        for score_path in score_paths:
            if score_path.suffix == ".json":
                _, data = load_json(score_path, root, "score-json")
                if data is None:
                    result = CheckResult(path=relpath(score_path, root), kind="score-json", ok=False, errors=["could not load score JSON"])
                    scores = {}
                else:
                    result, scores = validate_nested_numeric_mapping(score_path, root, "score-json", data, "score")
            elif score_path.name.endswith(".pkl.gz"):
                result, scores = validate_score_pickle(score_path, root)
            else:
                result = CheckResult(path=relpath(score_path, root), kind="scores", ok=False)
                result.errors.append("unsupported score extension; expected .json or .pkl.gz")
                scores = {}
            if scores:
                check_score_overlap(scores, qrels, query_ids, document_ids, result)
            results.append(result)
    elif not args.allow_missing:
        add_missing(results, root, "scores/*.json or scores/*.pkl.gz", "scores", args.allow_missing)

    ok = all(item.ok for item in results)
    return ok, results


def print_text(results: Sequence[CheckResult]) -> None:
    for result in results:
        status = "OK" if result.ok else "FAIL"
        print(f"[{status}] {result.kind}: {result.path} ({result.count} records)")
        if result.sample_ids:
            print(f"  sample ids: {', '.join(result.sample_ids)}")
        for warning in result.warnings:
            print(f"  warning: {warning}")
        for error in result.errors:
            print(f"  error: {error}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate SPLADE-style raw.tsv, qrel, and score fixture schemas.")
    parser.add_argument("root", help="Dataset root containing SPLADE-style subdirectories/files.")
    parser.add_argument("--documents", nargs="*", help="Document collection directories relative to root.")
    parser.add_argument("--queries", nargs="*", help="Query collection directories relative to root.")
    parser.add_argument("--qrels", help="Qrel JSON path relative to root, default qrel/qrel.json when present.")
    parser.add_argument("--scores", nargs="*", help="Score JSON or pkl.gz paths relative to root, default all files under scores/.")
    parser.add_argument("--triplets", help="Triplet raw.tsv path relative to root, default triplets/raw.tsv when present.")
    parser.add_argument("--allow-missing", action="store_true", help="Treat missing default files as warnings instead of failures.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    ok, results = validate(args)
    payload = {"ok": ok, "checks": [item.as_dict() for item in results]}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text(results)
        print(f"Overall: {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
