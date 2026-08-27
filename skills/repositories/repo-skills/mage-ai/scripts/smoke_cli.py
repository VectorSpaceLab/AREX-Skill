#!/usr/bin/env python3
"""Print mage-ai version and CLI help as a safe smoke test."""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description='Print the installed Mage package version and CLI help.')
    parser.add_argument('--command', default='--help', help='Additional mage CLI argument to pass after the module name.')
    args = parser.parse_args()

    try:
        version = metadata.version('mage-ai')
    except metadata.PackageNotFoundError:
        print('mage-ai is not installed')
        return 1

    print(f'mage-ai version: {version}')
    result = subprocess.run([sys.executable, '-m', 'mage_ai.cli.main', args.command], check=False, text=True, capture_output=True)
    print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, end='', file=sys.stderr)
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
