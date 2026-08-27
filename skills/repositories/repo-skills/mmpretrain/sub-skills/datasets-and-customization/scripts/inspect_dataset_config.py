#!/usr/bin/env python3
"""Inspect dataset-oriented config blocks without building datasets.

This helper loads a config, resolves dataset/dataloader trees, checks registry
visibility, and reports pipeline order. It does not build datasets or open
image files.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import importlib.util
import json
import os
from typing import Any, Dict, List, Optional

Config = None
DATASETS = None
TRANSFORMS = None
register_all_modules = None

DEFAULT_FIELDS = ('train_dataloader', 'val_dataloader', 'test_dataloader')
PIPELINE_LOAD_STEP = 'LoadImageFromFile'
PIPELINE_PACK_STEP = 'PackInputs'
OPTIONAL_ALBU_TYPES = {'Albumentations', 'Albu'}
IMAGE_PIPELINE_TYPES = {
    'LoadImageFromFile', 'RandomResizedCrop', 'ResizeEdge', 'CenterCrop',
    'RandAugment', 'RandomFlip', 'RandomCrop', 'RandomErasing',
    'PackInputs', 'PackMultiTaskInputs', 'Albumentations', 'Albu'
}
DATASET_FRIENDLY_NOTES = {
    'BaseDataset': 'generic annotation-driven dataset',
    'CustomDataset': 'folder scan or text annotation dataset',
    'ImageNet': 'ImageNet split-aware dataset',
    'KFoldDataset': 'fold wrapper around another dataset',
}
TRANSFORM_FRIENDLY_NOTES = {
    'LoadImageFromFile': 'loads img_path into img',
    'RandomResizedCrop': 'random crop plus resize',
    'ResizeEdge': 'resize along a chosen edge',
    'CenterCrop': 'center crop',
    'RandAugment': 'policy-based image augmentation',
    'PackInputs': 'packs inputs and DataSample',
    'PackMultiTaskInputs': 'packs multi-task labels and meta',
    'Albumentations': 'optional dependency',
    'Albu': 'optional dependency alias',
}
RELEVANT_DATASET_KEYS = (
    'type', 'data_root', 'ann_file', 'data_prefix', 'split', 'with_label',
    'classes', 'metainfo', 'lazy_init', 'filter_cfg', 'indices',
    'serialize_data', 'test_mode', 'pipeline', 'dataset', 'datasets',
    'batch_size', 'num_workers', 'persistent_workers', 'drop_last',
    'pin_memory', 'sampler', 'batch_sampler', 'collate_fn'
)


def load_runtime_modules() -> None:
    """Import MMEngine/MMPretrain helpers lazily.

    Keeping the imports here lets `--help` work even when the runtime
    dependencies are unavailable in a bare shell.
    """
    global Config, DATASETS, TRANSFORMS, register_all_modules
    if Config is not None:
        return

    try:
        from mmengine import Config as MMConfig
        from mmpretrain.registry import DATASETS as MM_DATASETS
        from mmpretrain.registry import TRANSFORMS as MM_TRANSFORMS
        from mmpretrain.utils.setup_env import (
            register_all_modules as MM_register_all_modules)
    except ImportError as exc:  # pragma: no cover - surfaced to user
        raise SystemExit(
            'This helper requires MMEngine and MMPretrain runtime '
            'dependencies. Install them before inspecting dataset configs.') from exc

    Config = MMConfig
    DATASETS = MM_DATASETS
    TRANSFORMS = MM_TRANSFORMS
    register_all_modules = MM_register_all_modules


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Inspect dataset-oriented MMPretrain configs safely')
    parser.add_argument('config', help='Config file path')
    parser.add_argument(
        '--field',
        action='append',
        default=[],
        help=('Dotted config path to inspect. Repeat to inspect multiple '
              'blocks. Defaults to train/val/test dataloaders.')
    )
    parser.add_argument(
        '--format',
        choices=('text', 'json'),
        default='text',
        help='Output format',
    )
    parser.add_argument(
        '--cfg-options',
        nargs='+',
        help='Override config values in key=value form',
    )
    return parser.parse_args()


def parse_cfg_options(tokens: Optional[List[str]]) -> Dict[str, Any]:
    """Parse a small `key=value` override list.

    The parser accepts dotted keys and Python-literal values.
    """
    if not tokens:
        return {}

    overrides: Dict[str, Any] = {}
    for token in tokens:
        if '=' not in token:
            raise SystemExit(
                f'Invalid cfg override "{token}". Use key=value syntax.')
        key, raw_value = token.split('=', 1)
        try:
            value = ast.literal_eval(raw_value)
        except Exception:
            value = raw_value
        assign_nested(overrides, key, value)
    return overrides


def assign_nested(target: Dict[str, Any], dotted_key: str, value: Any) -> None:
    node = target
    parts = dotted_key.split('.')
    for part in parts[:-1]:
        next_node = node.get(part)
        if not isinstance(next_node, dict):
            next_node = {}
            node[part] = next_node
        node = next_node
    node[parts[-1]] = value


def load_config(path: str, cfg_options: Optional[Dict[str, Any]] = None):
    if Config is None:
        raise RuntimeError('Runtime modules were not loaded.')
    cfg = Config.fromfile(path)
    if cfg_options:
        cfg.merge_from_dict(cfg_options)
    return cfg


def import_custom_modules(cfg) -> Dict[str, List[Dict[str, str]]]:
    block = cfg.get('custom_imports')
    report = {'imported': [], 'failed': []}
    if not block:
        return report

    imports = block.get('imports', []) if isinstance(block, dict) else []
    allow_failed = block.get('allow_failed_imports', False) if isinstance(
        block, dict) else False

    for module_name in imports:
        try:
            importlib.import_module(module_name)
            report['imported'].append({'module': module_name})
        except Exception as exc:  # pragma: no cover - surfaced to user
            report['failed'].append({'module': module_name, 'error': str(exc)})
            if not allow_failed:
                raise RuntimeError(
                    f'Failed to import custom module {module_name}: {exc}') from exc
    return report


def type_info(value: Any) -> Dict[str, Any]:
    if isinstance(value, str):
        return {'name': value, 'kind': 'string', 'module': None}
    if isinstance(value, type):
        return {'name': value.__name__, 'kind': 'class', 'module': value.__module__}
    if value is None:
        return {'name': None, 'kind': 'missing', 'module': None}
    return {
        'name': getattr(value, '__name__', repr(value)),
        'kind': type(value).__name__,
        'module': getattr(value, '__module__', None),
    }


def get_by_path(node: Any, dotted_path: str) -> Any:
    current = node
    for part in dotted_path.split('.'):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        try:
            if hasattr(current, '__contains__') and part in current:
                current = current[part]
                continue
        except Exception:
            pass
        if hasattr(current, part):
            current = getattr(current, part)
            continue
        return None
    return current


def join_like_root(root: Optional[str], child: Any) -> Any:
    if not isinstance(child, str):
        return child
    if not root or '://' in child or os.path.isabs(child):
        return child
    if '://' in root:
        return root.rstrip('/') + '/' + child.lstrip('/')
    return os.path.normpath(os.path.join(root, child))


def preview_sequence(value: Any, limit: int = 6) -> Any:
    if isinstance(value, dict):
        keys = list(value.keys())
        preview = {k: preview_sequence(value[k], limit=limit) for k in keys[:limit]}
        if len(keys) > limit:
            preview['...'] = f'+{len(keys) - limit} more'
        return preview
    if isinstance(value, (list, tuple)):
        items = [preview_sequence(item, limit=limit) for item in list(value[:limit])]
        if len(value) > limit:
            items.append(f'... +{len(value) - limit} more')
        return items
    return value


def resolve_registry_hits(type_name: Optional[str]) -> List[str]:
    if not type_name:
        return []
    hits = []
    if DATASETS.get(type_name) is not None:
        hits.append('DATASETS')
    if TRANSFORMS.get(type_name) is not None:
        hits.append('TRANSFORMS')
    return hits


def has_optional_albu() -> bool:
    return importlib.util.find_spec('albumentations') is not None


def find_transform_index(pipeline: Any, target: str) -> int:
    if not isinstance(pipeline, (list, tuple)):
        return -1
    for idx, transform in enumerate(pipeline):
        if isinstance(transform, dict):
            type_value = transform.get('type')
            if isinstance(type_value, str) and type_value == target:
                return idx
            if isinstance(type_value, type) and type_value.__name__ == target:
                return idx
        else:
            if transform.__class__.__name__ == target:
                return idx
    return -1


def summarize_transform(transform: Any, path: str) -> Dict[str, Any]:
    info = type_info(transform.get('type') if isinstance(transform, dict) else transform)
    name = info['name']
    summary: Dict[str, Any] = {
        'path': path,
        'type': name,
        'kind': info['kind'],
        'module': info['module'],
        'registry_hits': resolve_registry_hits(name if isinstance(name, str) else None),
        'note': TRANSFORM_FRIENDLY_NOTES.get(name),
        'fields': {},
        'warnings': [],
    }

    if isinstance(transform, dict):
        for key in ('type', 'prob', 'p', 'keys', 'order', 'scale', 'edge',
                    'crop_size', 'num_policies', 'magnitude_level',
                    'magnitude_std', 'policies', 'transforms', 'keymap'):
            if key in transform and key != 'type':
                summary['fields'][key] = preview_sequence(transform[key])

    if info['kind'] == 'string' and not summary['registry_hits'] and name not in TRANSFORM_FRIENDLY_NOTES:
        summary['warnings'].append('transform type is not registered in TRANSFORMS')

    if name in OPTIONAL_ALBU_TYPES and not has_optional_albu():
        summary['warnings'].append(
            'optional dependency albumentations is not installed')

    return summary


def summarize_pipeline(pipeline: Any, path: str) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        'path': path,
        'type': 'pipeline',
        'fields': {},
        'steps': [],
        'warnings': [],
    }
    if pipeline is None:
        summary['warnings'].append('pipeline is missing')
        return summary
    if not isinstance(pipeline, (list, tuple)):
        summary['warnings'].append('pipeline is not a list or tuple')
        summary['fields']['value'] = preview_sequence(pipeline)
        return summary

    for idx, transform in enumerate(pipeline):
        summary['steps'].append(summarize_transform(transform, f'{path}[{idx}]'))

    load_idx = find_transform_index(pipeline, PIPELINE_LOAD_STEP)
    pack_idx = find_transform_index(pipeline, PIPELINE_PACK_STEP)
    has_image_ops = any(step['type'] in IMAGE_PIPELINE_TYPES for step in summary['steps'])

    if load_idx < 0 and has_image_ops:
        summary['warnings'].append(
            f'{PIPELINE_LOAD_STEP} is missing, but the pipeline contains image transforms')
    elif load_idx > 0:
        summary['warnings'].append(
            f'{PIPELINE_LOAD_STEP} should usually be the first step')

    if pack_idx >= 0 and pack_idx != len(pipeline) - 1:
        summary['warnings'].append(
            f'{PIPELINE_PACK_STEP} should usually be the last step')

    return summary


def summarize_dataset_like(node: Any, path: str) -> Dict[str, Any]:
    if not isinstance(node, dict):
        return {
            'path': path,
            'type': type(node).__name__,
            'kind': 'value',
            'value': preview_sequence(node),
            'warnings': [],
        }

    info = type_info(node.get('type'))
    type_name = info['name']
    summary: Dict[str, Any] = {
        'path': path,
        'type': type_name,
        'kind': info['kind'],
        'module': info['module'],
        'registry_hits': resolve_registry_hits(type_name if isinstance(type_name, str) else None),
        'note': DATASET_FRIENDLY_NOTES.get(type_name),
        'fields': {},
        'warnings': [],
        'children': [],
    }

    for key in RELEVANT_DATASET_KEYS:
        if key in node and key not in {'type', 'pipeline', 'dataset', 'datasets'}:
            value = node[key]
            if key == 'metainfo' and isinstance(value, dict):
                meta_preview = {}
                if 'classes' in value:
                    meta_preview['classes'] = preview_sequence(value['classes'])
                if 'categories' in value:
                    meta_preview['categories'] = preview_sequence(value['categories'])
                for meta_key in value:
                    if meta_key not in meta_preview:
                        meta_preview[meta_key] = preview_sequence(value[meta_key])
                summary['fields'][key] = meta_preview
            elif key in {'classes', 'data_prefix', 'sampler', 'batch_sampler',
                         'collate_fn'}:
                summary['fields'][key] = preview_sequence(value)
            else:
                summary['fields'][key] = preview_sequence(value)

    data_root = node.get('data_root') if isinstance(node.get('data_root'), str) else None
    if 'ann_file' in node:
        summary['fields']['ann_file_resolved'] = join_like_root(data_root, node['ann_file'])
        if isinstance(node['ann_file'], str) and node['ann_file'] and not data_root and not os.path.isabs(node['ann_file']):
            summary['warnings'].append(
                'ann_file is relative but data_root is empty')
    if 'data_prefix' in node:
        prefix = node['data_prefix']
        if isinstance(prefix, dict):
            summary['fields']['data_prefix_resolved'] = {
                key: join_like_root(data_root, value)
                for key, value in prefix.items()
            }
        else:
            summary['fields']['data_prefix_resolved'] = join_like_root(data_root, prefix)
            if isinstance(prefix, str) and prefix and not data_root and not os.path.isabs(prefix):
                summary['warnings'].append(
                    'data_prefix is relative but data_root is empty')

    if 'pipeline' in node:
        summary['children'].append(summarize_pipeline(node['pipeline'], f'{path}.pipeline'))

    if 'dataset' in node:
        child = node['dataset']
        summary['children'].append(summarize_dataset_like(child, f'{path}.dataset'))
    if 'datasets' in node:
        child = node['datasets']
        if isinstance(child, list):
            for idx, item in enumerate(child):
                summary['children'].append(
                    summarize_dataset_like(item, f'{path}.datasets[{idx}]'))
        else:
            summary['children'].append(summarize_dataset_like(child, f'{path}.datasets'))

    if info['kind'] == 'string' and not summary['registry_hits'] and type_name not in DATASET_FRIENDLY_NOTES:
        summary['warnings'].append('dataset type is not registered in DATASETS')

    return summary


def render_text_block(block: Dict[str, Any], indent: int = 0) -> List[str]:
    pad = '  ' * indent
    lines: List[str] = []
    header = block.get('path', 'block')
    type_name = block.get('type')
    kind = block.get('kind')
    lines.append(f'{pad}{header}:')
    if type_name is not None:
        lines.append(f'{pad}  type: {type_name} ({kind})')
    if block.get('module'):
        lines.append(f'{pad}  module: {block["module"]}')
    if block.get('registry_hits'):
        lines.append(f'{pad}  registries: {", ".join(block["registry_hits"])}')
    if block.get('note'):
        lines.append(f'{pad}  note: {block["note"]}')

    fields = block.get('fields', {})
    for key, value in fields.items():
        lines.append(
            f'{pad}  {key}: {json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value}')

    if block.get('warnings'):
        for warning in block['warnings']:
            lines.append(f'{pad}  warning: {warning}')

    for child in block.get('children', []):
        lines.extend(render_text_block(child, indent + 1))

    for child in block.get('steps', []):
        lines.extend(render_text_block(child, indent + 1))

    if 'value' in block:
        lines.append(
            f'{pad}  value: {json.dumps(block["value"], ensure_ascii=False) if isinstance(block["value"], (dict, list)) else block["value"]}')

    return lines


def build_report(cfg, fields: List[str]) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        'config': getattr(cfg, 'filename', None),
        'default_scope': cfg.get('default_scope'),
        'custom_imports': import_custom_modules(cfg),
        'fields': [],
    }

    if not fields:
        fields = list(DEFAULT_FIELDS)

    for field in fields:
        node = get_by_path(cfg, field)
        if node is None:
            report['fields'].append({
                'path': field,
                'type': None,
                'kind': 'missing',
                'warnings': [f'path {field} not found in config'],
            })
            continue
        report['fields'].append(summarize_dataset_like(node, field))

    return report


def main() -> int:
    args = parse_args()
    load_runtime_modules()
    cfg_options = parse_cfg_options(args.cfg_options)
    cfg = load_config(args.config, cfg_options)
    register_all_modules(init_default_scope=False)
    report = build_report(cfg, args.field)

    if args.format == 'json':
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        lines = [f'config: {report["config"]}']
        if report.get('default_scope') is not None:
            lines.append(f'default_scope: {report["default_scope"]}')
        custom_imports = report.get('custom_imports', {})
        if custom_imports.get('imported'):
            imported_modules = ', '.join(item['module'] for item in custom_imports['imported'])
            lines.append(f'custom_imports imported: {imported_modules}')
        if custom_imports.get('failed'):
            for item in custom_imports['failed']:
                lines.append(f'custom_imports failed: {item["module"]} -> {item["error"]}')
        for block in report['fields']:
            lines.extend(render_text_block(block, indent=0))
        print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
