#!/usr/bin/env python3
"""Offline DataFlow pipeline-foundations smoke test.

Usage examples:
  python scripts/smoke_pipeline_foundations.py
  python scripts/smoke_pipeline_foundations.py --keep
  python scripts/smoke_pipeline_foundations.py --workdir dataflow-foundation-smoke
  python scripts/smoke_pipeline_foundations.py --demo-missing-key
  python scripts/smoke_pipeline_foundations.py --self-check-help

The script creates a tiny local JSONL file, compiles a two-step custom
OperatorABC pipeline, runs it without LLMs/network/GPU, and verifies the final
cache contents.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

from dataflow.core.operator import OperatorABC
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage


class AddLengthOperator(OperatorABC):
    """Add a string-length column."""

    def __init__(self) -> None:
        super().__init__()

    def run(self, storage, input_text, output_length):
        dataframe = storage.read(output_type="dataframe")
        if input_text not in dataframe.columns:
            raise KeyError(f"Missing input column {input_text!r}; available={list(dataframe.columns)!r}")
        output = dataframe.copy()
        output[output_length] = output[input_text].astype(str).str.len()
        return storage.write(output)


class AddLengthFlagOperator(OperatorABC):
    """Add a boolean flag based on a length column."""

    def __init__(self, threshold: int = 5) -> None:
        super().__init__()
        self.threshold = threshold

    def run(self, storage, input_length, output_flag):
        dataframe = storage.read(output_type="dataframe")
        if input_length not in dataframe.columns:
            raise KeyError(f"Missing input column {input_length!r}; available={list(dataframe.columns)!r}")
        output = dataframe.copy()
        output[output_flag] = output[input_length].astype(int) >= self.threshold
        return storage.write(output)


class TinyFoundationPipeline(PipelineABC):
    """Two deterministic operators over FileStorage."""

    def __init__(self, input_path: Path, cache_dir: Path, prefix: str, *, bad_input_key: bool = False) -> None:
        super().__init__()
        self.storage = FileStorage(
            first_entry_file_name=str(input_path),
            cache_path=str(cache_dir),
            file_name_prefix=prefix,
            cache_type="jsonl",
        )
        self.add_length = AddLengthOperator()
        self.add_flag = AddLengthFlagOperator(threshold=5)
        self.bad_input_key = bad_input_key

    def forward(self):
        self.add_length.run(
            storage=self.storage.step(),
            input_text="missing_text" if self.bad_input_key else "text",
            output_length="text_length",
        )
        self.add_flag.run(
            storage=self.storage.step(),
            input_length="text_length",
            output_flag="is_long",
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run an offline DataFlow custom-operator pipeline smoke test.",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="Directory for temporary input/cache files. Defaults to a temporary directory.",
    )
    parser.add_argument(
        "--prefix",
        default="foundation_smoke",
        help="FileStorage cache file prefix. Default: foundation_smoke.",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the auto-created temporary directory after a successful run.",
    )
    parser.add_argument(
        "--demo-missing-key",
        action="store_true",
        help="Intentionally compile a bad pipeline and verify that compile-time key validation fails.",
    )
    parser.add_argument(
        "--print-records",
        action="store_true",
        help="Print final records as JSON after validation.",
    )
    parser.add_argument(
        "--self-check-help",
        action="store_true",
        help="Verify that argparse --help text is available, then exit.",
    )
    return parser


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_step(input_path: Path, cache_dir: Path, prefix: str, step_number: int):
    storage = FileStorage(
        first_entry_file_name=str(input_path),
        cache_path=str(cache_dir),
        file_name_prefix=prefix,
        cache_type="jsonl",
    ).reset()
    for _ in range(step_number + 1):
        storage.step()
    return storage.read(output_type="dataframe")


def run_good_pipeline(workdir: Path, prefix: str, print_records: bool) -> None:
    input_path = workdir / "input.jsonl"
    cache_dir = workdir / "cache"
    records = [
        {"id": 1, "text": "a"},
        {"id": 2, "text": "hello"},
        {"id": 3, "text": "world!"},
    ]
    write_jsonl(input_path, records)

    pipeline = TinyFoundationPipeline(input_path=input_path, cache_dir=cache_dir, prefix=prefix)
    pipeline.compile()
    pipeline.forward()

    final_dataframe = read_step(input_path=input_path, cache_dir=cache_dir, prefix=prefix, step_number=2)
    expected_columns = {"id", "text", "text_length", "is_long"}
    missing = expected_columns.difference(final_dataframe.columns)
    if missing:
        raise AssertionError(f"Final output missing columns: {sorted(missing)}")

    lengths = final_dataframe["text_length"].tolist()
    flags = final_dataframe["is_long"].tolist()
    if lengths != [1, 5, 6]:
        raise AssertionError(f"Unexpected lengths: {lengths!r}")
    if flags != [False, True, True]:
        raise AssertionError(f"Unexpected flags: {flags!r}")

    final_path = cache_dir / f"{prefix}_step2.jsonl"
    if not final_path.exists():
        raise AssertionError(f"Expected final cache file does not exist: {final_path}")

    print(f"OK: compiled and ran offline DataFlow pipeline; final cache: {final_path}")
    if print_records:
        print(final_dataframe.to_json(orient="records", force_ascii=False, indent=2))


def run_missing_key_demo(workdir: Path, prefix: str) -> None:
    input_path = workdir / "input.jsonl"
    cache_dir = workdir / "cache"
    write_jsonl(input_path, [{"id": 1, "text": "a"}])
    pipeline = TinyFoundationPipeline(
        input_path=input_path,
        cache_dir=cache_dir,
        prefix=prefix,
        bad_input_key=True,
    )
    try:
        pipeline.compile()
    except KeyError as exc:
        message = str(exc)
        if "missing_text" not in message:
            raise AssertionError(f"Compile failed, but did not name the missing key: {message}") from exc
        print("OK: compile-time key validation rejected missing input key 'missing_text'.")
        return
    raise AssertionError("Expected pipeline.compile() to fail for missing input key, but it succeeded.")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.self_check_help:
        help_text = parser.format_help()
        if "--help" not in help_text or "--demo-missing-key" not in help_text:
            raise AssertionError("argparse help text did not include expected options")
        print("OK: argparse --help text is available.")
        return 0

    auto_temp = args.workdir is None
    workdir = args.workdir or Path(tempfile.mkdtemp(prefix="dataflow_foundation_smoke_"))
    workdir.mkdir(parents=True, exist_ok=True)

    try:
        if args.demo_missing_key:
            run_missing_key_demo(workdir=workdir, prefix=args.prefix)
        else:
            run_good_pipeline(workdir=workdir, prefix=args.prefix, print_records=args.print_records)
        print(f"workdir={workdir}")
        return 0
    finally:
        if auto_temp and not args.keep:
            shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
