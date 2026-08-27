#!/usr/bin/env python3
"""Safe MMAction2 config inspector.

This helper parses a trusted MMEngine/MMAction2 config and prints a compact
summary. It does not build datasets, instantiate models, scan media, download
weights, train, test, or write output files.
"""

from __future__ import annotations

import argparse
import ast
import os
import sys
from collections.abc import Mapping, Sequence
from typing import Any


def _parse_scalar(value: str) -> Any:
    """Parse a shell-provided cfg-option value conservatively."""
    value = value.strip()
    lowered = value.lower()
    if lowered == 'true':
        return True
    if lowered == 'false':
        return False
    if lowered in {'none', 'null'}:
        return None
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        pass
    if ',' in value and not any(value.startswith(ch) for ch in ('"', "'", '[', '(', '{')):
        return [_parse_scalar(part) for part in value.split(',')]
    return value


def _parse_cfg_options(items: list[str] | None) -> dict[str, Any]:
    options: dict[str, Any] = {}
    if not items:
        return options
    for item in items:
        if '=' not in item:
            raise argparse.ArgumentTypeError(
                f'cfg option {item!r} is not in KEY=VALUE form')
        key, raw_value = item.split('=', 1)
        key = key.strip()
        if not key:
            raise argparse.ArgumentTypeError(
                f'cfg option {item!r} has an empty key')
        options[key] = _parse_scalar(raw_value)
    return options


def _type_name(obj: Any) -> str:
    if isinstance(obj, Mapping):
        value = obj.get('type', '<none>')
        return str(value)
    return type(obj).__name__


def _to_plain(obj: Any) -> Any:
    """Convert ConfigDict/list-like objects to plain Python objects for display."""
    if isinstance(obj, Mapping):
        return {str(k): _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, tuple):
        return tuple(_to_plain(v) for v in obj)
    if isinstance(obj, list):
        return [_to_plain(v) for v in obj]
    return obj


def _short(value: Any, limit: int = 120) -> str:
    value = _to_plain(value)
    text = repr(value)
    if len(text) > limit:
        return text[: limit - 3] + '...'
    return text


def _pipeline_steps(pipeline: Any) -> list[str]:
    if pipeline is None:
        return []
    steps = []
    if isinstance(pipeline, Sequence) and not isinstance(pipeline, (str, bytes, bytearray)):
        for index, step in enumerate(pipeline):
            if isinstance(step, Mapping):
                label = str(step.get('type', '<missing-type>'))
                extras = []
                for key in ('clip_len', 'frame_interval', 'num_clips', 'test_mode',
                            'input_format', 'scale', 'crop_size', 'flip_ratio'):
                    if key in step:
                        extras.append(f'{key}={_short(step[key], 40)}')
                if extras:
                    label += ' (' + ', '.join(extras) + ')'
            else:
                label = type(step).__name__
            steps.append(f'{index}: {label}')
    else:
        steps.append(f'<non-list pipeline: {type(pipeline).__name__}>')
    return steps


def _dataset_from_dataloader(dataloader: Any) -> Any:
    if isinstance(dataloader, Mapping):
        return dataloader.get('dataset')
    return None


def _print_overview(cfg: Any, cfg_path: str, overrides: dict[str, Any]) -> None:
    print('MMAction2 config inspector')
    print('==========================')
    print(f'config_name: {os.path.basename(cfg_path)}')
    print(f'default_scope: {cfg.get("default_scope", "<missing>")}')
    print(f'top_level_keys: {", ".join(sorted(str(k) for k in cfg.keys()))}')
    if overrides:
        print('applied_overrides:')
        for key, value in overrides.items():
            print(f'  - {key} = {_short(value)}')
    else:
        print('applied_overrides: <none>')
    print()


def _print_model(cfg: Any) -> None:
    model = cfg.get('model')
    print('Model summary')
    print('-------------')
    if not isinstance(model, Mapping):
        print('model: <missing or non-dict>')
        print()
        return
    print(f'type: {_type_name(model)}')
    for key in ('backbone', 'neck', 'cls_head', 'bbox_head', 'roi_head',
                'data_preprocessor', 'train_cfg', 'test_cfg'):
        if key not in model:
            continue
        value = model[key]
        if isinstance(value, Mapping):
            print(f'{key}: type={_type_name(value)} keys={list(value.keys())}')
            if key in {'cls_head', 'bbox_head'}:
                for subkey in ('num_classes', 'in_channels', 'average_clips', 'multilabel'):
                    if subkey in value:
                        print(f'  {subkey}: {_short(value[subkey])}')
            if key == 'data_preprocessor':
                for subkey in ('mean', 'std', 'format_shape'):
                    if subkey in value:
                        print(f'  {subkey}: {_short(value[subkey])}')
        else:
            print(f'{key}: {_short(value)}')
    print()


