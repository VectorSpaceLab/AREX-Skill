#!/usr/bin/env python3
"""Validate the static MiniMind-V VLM parquet data contract."""
from __future__ import annotations
import argparse, io, json, sys
from pathlib import Path
from typing import Any, Iterable
REQUIRED_COLUMNS = ("conversations", "image_bytes")

def positive_int(value: str) -> int:
    try: parsed = int(value)
    except ValueError as exc: raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1: raise argparse.ArgumentTypeError("must be >= 1")
    return parsed

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Validate required columns, conversation structure, and image bytes for a MiniMind-V parquet file.")
    p.add_argument("parquet_path", type=Path, help="Path to a MiniMind-V VLM parquet file, for example dataset/sft_i2t.parquet.")
    p.add_argument("--max-rows", type=positive_int, default=100, help="Maximum rows to check from the start of the file.")
    p.add_argument("--max-errors", type=positive_int, default=20, help="Stop after this many errors.")
    return p

def load_pillow():
    try:
        from PIL import Image  # type: ignore
        return Image
    except Exception:
        return None

def normalize_conversations(value: Any) -> tuple[list[Any] | None, str | None]:
    if isinstance(value, str):
        if not value.strip(): return None, "conversations is an empty JSON string"
        try: value = json.loads(value)
        except json.JSONDecodeError as exc: return None, f"conversations is invalid JSON at char {exc.pos}: {exc.msg}"
    if not isinstance(value, list): return None, f"conversations must be a JSON string or list, got {type(value).__name__}"
    if not value: return None, "conversations list is empty"
    return value, None

def validate_conversations(value: Any) -> list[str]:
    conversations, problem = normalize_conversations(value)
    if problem: return [problem]
    assert conversations is not None
    problems: list[str] = []
    for i, turn in enumerate(conversations):
        if not isinstance(turn, dict):
            problems.append(f"conversation turn {i} must be an object, got {type(turn).__name__}"); continue
        if not isinstance(turn.get("role"), str) or not turn.get("role"):
            problems.append(f"conversation turn {i} role must be a non-empty string")
        if "content" not in turn:
            problems.append(f"conversation turn {i} is missing content")
        elif not isinstance(turn["content"], str):
            problems.append(f"conversation turn {i} content must be a string")
    return problems

def normalize_images(value: Any) -> tuple[list[Any] | None, str | None]:
    if value is None: return None, "image_bytes is missing/null"
    if isinstance(value, (bytes, bytearray, memoryview)): return [value], None
    if isinstance(value, (list, tuple)):
        if not value: return None, "image_bytes list is empty"
        return list(value), None
    return None, f"image_bytes must be bytes or a list of bytes, got {type(value).__name__}"

def validate_image_bytes(value: Any, pillow_image: Any | None) -> list[str]:
    images, problem = normalize_images(value)
    if problem: return [problem]
    assert images is not None
    problems: list[str] = []
    for i, item in enumerate(images):
        if item is None:
            problems.append(f"image_bytes[{i}] is null"); continue
        if not isinstance(item, (bytes, bytearray, memoryview)):
            problems.append(f"image_bytes[{i}] must be bytes-like, got {type(item).__name__}"); continue
        data = bytes(item)
        if not data:
            problems.append(f"image_bytes[{i}] is empty"); continue
        if pillow_image is not None:
            try:
                with pillow_image.open(io.BytesIO(data)) as img: img.verify()
            except Exception as exc:
                problems.append(f"image_bytes[{i}] is not PIL-decodable: {type(exc).__name__}: {exc}")
    return problems

def iter_rows(parquet_file: Any, columns: Iterable[str], max_rows: int):
    checked = 0
    for batch in parquet_file.iter_batches(batch_size=min(max_rows, 1024), columns=list(columns)):
        for row in batch.to_pylist():
            yield checked, row
            checked += 1
            if checked >= max_rows: return

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = args.parquet_path
    if not path.is_file(): print(f"FAIL: parquet file does not exist: {path}"); return 1
    try: import pyarrow.parquet as pq  # type: ignore
    except Exception as exc: print(f"FAIL: pyarrow is required to read parquet files: {exc}"); return 1
    try: parquet_file = pq.ParquetFile(path)
    except Exception as exc: print(f"FAIL: cannot open parquet file: {exc}"); return 1
    names = set(parquet_file.schema_arrow.names)
    missing = [c for c in REQUIRED_COLUMNS if c not in names]
    if missing: print(f"FAIL: missing required column(s): {', '.join(missing)}"); return 1
    if parquet_file.metadata and parquet_file.metadata.num_rows == 0: print("FAIL: parquet file has zero rows"); return 1
    pillow_image = load_pillow(); errors: list[str] = []; rows_checked = 0
    try:
        for row_index, row in iter_rows(parquet_file, REQUIRED_COLUMNS, args.max_rows):
            rows_checked += 1
            for problem in validate_conversations(row.get("conversations")): errors.append(f"row {row_index}: {problem}")
            for problem in validate_image_bytes(row.get("image_bytes"), pillow_image): errors.append(f"row {row_index}: {problem}")
            if len(errors) >= args.max_errors: break
    except Exception as exc: print(f"FAIL: error while reading parquet rows: {exc}"); return 1
    if rows_checked == 0: print("FAIL: no rows could be read from parquet file"); return 1
    total = "unknown total rows" if parquet_file.metadata is None else f"{parquet_file.metadata.num_rows} total rows"
    if errors:
        print(f"FAIL: checked {rows_checked} row(s), {total}; {len(errors)} validation error(s)")
        for item in errors[:args.max_errors]: print(f"- {item}")
        return 1
    decode = "image decode checked with Pillow" if pillow_image is not None else "image decode skipped because Pillow is unavailable"
    print(f"PASS: checked {rows_checked} row(s), {total}; required columns and sampled rows are valid; {decode}")
    return 0
if __name__ == "__main__": raise SystemExit(main())
