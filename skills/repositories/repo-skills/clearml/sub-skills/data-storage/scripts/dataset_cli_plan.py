#!/usr/bin/env python3
"""Build an offline clearml-data command sequence.

This helper prints shell commands only. It never imports ClearML, reads
credentials, or contacts a ClearML server.
"""

import argparse
import re
import shlex
import sys
from typing import Iterable, List, Optional, Sequence, Tuple

_STORAGE_SCHEMES = ("s3://", "gs://", "azure://")
_DEPRECATED_SCHEMES = ("http://", "https://")
_DATASET_ID_PLACEHOLDER = "DATASET_ID_FROM_CREATE"


def _split_mapping(value: str, option: str) -> Tuple[Optional[str], str]:
    if "=" not in value:
        return None, value
    folder, path = value.split("=", 1)
    folder = folder.strip()
    path = path.strip()
    if not folder or not path:
        raise argparse.ArgumentTypeError(
            "{} entries must be either PATH or DATASET_FOLDER=PATH".format(option)
        )
    return folder, path


def _storage_uri(value: str) -> str:
    value = value.strip()
    if not value:
        raise argparse.ArgumentTypeError("storage URI cannot be empty")
    if re.search(r"(?i)(access_key|secret|token|password)=", value):
        raise argparse.ArgumentTypeError(
            "storage URI appears to contain credentials; configure credentials outside the command"
        )
    return value


def _non_empty(value: str) -> str:
    value = value.strip()
    if not value:
        raise argparse.ArgumentTypeError("value cannot be empty")
    return value


def _quote_command(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts if part is not None)


def _base_dataset_id(args: argparse.Namespace) -> str:
    return args.existing_id or args.id_placeholder


def _create_command(args: argparse.Namespace) -> List[str]:
    if not args.name:
        raise ValueError("--name is required unless --existing-id is supplied")
    parts = ["clearml-data", "create"]
    if args.project:
        parts += ["--project", args.project]
    parts += ["--name", args.name]
    if args.version:
        parts += ["--version", args.version]
    if args.parents:
        parts += ["--parents"] + args.parents
    if args.storage:
        parts += ["--storage", args.storage]
    if args.tags:
        parts += ["--tags"] + args.tags
    return parts


def _add_command(dataset_id: str, dataset_folder: Optional[str], paths: Iterable[str], links: bool) -> List[str]:
    paths = list(paths)
    parts = ["clearml-data", "add", "--id", dataset_id]
    if dataset_folder:
        parts += ["--dataset-folder", dataset_folder]
    parts += ["--links" if links else "--files"] + paths
    return parts


def _sync_command(args: argparse.Namespace, folder: str, dataset_folder: Optional[str]) -> List[str]:
    parts = ["clearml-data", "sync", "--folder", folder]
    if args.existing_id:
        parts += ["--id", args.existing_id]
    else:
        if args.project:
            parts += ["--project", args.project]
        if args.name:
            parts += ["--name", args.name]
        if args.version:
            parts += ["--version", args.version]
        if args.parents:
            parts += ["--parents"] + args.parents
        if args.tags:
            parts += ["--tags"] + args.tags
    if dataset_folder:
        parts += ["--dataset-folder", dataset_folder]
    if args.storage:
        parts += ["--storage", args.storage]
    if args.skip_close:
        parts.append("--skip-close")
    if args.verbose:
        parts.append("--verbose")
    return parts


def build_commands(args: argparse.Namespace) -> List[List[str]]:
    if args.sync and (args.add or args.link):
        raise ValueError("Use either --sync or --add/--link in one plan, not both")
    if args.existing_id and args.parents:
        raise ValueError("--parents only applies when creating a new dataset")
    if args.no_uploads and (args.include_upload or args.include_close):
        raise ValueError("--no-uploads cannot be combined with --include-upload or --include-close")
    if args.close_disable_upload and not args.include_close:
        raise ValueError("--close-disable-upload requires --include-close")
    if args.skip_close and args.include_close:
        raise ValueError("--skip-close is only for sync plans and conflicts with --include-close")

    commands: List[List[str]] = []
    dataset_id = _base_dataset_id(args)

    if args.sync:
        for dataset_folder, folder in args.sync:
            commands.append(_sync_command(args, folder, dataset_folder))
        return commands

    if not args.existing_id:
        commands.append(_create_command(args))
    else:
        dataset_id = args.existing_id

    grouped_files = _group_mappings(args.add)
    grouped_links = _group_mappings(args.link)
    for dataset_folder, paths in grouped_files:
        commands.append(_add_command(dataset_id, dataset_folder, paths, links=False))
    for dataset_folder, paths in grouped_links:
        commands.append(_add_command(dataset_id, dataset_folder, paths, links=True))

    if args.include_upload:
        upload = ["clearml-data", "upload", "--id", dataset_id]
        if args.storage:
            upload += ["--storage", args.storage]
        if args.chunk_size is not None:
            upload += ["--chunk-size", str(args.chunk_size)]
        if args.max_workers is not None:
            upload += ["--max-workers", str(args.max_workers)]
        if args.verbose:
            upload.append("--verbose")
        commands.append(upload)

    if args.include_close:
        close = ["clearml-data", "close", "--id", dataset_id]
        if args.storage:
            close += ["--storage", args.storage]
        if args.close_disable_upload:
            close.append("--disable-upload")
        if args.chunk_size is not None:
            close += ["--chunk-size", str(args.chunk_size)]
        if args.max_workers is not None:
            close += ["--max-workers", str(args.max_workers)]
        if args.verbose:
            close.append("--verbose")
        commands.append(close)

    return commands


