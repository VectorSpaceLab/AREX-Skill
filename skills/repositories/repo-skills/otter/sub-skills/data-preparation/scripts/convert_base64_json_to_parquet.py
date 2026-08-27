#!/usr/bin/env python3
"""Convert a MIMIC-IT image JSON object to parquet with a base64 column.

Input JSON contract:
  {"IMAGE_ID": "base64-string", ...}

Output parquet contract:
  pandas index: image id
  required column: base64
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import shutil
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    raw = path.read_bytes()
    try:
        import orjson  # type: ignore

        return orjson.loads(raw)
    except Exception:
        return json.loads(raw.decode("utf-8"))


def normalize_base64_value(value: Any, key: str) -> str:
    if isinstance(value, list):
        if not value:
            raise ValueError(f"{key}: empty list cannot provide a base64 payload")
        value = value[0]
    elif isinstance(value, dict) and "base64" in value:
        value = value["base64"]
    if not isinstance(value, str):
        raise ValueError(f"{key}: expected string, list with first string, or object containing 'base64'")
    return "".join(value.split())


def decode_base64(value: str) -> bytes:
    padded = value + ("=" * ((-len(value)) % 4))
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def validate_payloads(records: list[tuple[str, str]], validate_images: bool) -> None:
    for key, value in records:
        try:
            raw = decode_base64(value)
        except (binascii.Error, ValueError, UnicodeEncodeError) as exc:
            raise ValueError(f"{key}: invalid base64 payload: {exc}") from exc
        if validate_images:
            try:
                from PIL import Image  # type: ignore
            except Exception as exc:  # pragma: no cover - environment dependent
                raise RuntimeError("Pillow is required for --validate-images") from exc
            try:
                Image.open(BytesIO(raw)).verify()
            except Exception as exc:
                raise ValueError(f"{key}: base64 decoded but Pillow could not verify image bytes: {exc}") from exc


def build_dataframe(records: list[tuple[str, str]]):
    try:
        import pandas as pd  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("pandas is required to write parquet") from exc
    df = pd.DataFrame.from_records(records, columns=["image_id", "base64"]).set_index("image_id")
    df.index = df.index.astype(str)
    return df


def ensure_output_available(output_path: Path, overwrite: bool) -> None:
    if output_path.exists():
        if not overwrite:
            raise FileExistsError(f"output exists: {output_path}; pass --overwrite to replace it")
        if output_path.is_dir():
            shutil.rmtree(output_path)
        else:
            output_path.unlink()


def write_single_parquet(df, output_path: Path, compression: str, overwrite: bool) -> None:
    ensure_output_available(output_path, overwrite)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=output_path.name + ".", suffix=".tmp", dir=str(output_path.parent))
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        df.to_parquet(tmp_path, engine="pyarrow", compression=compression, index=True)
        os.replace(tmp_path, output_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def write_partitioned_parquet(df, output_path: Path, rows_per_partition: int, compression: str, overwrite: bool) -> None:
    if rows_per_partition <= 0:
        raise ValueError("rows_per_partition must be positive")
    ensure_output_available(output_path, overwrite)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix=output_path.name + ".tmp.", dir=str(output_path.parent)))
    try:
        total = len(df)
        part = 0
        for start in range(0, total, rows_per_partition):
            stop = min(total, start + rows_per_partition)
            df.iloc[start:stop].to_parquet(tmp_dir / f"part-{part:05d}.parquet", engine="pyarrow", compression=compression, index=True)
            part += 1
        os.replace(tmp_dir, output_path)
    except Exception:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert MIMIC-IT image JSON to parquet with a base64 column.")
    parser.add_argument("input_json", help="Input JSON mapping image id to base64 string")
    parser.add_argument("output_parquet", help="Output parquet file, or output directory when --rows-per-partition is set")
    parser.add_argument("--rows-per-partition", type=int, default=0, help="Write a parquet directory split into this many rows per part")
    parser.add_argument("--compression", default="snappy", choices=["snappy", "gzip", "brotli", "zstd", "lz4", "none"], help="Parquet compression codec")
    parser.add_argument("--validate-sample", type=int, default=0, help="Number of records to base64-decode before writing; 0 disables")
    parser.add_argument("--validate-images", action="store_true", help="With --validate-sample, also verify decoded bytes with Pillow")
    parser.add_argument("--max-records", type=int, default=0, help="Convert only the first N records for a bounded run; 0 converts all")
    parser.add_argument("--dry-run", action="store_true", help="Load and validate input records but do not write parquet")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output path")
    args = parser.parse_args(argv)

    input_path = Path(args.input_json).expanduser()
    output_path = Path(args.output_parquet).expanduser()
    if not input_path.exists():
        print(f"ERROR: input JSON does not exist: {input_path}", file=sys.stderr)
        return 2

    try:
        data = load_json(input_path)
        if not isinstance(data, dict):
            raise ValueError("input JSON must be an object mapping image id to base64 string")
        records: list[tuple[str, str]] = []
        for idx, (key, value) in enumerate(data.items()):
            if args.max_records and idx >= args.max_records:
                break
            records.append((str(key), normalize_base64_value(value, str(key))))
        if not records:
            raise ValueError("no records to convert")
        if len({key for key, _ in records}) != len(records):
            raise ValueError("duplicate image ids after string normalization")
        if args.validate_sample:
            sample = records[: min(args.validate_sample, len(records))]
            validate_payloads(sample, validate_images=args.validate_images)
        if args.dry_run:
            print(f"OK: dry run validated {len(records)} record(s); no parquet was written")
            return 0
        df = build_dataframe(records)
        compression = None if args.compression == "none" else args.compression
        if args.rows_per_partition:
            write_partitioned_parquet(df, output_path, args.rows_per_partition, compression, args.overwrite)
            output_kind = "partitioned parquet directory"
        else:
            write_single_parquet(df, output_path, compression, args.overwrite)
            output_kind = "parquet file"
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK: wrote {len(records)} records to {output_kind}: {output_path}")
    print("Schema: index=image_id, column=base64")
    return 0


if __name__ == "__main__":
    sys.exit(main())
