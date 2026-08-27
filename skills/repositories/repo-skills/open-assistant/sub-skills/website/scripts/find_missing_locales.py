#!/usr/bin/env python3
"""Read-only locale audit for the Open-Assistant website.

Compares website/public/locales/en/*.json with other locale JSON files and
prints missing namespace files, missing nested keys, and values that are exactly
identical to English and therefore may be untranslated. The script never writes
files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit website locale JSON files against English reference files.")
    parser.add_argument("--repo-root", required=True, type=Path, help="Path to the Open-Assistant repository root.")
    parser.add_argument(
        "--lang",
        action="append",
        default=[],
        help="Language to audit. May be repeated or comma-separated. Defaults to every locale except en.",
    )
    return parser.parse_args()


def selected_langs(raw_langs: Iterable[str]) -> set[str]:
    langs: set[str] = set()
    for raw in raw_langs:
        for part in raw.split(","):
            lang = part.strip()
            if lang:
                langs.add(lang)
    return langs


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten nested dictionaries using dotted paths; keep lists/primitives as leaf values."""
    if not isinstance(value, dict):
        return {prefix or "<root>": value}
    out: dict[str, Any] = {}
    for key, child in value.items():
        child_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(child, dict):
            out.update(flatten(child, child_key))
        else:
            out[child_key] = child
    return out


def locale_dirs(locales_root: Path, wanted: set[str]) -> list[Path]:
    if wanted:
        return [locales_root / lang for lang in sorted(wanted)]
    return sorted(p for p in locales_root.iterdir() if p.is_dir() and p.name != "en")


def print_list(label: str, values: list[str], max_items: int) -> None:
    if not values:
        return
    shown = values[:max_items]
    suffix = "" if len(values) <= max_items else f" ... (+{len(values) - max_items} more)"
    print(f"  {label} ({len(values)}): {', '.join(shown)}{suffix}")


def audit_locale(en_files: list[Path], lang_dir: Path, max_items: int) -> tuple[int, int, int]:
    missing_files = 0
    missing_keys = 0
    untranslated = 0

    if not lang_dir.exists() or not lang_dir.is_dir():
        print(f"[{lang_dir.name}] missing locale directory")
        return len(en_files), 0, 0

    printed_lang_header = False
    for en_file in en_files:
        target_file = lang_dir / en_file.name
        if not target_file.exists():
            if not printed_lang_header:
                print(f"[{lang_dir.name}]")
                printed_lang_header = True
            print(f"  missing file: {en_file.name}")
            missing_files += 1
            continue

        try:
            en_json = load_json(en_file)
            target_json = load_json(target_file)
        except json.JSONDecodeError as exc:
            if not printed_lang_header:
                print(f"[{lang_dir.name}]")
                printed_lang_header = True
            print(f"  invalid json in {target_file.name}: {exc}")
            continue

        en_flat = flatten(en_json)
        target_flat = flatten(target_json)
        file_missing = sorted(k for k in en_flat if k not in target_flat)
        file_untranslated = sorted(k for k in en_flat if k in target_flat and target_flat[k] == en_flat[k])

        if file_missing or file_untranslated:
            if not printed_lang_header:
                print(f"[{lang_dir.name}]")
                printed_lang_header = True
            print(f"  {target_file.name}")
            print_list("missing keys", file_missing, max_items)
            print_list("potentially untranslated", file_untranslated, max_items)
            missing_keys += len(file_missing)
            untranslated += len(file_untranslated)

    return missing_files, missing_keys, untranslated


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    locales_root = repo_root / "website" / "public" / "locales"
    en_root = locales_root / "en"

    if not locales_root.is_dir():
        print(f"error: locale root not found: {locales_root}", file=sys.stderr)
        return 2
    if not en_root.is_dir():
        print(f"error: English reference locale not found: {en_root}", file=sys.stderr)
        return 2

    en_files = sorted(en_root.glob("*.json"))
    if not en_files:
        print(f"error: no English reference JSON files found under {en_root}", file=sys.stderr)
        return 2

    wanted = selected_langs(args.lang)
    totals = {"files": 0, "keys": 0, "untranslated": 0}
    audited = 0
    for lang_dir in locale_dirs(locales_root, wanted):
        if lang_dir.name == "en":
            continue
        audited += 1
        missing_files, missing_keys, untranslated = audit_locale(en_files, lang_dir, max_items=40)
        totals["files"] += missing_files
        totals["keys"] += missing_keys
        totals["untranslated"] += untranslated

    print(
        "summary: "
        f"audited={audited} missing_files={totals['files']} "
        f"missing_keys={totals['keys']} potentially_untranslated={totals['untranslated']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
