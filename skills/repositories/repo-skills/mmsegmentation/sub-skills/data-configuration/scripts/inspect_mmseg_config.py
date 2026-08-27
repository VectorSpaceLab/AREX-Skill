#!/usr/bin/env python3
"""Safely inspect an MMSegmentation MMEngine config."""

from __future__ import annotations

import argparse
import ast
import pprint
import sys
from pathlib import Path
from typing import Any, Iterable


class CfgOptionsAction(argparse.Action):
    """MMEngine DictAction when available, with a small fallback parser."""

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            try:
                from mmengine import DictAction as MMEngineDictAction
            except ImportError:
                from mmengine.config import DictAction as MMEngineDictAction

            action = MMEngineDictAction(
                option_strings=self.option_strings,
                dest=self.dest,
                nargs=self.nargs,
                const=self.const,
                default=self.default,
                type=self.type,
                choices=self.choices,
                required=self.required,
                help=self.help,
                metavar=self.metavar,
            )
            action(parser, namespace, values, option_string)
            return
        except Exception:
            parsed = {}
            for item in values:
                if '=' not in item:
                    parser.error(
                        f'{option_string} expects key=value entries; got {item!r}')
                key, raw_value = item.split('=', 1)
                parsed[key] = _parse_value(raw_value)
            setattr(namespace, self.dest, parsed)


def _parse_value(raw_value: str) -> Any:
    try:
        return ast.literal_eval(raw_value)
    except Exception:
        if ',' in raw_value and not raw_value.startswith(('"', "'")):
            return [_parse_value(part) for part in raw_value.split(',')]
        return raw_value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Inspect an MMSegmentation config without writing default example files.')
    parser.add_argument(
        '--config', required=True, help='Path to the MMEngine config file.')
    parser.add_argument(
        '--cfg-options',
        nargs='+',
        action=CfgOptionsAction,
        help='Override config fields with key=value pairs, e.g. a.b=1.')
    parser.add_argument(
        '--show-keys',
        nargs='*',
        default=None,
        metavar='KEY',
        help=('Show only top-level keys when passed without values, or show '
              'selected dotted keys such as train_dataloader.dataset.'))
    parser.add_argument(
        '--dump',
        default=None,
        help='Optional output config path. Nothing is written unless this is set.')
    return parser.parse_args()


def _resolve_key(config: Any, dotted_key: str) -> Any:
    current = config
    for part in dotted_key.split('.'):
        if isinstance(current, (list, tuple)):
            try:
                current = current[int(part)]
            except (ValueError, IndexError) as exc:
                raise KeyError(dotted_key) from exc
        elif isinstance(current, dict):
            if part not in current:
                raise KeyError(dotted_key)
            current = current[part]
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            raise KeyError(dotted_key)
    return current


def _format_value(value: Any) -> str:
    if hasattr(value, 'pretty_text'):
        return value.pretty_text
    return pprint.pformat(value, width=100, sort_dicts=False)


def _print_selected(config: Any, keys: Iterable[str]) -> int:
    missing = []
    for key in keys:
        try:
            value = _resolve_key(config, key)
        except KeyError:
            missing.append(key)
            continue
        print(f'## {key}')
        print(_format_value(value))
    if missing:
        print('Missing keys: ' + ', '.join(missing), file=sys.stderr)
        return 1
    return 0


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    if not config_path.is_file():
        print(f'Config path does not exist or is not a file: {config_path}', file=sys.stderr)
        return 2

    try:
        from mmengine import Config
    except Exception as exc:
        print(f'Failed to import mmengine.Config: {exc}', file=sys.stderr)
        return 2

    try:
        from mmseg.utils import register_all_modules
        register_all_modules(init_default_scope=False)
    except Exception as exc:
        print(f'Warning: could not register mmseg modules before config load: {exc}', file=sys.stderr)

    try:
        cfg = Config.fromfile(str(config_path))
        if args.cfg_options:
            cfg.merge_from_dict(args.cfg_options)
    except Exception as exc:
        print(f'Failed to load or merge config: {exc}', file=sys.stderr)
        return 2

    exit_code = 0
    if args.show_keys is not None:
        if len(args.show_keys) == 0:
            print('Top-level keys:')
            for key in cfg.keys():
                print(f'- {key}')
        else:
            exit_code = _print_selected(cfg, args.show_keys)
    else:
        print(cfg.pretty_text)

    if args.dump:
        dump_path = Path(args.dump)
        if dump_path.parent != Path('.'):
            dump_path.parent.mkdir(parents=True, exist_ok=True)
        cfg.dump(str(dump_path))
        print(f'Dumped config to: {dump_path}')

    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
