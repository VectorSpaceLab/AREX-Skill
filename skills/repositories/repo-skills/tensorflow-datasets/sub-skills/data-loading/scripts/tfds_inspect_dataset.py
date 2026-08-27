#!/usr/bin/env python3
"""Safe metadata-first inspector for existing TensorFlow Datasets datasets.

The script avoids downloads by default. Pass --download only when dataset
preparation/network/storage cost is explicitly acceptable.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from typing import Any


def _parse_scalar(value: str) -> Any:
    """Parse a CLI scalar for --builder-kwarg."""
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "none" or lowered == "null":
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _parse_builder_kwargs(items: list[str] | None) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    for item in items or []:
        if "=" not in item:
            raise argparse.ArgumentTypeError(
                f"builder kwarg must be KEY=VALUE, got {item!r}"
            )
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise argparse.ArgumentTypeError(f"empty builder kwarg key in {item!r}")
        kwargs[key] = _parse_scalar(value.strip())
    return kwargs


def _summarize_value(value: Any, *, max_items: int = 4) -> Any:
    """Return a compact, printable summary of tensors/arrays/nested values."""
    if isinstance(value, Mapping):
        return {str(k): _summarize_value(v, max_items=max_items) for k, v in value.items()}
    if isinstance(value, tuple):
        return tuple(_summarize_value(v, max_items=max_items) for v in value)
    if isinstance(value, list):
        return [_summarize_value(v, max_items=max_items) for v in value[:max_items]]
    shape = getattr(value, "shape", None)
    dtype = getattr(value, "dtype", None)
    if shape is not None or dtype is not None:
        cls = type(value).__name__
        return f"{cls}(shape={shape}, dtype={dtype})"
    if isinstance(value, (bytes, bytearray)):
        preview = bytes(value[:32])
        return f"bytes(len={len(value)}, preview={preview!r})"
    if isinstance(value, str) and len(value) > 80:
        return value[:77] + "..."
    return value


def _print_section(title: str) -> None:
    print(f"\n## {title}")


def _safe_attr(obj: Any, attr: str, default: Any = None) -> Any:
    try:
        return getattr(obj, attr)
    except Exception as exc:  # pragma: no cover - defensive for lazy metadata
        return f"<unavailable: {type(exc).__name__}: {exc}>"


def _iter_builder_configs(builder: Any) -> list[str]:
    configs = _safe_attr(builder, "BUILDER_CONFIGS", []) or []
    names: list[str] = []
    for config in configs:
        name = _safe_attr(config, "name", None)
        version = _safe_attr(config, "version", None)
        if name and version:
            names.append(f"{name}:{version}")
        elif name:
            names.append(str(name))
    return names


def _print_metadata(builder: Any, *, split_expr: str | None, show_files: bool) -> None:
    info = builder.info

    _print_section("Builder")
    print(f"name: {_safe_attr(info, 'name')}")
    print(f"full_name: {_safe_attr(info, 'full_name')}")
    print(f"version: {_safe_attr(info, 'version')}")
    print(f"data_dir: {_safe_attr(builder, 'data_dir')}")
    try:
        print(f"is_prepared: {builder.is_prepared()}")
    except Exception as exc:
        print(f"is_prepared: <unavailable: {type(exc).__name__}: {exc}>")

    configs = _iter_builder_configs(builder)
    if configs:
        print("builder_configs:")
        for config in configs:
            print(f"  - {config}")

    supervised_keys = _safe_attr(info, "supervised_keys")
    if supervised_keys:
        print(f"supervised_keys: {supervised_keys}")

    _print_section("Features")
    features = _safe_attr(info, "features")
    print(features if features else "<no feature metadata available>")

    _print_section("Splits")
    splits = _safe_attr(info, "splits")
    if not splits:
        print("<no split metadata available; data may not be prepared locally>")
    else:
        for split_name in splits.keys():
            split_info = splits[split_name]
            print(
                f"- {split_name}: "
                f"num_examples={_safe_attr(split_info, 'num_examples')}, "
                f"num_shards={_safe_attr(split_info, 'num_shards')}"
            )
            if show_files:
                filenames = _safe_attr(split_info, "filenames", [])
                for filename in filenames:
                    print(f"    file: {filename}")

    if split_expr:
        _print_section(f"Split expression: {split_expr}")
        try:
            split_info = info.splits[split_expr]
            print(f"num_examples: {split_info.num_examples}")
            print(f"num_shards: {split_info.num_shards}")
            instructions = getattr(split_info, "file_instructions", None)
            if instructions is not None:
                print(f"file_instructions_count: {len(instructions)}")
                for instruction in list(instructions)[:5]:
                    print(f"  - {instruction}")
                if len(instructions) > 5:
                    print(f"  ... {len(instructions) - 5} more")
        except Exception as exc:
            print(f"<unable to resolve split expression: {type(exc).__name__}: {exc}>")


def _inspect_tf_dataset(
    builder: Any,
    *,
    split: str | None,
    sample: int,
    as_supervised: bool,
    add_tfds_id: bool,
    tfds: Any,
) -> None:
    if sample <= 0:
        return
    if not split:
        raise SystemExit("--sample requires --split so the script samples only one dataset")

    _print_section("tf.data sample")
    read_config = tfds.ReadConfig(add_tfds_id=True) if add_tfds_id else None
    ds = builder.as_dataset(
        split=split,
        shuffle_files=False,
        as_supervised=as_supervised,
        read_config=read_config,
    )
    print(f"element_spec: {ds.element_spec}")
    for index, example in enumerate(ds.take(sample)):
        print(f"sample[{index}]: {_summarize_value(example)}")


def _inspect_data_source(
    *,
    tfds: Any,
    dataset: str,
    split: str | None,
    data_dir: str | None,
    download: bool,
    builder_kwargs: dict[str, Any],
    try_gcs: bool,
    sample: int,
) -> None:
    _print_section("Data source")
    source = tfds.data_source(
        dataset,
        split=split,
        data_dir=data_dir,
        download=download,
        builder_kwargs=builder_kwargs or None,
        try_gcs=try_gcs,
    )
    print(f"type: {type(source).__name__}")
    try:
        print(f"len: {len(source)}")
    except Exception as exc:
        print(f"len: <unavailable: {type(exc).__name__}: {exc}>")

    if sample > 0:
        if isinstance(source, Mapping):
            print("source is a mapping; pass --split to sample one split")
            return
        limit = min(sample, len(source)) if hasattr(source, "__len__") else sample
        for index in range(limit):
            print(f"source[{index}]: {_summarize_value(source[index])}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect TFDS builder metadata, features, splits, and optional tiny "
            "samples. No dataset download is attempted unless --download is set."
        )
    )
    parser.add_argument("dataset", help="Dataset name, optionally with config/version")
    parser.add_argument("--split", help="Split expression to inspect or sample")
    parser.add_argument("--data-dir", help="TFDS prepared-data root to inspect")
    parser.add_argument(
        "--try-gcs",
        action="store_true",
        help="Try public prepared TFDS GCS data for datasets hosted there",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Opt in to download_and_prepare before inspecting/sampling",
    )
    parser.add_argument(
        "--manual-dir",
        help="Manual download directory to pass through DownloadConfig; requires --download",
    )
    parser.add_argument(
        "--max-examples-per-split",
        type=int,
        help="Limit generated examples per split during --download preparation",
    )
    parser.add_argument(
        "--file-format",
        help="Builder/read file format, for example array_record or tfrecord",
    )
    parser.add_argument(
        "--builder-kwarg",
        action="append",
        metavar="KEY=VALUE",
        help="Extra builder kwarg; VALUE is parsed as JSON/bool/number/string",
    )
    parser.add_argument(
        "--show-files",
        action="store_true",
        help="Also print split filenames when metadata exposes them",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=0,
        help="Read and summarize N examples from --split after metadata inspection",
    )
    parser.add_argument(
        "--as-supervised",
        action="store_true",
        help="Use as_supervised=True when sampling through builder.as_dataset",
    )
    parser.add_argument(
        "--add-tfds-id",
        action="store_true",
        help="Add tfds_id while sampling through builder.as_dataset",
    )
    parser.add_argument(
        "--data-source",
        action="store_true",
        help="Inspect tfds.data_source instead of tf.data sampling",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.download and (args.manual_dir or args.max_examples_per_split is not None):
        parser.error("--manual-dir and --max-examples-per-split require --download")
    if args.sample < 0:
        parser.error("--sample must be non-negative")

    try:
        import tensorflow_datasets as tfds  # pylint: disable=import-outside-toplevel
    except Exception as exc:
        print(f"Failed to import tensorflow_datasets: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    try:
        builder_kwargs = _parse_builder_kwargs(args.builder_kwarg)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    if args.data_dir:
        builder_kwargs.setdefault("data_dir", args.data_dir)
    if args.file_format:
        builder_kwargs.setdefault("file_format", args.file_format)

    print(f"tensorflow_datasets_version: {getattr(tfds, '__version__', '<unknown>')}")
    builder = tfds.builder(args.dataset, try_gcs=args.try_gcs, **builder_kwargs)

    if args.download:
        print(
            "download: enabled; calling builder.download_and_prepare() before inspection",
            file=sys.stderr,
        )
        download_kwargs: dict[str, Any] = {}
        if args.manual_dir or args.max_examples_per_split is not None:
            download_kwargs["download_config"] = tfds.download.DownloadConfig(
                manual_dir=args.manual_dir,
                max_examples_per_split=args.max_examples_per_split,
            )
        builder.download_and_prepare(**download_kwargs)

    _print_metadata(builder, split_expr=args.split, show_files=args.show_files)

    if args.data_source:
        # tfds.data_source accepts data_dir separately; remove it from builder_kwargs
        # to avoid passing duplicate data_dir into tfds.builder internally.
        data_source_builder_kwargs = dict(builder_kwargs)
        data_source_builder_kwargs.pop("data_dir", None)
        _inspect_data_source(
            tfds=tfds,
            dataset=args.dataset,
            split=args.split,
            data_dir=args.data_dir,
            download=args.download,
            builder_kwargs=data_source_builder_kwargs,
            try_gcs=args.try_gcs,
            sample=args.sample,
        )
    else:
        _inspect_tf_dataset(
            builder,
            split=args.split,
            sample=args.sample,
            as_supervised=args.as_supervised,
            add_tfds_id=args.add_tfds_id,
            tfds=tfds,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