def _print_dataloaders(cfg: Any) -> None:
    print('Dataloader summary')
    print('------------------')
    found = False
    for phase in ('train', 'val', 'test'):
        name = f'{phase}_dataloader'
        dataloader = cfg.get(name)
        if not isinstance(dataloader, Mapping):
            print(f'{name}: <missing or non-dict>')
            continue
        found = True
        dataset = _dataset_from_dataloader(dataloader)
        print(f'{name}:')
        for key in ('batch_size', 'num_workers', 'persistent_workers'):
            if key in dataloader:
                print(f'  {key}: {_short(dataloader[key])}')
        sampler = dataloader.get('sampler')
        if isinstance(sampler, Mapping):
            print(f'  sampler: type={_type_name(sampler)} shuffle={sampler.get("shuffle", "<missing>")}')
        if isinstance(dataset, Mapping):
            print(f'  dataset.type: {_type_name(dataset)}')
            for key in ('ann_file', 'data_root', 'data_prefix', 'test_mode', 'split',
                        'filename_tmpl', 'with_offset', 'multi_class', 'multilabel',
                        'num_classes', 'custom_classes', 'start_index', 'modality'):
                if key in dataset:
                    print(f'  dataset.{key}: {_short(dataset[key])}')
            pipeline = dataset.get('pipeline')
            if pipeline is not None:
                print(f'  dataset.pipeline_steps: {len(_pipeline_steps(pipeline))}')
        else:
            print('  dataset: <missing or non-dict>')
    if not found:
        print('<no MMEngine-style dataloaders found>')
    print()


def _print_pipelines(cfg: Any) -> None:
    print('Pipeline summary')
    print('----------------')
    emitted = False
    for phase in ('train', 'val', 'test'):
        top_name = f'{phase}_pipeline'
        pipeline = cfg.get(top_name)
        if pipeline is None:
            dataloader = cfg.get(f'{phase}_dataloader')
            dataset = _dataset_from_dataloader(dataloader)
            if isinstance(dataset, Mapping):
                pipeline = dataset.get('pipeline')
                top_name = f'{phase}_dataloader.dataset.pipeline'
        if pipeline is None:
            print(f'{phase}: <missing>')
            continue
        emitted = True
        print(f'{top_name}:')
        for step in _pipeline_steps(pipeline):
            print(f'  - {step}')
    if not emitted:
        print('<no top-level or dataloader dataset pipelines found>')
    print()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            'Safely summarize a trusted MMAction2/MMEngine config without '
            'building datasets, scanning media, training, testing, or writing outputs.'))
    parser.add_argument('--config', required=True, help='trusted config file to inspect')
    parser.add_argument('--show-pipelines', action='store_true', help='print transform pipeline steps')
    parser.add_argument('--show-dataloaders', action='store_true', help='print train/val/test dataloader summaries')
    parser.add_argument('--show-model', action='store_true', help='print model and head/preprocessor summary')
    parser.add_argument(
        '--cfg-options',
        nargs='+',
        default=None,
        metavar='KEY=VALUE',
        help=('override config keys in memory. Quote list/tuple values, e.g. '
              'model.data_preprocessor.mean="[127.5,127.5,127.5]"'))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        overrides = _parse_cfg_options(args.cfg_options)
    except argparse.ArgumentTypeError as exc:
        print(f'Invalid --cfg-options: {exc}', file=sys.stderr)
        return 2

    try:
        from mmengine import Config
    except ModuleNotFoundError as exc:
        print(
            'Optional dependency failure: mmengine is required to parse MMAction2 '
            f'configs ({exc}). Install MMEngine in the active environment and retry.',
            file=sys.stderr)
        return 2

    try:
        cfg = Config.fromfile(args.config)
        if overrides:
            cfg.merge_from_dict(overrides)
    except Exception as exc:  # noqa: BLE001 - CLI should explain parser/config failures.
        print(f'Failed to parse or merge config safely: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 2

    _print_overview(cfg, args.config, overrides)
    if args.show_model:
        _print_model(cfg)
    if args.show_dataloaders:
        _print_dataloaders(cfg)
    if args.show_pipelines:
        _print_pipelines(cfg)
    if not (args.show_model or args.show_dataloaders or args.show_pipelines):
        print('No detail flags selected; use --show-dataloaders, --show-pipelines, and/or --show-model.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
