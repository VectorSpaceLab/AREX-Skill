#!/usr/bin/env python3
"""Search and optionally copy legacy XTuner config-zoo files.

This helper is intentionally independent of XTuner imports.  It expects the
caller to provide an explicit config root that already exists on the local
machine, such as an exported legacy config-zoo directory or an installed
package's config directory.  By default it matches tokens against file names and
relative paths without reading config file bodies.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

CONFIG_SUFFIXES = {".py", ".json"}


@dataclass(frozen=True)
class ConfigHit:
    name: str
    relpath: str
    family: str
    suffix: str


def positive_int_or_zero(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if value < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return value


def discover_configs(config_root: Path) -> list[ConfigHit]:
    hits: list[ConfigHit] = []
    for path in config_root.rglob("*"):
        if not path.is_file() or path.suffix not in CONFIG_SUFFIXES:
            continue
        rel = path.relative_to(config_root)
        if any(part.startswith(".") or part == "__pycache__" for part in rel.parts):
            continue
        if path.name.startswith(("_", ".")):
            continue
        family = rel.parts[0] if len(rel.parts) > 1 else ""
        hits.append(
            ConfigHit(
                name=path.stem,
                relpath=rel.as_posix(),
                family=family,
                suffix=path.suffix,
            )
        )
    return sorted(hits, key=lambda hit: (hit.family, hit.relpath, hit.name))


def casefold_list(values: Iterable[str]) -> list[str]:
    return [value.casefold() for value in values if value]


def filter_hits(args: argparse.Namespace, hits: list[ConfigHit]) -> list[ConfigHit]:
    tokens = casefold_list([*args.tokens, *args.token])
    families = set(casefold_list(args.family))
    exact = args.exact.casefold() if args.exact else None

    filtered: list[ConfigHit] = []
    for hit in hits:
        name = hit.name.casefold()
        relpath = hit.relpath.casefold()
        family = hit.family.casefold()
        haystack = f"{name} {relpath} {family}"

        if families and family not in families:
            continue
        if exact and exact not in {name, relpath, Path(relpath).stem.casefold()}:
            continue
        if tokens:
            matched = [token in haystack for token in tokens]
            if args.match_mode == "all" and not all(matched):
                continue
            if args.match_mode == "any" and not any(matched):
                continue
        filtered.append(hit)
    return filtered


def format_table(hits: list[ConfigHit]) -> str:
    if not hits:
        return "No legacy config candidates matched."
    headers = ("name", "family", "relative path")
    name_width = max(len(headers[0]), *(len(hit.name) for hit in hits))
    family_width = max(len(headers[1]), *(len(hit.family) for hit in hits))
    lines = [
        f"{headers[0]:<{name_width}}  {headers[1]:<{family_width}}  {headers[2]}",
        f"{'-' * name_width}  {'-' * family_width}  {'-' * len(headers[2])}",
    ]
    for hit in hits:
        lines.append(f"{hit.name:<{name_width}}  {hit.family:<{family_width}}  {hit.relpath}")
    return "\n".join(lines)


def emit_hits(args: argparse.Namespace, hits: list[ConfigHit]) -> None:
    limited = hits if args.limit == 0 else hits[: args.limit]
    if args.format == "json":
        payload = {
            "total_matches": len(hits),
            "shown_matches": len(limited),
            "matches": [asdict(hit) for hit in limited],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif args.format == "names":
        for hit in limited:
            print(hit.name)
    else:
        print(format_table(limited))
        if args.limit and len(hits) > args.limit:
            print(f"... {len(hits) - args.limit} more matches hidden by --limit {args.limit}.")


def copy_single(args: argparse.Namespace, hits: list[ConfigHit], config_root: Path) -> int:
    if not args.copy_to:
        return 0
    if len(hits) != 1:
        print(
            "Refusing to copy: filters must select exactly one config "
            f"(matched {len(hits)}). Add --exact or more tokens.",
            file=sys.stderr,
        )
        return 2

    src = config_root / hits[0].relpath
    copy_dir = Path(args.copy_to).expanduser().resolve()
    copy_dir.mkdir(parents=True, exist_ok=True)
    dst = copy_dir / f"{src.stem}{args.copy_suffix}{src.suffix}"
    if dst.exists() and not args.overwrite:
        print(f"Refusing to overwrite existing file: {dst}", file=sys.stderr)
        return 2
    shutil.copyfile(src, dst)
    print(f"Copied {hits[0].name} -> {dst}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Find legacy XTuner config files by tokens without importing XTuner "
            "or assuming a source checkout."
        )
    )
    parser.add_argument(
        "--config-root",
        required=True,
        type=Path,
        help="Existing directory containing legacy XTuner config files.",
    )
    parser.add_argument(
        "tokens",
        nargs="*",
        help="Case-insensitive tokens matched against config names and relative paths.",
    )
    parser.add_argument(
        "--token",
        action="append",
        default=[],
        help="Additional token filter; may be repeated.",
    )
    parser.add_argument(
        "--match-mode",
        choices=("all", "any"),
        default="all",
        help="Whether all tokens or any token must match. Default: all.",
    )
    parser.add_argument(
        "--family",
        action="append",
        default=[],
        help="Restrict to a first-level config family such as internlm, qwen, or llava.",
    )
    parser.add_argument(
        "--exact",
        help="Select an exact config name, relative path, or path stem before optional copying.",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json", "names"),
        default="table",
        help="Output format. Default: table.",
    )
    parser.add_argument(
        "--limit",
        type=positive_int_or_zero,
        default=50,
        help="Maximum rows to print; 0 prints all matches. Default: 50.",
    )
    parser.add_argument(
        "--copy-to",
        type=Path,
        help="Copy the single selected config to this directory with a _copy suffix.",
    )
    parser.add_argument(
        "--copy-suffix",
        default="_copy",
        help="Suffix inserted before the extension when --copy-to is used. Default: _copy.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow --copy-to to overwrite an existing destination file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config_root = args.config_root.expanduser().resolve()
    if not config_root.is_dir():
        print(f"Config root does not exist or is not a directory: {config_root}", file=sys.stderr)
        return 2

    hits = discover_configs(config_root)
    matches = filter_hits(args, hits)
    emit_hits(args, matches)
    copy_status = copy_single(args, matches, config_root)
    if copy_status:
        return copy_status
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
