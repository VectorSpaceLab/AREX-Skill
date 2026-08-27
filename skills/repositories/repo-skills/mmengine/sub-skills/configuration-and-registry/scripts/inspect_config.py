#!/usr/bin/env python3
"""Safely inspect an MMEngine config file or inline config string.

The script parses a config, optionally merges dotted key=value overrides, and
prints top-level keys. It does not build registry objects, run training, access
network resources, or write output files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any



def _import_config_api() -> tuple[Any, Any]:
    try:
        from mmengine.config import Config, DictAction
    except ModuleNotFoundError as exc:
        if exc.name == 'mmengine':
            raise RuntimeError(
                'MMEngine is not importable. Install mmengine in the active '
                'environment before parsing configs.'
            ) from exc
        raise
    return Config, DictAction


def _parse_value(raw: str) -> Any:
    _, DictAction = _import_config_api()
    return DictAction._parse_iterable(raw)


def _parse_override(override: str) -> tuple[str, Any]:
    if '=' not in override:
        raise ValueError(f'override must be KEY=VALUE, got {override!r}')
    key, raw_value = override.split('=', 1)
    key = key.strip()
    if not key:
        raise ValueError(f'override key is empty in {override!r}')
    return key, _parse_value(raw_value)


def _normalize_format(file_format: str) -> str:
    if file_format.startswith('.'):
        return file_format
    return f'.{file_format}'


def _load_config(args: argparse.Namespace) -> Any:
    Config, _ = _import_config_api()
    if args.from_string is not None:
        return Config.fromstring(args.from_string, _normalize_format(args.format))
    if args.config is None:
        raise ValueError('provide a config path or --from-string')
    return Config.fromfile(
        args.config,
        use_predefined_variables=not args.no_predefined_variables,
        import_custom_modules=not args.no_custom_imports,
        use_environment_variables=not args.no_environment_variables,
        lazy_import=args.lazy_import,
    )


def _summarize(value: Any) -> str:
    if isinstance(value, dict):
        keys = ', '.join(map(str, list(value.keys())[:8]))
        suffix = '' if len(value) <= 8 else ', ...'
        return f'dict[{len(value)}]({keys}{suffix})'
    if isinstance(value, (list, tuple)):
        return f'{type(value).__name__}[{len(value)}]'
    return type(value).__name__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Parse and inspect an MMEngine config without building objects.',
    )
    parser.add_argument(
        'config',
        nargs='?',
        help='Path to a Python, YAML, or JSON config file.',
    )
    parser.add_argument(
        '--from-string',
        help='Inline config text to parse instead of a file.',
    )
    parser.add_argument(
        '--format',
        default='py',
        help='Format for --from-string: py, yaml, yml, or json. Default: py.',
    )
    parser.add_argument(
        '--cfg-options',
        nargs='+',
        default=[],
        metavar='KEY=VALUE',
        help='Dotted overrides merged with Config.merge_from_dict.',
    )
    parser.add_argument(
        '--no-list-keys',
        action='store_true',
        help='Disallow numeric dotted keys from overriding list elements.',
    )
    parser.add_argument(
        '--no-predefined-variables',
        action='store_true',
        help='Disable predefined variables such as {{fileBasenameNoExtension}}.',
    )
    parser.add_argument(
        '--no-environment-variables',
        action='store_true',
        help='Disable {{$ENV:default}} substitution.',
    )
    parser.add_argument(
        '--no-custom-imports',
        action='store_true',
        help='Do not import modules listed in custom_imports.',
    )
    parser.add_argument(
        '--lazy-import',
        action=argparse.BooleanOptionalAction,
        default=None,
        help='Force or disable Config.fromfile lazy_import behavior.',
    )
    parser.add_argument(
        '--dump',
        action='store_true',
        help='Print the resolved config text after parsing and merging.',
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Print a machine-readable summary instead of text.',
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.config is not None and args.from_string is not None:
            raise ValueError('use either a config path or --from-string, not both')
        cfg = _load_config(args)

        overrides = dict(_parse_override(item) for item in args.cfg_options)
        if overrides:
            cfg.merge_from_dict(overrides, allow_list_keys=not args.no_list_keys)

        keys = list(cfg.keys())
        if args.json:
            payload = {
                'ok': True,
                'source': '<string>' if args.from_string is not None else str(Path(args.config)),
                'top_level_keys': keys,
                'summaries': {key: _summarize(cfg[key]) for key in keys},
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            source = '<string>' if args.from_string is not None else args.config
            print(f'Parsed MMEngine config: {source}')
            print(f'Top-level keys ({len(keys)}): {", ".join(map(str, keys))}')
            for key in keys:
                print(f'- {key}: {_summarize(cfg[key])}')

        if args.dump:
            print('\n--- Resolved Config ---')
            print(cfg.dump())

    except Exception as exc:  # noqa: BLE001 - command-line diagnostic boundary
        print(f'ERROR: {exc.__class__.__name__}: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
