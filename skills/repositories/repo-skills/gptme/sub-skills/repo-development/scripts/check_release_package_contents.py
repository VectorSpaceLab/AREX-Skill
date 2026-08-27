#!/usr/bin/env python3
"""Validate that built wheel/sdist archives contain the expected runtime assets."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from pathlib import Path

REQUIRED_FILES = (
    "gptme/server/webui-dist/index.html",
    "gptme/server/static/index.html",
    "gptme/server/static/main.js",
    "gptme/eval/tbench/setup.sh",
    "media/logo.png",
)
REQUIRED_PREFIXES = (
    "gptme/server/webui-dist/assets/",
)


def archive_members(path: Path) -> set[str]:
    """Return normalized member names from a wheel or source archive."""
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return set(archive.namelist())
    if path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as archive:
            members = archive.getnames()
        return {name.split("/", 1)[-1] for name in members if "/" in name}
    raise ValueError(f"unsupported package archive: {path}")


def validate_package(path: Path) -> None:
    """Raise ValueError if the package is missing expected runtime assets."""
    members = archive_members(path)
    missing: list[str] = []

    for required in REQUIRED_FILES:
        if required not in members:
            missing.append(required)

    for prefix in REQUIRED_PREFIXES:
        if not any(name.startswith(prefix) for name in members):
            missing.append(f"{prefix}*")

    if not any(name.startswith("media/") and name.endswith(".wav") for name in members):
        missing.append("media/*.wav")

    if missing:
        raise ValueError(
            f"{path} is missing required bundled assets: {', '.join(missing)}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", nargs="+", type=Path, help="Wheel or sdist archives to inspect")
    args = parser.parse_args()

    try:
        for archive in args.archives:
            validate_package(archive)
            print(f"Validated bundled assets in {archive}")
    except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile) as error:
        parser.exit(1, f"error: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
