#!/usr/bin/env python3
"""Inspect PaddleGAN export prefixes and confirm static files exist."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List, Optional


PDMODEL_SUFFIX = ".pdmodel"
PDPARAMS_SUFFIX = ".pdiparams"
PDPARAMS_INFO_SUFFIX = ".pdiparams.info"


def strip_export_suffix(path: Path) -> Path:
    text = str(path)
    for suffix in (PDPARAMS_INFO_SUFFIX, PDPARAMS_SUFFIX, PDMODEL_SUFFIX):
        if text.endswith(suffix):
            return Path(text[: -len(suffix)])
    return path


def artifact_paths(prefix: Path) -> Dict[str, Path]:
    prefix_text = str(prefix)
    return {
        "pdmodel": Path(prefix_text + PDMODEL_SUFFIX),
        "pdiparams": Path(prefix_text + PDPARAMS_SUFFIX),
        "info": Path(prefix_text + PDPARAMS_INFO_SUFFIX),
        "serving_client": prefix / "serving_client",
        "serving_server": prefix / "serving_server",
    }


def discover_prefixes(target: Path) -> List[Path]:
    if target.is_dir():
        prefixes = {strip_export_suffix(path) for path in target.rglob("*.pdmodel")}
        return sorted(prefixes, key=str)

    if target.exists():
        return [strip_export_suffix(target)]

    if any((Path(str(target) + suffix)).exists() for suffix in (PDMODEL_SUFFIX, PDPARAMS_SUFFIX, PDPARAMS_INFO_SUFFIX)):
        return [target]

    raise FileNotFoundError(f"export target not found: {target}")


def prefix_label(prefix: Path, root: Path) -> str:
    try:
        return str(prefix.relative_to(root))
    except ValueError:
        return prefix.name


def is_expected_match(prefix: Path, root: Path, expected: str) -> bool:
    candidates = {
        str(prefix),
        prefix.name,
        prefix_label(prefix, root),
        prefix_label(prefix, root).replace("\\", "/"),
    }
    return expected in candidates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check that a PaddleGAN export directory or prefix contains the expected static files.")
    parser.add_argument(
        "target",
        help="Export directory or model prefix to inspect.",
    )
    parser.add_argument(
        "--expect-prefix",
        action="append",
        default=[],
        help="Expected prefix name to confirm. Can be given multiple times.",
    )
    parser.add_argument(
        "--require-info",
        action="store_true",
        help="Fail if a .pdiparams.info file is missing for any checked prefix.",
    )
    parser.add_argument(
        "--require-serving",
        action="store_true",
        help="Fail if Serving client/server directories are missing for any checked prefix.",
    )
    return parser


def inspect_prefix(prefix: Path, require_info: bool, require_serving: bool) -> List[str]:
    report: List[str] = []
    artifacts = artifact_paths(prefix)
    pdmodel = artifacts["pdmodel"]
    pdiparams = artifacts["pdiparams"]
    info = artifacts["info"]
    client_dir = artifacts["serving_client"]
    server_dir = artifacts["serving_server"]

    missing = []
    if not pdmodel.exists():
        missing.append(".pdmodel")
    if not pdiparams.exists():
        missing.append(".pdiparams")
    if missing:
        raise FileNotFoundError(f"{prefix}: missing {' and '.join(missing)}")

    pdmodel_size = pdmodel.stat().st_size
    pdiparams_size = pdiparams.stat().st_size
    info_state = "present" if info.exists() else "missing"
    report.append(
        f"{prefix}: pdmodel={pdmodel_size} bytes, pdiparams={pdiparams_size} bytes, info={info_state}")

    if require_info and not info.exists():
        raise FileNotFoundError(f"{prefix}: missing .pdiparams.info")

    if require_serving:
        if not client_dir.exists() or not server_dir.exists():
            raise FileNotFoundError(
                f"{prefix}: missing Serving directories under {prefix.name}/")
        report.append(f"{prefix}: serving_client=present, serving_server=present")

    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    target = Path(args.target)
    prefixes = discover_prefixes(target)

    if not prefixes:
        parser.error(f"no export prefixes found under {args.target}")

    for expected in args.expect_prefix:
        if not any(is_expected_match(prefix, target if target.is_dir() else prefix.parent, expected) for prefix in prefixes):
            raise SystemExit(f"expected prefix not found: {expected}")

    print(f"Found {len(prefixes)} export prefix(es) under {target}")
    for prefix in prefixes:
        try:
            lines = inspect_prefix(prefix, args.require_info, args.require_serving)
        except Exception as exc:
            raise SystemExit(str(exc)) from exc
        for line in lines:
            print(line)

    if args.expect_prefix:
        print("All expected prefixes were found.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
