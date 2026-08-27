#!/usr/bin/env python3
"""Inspect the local Luminoth checkpoint index.

This helper is safe: it reads the checkpoint database and prints a summary or a
single checkpoint record. It does not refresh the remote index, download
anything, or mutate local state.

Examples:
  python scripts/inspect_checkpoint_index.py
  python scripts/inspect_checkpoint_index.py --id-or-alias accurate
  python scripts/inspect_checkpoint_index.py --lumi-home ./tmp-home --json
"""

import argparse
import json
import os
import sys
from pathlib import Path


def add_repo_root(repo_root: str) -> None:
    if not repo_root:
        return
    root = str(Path(repo_root).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Inspect the local Luminoth checkpoint index.'
    )
    parser.add_argument('--repo-root', help='Optional checkout root to add to sys.path before importing.')
    parser.add_argument('--lumi-home', help='Override the LUMI_HOME directory for this inspection.')
    parser.add_argument('--id-or-alias', help='If set, print just one checkpoint record.')
    parser.add_argument('--json', action='store_true', help='Print the selected record as JSON.')
    args = parser.parse_args()

    add_repo_root(args.repo_root)
    if args.lumi_home:
        os.environ['LUMI_HOME'] = args.lumi_home

    try:
        from luminoth.tools.checkpoint import (
            get_checkpoint,
            get_checkpoint_path,
            get_checkpoints_directory,
            read_checkpoint_db,
        )
    except ImportError as exc:
        print(f'Import failed: {exc}', file=sys.stderr)
        print('Install Luminoth and TensorFlow before inspecting checkpoints.', file=sys.stderr)
        return 1

    db = read_checkpoint_db()
    checkpoints = db.get('checkpoints', [])

    if args.id_or_alias:
        checkpoint = get_checkpoint(db, args.id_or_alias)
        if not checkpoint:
            print(f"Checkpoint {args.id_or_alias!r} not found in index.", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(checkpoint, indent=2, sort_keys=True))
        else:
            print(f"id: {checkpoint.get('id')}")
            print(f"name: {checkpoint.get('name')}")
            print(f"alias: {checkpoint.get('alias')}")
            print(f"source: {checkpoint.get('source')}")
            print(f"status: {checkpoint.get('status')}")
            print(f"model: {checkpoint.get('model')}")
            dataset = checkpoint.get('dataset', {})
            print(f"dataset.name: {dataset.get('name')}")
            print(f"dataset.num_classes: {dataset.get('num_classes')}")
            print(f"created_at: {checkpoint.get('created_at')}")
            print(f"checkpoint_path: {get_checkpoint_path(checkpoint.get('id'))}")
        return 0

    if not checkpoints:
        print('No checkpoints available.')
        print(f'checkpoint index: {os.path.join(get_checkpoints_directory(), "checkpoints.json")}')
        return 0

    if args.json:
        print(json.dumps(db, indent=2, sort_keys=True))
        return 0

    print('| {:>12} | {:>21} | {:>11} | {:>6} | {:>14} |'.format('id', 'name', 'alias', 'source', 'status'))
    print('=' * 70)
    for checkpoint in checkpoints:
        print('| {:>12} | {:>21} | {:>11} | {:>6} | {:>14} |'.format(
            checkpoint.get('id', ''),
            checkpoint.get('name', ''),
            checkpoint.get('alias', ''),
            checkpoint.get('source', ''),
            checkpoint.get('status', ''),
        ))
    print('=' * 70)
    print(f'checkpoint directory: {get_checkpoints_directory()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
