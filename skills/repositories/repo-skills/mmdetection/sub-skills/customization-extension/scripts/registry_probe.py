#!/usr/bin/env python3
"""Probe MMDetection registries and optional custom imports without training."""

from __future__ import annotations

import argparse
import importlib
import json
from typing import Iterable

REGISTRY_NAMES = [
    'DATASETS',
    'DATA_SAMPLERS',
    'EVALUATOR',
    'HOOKS',
    'LOG_PROCESSORS',
    'LOOPS',
    'METRICS',
    'MODELS',
    'MODEL_WRAPPERS',
    'OPTIMIZERS',
    'OPTIM_WRAPPERS',
    'OPTIM_WRAPPER_CONSTRUCTORS',
    'PARAM_SCHEDULERS',
    'RUNNERS',
    'RUNNER_CONSTRUCTORS',
    'TASK_UTILS',
    'TRANSFORMS',
    'VISBACKENDS',
    'VISUALIZERS',
    'WEIGHT_INITIALIZERS',
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='List MMDetection registry entries and verify custom import side effects.')
    parser.add_argument(
        '--registry',
        choices=REGISTRY_NAMES,
        default='MODELS',
        help='Registry to inspect.')
    parser.add_argument(
        '--imports',
        nargs='*',
        default=[],
        help='Module import paths to import before inspecting the registry.')
    parser.add_argument(
        '--contains',
        nargs='*',
        default=[],
        help='Registry entry names expected to be present after imports.')
    parser.add_argument(
        '--filter',
        default='',
        help='Case-insensitive substring filter for listed entry names.')
    parser.add_argument(
        '--limit',
        type=int,
        default=80,
        help='Maximum number of entry names to print. Use 0 for all.')
    parser.add_argument(
        '--json',
        action='store_true',
        help='Emit a JSON summary instead of human-readable text.')
    return parser.parse_args()


def import_modules(module_names: Iterable[str]) -> list[dict[str, str]]:
    results = []
    for module_name in module_names:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - report import diagnostics to users.
            results.append({
                'module': module_name,
                'ok': False,
                'error': f'{type(exc).__name__}: {exc}',
            })
        else:
            results.append({'module': module_name, 'ok': True, 'error': ''})
    return results


def main() -> int:
    args = parse_args()

    try:
        from mmengine.registry import init_default_scope
        from mmdet import registry as mmdet_registry
        from mmdet.utils import register_all_modules
    except Exception as exc:  # noqa: BLE001
        print(f'Failed to import MMDetection registry dependencies: {type(exc).__name__}: {exc}')
        return 2

    try:
        init_default_scope('mmdet')
        register_all_modules(init_default_scope=False)
    except Exception as exc:  # noqa: BLE001
        print(f'Failed to initialize MMDetection default scope: {type(exc).__name__}: {exc}')
        return 2

    import_results = import_modules(args.imports)
    registry = getattr(mmdet_registry, args.registry)
    names = sorted(registry.module_dict.keys())
    if args.filter:
        lowered = args.filter.lower()
        names = [name for name in names if lowered in name.lower()]

    missing = [name for name in args.contains if name not in registry.module_dict]
    shown_names = names if args.limit == 0 else names[:args.limit]
    summary = {
        'registry': args.registry,
        'imports': import_results,
        'count': len(names),
        'shown': shown_names,
        'contains': {name: name in registry.module_dict for name in args.contains},
        'missing': missing,
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f'Registry: {args.registry}')
        print(f'Entries matched: {len(names)}')
        for result in import_results:
            status = 'ok' if result['ok'] else f"failed ({result['error']})"
            print(f"Import {result['module']}: {status}")
        if args.contains:
            for name in args.contains:
                status = 'present' if name not in missing else 'missing'
                print(f'Contains {name}: {status}')
        print('Entries:')
        for name in shown_names:
            print(f'  {name}')
        if args.limit and len(names) > args.limit:
            print(f'  ... {len(names) - args.limit} more; rerun with --limit 0 to show all')

    return 1 if missing or any(not result['ok'] for result in import_results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
