#!/usr/bin/env python3
"""Resolve and validate a Luminoth training or eval config.

This helper is safe: it only reads config files and prints the effective key
values it can see. It does not start training or talk to cloud services.

Examples:
  python scripts/check_config_keys.py --config ./config.yml --mode train
  python scripts/check_config_keys.py --config ./config.yml --mode eval --override train.run_name=my-run
"""

import argparse
import sys
from pathlib import Path


def add_repo_root(repo_root: str) -> None:
    if not repo_root:
        return
    root = str(Path(repo_root).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)


def lookup(obj, dotted):
    current = obj
    for part in dotted.split('.'):
        if isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
        else:
            if not hasattr(current, part):
                return None
            current = getattr(current, part)
    return current


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Check that a Luminoth config has the keys a workflow needs.'
    )
    parser.add_argument('--repo-root', help='Optional checkout root to add to sys.path before importing.')
    parser.add_argument('--mode', choices=['train', 'eval', 'cloud'], default='train', help='Which workflow to validate against.')
    parser.add_argument('--config', action='append', required=True, help='YAML config file to load. Pass multiple times to merge files.')
    parser.add_argument('--override', action='append', default=[], help='Dot-notation override such as model.network.num_classes=3.')
    args = parser.parse_args()

    add_repo_root(args.repo_root)

    try:
        from luminoth.utils.config import get_config
    except ImportError as exc:
        print(f'Import failed: {exc}', file=sys.stderr)
        print('Install Luminoth and TensorFlow before running config checks.', file=sys.stderr)
        return 1

    try:
        config = get_config(args.config, override_params=tuple(args.override))
    except Exception as exc:
        print(f'Config load failed: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1

    required = ['model.type', 'dataset.type']
    if args.mode in {'train', 'eval'}:
        required.append('dataset.dir')
    if args.mode == 'eval':
        required.extend(['train.job_dir', 'train.run_name'])

    missing = [path for path in required if lookup(config, path) in (None, '')]
    if missing:
        print(f'missing required keys for mode {args.mode}:', file=sys.stderr)
        for path in missing:
            print(f'  - {path}', file=sys.stderr)
        print('resolved config still loaded, but the workflow is incomplete.', file=sys.stderr)
        return 2

    print(f'mode: {args.mode}')
    for path in ['model.type', 'dataset.type', 'dataset.dir', 'train.job_dir', 'train.run_name']:
        value = lookup(config, path)
        if value not in (None, ''):
            print(f'{path}: {value}')

    if args.mode == 'cloud':
        print('cloud note: the cloud helper will override train.job_dir with a gs:// path.')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
