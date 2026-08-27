#!/usr/bin/env python3
"""Check an Electricity Maps contrib Python environment without live network calls.

Examples:
    python scripts/check_environment.py --repo-root /path/to/electricitymaps-contrib
    python scripts/check_environment.py --repo-root . --check-optional

The script accepts --repo-root because parts of the repo lazily import parser
modules through top-level names such as ``parsers.FR``. Adding the checkout root
and ``electricitymap/contrib`` source root makes those imports explicit for
inspectors without embedding any machine-specific path in the generated skill.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import shutil
import sys
from pathlib import Path
from typing import Iterable


OPTIONAL_IMPORTS = [
    "requests",
    "pandas",
    "bs4",
    "lxml",
    "openpyxl",
    "xlrd",
    "odf",
    "cv2",
    "pytesseract",
    "pydataxm",
    "demjson3",
    "freezegun",
    "requests_mock",
    "syrupy",
    "testfixtures",
    "click",
    "ruff",
]


def add_repo_paths(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = Path(repo_root).expanduser().resolve()
    candidates = [root, root / "electricitymap" / "contrib", root / "libs" / "types" / "src"]
    for candidate in reversed(candidates):
        if candidate.exists():
            sys.path.insert(0, str(candidate))


def version_or_none(dist_name: str) -> str | None:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None


def import_optional(names: Iterable[str]) -> tuple[list[str], list[str]]:
    ok: list[str] = []
    missing: list[str] = []
    for name in names:
        try:
            importlib.import_module(name)
            ok.append(name)
        except Exception as exc:  # keep diagnostic broad for optional modules
            missing.append(f"{name} ({exc.__class__.__name__}: {exc})")
    return ok, missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Path to an electricitymaps-contrib checkout.")
    parser.add_argument(
        "--check-optional",
        action="store_true",
        help="Also import common parser/test optional dependencies.",
    )
    args = parser.parse_args()

    add_repo_paths(args.repo_root)

    print("== distribution metadata ==")
    for dist_name in ["electricitymap-contrib", "electricitymap-contrib-types"]:
        print(f"{dist_name}: {version_or_none(dist_name) or 'not-installed'}")

    try:
        from electricitymap.contrib import config
        from electricitymap.contrib.config.model import CONFIG_MODEL
        from electricitymap.contrib.parsers.lib.parsers import PARSER_DATA_TYPE_TO_DICT
        from electricitymap.contrib.types import ParserDataType
    except Exception as exc:
        print(f"ERROR: core imports failed: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        print(
            "Hint: install with `uv sync --extra parsers --group dev` or pass "
            "--repo-root so the checkout and libs/types source roots are importable.",
            file=sys.stderr,
        )
        return 1

    print("\n== config and parser registry ==")
    print(f"zones: {len(config.ZONES_CONFIG)}")
    print(f"exchanges: {len(config.EXCHANGES_CONFIG)}")
    print(f"parser data types: {len(PARSER_DATA_TYPE_TO_DICT)}")
    for data_type in [ParserDataType.PRODUCTION, ParserDataType.EXCHANGE, ParserDataType.PRODUCTION_CAPACITY]:
        print(f"{data_type.value} parsers: {len(PARSER_DATA_TYPE_TO_DICT[data_type])}")

    try:
        fn = CONFIG_MODEL.zones["DK-DK1"].parsers.get_function("production")
        print(f"lazy parser import DK-DK1 production: {fn.__module__}.{fn.__name__}")
    except Exception as exc:
        print(f"ERROR: lazy parser import failed: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        print(
            "Hint: this usually means the top-level `parsers` namespace is not importable; "
            "rerun with --repo-root or add <checkout>/electricitymap/contrib to PYTHONPATH.",
            file=sys.stderr,
        )
        return 1

    print("\n== distinctive console scripts on PATH ==")
    for script_name in ["test-parser", "test_parser", "capacity_update", "check", "format", "lint"]:
        print(f"{script_name}: {shutil.which(script_name) or 'not-on-PATH'}")

    if args.check_optional:
        print("\n== optional imports ==")
        ok, missing = import_optional(OPTIONAL_IMPORTS)
        print("ok: " + (", ".join(ok) if ok else "none"))
        if missing:
            print("missing:")
            for item in missing:
                print(f"  - {item}")
            return 2

    print("\nEnvironment check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
