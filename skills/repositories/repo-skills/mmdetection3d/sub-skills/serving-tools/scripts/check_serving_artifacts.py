#!/usr/bin/env python3
"""Check MMDetection3D serving packaging artifacts.

This script validates the files and names needed before packaging a TorchServe
archive. It never packages, starts a server, builds Docker images, downloads
weights, or touches a remote service.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Sequence


def _normalize_path(raw: str) -> Path:
    return Path(raw).expanduser()


def _check_existing_file(label: str, raw_path: str) -> tuple[bool, str]:
    path = _normalize_path(raw_path)
    if not str(raw_path).strip():
        return False, f'{label}: empty value'
    if path.is_file():
        return True, f'{label}: {path}'
    if path.exists():
        return False, f'{label}: {path} (exists but is not a file)'
    return False, f'{label}: {path} (missing)'


def _check_model_name(raw_name: str) -> tuple[bool, str]:
    name = raw_name.strip()
    if not name:
        return False, 'model-name: empty value'

    separators: list[str] = [os.sep]
    if os.path.altsep:
        separators.append(os.path.altsep)

    if any(sep in name for sep in separators):
        return False, f'model-name: {name} (must not contain path separators)'

    if name in {'.', '..'}:
        return False, f'model-name: {name} (invalid archive name)'

    return True, f'model-name: {name}'


def _check_output_folder(raw_path: str) -> tuple[bool, str]:
    path = _normalize_path(raw_path)
    if not str(raw_path).strip():
        return False, 'output-folder: empty value'
    if path.exists() and not path.is_dir():
        return False, f'output-folder: {path} (exists but is not a directory)'
    if path.exists():
        return True, f'output-folder: {path}'

    ancestor = path
    while not ancestor.exists():
        parent = ancestor.parent
        if parent == ancestor:
            break
        ancestor = parent

    if ancestor.exists() and not ancestor.is_dir():
        return (
            False,
            f'output-folder: {path} (nearest existing ancestor {ancestor} is not a directory)')

    if ancestor.exists() and not os.access(ancestor, os.W_OK | os.X_OK):
        return (
            False,
            f'output-folder: {path} (nearest existing ancestor {ancestor} is not writable)')

    return True, f'output-folder: {path} (will be created if needed)'


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Validate MMDetection3D serving packaging artifacts')
    parser.add_argument('config', help='config file path')
    parser.add_argument('checkpoint', help='checkpoint file path')
    parser.add_argument(
        '--handler',
        required=True,
        help='TorchServe handler file path')
    parser.add_argument(
        '--model-name',
        required=True,
        help='archive/model name to use during packaging')
    parser.add_argument(
        '--output-folder',
        required=True,
        help='directory where the packaged archive will be written')
    return parser.parse_args(argv)


def _print_check(ok: bool, message: str) -> None:
    status = 'OK' if ok else 'MISSING'
    print(f'{status}: {message}')


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    checks: list[tuple[bool, str]] = [
        _check_existing_file('config', args.config),
        _check_existing_file('checkpoint', args.checkpoint),
        _check_existing_file('handler', args.handler),
        _check_model_name(args.model_name),
        _check_output_folder(args.output_folder),
    ]

    missing: list[str] = []
    print('Serving packaging preflight')
    for ok, message in checks:
        _print_check(ok, message)
        if not ok:
            missing.append(message)

    if missing:
        print('\nMissing artifacts:')
        for message in missing:
            print(f'- {message}')
        return 1

    print('\nAll serving packaging artifacts are present.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
