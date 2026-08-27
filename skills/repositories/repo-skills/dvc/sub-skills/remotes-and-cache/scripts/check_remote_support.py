#!/usr/bin/env python3
"""Inspect installed DVC optional remote backend support without network I/O.

This helper checks Python package metadata and import availability for DVC remote
backend distributions. It does not import dvc itself, open credentials, access
remote URLs, or perform provider/network operations.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from dataclasses import dataclass
from importlib import metadata
from typing import Iterable


@dataclass(frozen=True)
class Backend:
    schemes: tuple[str, ...]
    extra: str
    distribution: str
    import_name: str
    note: str = ""


BACKENDS: tuple[Backend, ...] = (
    Backend(("s3",), "s3", "dvc-s3", "dvc_s3"),
    Backend(("gs",), "gs", "dvc-gs", "dvc_gs"),
    Backend(("azure",), "azure", "dvc-azure", "dvc_azure"),
    Backend(("oss",), "oss", "dvc-oss", "dvc_oss"),
    Backend(("ssh",), "ssh", "dvc-ssh", "dvc_ssh", "Use extra ssh_gssapi only when GSSAPI auth is required."),
    Backend(("hdfs",), "hdfs", "dvc-hdfs", "dvc_hdfs"),
    Backend(("webdav", "webdavs"), "webdav", "dvc-webdav", "dvc_webdav"),
    Backend(("webhdfs",), "webhdfs", "dvc-webhdfs", "dvc_webhdfs", "Use extra webhdfs_kerberos only when Kerberos is required."),
)

CORE_SCHEMES = {"", "file", "local", "http", "https", "remote"}


def normalize_scheme(value: str) -> str:
    value = value.strip().lower()
    if "://" in value:
        value = value.split("://", 1)[0]
    return value


def dist_version(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def import_available(import_name: str) -> bool:
    return importlib.util.find_spec(import_name) is not None


def backend_for_scheme(scheme: str) -> Backend | None:
    for backend in BACKENDS:
        if scheme in backend.schemes:
            return backend
    return None


def iter_requested(args: argparse.Namespace) -> Iterable[str]:
    if args.all:
        for backend in BACKENDS:
            yield backend.schemes[0]
        return
    for scheme in args.scheme or []:
        yield normalize_scheme(scheme)


def print_core_scheme(scheme: str) -> None:
    if scheme in {"", "file", "local"}:
        print(f"{scheme or '<local path>'}: local filesystem support is built in; no DVC extra is required.")
    elif scheme in {"http", "https"}:
        print(f"{scheme}: HTTP(S) support is a core DVC dependency; verify network credentials separately.")
    elif scheme == "remote":
        print("remote: remote:// references another configured DVC remote; check the referenced remote's scheme.")


def print_backend(backend: Backend, scheme: str) -> bool:
    version = dist_version(backend.distribution)
    has_import = import_available(backend.import_name)
    install = f"pip install 'dvc[{backend.extra}]'"

    print(f"{scheme}: {backend.distribution} / {backend.import_name}")
    if version:
        print(f"  distribution: installed ({version})")
    else:
        print("  distribution: missing")
    print(f"  import: {'available' if has_import else 'missing'}")

    if version and has_import:
        print("  advice: backend package appears importable; credential and URL validation still require DVC commands.")
        ok = True
    else:
        print(f"  advice: install the narrow DVC extra with: {install}")
        ok = False
    if backend.note:
        print(f"  note: {backend.note}")
    return ok


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check installed Python support for DVC optional remote backends without network access."
    )
    parser.add_argument(
        "--scheme",
        action="append",
        help="Remote URL scheme or URL to check, for example s3, gs, azure, ssh, webdav://host/path.",
    )
    parser.add_argument("--all", action="store_true", help="Check every optional backend known to this skill.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when a requested optional backend is missing or unrecognized.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.all and not args.scheme:
        parser.error("provide --scheme <scheme> or --all")

    overall_ok = True
    for index, scheme in enumerate(iter_requested(args)):
        if index:
            print()
        if scheme in CORE_SCHEMES:
            print_core_scheme(scheme)
            continue
        backend = backend_for_scheme(scheme)
        if backend is None:
            print(f"{scheme}: not recognized by this helper")
            print("  advice: verify the URL scheme against DVC help and configuration before using it.")
            overall_ok = False
            continue
        if not print_backend(backend, scheme):
            overall_ok = False
    return 0 if (overall_ok or not args.strict) else 2


if __name__ == "__main__":
    raise SystemExit(main())
