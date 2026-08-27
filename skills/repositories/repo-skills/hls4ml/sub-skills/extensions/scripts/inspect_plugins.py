#!/usr/bin/env python3
"""Inspect hls4ml backend plugin discovery without importing plugin modules.

The script reports the entry point group, the environment variable used for
ad hoc plugin modules, statically discovered built-in backend names, advertised
entry points, and raw environment module names. It never loads plugin modules.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from importlib import metadata
from pathlib import Path
from typing import Iterable

ENTRY_POINT_GROUP = 'hls4ml.backends'
ENV_PLUGIN_MODULES = 'HLS4ML_BACKEND_PLUGINS'


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Inspect hls4ml backend plugin discovery without importing plugin modules.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--json', action='store_true', help='Emit JSON instead of human-readable text.')
    return parser.parse_args(argv)


def _find_package_file(relative_path: str) -> Path | None:
    try:
        dist = metadata.distribution('hls4ml')
    except metadata.PackageNotFoundError:
        dist = None

    if dist is not None and dist.files is not None:
        for file in dist.files:
            if file.as_posix() == relative_path:
                candidate = Path(dist.locate_file(file))
                if candidate.is_file():
                    return candidate

    for parent in Path(__file__).resolve().parents:
        candidate = parent / relative_path
        if candidate.is_file():
            return candidate

    for base in map(Path, sys.path):
        candidate = base / relative_path
        if candidate.is_file():
            return candidate

    return None


def _discover_builtin_backends() -> list[str]:
    init_file = _find_package_file('hls4ml/backends/__init__.py')
    if init_file is None:
        return []

    try:
        tree = ast.parse(init_file.read_text(encoding='utf-8'), filename=str(init_file))
    except OSError:
        return []

    names: list[str] = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Name) and node.func.id == 'register_backend':
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    names.append(node.args[0].value.lower())
            self.generic_visit(node)

    Visitor().visit(tree)
    return sorted(dict.fromkeys(names))


def _discover_entry_points() -> list[dict[str, str]]:
    eps = metadata.entry_points()
    try:
        group_eps = eps.select(group=ENTRY_POINT_GROUP)
    except AttributeError:
        group_eps = eps.get(ENTRY_POINT_GROUP, [])  # type: ignore[assignment]

    discovered: list[dict[str, str]] = []
    for ep in group_eps:
        discovered.append({'name': ep.name, 'target': ep.value})
    return discovered


def _parse_env_modules() -> list[str]:
    raw = os.environ.get(ENV_PLUGIN_MODULES, '')
    if not raw:
        return []
    return [item for item in raw.split(os.pathsep) if item]


def build_report() -> dict[str, object]:
    return {
        'entry_point_group': ENTRY_POINT_GROUP,
        'env_var': ENV_PLUGIN_MODULES,
        'builtin_backends': _discover_builtin_backends(),
        'entry_points': _discover_entry_points(),
        'env_modules': _parse_env_modules(),
        'notes': [
            'This probe never imports plugin modules.',
            'Import hls4ml.backends only in a trusted environment when you want runtime registration.',
        ],
    }


def _format_text(report: dict[str, object]) -> str:
    lines = [
        'hls4ml backend plugin discovery',
        f"  entry point group : {report['entry_point_group']}",
        f"  env var           : {report['env_var']}",
    ]

    builtins = report['builtin_backends']
    if builtins:
        lines.append('  builtin backends   : ' + ', '.join(builtins))
    else:
        lines.append('  builtin backends   : not found')

    lines.append('  plugin entry points:')
    entry_points = report['entry_points']
    if entry_points:
        for ep in entry_points:
            lines.append(f"    - {ep['name']} -> {ep['target']}")
    else:
        lines.append('    - none')

    lines.append('  env modules (raw)  :')
    env_modules = report['env_modules']
    if env_modules:
        for module in env_modules:
            lines.append(f'    - {module}')
    else:
        lines.append('    - none')

    lines.append('  notes:')
    for note in report['notes']:
        lines.append(f'    - {note}')

    return '\n'.join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    report = build_report()

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_format_text(report))

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