def _group_mappings(items: Sequence[Tuple[Optional[str], str]]) -> List[Tuple[Optional[str], List[str]]]:
    grouped: List[Tuple[Optional[str], List[str]]] = []
    for dataset_folder, path in items:
        for existing_folder, paths in grouped:
            if existing_folder == dataset_folder:
                paths.append(path)
                break
        else:
            grouped.append((dataset_folder, [path]))
    return grouped


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a safe clearml-data command sequence without executing it."
    )
    parser.add_argument("--project", type=_non_empty, help="Dataset project for create/sync plans")
    parser.add_argument("--name", type=_non_empty, help="Dataset name for create/sync plans")
    parser.add_argument("--version", type=_non_empty, help="Dataset version")
    parser.add_argument("--storage", type=_storage_uri, help="Remote storage URI such as s3://bucket/path")
    parser.add_argument("--parent", dest="parents", action="append", type=_non_empty, help="Parent dataset ID")
    parser.add_argument("--tag", dest="tags", action="append", type=_non_empty, help="Dataset tag")
    parser.add_argument(
        "--add",
        action="append",
        type=lambda value: _split_mapping(value, "--add"),
        default=[],
        help="Add local PATH or DATASET_FOLDER=PATH. Repeat for multiple paths.",
    )
    parser.add_argument(
        "--link",
        action="append",
        type=lambda value: _split_mapping(value, "--link"),
        default=[],
        help="Add external URI link or DATASET_FOLDER=URI. Repeat for multiple links.",
    )
    parser.add_argument(
        "--sync",
        action="append",
        type=lambda value: _split_mapping(value, "--sync"),
        default=[],
        help="Sync local FOLDER or DATASET_FOLDER=FOLDER. Repeat for multiple commands.",
    )
    parser.add_argument("--existing-id", type=_non_empty, help="Plan against an existing dataset ID instead of create")
    parser.add_argument(
        "--id-placeholder",
        default=_DATASET_ID_PLACEHOLDER,
        type=_non_empty,
        help="Placeholder used after create before the real ID is known",
    )
    parser.add_argument("--include-upload", action="store_true", help="Append a clearml-data upload command")
    parser.add_argument("--include-close", action="store_true", help="Append a clearml-data close command")
    parser.add_argument(
        "--close-disable-upload",
        action="store_true",
        help="Add --disable-upload to close, requiring a prior successful upload",
    )
    parser.add_argument("--no-uploads", action="store_true", help="Assert that no upload/close command should be emitted")
    parser.add_argument("--skip-close", action="store_true", help="Add --skip-close to sync commands")
    parser.add_argument("--chunk-size", type=int, help="Dataset artifact chunk size in MB; use -1 for single chunk")
    parser.add_argument("--max-workers", type=int, help="Worker count for upload/close commands")
    parser.add_argument("--verbose", action="store_true", help="Add --verbose to supported commands")
    parser.add_argument("--numbered", action="store_true", help="Print commands with step numbers")
    return parser.parse_args(argv)


def _warnings(args: argparse.Namespace) -> List[str]:
    warnings: List[str] = []
    if args.storage and args.storage.startswith(_STORAGE_SCHEMES):
        scheme = args.storage.split(":", 1)[0]
        warnings.append("# Requires configured {} credentials and the matching ClearML storage extra.".format(scheme))
    if args.storage and args.storage.startswith(_DEPRECATED_SCHEMES):
        warnings.append("# HTTP(S) storage may be read-only or server-dependent; verify upload support before running.")
    if not args.existing_id and (args.add or args.link or args.include_upload or args.include_close):
        warnings.append("# Replace {} with the id printed by clearml-data create.".format(args.id_placeholder))
    if args.no_uploads:
        warnings.append("# No upload or close commands emitted because --no-uploads was requested.")
    return warnings


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    try:
        commands = build_commands(args)
    except ValueError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2

    for warning in _warnings(args):
        print(warning)
    for index, command in enumerate(commands, 1):
        rendered = _quote_command(command)
        if args.numbered:
            print("{:02d}. {}".format(index, rendered))
        else:
            print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
