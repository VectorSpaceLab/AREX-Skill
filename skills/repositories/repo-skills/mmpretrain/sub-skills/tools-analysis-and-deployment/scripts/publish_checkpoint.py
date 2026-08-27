#!/usr/bin/env python3
"""Publish a checkpoint without mutating the source file."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import os
import sys
import warnings
from collections import OrderedDict
from pathlib import Path


def locate_repo_root() -> Path:
    """Find the repository root that contains the mmpretrain package."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / 'mmpretrain' / '__init__.py').is_file():
            return parent
    raise RuntimeError(
        'Unable to locate the repository root that contains the mmpretrain '
        'package.')


REPO_ROOT = locate_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import torch  # noqa: E402
import mmpretrain  # noqa: E402


def resolve_existing_path(raw: str) -> Path:
    """Resolve an input file against the current working directory and repo."""
    candidate = Path(raw).expanduser()
    search_order = [candidate]
    if not candidate.is_absolute():
        search_order = [Path.cwd() / candidate, REPO_ROOT / candidate, candidate]
    for path in search_order:
        if path.exists():
            return path.resolve()
    raise FileNotFoundError(f'Cannot find input file: {raw}')


def load_checkpoint(in_file: Path):
    return torch.load(in_file, map_location='cpu')


def ensure_state_dict(checkpoint):
    if 'state_dict' not in checkpoint:
        checkpoint = dict(state_dict=checkpoint)
    return checkpoint


def build_dataset_meta(dataset_type: str | None) -> dict:
    if dataset_type is None:
        return {}
    from mmpretrain.registry import DATASETS

    dataset_class = DATASETS.get(dataset_type)
    if dataset_class is None:
        raise KeyError(f'Unknown dataset type: {dataset_type}')
    return getattr(dataset_class, 'METAINFO', {}) or {}


def drop_training_state(checkpoint: dict) -> None:
    for key in ['optimizer', 'param_schedulers', 'hook_msgs', 'message_hub']:
        checkpoint.pop(key, None)


def merge_ema_weights(checkpoint: dict, use_ema: bool) -> bool:
    ema_state_dict = checkpoint.pop('ema_state_dict', None)
    if ema_state_dict is None:
        return False

    print('The input checkpoint has EMA weights, ', end='')
    if not use_ema:
        print('stripping the EMA container and keeping the base state_dict.')
        return True

    print('merging EMA weights into state_dict.')
    base_state_dict = checkpoint.setdefault('state_dict', OrderedDict())
    merged = OrderedDict()
    for key, value in ema_state_dict.items():
        base_key = key[len('module.'):] if key.startswith('module.') else key
        merged[base_key] = value

    missing = sorted(set(merged) - set(base_state_dict))
    if missing:
        raise KeyError(
            'EMA weights do not match the base state_dict keys: ' +
            ', '.join(missing[:10]))
    base_state_dict.update(merged)
    return True


def build_published_checkpoint(in_file: Path, args: argparse.Namespace) -> dict:
    checkpoint = load_checkpoint(in_file)
    checkpoint = ensure_state_dict(checkpoint)
    drop_training_state(checkpoint)

    meta = checkpoint.get('meta', {})
    meta.setdefault('mmpretrain_version', mmpretrain.__version__)

    dataset_meta = build_dataset_meta(args.dataset_type)
    if args.dataset_type is not None:
        if dataset_meta:
            meta.setdefault('dataset_meta', dataset_meta)
        else:
            warnings.warn('Missing dataset meta information.')
            meta.setdefault('dataset_meta', {})
    else:
        meta.setdefault('dataset_meta', {})

    checkpoint['meta'] = meta
    merge_ema_weights(checkpoint, args.use_ema)
    return checkpoint


def save_checkpoint(checkpoint: dict, source_path: Path, out_target: Path,
                    force: bool) -> Path:
    out_target = out_target.expanduser()
    timestamp = datetime.datetime.now().strftime('%Y%m%d')

    if out_target.suffix == '.pth':
        final_path = out_target
        if final_path.exists() and not force:
            raise FileExistsError(
                f'Output file already exists: {final_path}. Use --force to '
                'overwrite it.')
        final_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        out_target.mkdir(parents=True, exist_ok=True)
        temp_seed = out_target / f'.{source_path.stem}.publish.tmp'
        torch.save(checkpoint, temp_seed)
        sha = hashlib.sha256(temp_seed.read_bytes()).hexdigest()[:8]
        final_path = out_target / f'{source_path.stem}_{timestamp}-{sha}.pth'
        if final_path.exists() and not force:
            temp_seed.unlink(missing_ok=True)
            raise FileExistsError(
                f'Output file already exists: {final_path}. Use --force to '
                'overwrite it.')
        os.replace(temp_seed, final_path)
        return final_path

    temp_path = final_path.with_name(f'.{final_path.name}.tmp')
    torch.save(checkpoint, temp_path)
    os.replace(temp_path, final_path)
    return final_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Publish a checkpoint without mutating the source file.')
    parser.add_argument('in_file', help='input checkpoint filename')
    parser.add_argument(
        'out_target',
        help='output .pth file or a directory that will receive a stamped file')
    parser.add_argument(
        '--dataset-type',
        type=str,
        default=None,
        help='dataset family used to populate dataset_meta in the checkpoint')
    parser.add_argument(
        '--use-ema',
        action='store_true',
        help='merge EMA weights into state_dict when the checkpoint provides them')
    parser.add_argument(
        '--force',
        action='store_true',
        help='overwrite an existing output file when the target resolves to a file')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    in_file = resolve_existing_path(args.in_file)
    out_target = Path(args.out_target).expanduser()
    checkpoint = build_published_checkpoint(in_file, args)
    final_path = save_checkpoint(checkpoint, in_file, out_target, args.force)
    print(f'Successfully generated published checkpoint at {final_path}.')


if __name__ == '__main__':
    main()
