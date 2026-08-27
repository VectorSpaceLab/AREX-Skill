#!/usr/bin/env python3
"""Inspect a local OpenLLM-style model catalog tree without network access.

Examples:
  python inspect_model_catalog.py --root ./some-repo
  python inspect_model_catalog.py --root ./some-repo --json

The helper expects a Bentos layout under `<root>/bentoml/bentos/` and simply
lists model/version directories and alias files.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


@dataclass
class BentoEntry:
    model: str
    version: str
    path: str
    has_bento_yaml: bool
    aliases: list[str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root to inspect.")
    parser.add_argument("--json", action="store_true", help="Render the results as JSON.")
    return parser


def iter_entries(root: Path) -> Iterable[BentoEntry]:
    bentos_root = root / "bentoml" / "bentos"
    if not bentos_root.exists():
        return []
    entries: list[BentoEntry] = []
    for model_dir in sorted(p for p in bentos_root.iterdir() if p.is_dir()):
        for version_dir in sorted(p for p in model_dir.iterdir()):
            if version_dir.is_dir():
                aliases = []
                for alias_file in sorted(model_dir.iterdir()):
                    if alias_file.is_file() and alias_file.name != version_dir.name:
                        try:
                            target = alias_file.read_text().strip()
                        except OSError:
                            continue
                        if target == version_dir.name:
                            aliases.append(alias_file.name)
                entries.append(
                    BentoEntry(
                        model=model_dir.name,
                        version=version_dir.name,
                        path=str(version_dir),
                        has_bento_yaml=(version_dir / "bento.yaml").exists(),
                        aliases=aliases,
                    )
                )
    return entries


def main() -> int:
    args = build_parser().parse_args()
    entries = list(iter_entries(args.root))
    payload = [asdict(entry) for entry in entries]
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False))
    else:
        if not entries:
            print("No bentos found.")
        for entry in entries:
            print(f"{entry.model}:{entry.version}  yaml={entry.has_bento_yaml}  aliases={','.join(entry.aliases) or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
