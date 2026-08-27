#!/usr/bin/env python3
"""Safe smoke checks for DVC's public Python API.

This helper imports DVC, prints version/API availability, and optionally probes
user-supplied repository metadata or reads a user-supplied tracked file. It does
not download or materialize directories by default; data access happens only when
--path is provided.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from collections.abc import Callable
from typing import Any


def _json_default(value: Any) -> str:
    return repr(value)


def _print_json(label: str, value: Any) -> None:
    print(f"\n[{label}]")
    print(json.dumps(value, indent=2, sort_keys=True, default=_json_default))


def _import_dvc() -> tuple[Any, Any]:
    try:
        import dvc
        import dvc.api
    except Exception as exc:  # noqa: BLE001 - user-facing smoke helper
        raise SystemExit(f"failed to import dvc/dvc.api: {exc}") from exc
    return dvc, dvc.api


def _metadata_distribution() -> dict[str, str | None]:
    try:
        version = importlib.metadata.version("dvc")
    except importlib.metadata.PackageNotFoundError:
        version = None
    return {"distribution": "dvc", "metadata_version": version}


def _call_optional(label: str, fn: Callable[[], Any], *, quiet: bool) -> None:
    try:
        _print_json(label, fn())
    except Exception as exc:  # noqa: BLE001 - report and continue by design
        if quiet:
            return
        print(f"\n[{label}] skipped/failed: {type(exc).__name__}: {exc}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect DVC's public Python API and optionally read one explicitly "
            "provided DVC-tracked file. No downloads or directory materialization "
            "are performed unless DVC itself must stream the requested --path."
        )
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="Local DVC repo path or Git URL. Defaults to DVC discovery from cwd.",
    )
    parser.add_argument(
        "--rev",
        default=None,
        help="Git revision, tag, branch, commit, or DVC experiment name to inspect.",
    )
    parser.add_argument(
        "--remote",
        default=None,
        help="DVC remote name for data URL/stream resolution.",
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Optional DVC-tracked file path to inspect/read. Directories are not materialized.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Text encoding for --path reads. Use --binary for byte reads.",
    )
    parser.add_argument(
        "--binary",
        action="store_true",
        help="Read --path in binary mode and report byte count instead of text preview.",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=4096,
        help="Maximum bytes/characters to read from --path for the preview. Default: 4096.",
    )
    parser.add_argument(
        "--show-url",
        action="store_true",
        help="Resolve dvc.api.get_url() for --path. This does not verify storage existence.",
    )
    parser.add_argument(
        "--show-params",
        action="store_true",
        help="Call dvc.api.params_show() for the selected repo/rev.",
    )
    parser.add_argument(
        "--show-metrics",
        action="store_true",
        help="Call dvc.api.metrics_show() for the selected repo/rev.",
    )
    parser.add_argument(
        "--show-experiments",
        action="store_true",
        help="Call dvc.api.exp_show() for the selected repo.",
    )
    parser.add_argument(
        "--fs-ls",
        default=None,
        metavar="PATH",
        help="List a repo path with dvc.api.DVCFileSystem without downloading files.",
    )
    parser.add_argument(
        "--quiet-optional-errors",
        action="store_true",
        help="Suppress stderr messages for optional params/metrics/experiments/list probes.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_bytes < 0:
        raise SystemExit("--max-bytes must be non-negative")

    dvc, api = _import_dvc()
    package_info = _metadata_distribution() | {
        "import": "dvc",
        "import_version": getattr(dvc, "__version__", None),
        "has_api_open": hasattr(api, "open"),
        "has_api_read": hasattr(api, "read"),
        "has_get_url": hasattr(api, "get_url"),
        "has_dvc_filesystem": hasattr(api, "DVCFileSystem"),
    }
    _print_json("package", package_info)

    common = {"repo": args.repo, "rev": args.rev, "remote": args.remote}

    if args.path:
        if args.show_url:
            _call_optional(
                "get_url",
                lambda: {"path": args.path, "url": api.get_url(args.path, **common)},
                quiet=args.quiet_optional_errors,
            )

        mode = "rb" if args.binary else "r"
        read_kwargs = common | {"mode": mode}
        if not args.binary:
            read_kwargs["encoding"] = args.encoding

        try:
            with api.open(args.path, **read_kwargs) as stream:
                preview = stream.read(args.max_bytes)
        except Exception as exc:  # noqa: BLE001 - user-facing smoke helper
            print(f"\n[read] failed: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2

        if args.binary:
            _print_json("read", {"path": args.path, "mode": mode, "bytes_read": len(preview)})
        else:
            _print_json(
                "read",
                {
                    "path": args.path,
                    "mode": mode,
                    "characters_read": len(preview),
                    "preview": preview,
                },
            )
    elif args.show_url:
        print("\n[get_url] skipped: --show-url requires --path", file=sys.stderr)

    repo_rev_kwargs = {"repo": args.repo, "rev": args.rev}
    if args.show_params:
        _call_optional(
            "params_show",
            lambda: api.params_show(**repo_rev_kwargs),
            quiet=args.quiet_optional_errors,
        )
    if args.show_metrics:
        _call_optional(
            "metrics_show",
            lambda: api.metrics_show(**repo_rev_kwargs),
            quiet=args.quiet_optional_errors,
        )
    if args.show_experiments:
        _call_optional(
            "exp_show",
            lambda: api.exp_show(repo=args.repo, revs=args.rev),
            quiet=args.quiet_optional_errors,
        )
    if args.fs_ls is not None:
        def list_with_fs() -> list[dict[str, Any]]:
            fs = api.DVCFileSystem(repo=args.repo, rev=args.rev, remote=args.remote)
            try:
                entries = fs.ls(args.fs_ls, detail=True)
                return [
                    {
                        "name": entry.get("name"),
                        "type": entry.get("type"),
                        "size": entry.get("size"),
                        "is_dvc_output": bool(entry.get("dvc_info", {}).get("isout")),
                    }
                    for entry in entries
                ]
            finally:
                fs.close()

        _call_optional("fs_ls", list_with_fs, quiet=args.quiet_optional_errors)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
