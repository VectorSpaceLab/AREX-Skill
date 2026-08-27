#!/usr/bin/env python3
"""
Inspect an img2dataset output folder without importing img2dataset.

The helper is safe by default: it lists files, samples tar members, and reads
parquet metadata columns when optional readers are installed. It does not run
native repository tests, download data, mutate output files, or import the
source package.

Example:
  python inspect_output_layout.py --output-folder out --expected-format webdataset --require-captions
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys
import tarfile
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
IMAGE_BYTE_COLUMNS = {"jpg", "jpeg", "png", "webp"}
EXPECTED_FORMATS = ("files", "webdataset", "parquet", "tfrecord", "dummy")


@dataclass
class Entry:
    path: str
    name: str
    is_dir: bool


class LocalFS:
    """Small local filesystem adapter used when fsspec is unavailable."""

    protocol = "file"

    @staticmethod
    def exists(path: str) -> bool:
        return os.path.exists(path)

    @staticmethod
    def isdir(path: str) -> bool:
        return os.path.isdir(path)

    @staticmethod
    def glob(pattern: str) -> List[str]:
        return glob.glob(pattern)

    @staticmethod
    def open(path: str, mode: str = "rb"):
        return open(path, mode)  # noqa: PTH123 - deliberate filesystem adapter


def _looks_remote(path: str) -> bool:
    parsed = urlparse(path)
    return bool(parsed.scheme and parsed.scheme != "file")


def _get_fs(path: str):
    try:
        import fsspec  # type: ignore
    except ImportError:
        if _looks_remote(path):
            raise SystemExit(
                "Remote or prefixed paths require fsspec in this helper. "
                "Install fsspec with the backend needed for the prefix, or inspect a local copy."
            )
        return LocalFS(), path
    fs, fs_path = fsspec.core.url_to_fs(path)
    return fs, fs_path


def _entry_name(path: str) -> str:
    return path.rstrip("/").split("/")[-1]


def _list_entries(fs, folder: str) -> List[Entry]:
    pattern = folder.rstrip("/") + "/*"
    try:
        paths = fs.glob(pattern)
    except Exception as exc:  # pylint: disable=broad-except
        raise SystemExit(f"Could not list output folder {folder!r}: {exc}") from exc
    if isinstance(paths, dict):
        paths = list(paths)
    entries: List[Entry] = []
    for path in sorted(paths):
        try:
            is_dir = bool(fs.isdir(path))
        except Exception:  # pylint: disable=broad-except
            is_dir = False
        entries.append(Entry(path=path, name=_entry_name(path), is_dir=is_dir))
    return entries


def _count_extensions(names: Iterable[str]) -> Dict[str, int]:
    counts: Dict[str, int] = collections.Counter()
    for name in names:
        _, ext = os.path.splitext(name.lower())
        if ext:
            counts[ext] += 1
        else:
            counts["<no-ext>"] += 1
    return dict(sorted(counts.items()))


def _is_numeric_shard_name(name: str) -> bool:
    return bool(re.fullmatch(r"\d+", name))


def _sample_files_subfolders(fs, subfolders: Sequence[Entry], limit: int) -> Tuple[List[str], Dict[str, int], int, int]:
    sampled: List[str] = []
    total_images = 0
    total_txt = 0
    aggregate: Dict[str, int] = collections.Counter()
    for entry in subfolders[:limit]:
        children = _list_entries(fs, entry.path)
        child_names = [child.name for child in children if not child.is_dir]
        counts = _count_extensions(child_names)
        for ext, count in counts.items():
            aggregate[ext] += count
        image_count = sum(counts.get(ext, 0) for ext in IMAGE_EXTENSIONS)
        txt_count = counts.get(".txt", 0)
        total_images += image_count
        total_txt += txt_count
        sampled.append(f"{entry.name}: {counts}")
    return sampled, dict(sorted(aggregate.items())), total_images, total_txt


def _inspect_tars(fs, tars: Sequence[Entry], limit: int) -> Tuple[List[str], int, int, List[str]]:
    summaries: List[str] = []
    total_images = 0
    total_txt = 0
    errors: List[str] = []
    for entry in tars[:limit]:
        try:
            with fs.open(entry.path, "rb") as file_obj:
                with tarfile.open(fileobj=file_obj, mode="r:*") as tar:
                    members = [member.name for member in tar.getmembers() if member.isfile()]
        except Exception as exc:  # pylint: disable=broad-except
            errors.append(f"{entry.name}: could not inspect tar members: {exc}")
            continue
        counts = _count_extensions(members)
        image_count = sum(counts.get(ext, 0) for ext in IMAGE_EXTENSIONS)
        txt_count = counts.get(".txt", 0)
        total_images += image_count
        total_txt += txt_count
        summaries.append(f"{entry.name}: {counts}")
    return summaries, total_images, total_txt, errors


def _inspect_parquet_with_pyarrow(fs, path: str) -> Tuple[Optional[List[str]], Optional[int], Optional[str]]:
    try:
        import pyarrow.parquet as pq  # type: ignore
    except ImportError:
        return None, None, "pyarrow is not installed"
    try:
        with fs.open(path, "rb") as file_obj:
            parquet_file = pq.ParquetFile(file_obj)
            columns = list(parquet_file.schema_arrow.names)
            rows = parquet_file.metadata.num_rows if parquet_file.metadata is not None else None
            return columns, rows, None
    except Exception as exc:  # pylint: disable=broad-except
        return None, None, str(exc)


def _inspect_parquet_with_pandas(fs, path: str) -> Tuple[Optional[List[str]], Optional[int], Optional[str]]:
    try:
        import pandas as pd  # type: ignore
    except ImportError:
        return None, None, "pandas is not installed"
    try:
        with fs.open(path, "rb") as file_obj:
            df = pd.read_parquet(file_obj)
        return list(df.columns), len(df.index), None
    except Exception as exc:  # pylint: disable=broad-except
        return None, None, str(exc)


def _inspect_parquets(fs, parquets: Sequence[Entry], limit: int) -> List[Dict[str, object]]:
    inspected: List[Dict[str, object]] = []
    for entry in parquets[:limit]:
        columns, rows, error = _inspect_parquet_with_pyarrow(fs, entry.path)
        engine = "pyarrow"
        if columns is None:
            columns, rows, pandas_error = _inspect_parquet_with_pandas(fs, entry.path)
            engine = "pandas"
            if columns is None:
                error = f"pyarrow: {error}; pandas: {pandas_error}"
            else:
                error = None
        inspected.append(
            {
                "name": entry.name,
                "engine": engine if columns is not None else None,
                "columns": columns,
                "rows": rows,
                "has_image_bytes_column": bool(columns and IMAGE_BYTE_COLUMNS.intersection(columns)),
                "has_caption_column": bool(columns and ({"caption", "txt"}.intersection(columns))),
                "error": error,
            }
        )
    return inspected


def _read_stats_sample(fs, stats: Sequence[Entry], limit: int) -> List[str]:
    summaries: List[str] = []
    for entry in stats[:limit]:
        try:
            with fs.open(entry.path, "r") as file_obj:
                data = json.load(file_obj)
            keys = [key for key in ["count", "successes", "failed_to_download", "failed_to_resize", "duration"] if key in data]
            summary = {key: data[key] for key in keys}
            summaries.append(f"{entry.name}: {summary}")
        except Exception as exc:  # pylint: disable=broad-except
            summaries.append(f"{entry.name}: could not parse stats JSON: {exc}")
    return summaries


def _infer_format(subfolders: Sequence[Entry], tars: Sequence[Entry], parquets_info: Sequence[Dict[str, object]], tfrecords: Sequence[Entry], root_images: Sequence[Entry]) -> str:
    if tfrecords:
        return "tfrecord"
    if tars:
        return "webdataset"
    if subfolders or root_images:
        return "files"
    if any(info.get("has_image_bytes_column") for info in parquets_info):
        return "parquet"
    if not parquets_info:
        return "dummy-or-empty"
    return "metadata-only-or-sidecar"


def _validate(
    expected: Optional[str],
    require_captions: bool,
    subfolders: Sequence[Entry],
    files_image_count: int,
    files_txt_count: int,
    tars: Sequence[Entry],
    tar_image_count: int,
    tar_txt_count: int,
    parquets: Sequence[Entry],
    parquet_info: Sequence[Dict[str, object]],
    tfrecords: Sequence[Entry],
    stats: Sequence[Entry],
    root_images: Sequence[Entry],
) -> List[str]:
    problems: List[str] = []
    has_image_parquet = any(info.get("has_image_bytes_column") for info in parquet_info)
    has_caption_parquet = any(info.get("has_caption_column") for info in parquet_info)

    if expected == "files":
        if not subfolders:
            problems.append("expected files output but no numeric shard subfolders were found")
        if not parquets:
            problems.append("expected files output but no root shard parquet metadata sidecar was found")
        if tars or tfrecords:
            problems.append("expected files output but tar or TFRecord shards were also found")
    elif expected == "webdataset":
        if not tars:
            problems.append("expected webdataset output but no .tar shard was found")
        if not parquets:
            problems.append("expected webdataset output but no root shard parquet metadata sidecar was found")
        if subfolders or tfrecords:
            problems.append("expected webdataset output but files subfolders or TFRecord shards were also found")
    elif expected == "parquet":
        if not parquets:
            problems.append("expected parquet output but no .parquet shard was found")
        elif parquet_info and not has_image_parquet and all(info.get("columns") for info in parquet_info):
            problems.append("expected parquet output but sampled parquet files lack an image bytes column such as jpg/png/webp")
        if tars or subfolders or tfrecords:
            problems.append("expected parquet output but tar, files subfolders, or TFRecord shards were also found")
    elif expected == "tfrecord":
        if not tfrecords:
            problems.append("expected tfrecord output but no .tfrecord shard was found")
        if not parquets:
            problems.append("expected tfrecord output but no root shard parquet metadata sidecar was found")
        if tars or subfolders:
            problems.append("expected tfrecord output but tar or files subfolders were also found")
    elif expected == "dummy":
        if subfolders or tars or parquets or tfrecords or root_images:
            problems.append("expected dummy output but sample artifacts were found; dummy should only leave stats JSON or an empty folder")

    if require_captions:
        if expected == "dummy":
            problems.append("captions were required, but dummy output never writes caption artifacts")
        elif expected == "files":
            if files_image_count and files_txt_count != files_image_count:
                problems.append(
                    f"captions required for files output, but sampled image/text counts differ: images={files_image_count}, txt={files_txt_count}"
                )
            if parquets and parquet_info and not has_caption_parquet:
                problems.append("captions required, but sampled parquet metadata has no caption or txt column")
        elif expected == "webdataset":
            if tar_image_count and tar_txt_count != tar_image_count:
                problems.append(
                    f"captions required for webdataset output, but sampled image/text member counts differ: images={tar_image_count}, txt={tar_txt_count}"
                )
            if parquets and parquet_info and not has_caption_parquet:
                problems.append("captions required, but sampled parquet metadata has no caption or txt column")
        elif expected in {"parquet", "tfrecord"}:
            if parquets and parquet_info and not has_caption_parquet:
                problems.append("captions required, but sampled parquet metadata has no caption or txt column")
            elif not parquets:
                problems.append("captions required, but no parquet metadata was available to audit captions")
        else:
            caption_evidence = files_txt_count or tar_txt_count or has_caption_parquet
            if not caption_evidence:
                problems.append("captions required, but no caption files, tar members, or metadata columns were found in the sample")

    if expected and expected != "dummy" and not stats:
        # Not always fatal for direct writer-class tests or manually staged outputs, so report as warning in stdout instead.
        pass

    return problems


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect an img2dataset output folder layout without importing img2dataset.",
    )
    parser.add_argument("--output-folder", required=True, help="Folder or fsspec-style prefix to inspect.")
    parser.add_argument(
        "--expected-format",
        choices=EXPECTED_FORMATS,
        default=None,
        help="Optional expected img2dataset output_format to validate.",
    )
    parser.add_argument(
        "--require-captions",
        action="store_true",
        help="Fail if sampled outputs lack expected caption artifacts or metadata columns.",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=5,
        help="Maximum number of shard subfolders/tars/parquets/stats files to inspect deeply.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    if args.sample_limit < 1:
        raise SystemExit("--sample-limit must be at least 1")

    fs, output_path = _get_fs(args.output_folder)
    try:
        exists = bool(fs.exists(output_path))
    except Exception as exc:  # pylint: disable=broad-except
        raise SystemExit(f"Could not access output folder {args.output_folder!r}: {exc}") from exc
    if not exists:
        raise SystemExit(f"Output folder does not exist or cannot be listed: {args.output_folder}")

    entries = _list_entries(fs, output_path)
    subfolders = [entry for entry in entries if entry.is_dir and _is_numeric_shard_name(entry.name)]
    tars = [entry for entry in entries if not entry.is_dir and entry.name.endswith(".tar")]
    parquets = [entry for entry in entries if not entry.is_dir and entry.name.endswith(".parquet")]
    tfrecords = [entry for entry in entries if not entry.is_dir and entry.name.endswith(".tfrecord")]
    stats = [entry for entry in entries if not entry.is_dir and entry.name.endswith("_stats.json")]
    root_images = [entry for entry in entries if not entry.is_dir and os.path.splitext(entry.name.lower())[1] in IMAGE_EXTENSIONS]
    ignored_dirs = [entry for entry in entries if entry.is_dir and not _is_numeric_shard_name(entry.name)]

    files_samples, files_counts, files_image_count, files_txt_count = _sample_files_subfolders(
        fs, subfolders, args.sample_limit
    )
    tar_samples, tar_image_count, tar_txt_count, tar_errors = _inspect_tars(fs, tars, args.sample_limit)
    parquet_info = _inspect_parquets(fs, parquets, args.sample_limit)
    stats_samples = _read_stats_sample(fs, stats, args.sample_limit)
    inferred = _infer_format(subfolders, tars, parquet_info, tfrecords, root_images)

    print("img2dataset output layout inspection")
    print(f"output_folder: {args.output_folder}")
    print(f"expected_format: {args.expected_format or '<not specified>'}")
    print(f"inferred_layout: {inferred}")
    print()
    print("root summary:")
    print(f"  numeric shard subfolders: {len(subfolders)}")
    print(f"  tar shards: {len(tars)}")
    print(f"  parquet files: {len(parquets)}")
    print(f"  tfrecord files: {len(tfrecords)}")
    print(f"  stats json files: {len(stats)}")
    if root_images:
        print(f"  root-level image files: {len(root_images)}")
    if ignored_dirs:
        print(f"  non-shard directories ignored: {[entry.name for entry in ignored_dirs[:args.sample_limit]]}")
    if args.expected_format and args.expected_format != "dummy" and not stats:
        print("  warning: no *_stats.json files found; direct writer tests may omit stats, but downloader runs use them for done shards")

    if files_samples:
        print("\nsampled files subfolders:")
        for line in files_samples:
            print(f"  {line}")
        print(f"  aggregate sampled counts: {files_counts}")
    if tar_samples or tar_errors:
        print("\nsampled tar shards:")
        for line in tar_samples:
            print(f"  {line}")
        for line in tar_errors:
            print(f"  warning: {line}")
    if parquet_info:
        print("\nsampled parquet metadata:")
        for info in parquet_info:
            if info["columns"] is None:
                print(f"  {info['name']}: could not inspect columns ({info['error']})")
            else:
                print(
                    f"  {info['name']}: rows={info['rows']}, "
                    f"image_bytes={info['has_image_bytes_column']}, "
                    f"captions={info['has_caption_column']}, columns={info['columns']}"
                )
    if stats_samples:
        print("\nsampled stats json:")
        for line in stats_samples:
            print(f"  {line}")

    problems = _validate(
        expected=args.expected_format,
        require_captions=args.require_captions,
        subfolders=subfolders,
        files_image_count=files_image_count,
        files_txt_count=files_txt_count,
        tars=tars,
        tar_image_count=tar_image_count,
        tar_txt_count=tar_txt_count,
        parquets=parquets,
        parquet_info=parquet_info,
        tfrecords=tfrecords,
        stats=stats,
        root_images=root_images,
    )

    if problems:
        print("\nlayout mismatches:")
        for problem in problems:
            print(f"  - {problem}")
        return 2

    print("\nlayout check: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
