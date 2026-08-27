#!/usr/bin/env python3
"""Validate DeepResearch prediction rollout files without external API calls.

The validator checks local JSONL structure, expected DeepSearch round files or
split files, HLE single-file shape, required fields, answer tags, prediction
quality, termination values, and round question-set consistency. It does not run
LLM judges and does not compute pass@k.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

DEEPSEARCH_DATASETS = {
    "gaia",
    "webwalker",
    "browsecomp_zh",
    "browsecomp_en_full",
    "xbench-deepsearch",
}
DATASET_WARNINGS = {
    "browsecomp_en": (
        "The inspected official script has a browsecomp_en-like default but "
        "does not list browsecomp_en in argparse choices. Prefer "
        "browsecomp_en_full unless your local evaluator version differs."
    )
}
HLE_DATASET = "hle"
REQUIRED_FIELDS = ("question", "answer", "messages", "prediction", "termination")
REQUIRED_FIELDS_HLE = ("question", "answer", "prediction")
KNOWN_TERMINATIONS = {
    "answer",
    "answered",
    "answer not found",
    "exceed available llm calls",
    "no answer found after 2h30mins",
    "generate an answer as token limit reached",
    "format error: generate an answer as token limit reached",
    "max_turns_reached",
    "max_tokens_reached",
    "unknown",
}
FAILED_PREDICTIONS = {"[failed]", "no answer found.", "no answer found", ""}
SPLIT_RE = re.compile(r"^iter(?P<round>[1-9][0-9]*)_split(?P<worker>[1-9][0-9]*)of(?P<total>[1-9][0-9]*)\.jsonl$")
UNSPLIT_RE = re.compile(r"^iter(?P<round>[1-9][0-9]*)\.jsonl$")


@dataclass
class IssueLog:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


@dataclass
class FileStats:
    path: Path
    records: int = 0
    questions: List[str] = field(default_factory=list)
    missing_fields: Counter = field(default_factory=Counter)
    non_object_lines: int = 0
    malformed_json_lines: int = 0
    empty_question: int = 0
    bad_messages: int = 0
    empty_messages: int = 0
    message_schema_issues: int = 0
    missing_answer_open_tag: int = 0
    missing_answer_close_tag: int = 0
    multiple_answer_blocks: int = 0
    empty_prediction: int = 0
    failed_prediction: int = 0
    non_string_prediction: int = 0
    missing_termination: int = 0
    empty_termination: int = 0
    unknown_termination: Counter = field(default_factory=Counter)
    tool_call_json_issues: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def question_set(self) -> Set[str]:
        return set(self.questions)

    @property
    def duplicate_questions(self) -> int:
        return sum(count - 1 for count in Counter(self.questions).values() if count > 1)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely validate DeepResearch rollout JSONL files before official API judging."
    )
    parser.add_argument(
        "path",
        help="DeepSearch rollout folder, or a single HLE prediction JSONL file when --dataset hle.",
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="One of gaia, webwalker, browsecomp_zh, browsecomp_en_full, xbench-deepsearch, or hle.",
    )
    parser.add_argument(
        "--allow-splits",
        action="store_true",
        help="Accept iterN_splitXofY.jsonl files from distributed run_multi_react.py output.",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=3,
        help="Expected DeepSearch rollout rounds. The official evaluator expects 3. Default: 3.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary instead of text.",
    )
    return parser.parse_args(argv)


def validate_dataset(dataset: str, issues: IssueLog) -> bool:
    if dataset == HLE_DATASET or dataset in DEEPSEARCH_DATASETS:
        return True
    if dataset in DATASET_WARNINGS:
        issues.warn(DATASET_WARNINGS[dataset])
        return True
    issues.error(
        f"Unsupported dataset {dataset!r}. Supported DeepSearch datasets: "
        f"{', '.join(sorted(DEEPSEARCH_DATASETS))}; HLE dataset: hle."
    )
    return False


def load_jsonl(path: Path, required_fields: Sequence[str], hle_mode: bool = False) -> FileStats:
    stats = FileStats(path=path)
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                raw = line.rstrip("\n")
                if not raw.strip():
                    continue
                try:
                    item = json.loads(raw)
                except json.JSONDecodeError as exc:
                    stats.malformed_json_lines += 1
                    stats.errors.append(f"{path.name}:{line_no}: malformed JSON: {exc.msg}")
                    continue
                if not isinstance(item, dict):
                    stats.non_object_lines += 1
                    stats.errors.append(f"{path.name}:{line_no}: line is {type(item).__name__}, expected object")
                    continue
                stats.records += 1
                validate_item(item, stats, line_no, required_fields, hle_mode=hle_mode)
    except FileNotFoundError:
        stats.errors.append(f"missing file: {path}")
    except OSError as exc:
        stats.errors.append(f"cannot read {path}: {exc}")

    if stats.records == 0 and not stats.errors:
        stats.warnings.append(f"{path.name}: contains no JSON records")
    return stats


def validate_item(
    item: Dict[str, object],
    stats: FileStats,
    line_no: int,
    required_fields: Sequence[str],
    hle_mode: bool = False,
) -> None:
    for field_name in required_fields:
        if field_name not in item:
            stats.missing_fields[field_name] += 1

    question = item.get("question")
    if isinstance(question, str) and question.strip():
        stats.questions.append(question.strip())
    else:
        stats.empty_question += 1
        if "question" in item:
            stats.errors.append(f"{stats.path.name}:{line_no}: question is missing or empty")

    prediction = item.get("prediction")
    if "prediction" in item:
        if not isinstance(prediction, str):
            stats.non_string_prediction += 1
            stats.errors.append(f"{stats.path.name}:{line_no}: prediction is not a string")
        else:
            stripped_prediction = prediction.strip()
            if not stripped_prediction:
                stats.empty_prediction += 1
            if stripped_prediction.lower() in FAILED_PREDICTIONS:
                stats.failed_prediction += 1

    if hle_mode:
        return

    messages = item.get("messages")
    if "messages" in item:
        if not isinstance(messages, list):
            stats.bad_messages += 1
            stats.errors.append(f"{stats.path.name}:{line_no}: messages is not a list")
            messages = []
        elif not messages:
            stats.empty_messages += 1
        else:
            validate_messages(messages, stats, line_no)

    if "termination" not in item:
        stats.missing_termination += 1
    else:
        term = item.get("termination")
        if not isinstance(term, str) or not term.strip():
            stats.empty_termination += 1
        else:
            normalized = term.strip().lower()
            if normalized not in KNOWN_TERMINATIONS:
                stats.unknown_termination[term.strip()] += 1


def validate_messages(messages: List[object], stats: FileStats, line_no: int) -> None:
    for idx, msg in enumerate(messages):
        if not isinstance(msg, dict):
            stats.message_schema_issues += 1
            continue
        role = msg.get("role")
        content = msg.get("content")
        if not isinstance(role, str) or not isinstance(content, str):
            stats.message_schema_issues += 1
            continue
        if role == "assistant":
            stats.tool_call_json_issues += count_tool_call_json_issues(content)

    last_content = ""
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "assistant" and isinstance(msg.get("content"), str):
            last_content = msg["content"]
            break
    if not last_content and isinstance(messages[-1], dict) and isinstance(messages[-1].get("content"), str):
        last_content = messages[-1]["content"]

    open_count = last_content.count("<answer>")
    close_count = last_content.count("</answer>")
    if open_count == 0:
        stats.missing_answer_open_tag += 1
    if close_count == 0:
        stats.missing_answer_close_tag += 1
    if open_count > 1 or close_count > 1:
        stats.multiple_answer_blocks += 1


def count_tool_call_json_issues(content: str) -> int:
    issues = 0
    start_tag = "<tool_call>"
    end_tag = "</tool_call>"
    start = 0
    while True:
        begin = content.find(start_tag, start)
        if begin == -1:
            break
        end = content.find(end_tag, begin + len(start_tag))
        if end == -1:
            issues += 1
            break
        block = content[begin + len(start_tag):end].strip()
        if block:
            try:
                parsed = json.loads(block)
                if not isinstance(parsed, dict) or "name" not in parsed or "arguments" not in parsed:
                    issues += 1
            except json.JSONDecodeError:
                # Python tool calls in this repo can use a non-JSON <code> wrapper;
                # count them as guidance warnings, not record-shape errors.
                issues += 1
        start = end + len(end_tag)
    return issues


def discover_deepsearch_files(folder: Path, rounds: int, allow_splits: bool, issues: IssueLog) -> Dict[int, List[Path]]:
    files_by_round: Dict[int, List[Path]] = {round_id: [] for round_id in range(1, rounds + 1)}
    if not folder.exists():
        issues.error(f"Input folder does not exist: {folder}")
        return files_by_round
    if not folder.is_dir():
        issues.error(f"DeepSearch validation expects a folder, got: {folder}")
        return files_by_round

    all_jsonl = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix == ".jsonl")
    split_seen = False
    for path in all_jsonl:
        unsplit = UNSPLIT_RE.match(path.name)
        if unsplit:
            round_id = int(unsplit.group("round"))
            if round_id in files_by_round:
                files_by_round[round_id].append(path)
            continue
        split = SPLIT_RE.match(path.name)
        if split:
            split_seen = True
            if allow_splits:
                round_id = int(split.group("round"))
                if round_id in files_by_round:
                    files_by_round[round_id].append(path)

    if split_seen and not allow_splits:
        issues.warn("Split-suffixed iter files were found but --allow-splits was not set; official judging requires unsuffixed iterN.jsonl files.")

    for round_id in range(1, rounds + 1):
        if not files_by_round[round_id]:
            expected = f"iter{round_id}.jsonl"
            if allow_splits:
                expected += f" or iter{round_id}_splitXofY.jsonl"
            issues.error(f"Missing required round {round_id} file: {expected}")
    if allow_splits:
        validate_split_coverage(files_by_round, issues)
    return files_by_round


def validate_split_coverage(files_by_round: Dict[int, List[Path]], issues: IssueLog) -> None:
    for round_id, files in files_by_round.items():
        split_files = []
        unsplit_files = []
        for path in files:
            match = SPLIT_RE.match(path.name)
            if match:
                split_files.append((path, int(match.group("worker")), int(match.group("total"))))
            else:
                unsplit_files.append(path)
        if split_files and unsplit_files:
            issues.warn(f"Round {round_id} has both unsplit and split files; avoid double-counting when merging.")
        if not split_files:
            continue
        totals = {total for _, _, total in split_files}
        if len(totals) != 1:
            issues.error(f"Round {round_id} split files disagree on total_splits: {sorted(totals)}")
            continue
        total = next(iter(totals))
        workers = {worker for _, worker, _ in split_files}
        expected = set(range(1, total + 1))
        missing = sorted(expected - workers)
        extra = sorted(workers - expected)
        if missing:
            issues.error(f"Round {round_id} is missing split worker(s): {missing} of {total}")
        if extra:
            issues.error(f"Round {round_id} has invalid split worker(s): {extra} for total {total}")


def validate_deepsearch(folder: Path, dataset: str, rounds: int, allow_splits: bool, issues: IssueLog) -> Dict[str, object]:
    files_by_round = discover_deepsearch_files(folder, rounds, allow_splits, issues)
    round_stats: Dict[int, List[FileStats]] = {}
    for round_id, paths in files_by_round.items():
        round_stats[round_id] = [load_jsonl(path, REQUIRED_FIELDS, hle_mode=False) for path in paths]

    for stats in iter_stats(round_stats):
        issues.errors.extend(stats.errors)
        issues.warnings.extend(stats.warnings)
        for field_name, count in stats.missing_fields.items():
            issues.error(f"{stats.path.name}: missing required field {field_name!r} in {count} record(s)")
        if stats.empty_prediction:
            issues.warn(f"{stats.path.name}: {stats.empty_prediction} empty prediction(s)")
        if stats.failed_prediction:
            issues.warn(f"{stats.path.name}: {stats.failed_prediction} failed/no-answer prediction marker(s)")
        if stats.empty_messages:
            issues.warn(f"{stats.path.name}: {stats.empty_messages} record(s) have empty messages")
        if stats.message_schema_issues:
            issues.warn(f"{stats.path.name}: {stats.message_schema_issues} message schema issue(s)")
        if stats.missing_answer_open_tag or stats.missing_answer_close_tag:
            issues.warn(
                f"{stats.path.name}: answer-tag issues: missing <answer> in {stats.missing_answer_open_tag}, "
                f"missing </answer> in {stats.missing_answer_close_tag} record(s)"
            )
        if stats.multiple_answer_blocks:
            issues.warn(f"{stats.path.name}: {stats.multiple_answer_blocks} record(s) have multiple answer tag blocks")
        if stats.missing_termination or stats.empty_termination:
            issues.warn(
                f"{stats.path.name}: termination issues: missing {stats.missing_termination}, empty {stats.empty_termination}"
            )
        if stats.unknown_termination:
            issues.warn(f"{stats.path.name}: unknown termination values {dict(stats.unknown_termination)}")
        if stats.tool_call_json_issues:
            issues.warn(f"{stats.path.name}: {stats.tool_call_json_issues} tool_call JSON/schema issue(s)")
        if stats.duplicate_questions:
            issues.warn(f"{stats.path.name}: {stats.duplicate_questions} duplicate question record(s)")

    validate_round_question_sets(round_stats, issues)
    return build_summary(dataset, round_stats, hle=False)


def validate_hle(path: Path, dataset: str, issues: IssueLog) -> Dict[str, object]:
    if path.is_dir():
        candidates = sorted(p for p in path.iterdir() if p.is_file() and p.suffix == ".jsonl" and not p.name.endswith(".eval_details.jsonl"))
        if len(candidates) != 1:
            issues.error(f"HLE validation expects one JSONL file or a directory containing exactly one JSONL file; found {len(candidates)}")
            return {"dataset": dataset, "mode": "hle", "files": []}
        path = candidates[0]
    if not path.exists():
        issues.error(f"Input file does not exist: {path}")
        return {"dataset": dataset, "mode": "hle", "files": []}
    if not path.is_file():
        issues.error(f"HLE validation expects a JSONL file, got: {path}")
        return {"dataset": dataset, "mode": "hle", "files": []}

    stats = load_jsonl(path, REQUIRED_FIELDS_HLE, hle_mode=True)
    issues.errors.extend(stats.errors)
    issues.warnings.extend(stats.warnings)
    for field_name, count in stats.missing_fields.items():
        issues.error(f"{stats.path.name}: missing required field {field_name!r} in {count} record(s)")
    if stats.empty_prediction:
        issues.warn(f"{stats.path.name}: {stats.empty_prediction} empty prediction(s)")
    if stats.failed_prediction:
        issues.warn(f"{stats.path.name}: {stats.failed_prediction} failed/no-answer prediction marker(s)")
    if stats.duplicate_questions:
        issues.warn(f"{stats.path.name}: {stats.duplicate_questions} duplicate question record(s)")
    return {
        "dataset": dataset,
        "mode": "hle",
        "files": [file_stats_to_dict(stats)],
        "totals": aggregate_totals([stats]),
    }


def iter_stats(round_stats: Dict[int, List[FileStats]]) -> Iterable[FileStats]:
    for round_id in sorted(round_stats):
        for stats in round_stats[round_id]:
            yield stats


def validate_round_question_sets(round_stats: Dict[int, List[FileStats]], issues: IssueLog) -> None:
    question_sets: Dict[int, Set[str]] = {}
    for round_id, stats_list in round_stats.items():
        combined: Set[str] = set()
        for stats in stats_list:
            combined.update(stats.question_set)
        if combined:
            question_sets[round_id] = combined
    if len(question_sets) <= 1:
        return
    baseline_round = min(question_sets)
    baseline = question_sets[baseline_round]
    for round_id, current in sorted(question_sets.items()):
        if round_id == baseline_round:
            continue
        missing = sorted(baseline - current)
        extra = sorted(current - baseline)
        if missing or extra:
            issues.error(
                f"Round {round_id} question set differs from round {baseline_round}: "
                f"missing {len(missing)}, extra {len(extra)}"
            )


def aggregate_totals(stats_list: Sequence[FileStats]) -> Dict[str, object]:
    totals = Counter()
    unknown_termination = Counter()
    records = 0
    unique_questions: Set[str] = set()
    duplicate_questions = 0
    for stats in stats_list:
        records += stats.records
        unique_questions.update(stats.question_set)
        duplicate_questions += stats.duplicate_questions
        totals["malformed_json_lines"] += stats.malformed_json_lines
        totals["non_object_lines"] += stats.non_object_lines
        totals["empty_question"] += stats.empty_question
        totals["bad_messages"] += stats.bad_messages
        totals["empty_messages"] += stats.empty_messages
        totals["message_schema_issues"] += stats.message_schema_issues
        totals["missing_answer_open_tag"] += stats.missing_answer_open_tag
        totals["missing_answer_close_tag"] += stats.missing_answer_close_tag
        totals["multiple_answer_blocks"] += stats.multiple_answer_blocks
        totals["empty_prediction"] += stats.empty_prediction
        totals["failed_prediction"] += stats.failed_prediction
        totals["non_string_prediction"] += stats.non_string_prediction
        totals["missing_termination"] += stats.missing_termination
        totals["empty_termination"] += stats.empty_termination
        totals["tool_call_json_issues"] += stats.tool_call_json_issues
        for field_name, count in stats.missing_fields.items():
            totals[f"missing_field:{field_name}"] += count
        unknown_termination.update(stats.unknown_termination)
    return {
        "records": records,
        "unique_questions": len(unique_questions),
        "duplicate_questions": duplicate_questions,
        **dict(totals),
        "unknown_termination": dict(unknown_termination),
    }


def file_stats_to_dict(stats: FileStats) -> Dict[str, object]:
    return {
        "path": stats.path.name,
        "records": stats.records,
        "unique_questions": len(stats.question_set),
        "duplicate_questions": stats.duplicate_questions,
        "missing_fields": dict(stats.missing_fields),
        "malformed_json_lines": stats.malformed_json_lines,
        "non_object_lines": stats.non_object_lines,
        "empty_question": stats.empty_question,
        "bad_messages": stats.bad_messages,
        "empty_messages": stats.empty_messages,
        "message_schema_issues": stats.message_schema_issues,
        "answer_tag_issues": {
            "missing_open": stats.missing_answer_open_tag,
            "missing_close": stats.missing_answer_close_tag,
            "multiple_blocks": stats.multiple_answer_blocks,
        },
        "prediction_issues": {
            "empty": stats.empty_prediction,
            "failed_marker": stats.failed_prediction,
            "non_string": stats.non_string_prediction,
        },
        "termination_issues": {
            "missing": stats.missing_termination,
            "empty": stats.empty_termination,
            "unknown": dict(stats.unknown_termination),
        },
        "tool_call_json_issues": stats.tool_call_json_issues,
    }


def build_summary(dataset: str, round_stats: Dict[int, List[FileStats]], hle: bool) -> Dict[str, object]:
    rounds = []
    for round_id in sorted(round_stats):
        stats_list = round_stats[round_id]
        rounds.append(
            {
                "round": round_id,
                "files": [file_stats_to_dict(stats) for stats in stats_list],
                "totals": aggregate_totals(stats_list),
            }
        )
    return {
        "dataset": dataset,
        "mode": "hle" if hle else "deepsearch",
        "rounds": rounds,
        "totals": aggregate_totals(list(iter_stats(round_stats))),
    }


def print_text_report(summary: Dict[str, object], issues: IssueLog) -> None:
    print(f"Dataset: {summary.get('dataset')}")
    print(f"Mode: {summary.get('mode')}")
    if summary.get("mode") == "hle":
        for file_info in summary.get("files", []):
            print(f"File {file_info['path']}: {file_info['records']} record(s), {file_info['unique_questions']} unique question(s)")
    else:
        for round_info in summary.get("rounds", []):
            file_names = ", ".join(file_info["path"] for file_info in round_info.get("files", [])) or "<missing>"
            totals = round_info.get("totals", {})
            print(
                f"Round {round_info['round']}: {file_names} | "
                f"records={totals.get('records', 0)} unique_questions={totals.get('unique_questions', 0)}"
            )
    totals = summary.get("totals", {})
    if totals:
        print("Totals:")
        for key in sorted(totals):
            print(f"  {key}: {totals[key]}")
    if issues.warnings:
        print("Warnings:", file=sys.stderr)
        for warning in issues.warnings:
            print(f"  - {warning}", file=sys.stderr)
    if issues.errors:
        print("Errors:", file=sys.stderr)
        for error in issues.errors:
            print(f"  - {error}", file=sys.stderr)
        print("Result: NOT READY for official judging.", file=sys.stderr)
    else:
        print("Result: local preflight passed. This is not an official judge metric.")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    issues = IssueLog()
    validate_dataset(args.dataset, issues)
    input_path = Path(args.path)

    if args.rounds != 3 and args.dataset != HLE_DATASET:
        issues.warn("The official DeepSearch evaluator expects exactly 3 rounds; custom --rounds is for local diagnostics only.")

    if args.dataset == HLE_DATASET:
        if args.allow_splits:
            issues.warn("--allow-splits is ignored for HLE single-file validation.")
        summary = validate_hle(input_path, args.dataset, issues)
    else:
        summary = validate_deepsearch(input_path, args.dataset, args.rounds, args.allow_splits, issues)

    if args.json:
        payload = {
            "ready": not issues.errors,
            "errors": issues.errors,
            "warnings": issues.warnings,
            "summary": summary,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text_report(summary, issues)
    return 1 if issues.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
