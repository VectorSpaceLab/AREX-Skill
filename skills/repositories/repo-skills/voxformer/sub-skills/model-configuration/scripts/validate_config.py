#!/usr/bin/env python3
"""Read-only, dependency-light VoxFormer config preflight.

The default path parses literals and simple expressions with the Python AST; it
never imports the repository or executes a config. ``--use-mmcv`` adds an
optional trusted-environment Config.fromfile check for legacy OpenMMLab users.
"""
from __future__ import annotations

import argparse
import ast
import copy
import operator
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


class _Unknown:
    pass


UNKNOWN = _Unknown()


_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
}
_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _safe_expr(node: ast.AST, env: Dict[str, Any]) -> Any:
    """Evaluate only config literal syntax and simple arithmetic."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return env.get(node.id, UNKNOWN)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values = [_safe_expr(item, env) for item in node.elts]
        if any(value is UNKNOWN for value in values):
            return UNKNOWN
        if isinstance(node, ast.Tuple):
            return tuple(values)
        if isinstance(node, ast.Set):
            return set(values)
        return values
    if isinstance(node, ast.Dict):
        result: Dict[Any, Any] = {}
        for key_node, value_node in zip(node.keys, node.values):
            if key_node is None:  # **mapping is intentionally unsupported.
                return UNKNOWN
            key = _safe_expr(key_node, env)
            value = _safe_expr(value_node, env)
            if key is UNKNOWN or value is UNKNOWN:
                return UNKNOWN
            result[key] = value
        return result
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
        value = _safe_expr(node.operand, env)
        if value is UNKNOWN:
            return UNKNOWN
        return _UNARYOPS[type(node.op)](value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        left = _safe_expr(node.left, env)
        right = _safe_expr(node.right, env)
        if left is UNKNOWN or right is UNKNOWN:
            return UNKNOWN
        try:
            return _BINOPS[type(node.op)](left, right)
        except (ArithmeticError, TypeError):
            return UNKNOWN
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id not in {"dict", "list", "tuple"}:
            return UNKNOWN
        args = [_safe_expr(arg, env) for arg in node.args]
        kwargs = {kw.arg: _safe_expr(kw.value, env) for kw in node.keywords}
        if any(value is UNKNOWN for value in args + list(kwargs.values())):
            return UNKNOWN
        try:
            if node.func.id == "dict":
                if args:
                    return dict(args[0], **kwargs)
                return kwargs
            if kwargs:
                return UNKNOWN
            return list(args) if node.func.id == "list" else tuple(args)
        except (TypeError, ValueError):
            return UNKNOWN
    return UNKNOWN


def _assign_name(target: ast.AST) -> Optional[str]:
    return target.id if isinstance(target, ast.Name) else None


def _read_assignments(path: Path) -> Tuple[Dict[str, Any], List[str]]:
    """Read top-level assignments without importing or executing the file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        raise ValueError(f"syntax error at line {exc.lineno}: {exc.msg}") from exc

    env: Dict[str, Any] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            value = _safe_expr(statement.value, env)
            for target in statement.targets:
                name = _assign_name(target)
                if name:
                    env[name] = value
        elif isinstance(statement, ast.AnnAssign):
            name = _assign_name(statement.target)
            if name and statement.value is not None:
                env[name] = _safe_expr(statement.value, env)
    base_value = env.get("_base_", [])
    if isinstance(base_value, str):
        bases = [base_value]
    elif isinstance(base_value, (list, tuple)):
        bases = [base for base in base_value if isinstance(base, str)]
    else:
        bases = []
    return env, bases


