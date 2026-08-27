#!/usr/bin/env python3
"""List installed OpenCompass model and dataset config files.

This is a portable wrapper for skill users. It tries OpenCompass' own
``match_files`` helper first, then falls back to package-file discovery so it
can still inspect installed config package data when some utility imports fail.
"""

from __future__ import annotations

import argparse
import fnmatch
import importlib
import json
import os
import sys
from pathlib import Path
from typing import List, Sequence, Tuple

ConfigRow = Tuple[str, str]


def _normalize_patterns(patterns: Sequence[str]) -> List[str]:
    if not patterns:
        return ['*']
    return list(patterns)


def _match_text(text: str, patterns: Sequence[str], exact: bool) -> bool:
    if not patterns:
        return True
    lowered = text.lower()
    for pattern in patterns:
        pattern_lower = pattern.lower()
        if exact:
            if fnmatch.fnmatchcase(lowered, pattern_lower):
                return True
            continue
        if any(ch in pattern_lower for ch in '*?['):
            if fnmatch.fnmatchcase(lowered, pattern_lower):
                return True
        elif pattern_lower in lowered:
            return True
    return False


def _rows_from_match_files(kind: str, patterns: Sequence[str], exact: bool) -> List[ConfigRow]:
    if exact:
        return []
    try:
        from opencompass.utils import match_files  # type: ignore
    except Exception:
        return []

    root = f'opencompass/configs/{kind}/'
    try:
        rows = match_files(root, list(patterns), fuzzy=True)
    except Exception:
        return []
    return [(str(name), str(path)) for name, path in rows]


def _source_tree_roots(kind: str) -> List[Path]:
    roots: List[Path] = []
    candidates = [Path.cwd(), *Path.cwd().parents]
    script_path = Path(__file__).resolve()
    candidates.extend([script_path.parent, *script_path.parents])
    for candidate in candidates:
        config_root = candidate / 'opencompass' / 'configs' / kind
        if config_root.exists() and config_root not in roots:
            roots.append(config_root)
    return roots


def _config_roots(kind: str) -> List[Path]:
    roots: List[Path] = []
    try:
        package = importlib.import_module('opencompass')
    except Exception:
        package = None

    if package is not None:
        for package_root in getattr(package, '__path__', []):
            config_root = Path(package_root) / 'configs' / kind
            if config_root.exists():
                roots.append(config_root)
    roots.extend(root for root in _source_tree_roots(kind) if root not in roots)
    return roots


def _rows_from_package(kind: str, patterns: Sequence[str], exact: bool) -> List[ConfigRow]:
    base_paths = _config_roots(kind)
    if not base_paths:
        raise RuntimeError(
            f'Could not find opencompass/configs/{kind}. Is OpenCompass installed with configs?'
        )

    rows: List[ConfigRow] = []
    for base_path in base_paths:
        for file_path in base_path.rglob('*.py'):
            if file_path.name == '__init__.py':
                continue
            relative = file_path.relative_to(base_path)
            config_path = f'opencompass/configs/{kind}/{relative.as_posix()}'
            label = relative.with_suffix('').as_posix()
            searchable = f'{label} {config_path}'
            if _match_text(searchable, patterns, exact):
                rows.append((label, config_path))
    return sorted(set(rows), key=lambda row: row[1])


def _list_kind(kind: str, patterns: Sequence[str], exact: bool) -> List[ConfigRow]:
    rows = _rows_from_match_files(kind, patterns, exact)
    if rows:
        return sorted(set(rows), key=lambda row: row[1])
    return _rows_from_package(kind, patterns, exact)


def _format_table(title: str, rows: Sequence[ConfigRow]) -> str:
    if not rows:
        return f'{title}: no matches'
    name_width = max(len(title), *(len(row[0]) for row in rows), 4)
    path_width = max(*(len(row[1]) for row in rows), 11)
    lines = [title, f'  {"Name":<{name_width}}  Config Path', f'  {"-" * name_width}  {"-" * path_width}']
    lines.extend(f'  {name:<{name_width}}  {path}' for name, path in rows)
    return '\n'.join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='List installed OpenCompass model and dataset configs.')
    parser.add_argument('patterns', nargs='*', help='Substring or wildcard patterns. Defaults to *')
    parser.add_argument('--kind', choices=['all', 'models', 'datasets'], default='all')
    parser.add_argument('--format', choices=['table', 'json'], default='table')
    parser.add_argument('--exact', action='store_true', help='Use shell-style wildcard matching only')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    patterns = _normalize_patterns(args.patterns)
    kinds = ['models', 'datasets'] if args.kind == 'all' else [args.kind]

    output = {}
    for kind in kinds:
        output[kind] = _list_kind(kind, patterns, args.exact)

    if args.format == 'json':
        print(json.dumps({kind: [{'name': name, 'path': path} for name, path in rows]
                          for kind, rows in output.items()}, indent=2, sort_keys=True))
    else:
        print('\n\n'.join(_format_table(kind.title(), rows) for kind, rows in output.items()))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'error: {exc}', file=sys.stderr)
        raise SystemExit(2)
