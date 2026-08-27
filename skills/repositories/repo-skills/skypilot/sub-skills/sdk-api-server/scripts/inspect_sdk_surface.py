#!/usr/bin/env python3
"""Inspect a locally installed SkyPilot SDK surface without starting servers."""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from typing import Any, Dict, Iterable

DEFAULT_NAMES = (
    'launch',
    'exec',
    'status',
    'start',
    'stop',
    'down',
    'get',
    'stream_and_get',
    'api_start',
    'api_stop',
    'api_status',
    'api_login',
    'api_info',
)

ASYNC_NAMES = (
    'launch',
    'exec',
    'status',
    'get',
    'stream_and_get',
    'api_status',
    'api_login',
    'api_info',
    'api_stop',
)


def _signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return '<signature unavailable>'


def _collect(module: Any, names: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    collected: Dict[str, Dict[str, Any]] = {}
    for name in names:
        obj = getattr(module, name, None)
        if obj is None:
            collected[name] = {'present': False}
            continue
        collected[name] = {
            'present': True,
            'type': type(obj).__name__,
            'callable': callable(obj),
            'signature': _signature(obj) if callable(obj) else None,
        }
    return collected


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Import SkyPilot and print selected SDK/API-server signatures. '
            'This is read-only and does not start or contact an API server.'),
    )
    parser.add_argument(
        '--names',
        nargs='*',
        default=list(DEFAULT_NAMES),
        help='Specific sky.client.sdk function names to inspect.',
    )
    parser.add_argument(
        '--include-async',
        action='store_true',
        help='Also inspect selected sky.client.sdk_async functions.',
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Emit machine-readable JSON instead of a text report.',
    )
    args = parser.parse_args()

    try:
        import sky
        from sky.client import sdk
    except Exception as exc:  # pylint: disable=broad-except
        print(f'Failed to import SkyPilot: {exc}', file=sys.stderr)
        return 1

    result: Dict[str, Any] = {
        'sky_version': getattr(sky, '__version__', '<unknown>'),
        'sky_commit': getattr(sky, '__commit__', '<unknown>'),
        'sdk': _collect(sdk, args.names),
    }

    if args.include_async:
        try:
            from sky.client import sdk_async
            result['sdk_async'] = _collect(sdk_async, ASYNC_NAMES)
        except Exception as exc:  # pylint: disable=broad-except
            result['sdk_async_error'] = str(exc)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print(f"SkyPilot version: {result['sky_version']}")
    print(f"SkyPilot commit: {result['sky_commit']}")
    print('\nSDK signatures:')
    for name, info in result['sdk'].items():
        if not info.get('present'):
            print(f'  {name}: <missing>')
            continue
        signature = info.get('signature') or '<not callable>'
        print(f'  {name}{signature}')

    if args.include_async:
        print('\nAsync SDK signatures:')
        if 'sdk_async_error' in result:
            print(f"  <error: {result['sdk_async_error']}>")
        else:
            for name, info in result['sdk_async'].items():
                if not info.get('present'):
                    print(f'  {name}: <missing>')
                    continue
                signature = info.get('signature') or '<not callable>'
                print(f'  {name}{signature}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
