#!/usr/bin/env python3
"""Safely summarize a BEVFormer config without OpenMMLab imports.

The helper uses a static AST-based parser so it can run even when mmcv or the
original source checkout is unavailable. It resolves local _base_ files when
those files exist relative to the config path or the optional repo root.
"""

from __future__ import annotations

import argparse
import ast
import copy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


UNRESOLVED = "<unresolved>"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize a BEVFormer config in a safe static way.")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to a BEVFormer config file to inspect.")
    parser.add_argument(
        "--repo-root",
        help="Optional repo root used to resolve relative config paths.")
    return parser.parse_args()


def resolve_initial_path(raw: str, repo_root: Optional[Path]) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    if repo_root is not None:
        return (repo_root / path).resolve()
    return path.resolve()


def resolve_relative(raw: str, anchor: Path) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return (anchor / path).resolve()


def display_path(path: Path, repo_root: Optional[Path]) -> str:
    candidates = []
    if repo_root is not None:
        candidates.append(repo_root)
    candidates.append(Path.cwd().resolve())
    for candidate in candidates:
        try:
            return str(path.resolve().relative_to(candidate))
        except Exception:
            continue
    return str(path)


def is_name_assign(node: ast.AST, name: str) -> bool:
    return (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == name
    )


def is_target_assign(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(
            node.targets[0], ast.Name):
        return node.targets[0].id
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return None


def safe_eval(node: ast.AST, env: Dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return env.get(node.id, UNRESOLVED)
    if isinstance(node, ast.List):
        return [safe_eval(elem, env) for elem in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(safe_eval(elem, env) for elem in node.elts)
    if isinstance(node, ast.Set):
        return {safe_eval(elem, env) for elem in node.elts}
    if isinstance(node, ast.Dict):
        result: Dict[Any, Any] = {}
        for key_node, value_node in zip(node.keys, node.values):
            key = safe_eval(key_node, env) if key_node is not None else UNRESOLVED
            value = safe_eval(value_node, env)
            if key is UNRESOLVED:
                continue
            result[key] = value if value is not UNRESOLVED else UNRESOLVED
        return result
    if isinstance(node, ast.UnaryOp):
        operand = safe_eval(node.operand, env)
        if operand is UNRESOLVED:
            return UNRESOLVED
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.Not):
            return not operand
        if isinstance(node.op, ast.Invert):
            return ~operand
        return UNRESOLVED
    if isinstance(node, ast.BinOp):
        left = safe_eval(node.left, env)
        right = safe_eval(node.right, env)
        if left is UNRESOLVED or right is UNRESOLVED:
            return UNRESOLVED
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.FloorDiv):
            return left // right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.Pow):
            return left**right
        return UNRESOLVED
    if isinstance(node, ast.BoolOp):
        values = [safe_eval(value, env) for value in node.values]
        if any(value is UNRESOLVED for value in values):
            return UNRESOLVED
        if isinstance(node.op, ast.And):
            result = values[0]
            for value in values[1:]:
                result = result and value
            return result
        if isinstance(node.op, ast.Or):
            result = values[0]
            for value in values[1:]:
                result = result or value
            return result
        return UNRESOLVED
    if isinstance(node, ast.Compare):
        left = safe_eval(node.left, env)
        if left is UNRESOLVED:
            return UNRESOLVED
        current = left
        for op, comparator in zip(node.ops, node.comparators):
            right = safe_eval(comparator, env)
            if right is UNRESOLVED:
                return UNRESOLVED
            if isinstance(op, ast.Eq):
                ok = current == right
            elif isinstance(op, ast.NotEq):
                ok = current != right
            elif isinstance(op, ast.Lt):
                ok = current < right
            elif isinstance(op, ast.LtE):
                ok = current <= right
            elif isinstance(op, ast.Gt):
                ok = current > right
            elif isinstance(op, ast.GtE):
                ok = current >= right
            else:
                return UNRESOLVED
            if not ok:
                return False
            current = right
        return True
    if isinstance(node, ast.Call):
        func_name = node.func.id if isinstance(node.func, ast.Name) else None
        if func_name == 'dict':
            result: Dict[str, Any] = {}
            for arg in node.args:
                value = safe_eval(arg, env)
                if value is UNRESOLVED or not isinstance(value, dict):
                    return UNRESOLVED
                result.update(value)
            for keyword in node.keywords:
                value = safe_eval(keyword.value, env)
                result[keyword.arg] = value if value is not UNRESOLVED else UNRESOLVED
            return result
        if func_name == 'list' and len(node.args) == 1:
            value = safe_eval(node.args[0], env)
            if value is UNRESOLVED:
                return UNRESOLVED
            return list(value)
        if func_name == 'tuple' and len(node.args) == 1:
            value = safe_eval(node.args[0], env)
            if value is UNRESOLVED:
                return UNRESOLVED
            return tuple(value)
        if func_name == 'set' and len(node.args) == 1:
            value = safe_eval(node.args[0], env)
            if value is UNRESOLVED:
                return UNRESOLVED
            return set(value)
        return UNRESOLVED
    return UNRESOLVED


def normalize_base_list(value: Any) -> List[str]:
    if value is UNRESOLVED or value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [item for item in value if isinstance(item, str)]
    return []


def deep_merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge_dicts(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def extract_base_paths(tree: ast.Module, env: Dict[str, Any]) -> List[str]:
    last_value: Any = []
    for node in tree.body:
        if is_name_assign(node, '_base_'):
            value = safe_eval(node.value, env)
            if value is not UNRESOLVED:
                last_value = value
    return normalize_base_list(last_value)


def load_config(path: Path, repo_root: Optional[Path], stack: Tuple[Path, ...] = ()) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    resolved = path.resolve()
    if resolved in stack:
        chain = ' -> '.join(display_path(item, repo_root) for item in stack + (resolved,))
        raise RuntimeError(f'cyclic _base_ chain detected: {chain}')

    source = resolved.read_text(encoding='utf-8')
    tree = ast.parse(source, filename=str(resolved))

    direct_bases = extract_base_paths(tree, {})
    merged_env: Dict[str, Any] = {}
    missing_bases: List[str] = []

    next_stack = stack + (resolved,)
    for raw_base in direct_bases:
        base_path = resolve_relative(raw_base, resolved.parent)
        if not base_path.exists():
            missing_bases.append(display_path(base_path, repo_root))
            continue
        base_env, _ = load_config(base_path, repo_root, next_stack)
        merged_env = deep_merge_dicts(merged_env, base_env)

    env = copy.deepcopy(merged_env)
    for node in tree.body:
        target_name = is_target_assign(node)
        if target_name is None or target_name == '_base_':
            continue
        value_node = node.value if isinstance(node, ast.Assign) else node.value
        value = safe_eval(value_node, env)
        if value is not UNRESOLVED:
            env[target_name] = value

    meta = {
        'path': resolved,
        'direct_bases': direct_bases,
        'missing_bases': missing_bases,
    }
    return env, meta


def lookup(mapping: Dict[str, Any], path: Sequence[str], default: Any = None) -> Any:
    current: Any = mapping
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def first_non_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def fmt(value: Any) -> str:
    if value is None:
        return '(not set)'
    if value is UNRESOLVED:
        return UNRESOLVED
    if isinstance(value, str):
        return value
    return repr(value)


def print_section(title: str) -> None:
    print(f'== {title} ==')


def summarize(cfg: Dict[str, Any], meta: Dict[str, Any], config_path: Path, repo_root: Optional[Path]) -> None:
    model = cfg.get('model', {}) if isinstance(cfg.get('model', {}), dict) else {}
    data = cfg.get('data', {}) if isinstance(cfg.get('data', {}), dict) else {}
    train = data.get('train', {}) if isinstance(data.get('train', {}), dict) else {}
    val = data.get('val', {}) if isinstance(data.get('val', {}), dict) else {}
    test = data.get('test', {}) if isinstance(data.get('test', {}), dict) else {}
    pts_head = model.get('pts_bbox_head', {}) if isinstance(model.get('pts_bbox_head', {}), dict) else {}
    transformer = pts_head.get('transformer', {}) if isinstance(pts_head.get('transformer', {}), dict) else {}
    encoder = transformer.get('encoder', {}) if isinstance(transformer.get('encoder', {}), dict) else {}
    decoder = transformer.get('decoder', {}) if isinstance(transformer.get('decoder', {}), dict) else {}
    img_backbone = model.get('img_backbone', {}) if isinstance(model.get('img_backbone', {}), dict) else {}
    img_neck = model.get('img_neck', {}) if isinstance(model.get('img_neck', {}), dict) else {}
    train_cfg_value = model.get('train_cfg')
    if not isinstance(train_cfg_value, dict):
        train_cfg_value = cfg.get('train_cfg', {})
    train_cfg = train_cfg_value if isinstance(train_cfg_value, dict) else {}
    train_pts = train_cfg.get('pts', {}) if isinstance(train_cfg.get('pts', {}), dict) else {}
    optimizer = cfg.get('optimizer', {}) if isinstance(cfg.get('optimizer', {}), dict) else {}
    lr_config = cfg.get('lr_config', {}) if isinstance(cfg.get('lr_config', {}), dict) else {}
    runner = cfg.get('runner', {}) if isinstance(cfg.get('runner', {}), dict) else {}
    evaluation = cfg.get('evaluation', {}) if isinstance(cfg.get('evaluation', {}), dict) else {}

    print_section('path')
    print(f'config: {display_path(config_path, repo_root)}')
    if repo_root is not None:
        print(f'repo_root: {display_path(repo_root, repo_root)}')
    print('parser: static AST')

    print_section('inheritance')
    bases = meta.get('direct_bases', [])
    if bases:
        for base in bases:
            base_path = resolve_relative(base, config_path.parent)
            print(f'- {display_path(base_path, repo_root)}')
    else:
        print('(no _base_ entries found)')
    if meta.get('missing_bases'):
        print('missing:')
        for item in meta['missing_bases']:
            print(f'- {item}')

    print_section('plugin')
    print(f'plugin: {fmt(cfg.get("plugin"))}')
    print(f'plugin_dir: {fmt(cfg.get("plugin_dir"))}')

    print_section('model')
    print(f'type: {fmt(model.get("type"))}')
    print(f'use_grid_mask: {fmt(model.get("use_grid_mask"))}')
    print(f'video_test_mode: {fmt(model.get("video_test_mode"))}')
    if 'frames' in model:
        print(f'frames: {fmt(model.get("frames"))}')
    if 'queue_length' in cfg:
        print(f'queue_length: {fmt(cfg.get("queue_length"))}')
    if 'num_levels' in model:
        print(f'num_levels: {fmt(model.get("num_levels"))}')
    if 'num_mono_levels' in model:
        print(f'num_mono_levels: {fmt(model.get("num_mono_levels"))}')
    if 'mono_loss_weight' in model:
        print(f'mono_loss_weight: {fmt(model.get("mono_loss_weight"))}')
    if 'group_detr' in pts_head:
        print(f'group_detr: {fmt(pts_head.get("group_detr"))}')
    if 'load_from' in cfg:
        print(f'load_from: {fmt(cfg.get("load_from"))}')
    if 'pretrained' in model:
        print(f'pretrained: {fmt(model.get("pretrained"))}')

    print('backbone:')
    print(f'- type: {fmt(img_backbone.get("type"))}')
    for key in ('depth', 'out_indices', 'with_cp', 'style', 'norm_cfg', 'stage_with_dcn'):
        if key in img_backbone:
            print(f'- {key}: {fmt(img_backbone.get(key))}')
    print('neck:')
    print(f'- type: {fmt(img_neck.get("type"))}')
    for key in ('in_channels', 'out_channels', 'num_outs', 'start_level'):
        if key in img_neck:
            print(f'- {key}: {fmt(img_neck.get(key))}')

    print('head:')
    print(f'- type: {fmt(pts_head.get("type"))}')
    for key in ('bev_h', 'bev_w', 'num_query', 'num_classes', 'with_box_refine', 'as_two_stage'):
        if key in pts_head:
            print(f'- {key}: {fmt(pts_head.get(key))}')
    if isinstance(transformer, dict) and transformer:
        print(f'- transformer.type: {fmt(transformer.get("type"))}')
        if 'frames' in transformer:
            print(f'- transformer.frames: {fmt(transformer.get("frames"))}')
        if 'inter_channels' in transformer:
            print(f'- transformer.inter_channels: {fmt(transformer.get("inter_channels"))}')
        if 'num_fusion' in transformer:
            print(f'- transformer.num_fusion: {fmt(transformer.get("num_fusion"))}')
        print(f'- encoder.type: {fmt(encoder.get("type"))}')
        for key in ('num_layers', 'num_points_in_pillar', 'return_intermediate', 'dataset_type'):
            if key in encoder:
                print(f'- encoder.{key}: {fmt(encoder.get(key))}')
        print(f'- decoder.type: {fmt(decoder.get("type"))}')
        if 'num_layers' in decoder:
            print(f'- decoder.num_layers: {fmt(decoder.get("num_layers"))}')
        attn_cfgs = lookup(encoder, ('transformerlayers', 'attn_cfgs'), [])
        if isinstance(attn_cfgs, list):
            print(f'- encoder.attn_cfgs: {[item.get("type") if isinstance(item, dict) else item for item in attn_cfgs]}')
        dec_attn_cfgs = lookup(decoder, ('transformerlayers', 'attn_cfgs'), [])
        if isinstance(dec_attn_cfgs, list):
            print(f'- decoder.attn_cfgs: {[item.get("type") if isinstance(item, dict) else item for item in dec_attn_cfgs]}')
    if 'bbox_coder' in pts_head:
        bbox_coder = pts_head.get('bbox_coder', {})
        print(f'- bbox_coder.type: {fmt(bbox_coder.get("type"))}')
        for key in ('max_num', 'num_classes', 'score_threshold'):
            if key in bbox_coder:
                print(f'- bbox_coder.{key}: {fmt(bbox_coder.get(key))}')
    if 'positional_encoding' in pts_head:
        pos = pts_head.get('positional_encoding', {})
        print(f'- positional_encoding.type: {fmt(pos.get("type"))}')
        for key in ('num_feats', 'row_num_embed', 'col_num_embed'):
            if key in pos:
                print(f'- positional_encoding.{key}: {fmt(pos.get(key))}')

    if 'fcos3d_bbox_head' in model:
        mono_head = model.get('fcos3d_bbox_head', {})
        print(f'- fcos3d_bbox_head.type: {fmt(mono_head.get("type"))}')
        for key in ('num_classes', 'in_channels', 'strides', 'box3d_on'):
            if key in mono_head:
                print(f'- fcos3d_bbox_head.{key}: {fmt(mono_head.get(key))}')

    print_section('data')
    print(f'samples_per_gpu: {fmt(data.get("samples_per_gpu"))}')
    print(f'workers_per_gpu: {fmt(data.get("workers_per_gpu"))}')
    for split_name, split in (('train', train), ('val', val), ('test', test)):
        if not isinstance(split, dict) or not split:
            continue
        print(f'{split_name}:')
        for key in ('type', 'data_root', 'ann_file', 'test_mode', 'use_valid_flag', 'bev_size', 'queue_length', 'frames', 'box_type_3d'):
            if key in split:
                print(f'- {key}: {fmt(split.get(key))}')
        if 'modality' in split:
            modality = split.get('modality', {}) if isinstance(split.get('modality', {}), dict) else {}
            print(f'- modality.use_camera: {fmt(modality.get("use_camera"))}')
            print(f'- modality.use_external: {fmt(modality.get("use_external"))}')
            print(f'- modality.use_lidar: {fmt(modality.get("use_lidar"))}')
        if 'mono_cfg' in split:
            mono_cfg = split.get('mono_cfg', {}) if isinstance(split.get('mono_cfg', {}), dict) else {}
            print(f'- mono_cfg.name: {fmt(mono_cfg.get("name"))}')
            print(f'- mono_cfg.data_root: {fmt(mono_cfg.get("data_root"))}')
            print(f'- mono_cfg.min_num_lidar_points: {fmt(mono_cfg.get("min_num_lidar_points"))}')
            print(f'- mono_cfg.min_box_visibility: {fmt(mono_cfg.get("min_box_visibility"))}')

    print_section('schedule')
    if optimizer:
        print(f'optimizer.type: {fmt(optimizer.get("type"))}')
        for key in ('lr', 'weight_decay'):
            if key in optimizer:
                print(f'optimizer.{key}: {fmt(optimizer.get(key))}')
    if lr_config:
        print(f'lr_config.policy: {fmt(lr_config.get("policy"))}')
        if 'step' in lr_config:
            print(f'lr_config.step: {fmt(lr_config.get("step"))}')
        if 'min_lr_ratio' in lr_config:
            print(f'lr_config.min_lr_ratio: {fmt(lr_config.get("min_lr_ratio"))}')
    if runner:
        print(f'runner.type: {fmt(runner.get("type"))}')
        if 'max_epochs' in runner:
            print(f'runner.max_epochs: {fmt(runner.get("max_epochs"))}')
    if 'total_epochs' in cfg:
        print(f'total_epochs: {fmt(cfg.get("total_epochs"))}')
    if evaluation:
        print(f'evaluation.interval: {fmt(evaluation.get("interval"))}')

    print_section('train_cfg')
    if train_pts:
        print(f'grid_size: {fmt(train_pts.get("grid_size"))}')
        print(f'voxel_size: {fmt(train_pts.get("voxel_size"))}')
        print(f'point_cloud_range: {fmt(train_pts.get("point_cloud_range"))}')
        print(f'out_size_factor: {fmt(train_pts.get("out_size_factor"))}')
        assigner = train_pts.get('assigner', {}) if isinstance(train_pts.get('assigner', {}), dict) else {}
        print(f'assigner.type: {fmt(assigner.get("type"))}')
    else:
        print('(no pts train_cfg detected)')

    if cfg.get('plugin') and cfg.get('plugin_dir'):
        print_section('routing note')
        print('plugin import is required before any build-time config inspection.')
        print('dataset layout, distributed launch, and analysis tasks are routed to their dedicated sub-skills.')


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else None
    config_path = resolve_initial_path(args.config, repo_root)
    if not config_path.exists():
        print(f'config not found: {display_path(config_path, repo_root)}', file=sys.stderr)
        return 2

    try:
        cfg, meta = load_config(config_path, repo_root)
    except Exception as exc:
        print(f'failed to inspect config: {exc}', file=sys.stderr)
        return 1

    summarize(cfg, meta, config_path, repo_root)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