def _deep_merge(parent: Dict[str, Any], child: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(parent)
    for key, value in child.items():
        if isinstance(result.get(key), dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _load_static(path: Path, active: Optional[Iterable[Path]] = None) -> Tuple[Dict[str, Any], List[Path], List[str]]:
    path = path.resolve()
    active_paths = set(active or [])
    if path in active_paths:
        raise ValueError(f"cyclic config inheritance at {path}")
    if not path.is_file():
        raise FileNotFoundError(str(path))

    env, base_names = _read_assignments(path)
    merged: Dict[str, Any] = {}
    chain: List[Path] = []
    warnings: List[str] = []
    next_active = active_paths | {path}
    for base_name in base_names:
        base_path = (path.parent / base_name).resolve()
        if not base_path.is_file():
            warnings.append(f"missing base: {base_name} (resolved {base_path})")
            continue
        base_cfg, base_chain, base_warnings = _load_static(base_path, next_active)
        merged = _deep_merge(merged, base_cfg)
        chain.extend(base_chain)
        warnings.extend(base_warnings)
    # _base_ is metadata, not a runtime dictionary key.
    local = {key: value for key, value in env.items() if key != "_base_" and value is not UNKNOWN}
    merged = _deep_merge(merged, local)
    chain.append(path)
    return merged, chain, warnings


def _get(mapping: Any, *keys: str, default: Any = None) -> Any:
    value = mapping
    for key in keys:
        if not isinstance(value, dict):
            return default
        value = value.get(key, default)
    return value


def _fmt(value: Any) -> str:
    if value is UNKNOWN:
        return "<unresolved>"
    return repr(value)


def _volume_dims(point_cloud_range: Any, voxel_size: Any) -> Optional[List[int]]:
    if not (isinstance(point_cloud_range, (list, tuple)) and isinstance(voxel_size, (list, tuple))):
        return None
    if len(point_cloud_range) != 6 or len(voxel_size) != 3:
        return None
    try:
        dims = [(float(point_cloud_range[i + 3]) - float(point_cloud_range[i])) / float(voxel_size[i]) for i in range(3)]
        rounded = [int(round(dim)) for dim in dims]
        if any(abs(dim - rounded[i]) > 1e-5 for i, dim in enumerate(dims)):
            return None
        return rounded
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _validate(cfg: Dict[str, Any], path: Path) -> Tuple[Dict[str, Any], List[str]]:
    model = _get(cfg, "model", default={})
    train_data = _get(cfg, "data", "train", default={})
    val_data = _get(cfg, "data", "val", default={})
    test_data = _get(cfg, "data", "test", default={})
    head = _get(model, "pts_bbox_head", default={})
    cross = _get(head, "cross_transformer", default={})
    self_transformer = _get(head, "self_transformer", default={})
    temporal = _get(train_data, "temporal", default=[])
    stage = "stage-1" if model.get("type") == "LMSCNet_SS" or train_data.get("type") == "SemanticKittiDatasetStage1" else "stage-2" if model.get("type") == "VoxFormer" or train_data.get("type") == "SemanticKittiDatasetStage2" else "unknown"
    custom_3d = any("3D" in str(_get(section, "type", default="")) or "3DCustom" in str(_get(section, "type", default="")) for section in (self_transformer, _get(self_transformer, "encoder", default={}), _get(_get(self_transformer, "encoder", default={}), "transformerlayers", default={}), _get(_get(_get(self_transformer, "encoder", default={}), "transformerlayers", default={}), "attn_cfgs", default={}) if isinstance(_get(_get(self_transformer, "encoder", default={}), "transformerlayers", default={}), dict) else {})
    )
    if "deform3D" in path.name or "deform3d" in path.name.lower():
        custom_3d = True
    temporal_mode = "temporal/multi-image" if temporal else "single-image"
    warnings: List[str] = []

    if cfg.get("plugin") is not True:
        warnings.append("plugin is not True; project registries will not be imported by the tools")
    if cfg.get("plugin_dir") != "projects/mmdet3d_plugin/":
        warnings.append("plugin_dir is not the public projects/mmdet3d_plugin/ route")
    split_types = {str(section.get("type")) for section in (train_data, val_data, test_data) if isinstance(section, dict) and "type" in section}
    if len(split_types) > 1:
        warnings.append("train/val/test dataset types differ")
    if stage == "stage-1":
        if model.get("type") != "LMSCNet_SS":
            warnings.append("stage-1 dataset requires model.type=LMSCNet_SS")
        if train_data.get("type") != "SemanticKittiDatasetStage1":
            warnings.append("stage-1 model requires SemanticKittiDatasetStage1")
        if model.get("class_num") != 2:
            warnings.append("public QPN contract uses model.class_num=2")
    elif stage == "stage-2":
        if model.get("type") != "VoxFormer":
            warnings.append("stage-2 dataset requires model.type=VoxFormer")
        if train_data.get("type") != "SemanticKittiDatasetStage2":
            warnings.append("stage-2 model requires SemanticKittiDatasetStage2")
        if _get(head, "embed_dims", default=None) is None:
            warnings.append("stage-2 model is missing model.pts_bbox_head.embed_dims")
        for split_name, section in (("train", train_data), ("val", val_data), ("test", test_data)):
            if isinstance(section, dict) and section.get("temporal", temporal) != temporal:
                warnings.append(f"data.{split_name}.temporal differs from data.train.temporal")
        num_cams = cross.get("num_cams")
        self_num_cams = self_transformer.get("num_cams")
        if num_cams != self_num_cams:
            warnings.append("cross_transformer.num_cams and self_transformer.num_cams differ")
        if isinstance(num_cams, int) and temporal and num_cams != len(temporal) + 1:
            warnings.append("temporal offsets imply current image plus references, but num_cams does not match")
        if isinstance(num_cams, int) and not temporal and num_cams != 1:
            warnings.append("single-image data has no temporal offsets but num_cams is not 1")
        if not _get(model, "pretrained", "img", default=None):
            warnings.append("stage-2 model.pretrained.img is missing")
    if custom_3d and stage != "stage-2":
        warnings.append("deform3D attention is only defined for stage-2 VoxFormer presets")
    if stage == "stage-2" and _get(head, "bev_h") and _get(head, "bev_w") and _get(head, "bev_z"):
        dims = _volume_dims(cfg.get("point_cloud_range"), cfg.get("voxel_size"))
        coarse = [_get(head, "bev_h"), _get(head, "bev_w"), _get(head, "bev_z")]
        if dims and [value * 2 for value in coarse] != dims:
            warnings.append("public head coarse dimensions do not upsample by 2 to the implied full voxel volume")
    return {
        "stage": stage,
        "mode": temporal_mode,
        "custom_3d": custom_3d,
        "model": model,
        "head": head,
        "cross": cross,
        "self_transformer": self_transformer,
        "train_data": train_data,
        "val_data": val_data,
        "test_data": test_data,
    }, warnings


def _mmcv_check(path: Path) -> Tuple[str, Optional[str]]:
    try:
        from mmcv import Config  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional stack
        return "unavailable", f"{type(exc).__name__}: {exc}"
    try:
        cfg = Config.fromfile(str(path))
        model_type = cfg.get("model", {}).get("type") if hasattr(cfg.get("model", {}), "get") else None
        return "loaded", str(model_type)
    except Exception as exc:  # pragma: no cover - depends on optional stack
        return "failed", f"{type(exc).__name__}: {exc}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only static preflight for a VoxFormer Python config.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("config", help="config file to inspect")
    parser.add_argument(
        "--use-mmcv",
        action="store_true",
        help="also call mmcv.Config.fromfile in the current environment; never imports the project plugin",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    supplied = Path(args.config).expanduser()
    if not supplied.is_file():
        print(f"config not found: {args.config}", file=sys.stderr)
        return 2
    path = supplied.resolve()
    try:
        cfg, chain, inheritance_warnings = _load_static(path)
    except FileNotFoundError as exc:
        print(f"config not found: {exc.args[0]}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"config invalid: {exc}", file=sys.stderr)
        return 1

    details, warnings = _validate(cfg, path)
    warnings = inheritance_warnings + warnings
    model = details["model"]
    head = details["head"]
    cross = details["cross"]
    self_transformer = details["self_transformer"]
    train_data = details["train_data"]
    volume = _volume_dims(cfg.get("point_cloud_range"), cfg.get("voxel_size"))

    print("status: " + ("warning" if warnings else "ok"))
    print(f"config: {path}")
    print("bases: " + (", ".join(str(item) for item in chain[:-1]) if len(chain) > 1 else "none"))
    print("inheritance_chain: " + " -> ".join(str(item) for item in chain))
    print(f"stage: {details['stage']}")
    print(f"input_mode: {details['mode']}")
    print(f"attention_variant: {'custom-deform3D' if details['custom_3d'] else 'standard'}")
    print(f"model.type: {_fmt(model.get('type'))}")
    print(f"dataset.train.type: {_fmt(train_data.get('type'))}")
    print(f"dataset.val.type: {_fmt(_get(details['val_data'], 'type'))}")
    print(f"dataset.test.type: {_fmt(_get(details['test_data'], 'type'))}")
    print(f"plugin: {_fmt(cfg.get('plugin'))}")
    print(f"plugin_dir: {_fmt(cfg.get('plugin_dir'))}")
    print(f"point_cloud_range: {_fmt(cfg.get('point_cloud_range'))}")
    print(f"voxel_size: {_fmt(cfg.get('voxel_size'))}")
    print(f"implied_volume_xyz: {_fmt(volume)}")
    print(f"head.bev_h_w_z: {_fmt([head.get('bev_h'), head.get('bev_w'), head.get('bev_z')] if head else None)}")
    print(f"head.embed_dims: {_fmt(head.get('embed_dims'))}")
    print(f"transformer.num_cams: {_fmt([cross.get('num_cams'), self_transformer.get('num_cams')])}")
    print(f"data.train.temporal: {_fmt(train_data.get('temporal'))}")
    print(f"data.train.labels_tag: {_fmt(train_data.get('labels_tag'))}")
    print(f"data.train.query_tag: {_fmt(train_data.get('query_tag'))}")
    print(f"model.pretrained: {_fmt(model.get('pretrained'))}")
    print(f"load_from: {_fmt(cfg.get('load_from'))}")
    print(f"resume_from: {_fmt(cfg.get('resume_from'))}")
    print(f"checkpoint_config: {_fmt(cfg.get('checkpoint_config'))}")
    if args.use_mmcv:
        mmcv_status, mmcv_detail = _mmcv_check(path)
        print(f"mmcv: {mmcv_status}" + (f" ({mmcv_detail})" if mmcv_detail else ""))
        if mmcv_status == "failed":
            return 1
    else:
        print("mmcv: not requested")
    if warnings:
        for warning in warnings:
            print(f"warning: {warning}")
    else:
        print("warnings: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
