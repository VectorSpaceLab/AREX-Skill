#!/usr/bin/env python3
"""Validate a PyG GraphGym YAML config without running training."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

KNOWN_TOP_LEVEL = {
    'accelerator', 'benchmark', 'bn', 'custom_metrics', 'dataset', 'devices',
    'gnn', 'gpu_mem', 'mem', 'metric_agg', 'metric_best', 'model',
    'num_threads', 'num_workers', 'optim', 'out_dir', 'print', 'round', 'seed',
    'share', 'tensorboard_agg', 'tensorboard_each_run', 'train', 'val',
    'view_emb',
}

KNOWN_NESTED = {
    'dataset': {
        'cache_load', 'cache_save', 'dir', 'edge_dim', 'edge_encoder',
        'edge_encoder_bn', 'edge_encoder_name', 'edge_message_ratio',
        'edge_negative_sampling_ratio', 'edge_train_mode', 'encoder',
        'encoder_bn', 'encoder_dim', 'encoder_name', 'format', 'label_column',
        'label_table', 'location', 'name', 'node_encoder', 'node_encoder_bn',
        'node_encoder_name', 'remove_feature', 'resample_disjoint',
        'resample_negative', 'shuffle_split', 'split', 'split_mode', 'task',
        'task_type', 'to_undirected', 'transform', 'transductive', 'tu_simple',
    },
    'train': {
        'auto_resume', 'batch_size', 'ckpt_clean', 'ckpt_period',
        'enable_ckpt', 'epoch_resume', 'eval_period', 'iter_per_epoch',
        'neighbor_sizes', 'node_per_graph', 'radius', 'sample_node', 'sampler',
        'skip_train_eval', 'train_parts', 'walk_length',
    },
    'val': {'node_per_graph', 'radius', 'sample_node', 'sampler'},
    'model': {
        'edge_decoding', 'graph_pooling', 'loss_fun', 'match_upper',
        'size_average', 'thresh', 'type',
    },
    'gnn': {
        'act', 'agg', 'att_final_linear', 'att_final_linear_bn', 'att_heads',
        'batchnorm', 'clear_feature', 'dim_inner', 'dropout', 'head',
        'keep_edge', 'l2norm', 'layer_type', 'layers_mp', 'layers_post_mp',
        'layers_pre_mp', 'msg_direction', 'normalize_adj', 'self_msg',
        'skip_every', 'stage_type',
    },
    'optim': {
        'base_lr', 'lr_decay', 'max_epoch', 'momentum', 'optimizer',
        'scheduler', 'steps', 'weight_decay',
    },
    'bn': {'eps', 'mom'},
    'mem': {'inplace'},
    'share': {'dim_in', 'dim_out', 'num_splits'},
}

ENUMS = {
    ('accelerator',): {'cpu', 'cuda', 'auto'},
    ('dataset', 'task'): {'node', 'edge', 'graph', 'link_pred'},
    ('dataset', 'task_type'): {
        'classification', 'regression', 'classification_binary',
        'classification_multi',
    },
    ('train', 'sampler'): {
        'full_batch', 'neighbor', 'random_node', 'saint_rw', 'saint_node',
        'saint_edge', 'cluster',
    },
    ('val', 'sampler'): {
        'full_batch', 'neighbor', 'random_node', 'saint_rw', 'saint_node',
        'saint_edge', 'cluster',
    },
    ('model', 'type'): {'gnn'},
    ('model', 'loss_fun'): {'cross_entropy', 'mse'},
    ('model', 'edge_decoding'): {'dot', 'cosine_similarity', 'concat'},
    ('model', 'graph_pooling'): {'add', 'mean', 'max'},
    ('gnn', 'layer_type'): {
        'linear', 'mlp', 'gcnconv', 'sageconv', 'gatconv', 'ginconv',
        'splineconv', 'generalconv', 'generaledgeconv', 'generalsampleedgeconv',
    },
    ('gnn', 'stage_type'): {'stack', 'skipsum', 'skipconcat'},
    ('gnn', 'act'): {'relu', 'selu', 'prelu', 'elu', 'lrelu_01', 'lrelu_025', 'lrelu_05'},
    ('gnn', 'agg'): {'add', 'mean', 'max'},
    ('optim', 'optimizer'): {'adam', 'sgd'},
    ('optim', 'scheduler'): {'none', 'step', 'steps', 'cos'},
}

POSITIVE_INTS = {
    ('devices',), ('num_threads',), ('train', 'batch_size'),
    ('train', 'eval_period'), ('train', 'ckpt_period'),
    ('train', 'iter_per_epoch'), ('gnn', 'layers_mp'),
    ('gnn', 'layers_post_mp'), ('gnn', 'dim_inner'), ('optim', 'max_epoch'),
}

NONNEGATIVE_INTS = {('seed',), ('num_workers',), ('gnn', 'layers_pre_mp')}

NUMERIC = {
    ('optim', 'base_lr'), ('optim', 'weight_decay'), ('optim', 'momentum'),
    ('optim', 'lr_decay'), ('gnn', 'dropout'), ('gnn', 'keep_edge'),
    ('bn', 'eps'), ('bn', 'mom'), ('model', 'thresh'),
}

BOOLEANS = {
    ('benchmark',), ('gpu_mem',), ('tensorboard_agg',),
    ('tensorboard_each_run',), ('view_emb',), ('dataset', 'node_encoder'),
    ('dataset', 'edge_encoder'), ('dataset', 'encoder'),
    ('dataset', 'shuffle_split'), ('dataset', 'transductive'),
    ('dataset', 'cache_save'), ('dataset', 'cache_load'),
    ('dataset', 'to_undirected'), ('train', 'enable_ckpt'),
    ('train', 'auto_resume'), ('train', 'ckpt_clean'),
    ('train', 'skip_train_eval'), ('gnn', 'batchnorm'),
    ('gnn', 'normalize_adj'), ('gnn', 'l2norm'), ('mem', 'inplace'),
}


def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def load_yaml(path: Path) -> tuple[Any | None, str | None]:
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        return None, "Missing optional dependency 'PyYAML'. Install pyyaml to parse GraphGym YAML configs."

    try:
        with path.open('r', encoding='utf-8') as handle:
            data = yaml.safe_load(handle)
    except Exception as exc:  # noqa: BLE001
        return None, f'YAML parse error: {exc}'

    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, 'Top-level YAML document must be a mapping.'
    return data, None


def path_get(config: dict[str, Any], key_path: tuple[str, ...]) -> Any:
    current: Any = config
    for key in key_path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def check_config(config: dict[str, Any], strict: bool) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    for key, value in config.items():
        if key not in KNOWN_TOP_LEVEL:
            message = f"Unknown top-level key '{key}'. If this is custom, confirm it is registered before config loading."
            (errors if strict else warnings).append(message)
        if isinstance(value, dict) and key in KNOWN_NESTED:
            for nested_key in value:
                if nested_key not in KNOWN_NESTED[key]:
                    message = f"Unknown key '{key}.{nested_key}'. If this is custom, confirm it has a registered default."
                    (errors if strict else warnings).append(message)

    for key_path, allowed in ENUMS.items():
        value = path_get(config, key_path)
        if value is not None and value not in allowed:
            dotted = '.'.join(key_path)
            warnings.append(f"{dotted}={value!r} is not one of common built-ins: {sorted(allowed)}. Custom registry keys must be imported before training.")

    for key_path in POSITIVE_INTS:
        value = path_get(config, key_path)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value <= 0):
            errors.append(f"{'.'.join(key_path)} must be a positive integer.")

    for key_path in NONNEGATIVE_INTS:
        value = path_get(config, key_path)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
            errors.append(f"{'.'.join(key_path)} must be a non-negative integer.")

    for key_path in NUMERIC:
        value = path_get(config, key_path)
        if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool)):
            errors.append(f"{'.'.join(key_path)} must be numeric.")

    for key_path in BOOLEANS:
        value = path_get(config, key_path)
        if value is not None and not isinstance(value, bool):
            errors.append(f"{'.'.join(key_path)} must be a boolean, not {type(value).__name__}.")

    split = path_get(config, ('dataset', 'split'))
    if split is not None:
        if not isinstance(split, list) or len(split) not in {2, 3}:
            errors.append('dataset.split must be a list of two or three numeric ratios.')
        elif not all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in split):
            errors.append('dataset.split must contain only numeric ratios.')
        elif not 0.99 <= sum(float(item) for item in split) <= 1.01:
            warnings.append('dataset.split ratios usually sum to 1.0.')

    if path_get(config, ('accelerator',)) in {'cuda', 'auto'}:
        warnings.append('GPU/auto accelerator may make runs machine-dependent; use accelerator: cpu for portable smoke checks.')

    max_epoch = path_get(config, ('optim', 'max_epoch'))
    if isinstance(max_epoch, int) and max_epoch > 20:
        warnings.append('optim.max_epoch is greater than 20; keep smoke configs small and ask before launching training.')

    out_dir = path_get(config, ('out_dir',))
    if isinstance(out_dir, str) and Path(out_dir).is_absolute():
        warnings.append('out_dir is absolute; public skill examples should use portable relative output paths.')

    return warnings, errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Statically validate a PyG GraphGym YAML config without running training.',
    )
    parser.add_argument('config', type=Path, help='Path to a GraphGym YAML config file.')
    parser.add_argument(
        '--strict', action='store_true',
        help='Treat unknown non-custom-looking keys as errors instead of warnings.',
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    dependency_status = {
        'yaml': module_available('yaml'),
        'yacs': module_available('yacs'),
        'pytorch_lightning': module_available('pytorch_lightning') or module_available('lightning'),
        'protobuf': module_available('google.protobuf'),
        'torch_geometric': module_available('torch_geometric'),
    }

    config, parse_error = load_yaml(args.config)
    if parse_error is not None:
        result = {
            'ok': False,
            'config': str(args.config),
            'dependency_status': dependency_status,
            'recognized_sections': [],
            'warnings': [],
            'errors': [parse_error],
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    assert isinstance(config, dict)
    warnings, errors = check_config(config, strict=args.strict)

    if not dependency_status['yacs']:
        warnings.append("GraphGym training requires the optional 'yacs' config dependency.")
    if not dependency_status['pytorch_lightning']:
        warnings.append("GraphGym training may require 'pytorch_lightning' or the compatible Lightning package.")
    if not dependency_status['protobuf']:
        warnings.append("Some GraphGym workflows may require 'protobuf'.")
    if not dependency_status['torch_geometric']:
        warnings.append("torch_geometric is not importable; install PyG before running GraphGym.")

    result = {
        'ok': not errors,
        'config': str(args.config),
        'dependency_status': dependency_status,
        'recognized_sections': sorted(key for key in config if key in KNOWN_TOP_LEVEL),
        'warnings': warnings,
        'errors': errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == '__main__':
    sys.exit(main())
