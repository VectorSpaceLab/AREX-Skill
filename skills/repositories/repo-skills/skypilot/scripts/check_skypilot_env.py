#!/usr/bin/env python3
"""Safe SkyPilot environment check for agent workflows.

This helper imports SkyPilot, reports version and selected public surfaces, and
optionally checks that the `sky` CLI can print help. It never launches clusters,
starts services, contacts clouds, or reads credentials.
"""

import argparse
import importlib
import inspect
import json
import pathlib
import shutil
import subprocess
import sys
from typing import Any, Dict, Optional


def _signature(module: Any, name: str) -> str:
    obj = getattr(module, name, None)
    if obj is None:
        return 'missing'
    if not callable(obj):
        return f'not-callable:{type(obj).__name__}'
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError) as exc:
        return f'unavailable:{exc}'


def _find_executable(command: str) -> Optional[str]:
    executable = shutil.which(command)
    if executable is not None:
        return executable
    sibling = pathlib.Path(sys.executable).with_name(command)
    if sibling.exists() and sibling.is_file():
        return str(sibling)
    return None


def _run_help(command: str, timeout: int) -> Dict[str, Any]:
    executable = _find_executable(command)
    if executable is None:
        return {'ok': False, 'error': f'{command!r} not found on PATH or beside the current Python'}
    try:
        result = subprocess.run(
            [executable, '--help'],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {'ok': False, 'error': f'{command} --help timed out'}
    return {
        'ok': result.returncode == 0,
        'returncode': result.returncode,
        'first_stdout_line': result.stdout.splitlines()[0] if result.stdout else '',
        'stderr_excerpt': result.stderr.strip().splitlines()[:3],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Check a SkyPilot install without launching resources.')
    parser.add_argument('--check-cli', action='store_true', help='Also run `sky --help` when the CLI is on PATH.')
    parser.add_argument('--json', action='store_true', help='Print JSON instead of a human summary.')
    parser.add_argument('--timeout', type=int, default=15, help='Timeout in seconds for CLI help checks.')
    args = parser.parse_args()

    report: Dict[str, Any] = {'ok': False, 'python': sys.version.split()[0]}
    try:
        sky = importlib.import_module('sky')
    except Exception as exc:  # pylint: disable=broad-except
        report['error'] = f'failed to import sky: {exc}'
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(report['error'], file=sys.stderr)
        return 1

    report.update({
        'ok': True,
        'version': getattr(sky, '__version__', None),
        'public_surfaces': {
            name: _signature(sky, name)
            for name in ('launch', 'exec', 'status', 'start', 'stop', 'down', 'get', 'tail_logs', 'Task', 'Resources', 'Storage')
        },
    })

    if args.check_cli:
        report['sky_help'] = _run_help('sky', args.timeout)
        if not report['sky_help']['ok']:
            report['ok'] = False

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"SkyPilot import: ok (version={report['version']})")
        if args.check_cli:
            sky_help = report['sky_help']
            if sky_help['ok']:
                print(f"sky --help: ok ({sky_help['first_stdout_line']})")
            else:
                print(f"sky --help: failed ({sky_help.get('error') or sky_help.get('stderr_excerpt')})", file=sys.stderr)
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
