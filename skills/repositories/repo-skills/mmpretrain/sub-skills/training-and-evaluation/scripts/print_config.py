#!/usr/bin/env python3
"""Print a resolved MMPreTrain config.

This helper is safe to run as a preview step: it only reads a config file,
applies optional overrides, and prints the final merged config to stdout.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Any


def _split_top_level_commas(text: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    quote: str | None = None
    escape = False
    opening = {'[': ']', '(': ')', '{': '}'}
    closing = set(opening.values())

    for ch in text:
        if quote is not None:
            buf.append(ch)
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote:
                quote = None
            continue

        if ch in {'"', "'"}:
            quote = ch
            buf.append(ch)
            continue

        if ch in opening:
            depth += 1
        elif ch in closing and depth > 0:
            depth -= 1

        if ch == ',' and depth == 0:
            token = ''.join(buf).strip()
            if token:
                parts.append(token)
            buf = []
        else:
            buf.append(ch)

    token = ''.join(buf).strip()
    if token:
        parts.append(token)
    return parts


def _parse_cfg_value(raw: str) -> Any:
    text = raw.strip()
    if not text:
        return ''

    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        text = text[1:-1]

    lowered = text.lower()
    if lowered == 'true':
        return True
    if lowered == 'false':
        return False
    if lowered in {'none', 'null'}:
        return None

    if text.startswith('[') and text.endswith(']'):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [_parse_cfg_value(part) for part in _split_top_level_commas(inner)]

    if text.startswith('(') and text.endswith(')'):
        inner = text[1:-1].strip()
        if not inner:
            return ()
        return tuple(_parse_cfg_value(part) for part in _split_top_level_commas(inner))

    if text.startswith('{') and text.endswith('}'):
        try:
            return ast.literal_eval(text)
        except (ValueError, SyntaxError):
            pass

    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        if ',' in text:
            parts = _split_top_level_commas(text)
            if len(parts) > 1:
                return [_parse_cfg_value(part) for part in parts]
        return text


def _parse_cfg_options(items: list[str] | None) -> dict[str, Any]:
    options: dict[str, Any] = {}
    if not items:
        return options

    for token in items:
        if '=' not in token:
            raise ValueError(f'Invalid cfg option {token!r}; expected KEY=VALUE')
        key, raw = token.split('=', 1)
        key = key.strip()
        if not key:
            raise ValueError(f'Invalid cfg option {token!r}; key is empty')
        options[key] = _parse_cfg_value(raw)
    return options


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Print a resolved MMPreTrain config',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('config', help='Config file to load')
    parser.add_argument(
        '--cfg-options',
        nargs='+',
        metavar='KEY=VALUE',
        help='Override config values before printing.',
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        cfg_options = _parse_cfg_options(args.cfg_options)
    except ValueError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2

    try:
        from mmengine.config import Config
    except ImportError:
        print(
            'error: mmengine is required to load configs for this helper. '
            'Install the package dependencies and retry.',
            file=sys.stderr,
        )
        return 1

    cfg_path = Path(args.config)
    if not cfg_path.is_file():
        print(f'error: config file not found: {cfg_path}', file=sys.stderr)
        return 2

    cfg = Config.fromfile(str(cfg_path))
    if cfg_options:
        cfg.merge_from_dict(cfg_options)

    pretty_text = cfg.pretty_text
    end = '' if pretty_text.endswith('\n') else '\n'
    print(pretty_text, end=end)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
