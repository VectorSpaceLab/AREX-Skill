#!/usr/bin/env python3
"""Safely inspect a ZIP-based upload without extracting it.

This mirrors the GeoNode upload safety contract for ZIP/KMZ/OOXML/ODF inputs:
member names, symlinks, entry count, expansion size, and compression ratios are
checked from the central directory. It is a preflight aid, not a replacement
for the deployed server's serializer and format handler.
"""
from __future__ import annotations

import argparse
import io
import os
import posixpath
import stat
import sys
import zipfile

MAX_ENTRIES = 10_000
MAX_TOTAL_UNCOMPRESSED = 2 * 1024 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100
MIN_COMPRESSED_FOR_RATIO_CHECK = 1024
MAX_TOTAL_COMPRESSION_RATIO = 100
MIN_TOTAL_COMPRESSED_FOR_RATIO_CHECK = 8 * 1024


class ArchiveValidationError(ValueError):
    """The archive has a structure unsafe for extraction."""


def check_name(name: str) -> None:
    if not name:
        raise ArchiveValidationError("empty archive entry name")
    if "\x00" in name:
        raise ArchiveValidationError(f"NUL byte in archive entry: {name!r}")
    if name.startswith(("/", "\\")) or (len(name) >= 2 and name[1] == ":"):
        raise ArchiveValidationError(f"absolute path in archive entry: {name!r}")
    normalized = name.replace("\\", "/")
    if any(part == ".." for part in normalized.split("/")):
        raise ArchiveValidationError(f"path traversal in archive entry: {name!r}")
    resolved = posixpath.normpath(normalized)
    if resolved == ".." or resolved.startswith("../"):
        raise ArchiveValidationError(f"path traversal in archive entry: {name!r}")


def validate(source: str | os.PathLike[str] | io.BytesIO) -> None:
    try:
        with zipfile.ZipFile(source) as archive:
            entries = archive.infolist()
    except (OSError, zipfile.BadZipFile) as exc:
        raise ArchiveValidationError(f"not a valid ZIP archive: {exc}") from exc

    if len(entries) > MAX_ENTRIES:
        raise ArchiveValidationError(f"archive has {len(entries)} entries; maximum is {MAX_ENTRIES}")

    total_uncompressed = 0
    total_compressed = 0
    for info in entries:
        check_name(info.filename)
        unix_mode = info.external_attr >> 16
        if unix_mode and stat.S_ISLNK(unix_mode):
            raise ArchiveValidationError(f"symlink entry is not allowed: {info.filename!r}")
        total_uncompressed += info.file_size
        total_compressed += info.compress_size
        if total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
            raise ArchiveValidationError("archive expands beyond the 2 GiB safety limit")
        if info.compress_size >= MIN_COMPRESSED_FOR_RATIO_CHECK and info.file_size:
            ratio = info.file_size / max(info.compress_size, 1)
            if ratio > MAX_COMPRESSION_RATIO:
                raise ArchiveValidationError(f"suspicious compression ratio for {info.filename!r}: {ratio:.0f}x")

    if total_compressed >= MIN_TOTAL_COMPRESSED_FOR_RATIO_CHECK and total_uncompressed:
        ratio = total_uncompressed / max(total_compressed, 1)
        if ratio > MAX_TOTAL_COMPRESSION_RATIO:
            raise ArchiveValidationError(f"suspicious cumulative compression ratio: {ratio:.0f}x")


def make_fixture(*entries: tuple[str, bytes, int | None]) -> io.BytesIO:
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data, mode in entries:
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED
            if mode is not None:
                info.external_attr = mode << 16
            archive.writestr(info, data)
    result.seek(0)
    return result


def self_test() -> None:
    validate(make_fixture(("data/feature.geojson", b'{"type":"Feature"}', None)))
    for label, fixture in (
        ("malformed archive", io.BytesIO(b"not a zip")),
        ("path traversal", make_fixture(("../escape.txt", b"x", None))),
        ("symlink", make_fixture(("link", b"target", stat.S_IFLNK | 0o777))),
    ):
        try:
            validate(fixture)
        except ArchiveValidationError:
            continue
        raise AssertionError(f"self-test failed to reject {label}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a ZIP/KMZ/OOXML/ODF upload without extracting it. "
            "Rejects traversal, absolute paths, symlinks, oversized expansion, "
            "and suspicious compression ratios. Use --self-test for a tiny fixture check."
        )
    )
    parser.add_argument("archive", nargs="?", help="archive file to inspect")
    parser.add_argument("--self-test", action="store_true", help="run clean, malformed, traversal, and symlink fixtures")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("self-test passed")
        return 0
    if not args.archive:
        parser.error("an archive path is required unless --self-test is used")
    try:
        validate(args.archive)
    except ArchiveValidationError as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        return 1
    print(f"ACCEPTED STRUCTURE: {args.archive}")
    print("This does not prove that the archive contains a valid GeoNode data format.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
