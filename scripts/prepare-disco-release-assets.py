#!/usr/bin/env python3
"""Prepare installer files for attachment to a DisCo GitHub Release.

This command does not publish an npm package or upload a GitHub Release. It
creates an auditable asset directory containing the two stable installer
entry points, their SHA-256 manifest, and release metadata.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import NoReturn


PACKAGE_NAME = "@arex-skill/disco"
ASSET_NAMES = ("install-disco.sh", "install-disco.ps1")
FORBIDDEN_PATTERNS = (
    "@auto-ml-skills/disco",
    "@earendil-works/pi-coding-agent",
    "/root/github-repos/",
    "/root/.agents/",
    "/root/.disco/",
    "/root/github-repos/pi-to-disco",
)


def fail(message: str) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def package_version(root: Path) -> str:
    package_path = root / "cli" / "package.json"
    try:
        data = json.loads(package_path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot read {package_path}: {exc}")
    name = data.get("name")
    version = data.get("version")
    if name != PACKAGE_NAME:
        fail(f"{package_path} has package name {name!r}; expected {PACKAGE_NAME!r}")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail(f"{package_path} has an invalid release version: {version!r}")
    return version


def validate_asset(path: Path) -> None:
    if not path.is_file():
        fail(f"missing installer asset: {path}")
    text = path.read_text(encoding="utf-8")
    if PACKAGE_NAME not in text:
        fail(f"{path} does not target {PACKAGE_NAME}")
    for forbidden in FORBIDDEN_PATTERNS:
        if forbidden in text:
            fail(f"{path} contains forbidden stale or local reference: {forbidden}")


def main(argv: list[str] | None = None) -> int:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default=str(root / "dist" / "disco-release-assets"),
        help="Directory to write release assets (default: dist/disco-release-assets)",
    )
    args = parser.parse_args(argv)
    version = package_version(root)
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    checksums: list[str] = []
    for name in ASSET_NAMES:
        source = root / "scripts" / name
        validate_asset(source)
        destination = output_dir / name
        shutil.copyfile(source, destination)
        if name.endswith(".sh"):
            destination.chmod(0o755)
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        checksums.append(f"{digest}  {name}")

    (output_dir / "SHA256SUMS").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    (output_dir / "release-metadata.json").write_text(
        json.dumps(
            {
                "packageName": PACKAGE_NAME,
                "packageVersion": version,
                "assets": list(ASSET_NAMES),
                "checksumsFile": "SHA256SUMS",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Prepared DisCo installer assets for {PACKAGE_NAME}@{version} in {output_dir}")
    print(f"Attach {', '.join(ASSET_NAMES)} and SHA256SUMS to the matching GitHub Release.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
