#!/usr/bin/env python3
"""Validate local DeepSearcher evaluation inputs without running evaluation.

This helper only reads JSON/YAML and optionally creates the requested output
folders. It never imports DeepSearcher, initializes providers, contacts a
network service, loads a corpus, retrieves, or queries.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - depends on caller environment
    yaml = None
    YAML_IMPORT_ERROR = exc
else:
    YAML_IMPORT_ERROR = None

SUPPORTED_DATASETS = {"2wikimultihopqa"}
REQUIRED_FEATURES = ("llm", "embedding", "file_loader", "web_crawler", "vector_db")
EXPECTED_OUTPUT_FILES = ("details.csv", "statistics.json")


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate 2Wiki-style DeepSearcher evaluation JSON/YAML inputs "
            "without importing DeepSearcher or calling providers."
        )
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Dataset name; the supported scorer currently accepts 2wikimultihopqa.",
    )
    parser.add_argument(
        "--corpus",
        required=True,
        type=Path,
        help="Path to the corpus JSON array (title/text records).",
    )
    parser.add_argument(
        "--questions",
        required=True,
        type=Path,
        help="Path to the question/ground-truth JSON array.",
    )
    parser.add_argument(
        "--config-yaml",
        "--config_yaml",
        dest="config_yaml",
        required=True,
        type=Path,
        help="Path to the DeepSearcher evaluation YAML configuration.",
    )
    parser.add_argument(
        "--output-dir",
        "--output_dir",
        dest="output_dir",
        required=True,
        type=Path,
        help="Evaluation output root; reports go below this path and --flag.",
    )
    parser.add_argument(
        "--flag",
        default="result",
        help="Report subdirectory below output-dir (default: result).",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=None,
        help="Validate only the first N question records; default validates all records.",
    )
    parser.add_argument(
        "--create-output-dir",
        action="store_true",
        help="Create output-dir/flag after validation; default only previews creation.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report.")
    return parser.parse_args()


def read_json(path: Path, label: str, result: Validation) -> Any | None:
    if not path.exists():
        result.error(f"{label} file does not exist: {path}")
        return None
    if not path.is_file():
        result.error(f"{label} path is not a file: {path}")
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        result.error(f"Could not read {label} JSON {path}: {exc}")
        return None


def validate_corpus(data: Any, result: Validation) -> tuple[int, set[str]]:
    if not isinstance(data, list):
        result.error("Corpus JSON must be a top-level array of objects.")
        return 0, set()

    titles: set[str] = set()
    duplicate_count = 0
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            result.error(f"Corpus record {index} must be an object.")
            continue
        title = item.get("title")
        text = item.get("text")
        if not isinstance(title, str) or not title.strip():
            result.error(f"Corpus record {index} must have a non-empty string 'title'.")
        elif title in titles:
            duplicate_count += 1
        else:
            titles.add(title)
        if not isinstance(text, str) or not text.strip():
            result.error(f"Corpus record {index} must have a non-empty string 'text'.")

    if not data:
        result.error("Corpus JSON must contain at least one record.")
    if duplicate_count:
        result.warning(f"Corpus contains {duplicate_count} duplicate title record(s); title recall may be ambiguous.")
    return len(data), titles


def validate_supporting_fact(value: Any, sample_index: int, fact_index: int, result: Validation) -> str | None:
    if not isinstance(value, list) or len(value) != 2:
        result.error(
            f"Question record {sample_index} supporting_facts item {fact_index} "
            "must be a two-item JSON array [title, sentence_index]."
        )
        return None
    title = value[0]
    if not isinstance(title, str) or not title.strip():
        result.error(
            f"Question record {sample_index} supporting_facts item {fact_index} "
            "must have a non-empty string title as its first item."
        )
        return None
    return title


def validate_questions(
    data: Any,
    result: Validation,
    titles: set[str],
    sample_limit: int | None,
) -> tuple[int, int, list[str]]:
    if not isinstance(data, list):
        result.error("Questions JSON must be a top-level array of objects.")
        return 0, 0, []
    if not data:
        result.error("Questions JSON must contain at least one record.")
        return 0, 0, []

    if sample_limit is not None and sample_limit <= 0:
        result.error("--sample-limit must be a positive integer when provided.")
        return len(data), 0, []

    records = data if sample_limit is None else data[:sample_limit]
    missing_titles: list[str] = []
    valid_facts = 0
    for index, item in enumerate(records):
        if not isinstance(item, dict):
            result.error(f"Question record {index} must be an object.")
            continue
        question = item.get("question")
        if not isinstance(question, str) or not question.strip():
            result.error(f"Question record {index} must have a non-empty string 'question'.")
        facts = item.get("supporting_facts")
        if not isinstance(facts, list) or not facts:
            result.error(f"Question record {index} must have a non-empty 'supporting_facts' list.")
            continue
        record_valid = True
        for fact_index, fact in enumerate(facts):
            title = validate_supporting_fact(fact, index, fact_index, result)
            if title is None:
                record_valid = False
            elif title not in titles:
                missing_titles.append(title)
        if record_valid:
            valid_facts += 1

    if missing_titles:
        unique_missing = sorted(set(missing_titles))
        preview = ", ".join(repr(title) for title in unique_missing[:5])
        suffix = "" if len(unique_missing) <= 5 else f" (+{len(unique_missing) - 5} more)"
        result.warning(
            f"{len(unique_missing)} supporting-fact title(s) are absent from the corpus: {preview}{suffix}. "
            "Recall cannot be positive for a missing gold title."
        )
    if sample_limit is not None and sample_limit < len(data):
        result.note(f"Validated the first {sample_limit} of {len(data)} question records (--sample-limit).")
    return len(data), len(records), missing_titles


def load_yaml(path: Path, result: Validation) -> dict[str, Any] | None:
    if not path.exists():
        result.error(f"Config YAML file does not exist: {path}")
        return None
    if not path.is_file():
        result.error(f"Config YAML path is not a file: {path}")
        return None
    if yaml is None:
        result.error(f"PyYAML is required to parse config YAML: {YAML_IMPORT_ERROR}")
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        result.error(f"Could not parse config YAML {path}: {exc}")
        return None
    if not isinstance(value, dict):
        result.error("Config YAML must contain a top-level mapping.")
        return None
    return value


def validate_config(config: dict[str, Any] | None, result: Validation) -> None:
    if config is None:
        return
    provide_settings = config.get("provide_settings")
    if not isinstance(provide_settings, dict):
        result.error("Config YAML must contain a 'provide_settings' mapping.")
        return

    missing = [feature for feature in REQUIRED_FEATURES if feature not in provide_settings]
    if missing:
        result.error("Config YAML is missing provide_settings feature section(s): " + ", ".join(missing))
    for feature in REQUIRED_FEATURES:
        section = provide_settings.get(feature)
        if not isinstance(section, dict):
            result.error(f"provide_settings.{feature} must be a mapping.")
            continue
        provider = section.get("provider")
        if not isinstance(provider, str) or not provider.strip():
            result.error(f"provide_settings.{feature}.provider must be a non-empty string.")
        provider_config = section.get("config")
        if provider_config is None:
            result.warning(f"provide_settings.{feature}.config is absent; use an empty mapping if no options are needed.")
        elif not isinstance(provider_config, dict):
            result.error(f"provide_settings.{feature}.config must be a mapping.")

    for section_name in ("query_settings", "load_settings"):
        if section_name not in config:
            result.error(f"Config YAML is missing '{section_name}' section.")
        elif not isinstance(config[section_name], dict):
            result.error(f"Config YAML '{section_name}' section must be a mapping.")

    loader = provide_settings.get("file_loader")
    if isinstance(loader, dict) and loader.get("provider") == "JsonFileLoader":
        loader_config = loader.get("config")
        if isinstance(loader_config, dict) and loader_config.get("text_key") != "text":
            result.warning(
                "JsonFileLoader is selected but file_loader.config.text_key is not 'text'; "
                "the standard corpus may not load its passage text."
            )
    elif isinstance(loader, dict):
        result.warning(
            "The selected file loader is not JsonFileLoader; confirm it can read the corpus's title/text JSON records."
        )


def validate_output(output_dir: Path, flag: str, result: Validation, create: bool) -> Path | None:
    if not flag or flag in {".", ".."} or "/" in flag or "\\" in flag:
        result.error("--flag must be a non-empty single directory name without path separators.")
        return None
    report_dir = output_dir / flag
    if output_dir.exists() and not output_dir.is_dir():
        result.error(f"Output path exists but is not a directory: {output_dir}")
        return None
    if report_dir.exists() and not report_dir.is_dir():
        result.error(f"Report path exists but is not a directory: {report_dir}")
        return None

    if report_dir.exists():
        present = [name for name in EXPECTED_OUTPUT_FILES if (report_dir / name).exists()]
        if present:
            result.note(
                f"Existing report file(s) detected in {report_dir}: {', '.join(present)}. "
                "A compatible run can resume from existing details.csv."
            )
        else:
            result.note(f"Output report directory already exists: {report_dir}")
    elif create:
        try:
            report_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            result.error(f"Could not create output directory {report_dir}: {exc}")
            return report_dir
        result.note(f"Created output report directory: {report_dir}")
    else:
        result.note(f"Output directory does not exist; preview only: would create {report_dir}")
    return report_dir


def build_report(args: argparse.Namespace) -> tuple[Validation, dict[str, Any]]:
    result = Validation()
    if args.dataset not in SUPPORTED_DATASETS:
        result.error(
            f"Unsupported dataset {args.dataset!r}; supported dataset names: "
            + ", ".join(sorted(SUPPORTED_DATASETS))
        )

    corpus_data = read_json(args.corpus, "Corpus", result)
    questions_data = read_json(args.questions, "Questions", result)
    corpus_count, titles = validate_corpus(corpus_data, result) if corpus_data is not None else (0, set())
    question_count, checked_questions, missing_titles = (
        validate_questions(questions_data, result, titles, args.sample_limit)
        if questions_data is not None
        else (0, 0, [])
    )
    config = load_yaml(args.config_yaml, result)
    validate_config(config, result)
    report_dir = validate_output(args.output_dir, args.flag, result, args.create_output_dir)

    result.note("No DeepSearcher import, provider initialization, network call, corpus load, retrieve, or query was performed.")
    payload = {
        "ok": not result.errors,
        "dataset": args.dataset,
        "corpus_records": corpus_count,
        "corpus_unique_titles": len(titles),
        "question_records": question_count,
        "questions_checked": checked_questions,
        "missing_supporting_titles": len(set(missing_titles)),
        "report_directory": str(report_dir) if report_dir is not None else None,
        "output_directory_created": bool(report_dir and report_dir.exists() and args.create_output_dir),
        "errors": result.errors,
        "warnings": result.warnings,
        "notes": result.notes,
    }
    return result, payload


def print_report(result: Validation, payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    status = "PASS" if not result.errors else "FAIL"
    print(f"{status}: evaluation input validation")
    print(f"dataset: {payload['dataset']}")
    print(f"corpus records: {payload['corpus_records']} (unique titles: {payload['corpus_unique_titles']})")
    print(f"question records: {payload['question_records']} (checked: {payload['questions_checked']})")
    print(f"report directory: {payload['report_directory']}")
    for label, messages in (("ERROR", result.errors), ("WARNING", result.warnings), ("NOTE", result.notes)):
        for message in messages:
            print(f"{label}: {message}")


def main() -> int:
    args = parse_args()
    result, payload = build_report(args)
    print_report(result, payload, args.json)
    return 0 if not result.errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
