#!/usr/bin/env python3
"""Assemble safe `tfds build` commands without executing them.

The helper is intentionally conservative: by default it emits a top-level
`--dry_run=True`, an explicit temporary `--data_dir`, and
`--max_examples_per_split=1`. It does not import TensorFlow Datasets and it does
not run the generated command.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Sequence

FILE_FORMATS = ("tfrecord", "riegeli", "array_record", "parquet")


def _default_data_dir() -> str:
    return str(Path(tempfile.gettempdir()) / "tfds-build-data")


def _quote_command(argv: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in argv)


def _add_bool(argv: list[str], flag: str, value: bool) -> None:
    if value:
        argv.append(f"{flag}=True")


def build_tfds_build_command(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    """Builds the argv list and safety notes for a `tfds build` command."""
    notes: list[str] = []

    if args.current_dir and args.datasets:
        raise ValueError("Use either positional datasets or --current-dir, not both.")
    if args.exclude_datasets and (args.datasets or args.current_dir):
        raise ValueError("--exclude-datasets cannot be combined with explicit datasets/current-dir.")
    if args.use_dataset_flag and args.current_dir:
        raise ValueError("--use-dataset-flag cannot be combined with --current-dir.")
    if not args.current_dir and not args.datasets and not args.exclude_datasets:
        raise ValueError("Provide at least one dataset, pass --current-dir, or use --exclude-datasets.")
    if args.download_only and args.register_checksums:
        raise ValueError("TFDS rejects --download_only=True with --register_checksums=True.")
    if args.overwrite and args.fail_if_exists:
        raise ValueError("--overwrite=True and --fail_if_exists=True express opposite policies.")
    if args.full_build and args.max_examples_per_split is not None:
        raise ValueError("Use either --full-build or --max-examples-per-split, not both.")
    if args.no_dry_run and args.full_build and not args.allow_full_build:
        raise ValueError("Execution-ready full builds require --allow-full-build.")
    if args.no_dry_run and args.overwrite and not args.allow_overwrite:
        raise ValueError("Execution-ready overwrite commands require --allow-overwrite.")
    if args.no_dry_run and args.publish_dir and not args.allow_publish:
        raise ValueError("Execution-ready publish commands require --allow-publish.")

    argv: list[str] = [args.tfds_bin]
    if not args.no_dry_run:
        argv.append("--dry_run=True")
        notes.append("dry_run is enabled; the generated command prints parsed arguments and exits")
    else:
        notes.append("dry_run is disabled; review side effects before running")

    argv.append("build")

    if args.use_dataset_flag:
        # Put --dataset at the end because it consumes a list of following values.
        delayed_dataset_values = list(args.datasets)
    else:
        delayed_dataset_values = []
        argv.extend(args.datasets)

    argv.extend(["--data_dir", args.data_dir])
    notes.append("data_dir is explicit")

    if args.download_dir:
        argv.extend(["--download_dir", args.download_dir])
    if args.extract_dir:
        argv.extend(["--extract_dir", args.extract_dir])
    if args.manual_dir:
        argv.extend(["--manual_dir", args.manual_dir])
    _add_bool(argv, "--add_name_to_manual_dir", args.add_name_to_manual_dir)

    if not args.full_build:
        max_examples = 1 if args.max_examples_per_split is None else args.max_examples_per_split
        argv.extend(["--max_examples_per_split", str(max_examples)])
        notes.append(f"max_examples_per_split={max_examples} bounds generation")
    else:
        notes.append("full build requested; no max_examples_per_split limit is emitted")

    if args.config is not None:
        argv.extend(["--config", args.config])
    if args.config_idx is not None:
        argv.extend(["--config_idx", str(args.config_idx)])
    if args.imports:
        argv.extend(["--imports", args.imports])
    if args.download_config:
        # Validate that the string is JSON so the generated command is reviewable.
        json.loads(args.download_config)
        argv.extend(["--download_config", args.download_config])
    if args.file_format:
        argv.extend(["--file_format", args.file_format])
    if args.max_shard_size_mb is not None:
        argv.extend(["--max_shard_size_mb", str(args.max_shard_size_mb)])
    if args.num_shards is not None:
        argv.extend(["--num_shards", str(args.num_shards)])
    if args.num_processes != 1:
        argv.extend(["--num-processes", str(args.num_processes)])
        notes.append("parallel build processes may increase resource use and make build order nondeterministic")

    _add_bool(argv, "--download_only", args.download_only)
    _add_bool(argv, "--register_checksums", args.register_checksums)
    _add_bool(argv, "--force_checksums_validation", args.force_checksums_validation)
    _add_bool(argv, "--overwrite", args.overwrite)
    _add_bool(argv, "--fail_if_exists", args.fail_if_exists)
    _add_bool(argv, "--update_metadata_only", args.update_metadata_only)
    _add_bool(argv, "--nondeterministic_order", args.nondeterministic_order)
    _add_bool(argv, "--skip_if_published", args.skip_if_published)
    _add_bool(argv, "--experimental_latest_version", args.experimental_latest_version)

    if args.beam_pipeline_options:
        argv.extend(["--beam_pipeline_options", args.beam_pipeline_options])
        notes.append("Beam runner semantics are not validated by this helper")
    if args.publish_dir:
        argv.extend(["--publish_dir", args.publish_dir])
        notes.append("publish_dir causes a post-build copy when dry_run is disabled")
    if args.exclude_datasets:
        argv.extend(["--exclude_datasets", args.exclude_datasets])

    if args.use_dataset_flag:
        if not delayed_dataset_values:
            raise ValueError("--use-dataset-flag requires one or more dataset names.")
        argv.append("--dataset")
        argv.extend(delayed_dataset_values)

    return argv, notes


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assemble a safe `tfds build` command without executing it.",
    )
    parser.add_argument("datasets", nargs="*", help="Dataset names, local folders, or builder scripts.")
    parser.add_argument("--current-dir", action="store_true", help="Build the current directory by emitting no dataset selector.")
    parser.add_argument("--tfds-bin", default="tfds", help="CLI executable name to place at the start of the command.")
    parser.add_argument("--data-dir", default=_default_data_dir(), help="Explicit TFDS data_dir to emit.")
    parser.add_argument("--download-dir", help="Explicit download directory.")
    parser.add_argument("--extract-dir", help="Explicit extraction directory.")
    parser.add_argument("--manual-dir", help="Explicit manual-download directory.")
    parser.add_argument("--add-name-to-manual-dir", action="store_true", help="Emit --add_name_to_manual_dir=True.")
    parser.add_argument("--use-dataset-flag", action="store_true", help="Emit datasets through --dataset instead of positional args.")

    config_group = parser.add_mutually_exclusive_group()
    config_group.add_argument("--config", help="Builder config name or JSON config object.")
    config_group.add_argument("--config-idx", type=int, help="Builder config index to emit as --config_idx.")

    limit_group = parser.add_mutually_exclusive_group()
    limit_group.add_argument("--max-examples-per-split", type=int, default=None, help="Prototype example limit; default is 1 when --full-build is absent.")
    limit_group.add_argument("--full-build", action="store_true", help="Omit --max_examples_per_split.")

    parser.add_argument("--imports", help="Comma-separated modules to import for dataset registration.")
    parser.add_argument("--download-config", help="JSON string forwarded to TFDS DownloadConfig.")
    parser.add_argument("--file-format", choices=FILE_FORMATS, help="Output file format for generated examples.")
    parser.add_argument("--max-shard-size-mb", type=int, help="Maximum shard size in MB.")
    parser.add_argument("--num-shards", type=int, help="Forced number of shards.")
    parser.add_argument("--num-processes", type=int, default=1, help="Parallel dataset build processes.")
    parser.add_argument("--beam-pipeline-options", help="Comma-separated Beam PipelineOptions payload.")
    parser.add_argument("--publish-dir", help="Optional publish root.")
    parser.add_argument("--exclude-datasets", help="Comma-separated datasets to exclude when building all others.")

    parser.add_argument("--download-only", action="store_true", help="Emit --download_only=True.")
    parser.add_argument("--register-checksums", action="store_true", help="Emit --register_checksums=True.")
    parser.add_argument("--force-checksums-validation", action="store_true", help="Emit --force_checksums_validation=True.")
    parser.add_argument("--overwrite", action="store_true", help="Emit --overwrite=True; dangerous without a staging data_dir.")
    parser.add_argument("--fail-if-exists", action="store_true", help="Emit --fail_if_exists=True.")
    parser.add_argument("--update-metadata-only", action="store_true", help="Emit --update_metadata_only=True.")
    parser.add_argument("--nondeterministic-order", action="store_true", help="Emit --nondeterministic_order=True.")
    parser.add_argument("--skip-if-published", action="store_true", help="Emit --skip_if_published=True.")
    parser.add_argument("--experimental-latest-version", action="store_true", help="Emit --experimental_latest_version=True.")

    parser.add_argument("--no-dry-run", action="store_true", help="Do not emit top-level --dry_run=True.")
    parser.add_argument("--allow-full-build", action="store_true", help="Required with --no-dry-run --full-build.")
    parser.add_argument("--allow-overwrite", action="store_true", help="Required with --no-dry-run --overwrite.")
    parser.add_argument("--allow-publish", action="store_true", help="Required with --no-dry-run --publish-dir.")
    parser.add_argument("--json", action="store_true", help="Print JSON with argv, command, and safety notes.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        command, notes = build_tfds_build_command(args)
    except Exception as exc:  # argparse-friendly error display
        parser.error(str(exc))
        return 2

    if args.json:
        print(json.dumps({"argv": command, "command": _quote_command(command), "notes": notes}, indent=2))
    else:
        print(_quote_command(command))
        if notes:
            print("\nNotes:", file=sys.stderr)
            for note in notes:
                print(f"- {note}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
