#!/usr/bin/env python3
"""Inspect safe `sky` CLI help for selected command groups.

This helper only runs help commands. It never launches clusters, starts API
servers, submits jobs, deploys services, or reads cloud credentials.
"""

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional

DEFAULT_GROUPS = ['root', 'launch', 'exec', 'status', 'logs', 'queue', 'jobs', 'serve', 'api', 'gpus', 'storage', 'volumes']


def _find_executable(command: str) -> Optional[str]:
    executable = shutil.which(command)
    if executable is not None:
        return executable
    sibling = pathlib.Path(sys.executable).with_name(command)
    if sibling.exists() and sibling.is_file():
        return str(sibling)
    return None


def _command_for_group(executable: str, group: str) -> List[str]:
    if group == 'root':
        return [executable, '--help']
    return [executable, group, '--help']


def _inspect_group(executable: str, group: str, timeout: int, lines: int) -> Dict[str, Any]:
    command = _command_for_group(executable, group)
    try:
        result = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {'group': group, 'ok': False, 'command': command, 'error': 'timed out'}
    stdout_lines = result.stdout.splitlines()
    return {
        'group': group,
        'ok': result.returncode == 0,
        'command': command,
        'returncode': result.returncode,
        'summary': stdout_lines[:lines],
        'stderr': result.stderr.strip().splitlines()[:5],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Print safe SkyPilot CLI help summaries.')
    parser.add_argument('--sky', default='sky', help='SkyPilot CLI executable name or path.')
    parser.add_argument('--group', action='append', choices=DEFAULT_GROUPS, help='Command group to inspect; repeatable. Defaults to common groups.')
    parser.add_argument('--lines', type=int, default=12, help='Number of help lines to include per group.')
    parser.add_argument('--timeout', type=int, default=15, help='Timeout in seconds for each help command.')
    parser.add_argument('--json', action='store_true', help='Print JSON instead of text.')
    args = parser.parse_args()

    executable = _find_executable(args.sky) if '/' not in args.sky else args.sky
    if executable is None:
        print(f'Could not find {args.sky!r} on PATH or beside the current Python. Install SkyPilot or pass --sky /path/to/sky.', file=sys.stderr)
        return 1

    groups = args.group or DEFAULT_GROUPS
    results = [_inspect_group(executable, group, args.timeout, args.lines) for group in groups]

    if args.json:
        print(json.dumps({'ok': all(item['ok'] for item in results), 'groups': results}, indent=2))
    else:
        for item in results:
            status = 'ok' if item['ok'] else 'failed'
            print(f"## {item['group']} ({status})")
            for line in item.get('summary', []):
                print(line)
            if item.get('stderr'):
                print('stderr:', ' | '.join(item['stderr']))
            print()
    return 0 if all(item['ok'] for item in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
