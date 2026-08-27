#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sdgx.data_connectors.csv_connector import CsvConnector
from sdgx.data_loader import DataLoader
from sdgx.data_models.metadata import Metadata


def split_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [part.strip() for part in value.split(",") if part.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a CSV with SDGX Metadata and optionally save JSON.")
    parser.add_argument("csv", help="Input CSV file.")
    parser.add_argument("--output", "-o", help="Write metadata JSON to this path.")
    parser.add_argument("--max-chunk", type=int, default=10, help="Maximum chunks for Metadata.from_dataloader.")
    parser.add_argument("--chunksize", type=int, default=10000, help="DataLoader chunk size.")
    parser.add_argument("--cache-dir", help="Optional DiskCache directory.")
    parser.add_argument("--include-inspectors", help="Comma-separated inspector names.")
    parser.add_argument("--exclude-inspectors", help="Comma-separated inspector names.")
    parser.add_argument("--primary-key", action="append", default=[], help="Primary key column; repeatable.")
    parser.add_argument("--datetime-format", action="append", default=[], metavar="COL=FORMAT", help="Datetime format override; repeatable.")
    parser.add_argument("--check", action="store_true", help="Run metadata.check() before output.")
    args = parser.parse_args()

    connector = CsvConnector(path=args.csv)
    loader_kwargs = {}
    if args.cache_dir:
        loader_kwargs["cacher_kwargs"] = {"cache_dir": args.cache_dir}
    loader = DataLoader(connector, chunksize=args.chunksize, **loader_kwargs)
    try:
        metadata = Metadata.from_dataloader(
            loader,
            max_chunk=args.max_chunk,
            primary_keys=set(args.primary_key) if args.primary_key else None,
            include_inspectors=split_csv(args.include_inspectors),
            exclude_inspectors=split_csv(args.exclude_inspectors),
            check=False,
        )
        for item in args.datetime_format:
            if "=" not in item:
                raise SystemExit(f"--datetime-format must be COL=FORMAT, got {item!r}")
            col, fmt = item.split("=", 1)
            metadata.datetime_format[col] = fmt
        if args.check:
            metadata.check()
        if args.output:
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            metadata.save(out)
            print(out)
        else:
            print(metadata._dump_json())
    finally:
        loader.finalize(clear_cache=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
