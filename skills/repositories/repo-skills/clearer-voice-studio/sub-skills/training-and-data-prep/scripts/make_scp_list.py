#!/usr/bin/env python3
"""Create sorted one-path-per-line audio/video scp lists safely.

Dry-run is the default. Pass --write to create or overwrite the output file.
This script only scans the filesystem; it does not decode media or import repo
training modules.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Set

DEFAULT_EXTENSIONS = ".wav,.flac,.mp3,.m4a,.ogg,.opus,.aac,.aiff,.wma,.webm,.mp4,.avi,.mov,.mkv"


def parse_extensions(raw: str) -> Set[str]:
    exts: Set[str] = set()
    for item in raw.split(","):
        item = item.strip().lower()
        if not item:
            continue
        if not item.startswith("."):
            item = "." + item
        exts.add(item)
    return exts


def iter_files(root: Path, extensions: Set[str]) -> List[Path]:
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in extensions]
    return sorted(files, key=lambda p: str(p.resolve()).lower())


def format_path(path: Path, input_dir: Path, absolute: bool, relative_to: Path | None) -> str:
    if absolute:
        return str(path.resolve())
    if relative_to is not None:
        try:
            return str(path.resolve().relative_to(relative_to.resolve()))
        except ValueError:
            return str(path.resolve())
    try:
        return str(path.relative_to(input_dir))
    except ValueError:
        return str(path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a sorted one-path-per-line list for ClearerVoice-Studio inference or data-prep inputs. Dry-run is default.")
    parser.add_argument("--input-dir", required=True, help="Directory to scan recursively")
    parser.add_argument("--output-scp", required=True, help="Destination .scp/.lst path")
    parser.add_argument("--extensions", default=DEFAULT_EXTENSIONS, help="Comma-separated extensions to include")
    parser.add_argument("--absolute", action="store_true", help="Write absolute paths")
    parser.add_argument("--relative-to", help="Write paths relative to this directory; ignored if --absolute is set")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=True, help="Preview only; this is the default")
    parser.add_argument("--write", dest="dry_run", action="store_false", help="Actually write --output-scp")
    parser.add_argument("--json", action="store_true", help="Emit a JSON summary instead of text")
    args = parser.parse_args(argv)

    input_dir = Path(args.input_dir).expanduser().resolve()
    output_scp = Path(args.output_scp).expanduser()
    relative_to = Path(args.relative_to).expanduser().resolve() if args.relative_to else None
    extensions = parse_extensions(args.extensions)

    summary = {
        "input_dir": str(input_dir),
        "output_scp": str(output_scp),
        "extensions": sorted(extensions),
        "absolute": args.absolute,
        "relative_to": str(relative_to) if relative_to else None,
        "dry_run": args.dry_run,
        "count": 0,
        "preview": [],
        "written": False,
        "errors": [],
    }

    if not input_dir.is_dir():
        summary["errors"].append("--input-dir does not exist or is not a directory")
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            print(f"ERROR: {summary['errors'][0]}", file=sys.stderr)
        return 2

    files = iter_files(input_dir, extensions)
    lines = [format_path(path, input_dir, args.absolute, relative_to) for path in files]
    lines = sorted(lines)
    summary["count"] = len(lines)
    summary["preview"] = lines[:20]

    if not args.dry_run:
        output_scp.parent.mkdir(parents=True, exist_ok=True)
        output_scp.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        summary["written"] = True

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        action = "Would write" if args.dry_run else "Wrote"
        print(f"{action} {len(lines)} entries to {output_scp}")
        print(f"Input directory: {input_dir}")
        print(f"Extensions: {', '.join(sorted(extensions))}")
        if args.dry_run:
            print("Dry-run mode: pass --write to create the file.")
        if lines:
            print("Preview:")
            for line in lines[:20]:
                print(f"  {line}")
            if len(lines) > 20:
                print(f"  ... {len(lines) - 20} more")
        else:
            print("No matching files found.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
