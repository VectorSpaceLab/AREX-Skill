#!/usr/bin/env python3
"""Static MapTR configuration checker.

This tool parses a Python/MMCV config and checks structural MapTR contracts. It
never imports the plugin, builds a model, opens a dataset, or executes a model
forward. `mmcv.Config.fromfile` evaluates the selected config and its bases, so
use it only with trusted local config files. When mmcv is unavailable, the
fallback parser intentionally reports that inherited values may be unresolved.
"""

from __future__ import print_function

import argparse
import ast
import json
import sys
import tempfile
from pathlib import Path


class _Unknown(object):
    def __repr__(self):
        return "<unresolved>"


UNKNOWN = _Unknown()


class Issue(object):
    def __init__(self, level, path, message):
        self.level = level
        self.path = path
        self.message = message

    def line(self):
        prefix = self.level.upper()
        location = (self.path + ": ") if self.path else ""
        return "{}: {}{}".format(prefix, location, self.message)


def _is_unknown(value):
    return value is UNKNOWN


def _eval_ast(node, env):
    """Evaluate the small literal subset used by the observed configs."""
    if isinstance(node, ast.Constant):
        return node.value
    # Python 3.7 compatibility for old inspection environments.
    if isinstance(node, ast.Name):
        return env.get(node.id, UNKNOWN)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values = [_eval_ast(item, env) for item in node.elts]
        kind = list if isinstance(node, ast.List) else tuple
        if isinstance(node, ast.Set):
            try:
                return set(values)
            except TypeError:
                return UNKNOWN
        return kind(values)
    if isinstance(node, ast.Dict):
        result = {}
        for key, value_node in zip(node.keys, node.values):
            if key is None:  # **mapping expansion
                value = _eval_ast(value_node, env)
                if isinstance(value, dict):
                    result.update(value)
                else:
                    return UNKNOWN
                continue
            key_value = _eval_ast(key, env)
            value = _eval_ast(value_node, env)
            if _is_unknown(key_value):
                return UNKNOWN
            result[key_value] = value
        return result
    if isinstance(node, ast.UnaryOp):
        value = _eval_ast(node.operand, env)
        if _is_unknown(value):
            return UNKNOWN
        try:
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return +value
            if isinstance(node.op, ast.Not):
                return not value
        except Exception:
            return UNKNOWN
        return UNKNOWN
    if isinstance(node, ast.BinOp):
        left = _eval_ast(node.left, env)
        right = _eval_ast(node.right, env)
        if _is_unknown(left) or _is_unknown(right):
            return UNKNOWN
        try:
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
        except Exception:
            return UNKNOWN
        return UNKNOWN
    if isinstance(node, ast.Subscript):
        value = _eval_ast(node.value, env)
        index = _eval_ast(node.slice, env)
        if _is_unknown(value) or _is_unknown(index):
            return UNKNOWN
        try:
            return value[index]
        except Exception:
            return UNKNOWN
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "dict":
            result = {}
            for positional in node.args:
                value = _eval_ast(positional, env)
                if not isinstance(value, dict):
                    return UNKNOWN
                result.update(value)
            for keyword in node.keywords:
                value = _eval_ast(keyword.value, env)
                if keyword.arg is None:
                    if not isinstance(value, dict):
                        return UNKNOWN
                    result.update(value)
                else:
                    result[keyword.arg] = value
            return result
        if isinstance(node.func, ast.Name) and node.func.id == "len" and len(node.args) == 1:
            value = _eval_ast(node.args[0], env)
            try:
                return len(value)
            except Exception:
                return UNKNOWN
        return UNKNOWN
    return UNKNOWN


def _ast_config(path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    env = {}
    for statement in tree.body:
        targets = []
        value_node = None
        if isinstance(statement, ast.Assign):
            targets = statement.targets
            value_node = statement.value
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            targets = [statement.target]
            value_node = statement.value
        if value_node is None:
            continue
        value = _eval_ast(value_node, env)
        for target in targets:
            if isinstance(target, ast.Name):
                env[target.id] = value
    return env


def _plain(value):
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if hasattr(value, "to_dict"):
        try:
            return _plain(value.to_dict())
        except Exception:
            pass
    if hasattr(value, "items"):
        try:
            return {str(key): _plain(item) for key, item in value.items()}
        except Exception:
            pass
    return value


def load_config(path):
    """Return (plain config, parser label, parser warning)."""
    try:
        from mmcv import Config  # type: ignore
    except ImportError:
        try:
            data = _ast_config(path)
        except (SyntaxError, ValueError) as exc:
            raise RuntimeError("AST fallback could not parse config: {}".format(exc))
        return data, "AST fallback", "mmcv is unavailable; _base_ inheritance and dynamic expressions may be unresolved"

    try:
        cfg = Config.fromfile(str(path))
    except Exception as exc:
        raise RuntimeError("mmcv.Config.fromfile failed: {}".format(exc))
    return _plain(cfg), "mmcv.Config", None


def get_path(root, path, default=UNKNOWN):
    current = root
    for component in path.split(".") if path else []:
        if isinstance(current, dict) and component in current:
            current = current[component]
        else:
            return default
    return current


def _walk(value, prefix=""):
    if isinstance(value, dict):
        for key, item in value.items():
            child = "{}.{}".format(prefix, key) if prefix else str(key)
            yield child, item
            for nested in _walk(item, child):
                yield nested
    elif isinstance(value, list):
        for index, item in enumerate(value):
            child = "{}[{}]".format(prefix, index)
            yield child, item
            for nested in _walk(item, child):
                yield nested


def _numbers(value, length=None):
    if _is_unknown(value) or not isinstance(value, (list, tuple)):
        return False
    if length is not None and len(value) != length:
        return False
    return all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value)


def _equal_sequence(left, right):
    if _is_unknown(left) or _is_unknown(right):
        return False
    if not isinstance(left, (list, tuple)) or not isinstance(right, (list, tuple)):
        return False
    if len(left) != len(right):
        return False
    return all(abs(float(a) - float(b)) < 1e-8 for a, b in zip(left, right))


def _append(issues, level, path, message):
    issues.append(Issue(level, path, message))


def _require(root, path, issues, inherited_possible=True):
    value = get_path(root, path)
    if _is_unknown(value):
        level = "WARN" if inherited_possible else "ERROR"
        message = "required value is unresolved"
        if inherited_possible:
            message += " (it may be supplied by _base_ inheritance)"
        _append(issues, level, path, message)
    return value


def _collect_key_paths(root, key):
    return [(path, value) for path, value in _walk(root) if path.split(".")[-1].split("[")[0] == key]


def check_config(config, config_path):
    issues = []
    required = [
        "plugin", "plugin_dir", "point_cloud_range", "map_classes",
        "input_modality", "model", "data",
    ]
    for path in required:
        _require(config, path, issues)

    plugin = get_path(config, "plugin")
    if plugin is not UNKNOWN and plugin is not True:
        _append(issues, "ERROR", "plugin", "must be True so custom registries are loaded")

    plugin_dir = get_path(config, "plugin_dir")
    plugin_path = None
    if plugin_dir is not UNKNOWN:
        if not isinstance(plugin_dir, str) or not plugin_dir.strip():
            _append(issues, "ERROR", "plugin_dir", "must be a non-empty package-relative directory")
        else:
            candidates = [Path.cwd() / plugin_dir, config_path.parent / plugin_dir]
            for candidate in candidates:
                if candidate.exists() and candidate.is_dir():
                    plugin_path = candidate.resolve()
                    break
            if plugin_path is None:
                _append(issues, "ERROR", "plugin_dir", "directory does not exist: {}".format(plugin_dir))
            else:
                if not (plugin_path / "__init__.py").exists():
                    _append(issues, "WARN", "plugin_dir", "directory exists but has no __init__.py; importability is unproven")

    pc_range = get_path(config, "point_cloud_range")
    if not _numbers(pc_range, 6):
        _append(issues, "ERROR", "point_cloud_range", "must be six numeric values [xmin,ymin,zmin,xmax,ymax,zmax]")
    elif not (pc_range[0] < pc_range[3] and pc_range[1] < pc_range[4] and pc_range[2] < pc_range[5]):
        _append(issues, "ERROR", "point_cloud_range", "minimum bounds must be smaller than maximum bounds")

    map_classes = get_path(config, "map_classes")
    if not isinstance(map_classes, (list, tuple)) or not map_classes or not all(isinstance(item, str) for item in map_classes):
        _append(issues, "ERROR", "map_classes", "must be a non-empty list of class names")

    model = get_path(config, "model")
    if isinstance(model, dict):
        model_type = model.get("type", UNKNOWN)
        if model_type is not UNKNOWN and model_type != "MapTR":
            _append(issues, "ERROR", "model.type", "must be MapTR, got {!r}".format(model_type))
        head = model.get("pts_bbox_head", UNKNOWN)
        if isinstance(head, dict):
            if head.get("type", UNKNOWN) not in (UNKNOWN, "MapTRHead"):
                _append(issues, "ERROR", "model.pts_bbox_head.type", "must be MapTRHead")
        elif head is not UNKNOWN:
            _append(issues, "ERROR", "model.pts_bbox_head", "must be a mapping")
    elif model is not UNKNOWN:
        _append(issues, "ERROR", "model", "must be a mapping")

    head = get_path(config, "model.pts_bbox_head")
    transformer = get_path(head, "transformer") if isinstance(head, dict) else UNKNOWN
    encoder = get_path(transformer, "encoder") if isinstance(transformer, dict) else UNKNOWN
    decoder = get_path(transformer, "decoder") if isinstance(transformer, dict) else UNKNOWN
    encoder_type = get_path(encoder, "type") if isinstance(encoder, dict) else UNKNOWN
    modality = get_path(config, "model.modality")
    input_modality = get_path(config, "input_modality")
    use_lidar = get_path(input_modality, "use_lidar") if isinstance(input_modality, dict) else UNKNOWN
    fusion = modality == "fusion" or use_lidar is True or get_path(transformer, "modality") == "fusion"

    if encoder_type is UNKNOWN:
        _append(issues, "WARN", "model.pts_bbox_head.transformer.encoder.type", "encoder type is unresolved")
    elif encoder_type not in ("BEVFormerEncoder", "LSSTransform"):
        _append(issues, "WARN", "model.pts_bbox_head.transformer.encoder.type", "unrecognized encoder family {!r}".format(encoder_type))

    has_gkt = any(value == "GeometryKernelAttention" for _, value in _collect_key_paths(config, "type"))
    has_bevformer_sca = any(value == "SpatialCrossAttention" for _, value in _collect_key_paths(config, "type"))
    has_lss = encoder_type == "LSSTransform"
    if fusion:
        family = "fusion + {}".format("LSS" if has_lss else "GKT" if has_gkt else "attention")
    elif has_lss:
        family = "BEV pool / LSS"
    elif has_gkt:
        family = "GKT camera"
    elif has_bevformer_sca:
        family = "BEVFormer camera"
    else:
        family = "unknown / unresolved"

    if isinstance(head, dict):
        for key in ("bev_h", "bev_w", "num_vec", "num_pts_per_vec", "num_pts_per_gt_vec"):
            _require(config, "model.pts_bbox_head." + key, issues)
        head_classes = head.get("num_classes", UNKNOWN)
        if isinstance(map_classes, (list, tuple)) and isinstance(head_classes, int) and head_classes != len(map_classes):
            _append(issues, "ERROR", "model.pts_bbox_head.num_classes", "{} does not equal len(map_classes)={}".format(head_classes, len(map_classes)))
        coder = head.get("bbox_coder", UNKNOWN)
        if isinstance(coder, dict):
            coder_range = coder.get("pc_range", UNKNOWN)
            if not _is_unknown(pc_range) and not _is_unknown(coder_range) and not _equal_sequence(pc_range, coder_range):
                _append(issues, "ERROR", "model.pts_bbox_head.bbox_coder.pc_range", "does not match top-level point_cloud_range")
            coder_classes = coder.get("num_classes", UNKNOWN)
            if isinstance(map_classes, (list, tuple)) and isinstance(coder_classes, int) and coder_classes != len(map_classes):
                _append(issues, "ERROR", "model.pts_bbox_head.bbox_coder.num_classes", "does not equal map class count")
        positional = head.get("positional_encoding", UNKNOWN)
        if encoder_type == "BEVFormerEncoder" and not isinstance(positional, dict):
            _append(issues, "ERROR", "model.pts_bbox_head.positional_encoding", "BEVFormerEncoder requires positional encoding")

    # Compare every explicit pc_range consumer other than post-center boxes.
    range_paths = []
    for path, value in _walk(config):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in ("pc_range", "point_cloud_range") and isinstance(value, (list, tuple)):
            range_paths.append((path, value))
    lidar_range = get_path(config, "lidar_point_cloud_range")
    if not _is_unknown(pc_range):
        for path, value in range_paths:
            # Fusion deliberately has a second, finer LiDAR range. The
            # nested key is still named point_cloud_range in its voxel/filter
            # dictionaries, so allow that exact secondary value.
            if fusion and _equal_sequence(value, lidar_range):
                continue
            if _is_unknown(value):
                _append(issues, "WARN", path, "range is unresolved")
            elif not _equal_sequence(pc_range, value):
                _append(issues, "ERROR", path, "does not match top-level point_cloud_range")

    train_pts = get_path(config, "train_cfg.pts")
    if _is_unknown(train_pts):
        train_pts = get_path(config, "model.train_cfg.pts")
    if isinstance(train_pts, dict):
        assigner = train_pts.get("assigner", UNKNOWN)
        if isinstance(assigner, dict) and not _is_unknown(pc_range):
            assigner_range = assigner.get("pc_range", UNKNOWN)
            if not _is_unknown(assigner_range) and not _equal_sequence(pc_range, assigner_range):
                _append(issues, "ERROR", "train_cfg.pts.assigner.pc_range", "does not match top-level point_cloud_range")

    bev_h = get_path(head, "bev_h") if isinstance(head, dict) else UNKNOWN
    bev_w = get_path(head, "bev_w") if isinstance(head, dict) else UNKNOWN
    if isinstance(config.get("data", UNKNOWN), dict) and not _is_unknown(bev_h) and not _is_unknown(bev_w):
        for split in ("train", "val", "test"):
            split_cfg = get_path(config, "data." + split)
            if isinstance(split_cfg, dict):
                bev_size = split_cfg.get("bev_size", UNKNOWN)
                if isinstance(bev_size, (list, tuple)) and len(bev_size) == 2 and (bev_size[0] != bev_h or bev_size[1] != bev_w):
                    _append(issues, "ERROR", "data.{}.bev_size".format(split), "does not match head bev_h/bev_w")
                split_classes = split_cfg.get("map_classes", UNKNOWN)
                if isinstance(map_classes, (list, tuple)) and isinstance(split_classes, (list, tuple)) and list(split_classes) != list(map_classes):
                    _append(issues, "ERROR", "data.{}.map_classes".format(split), "does not match top-level map_classes".format(split))
                fixed = split_cfg.get("fixed_ptsnum_per_line", UNKNOWN)
                gt_points = get_path(head, "num_pts_per_gt_vec") if isinstance(head, dict) else UNKNOWN
                if not _is_unknown(fixed) and not _is_unknown(gt_points) and fixed != gt_points:
                    _append(issues, "ERROR", "data.{}.fixed_ptsnum_per_line".format(split), "does not match head num_pts_per_gt_vec")

    if has_gkt:
        attention_paths = [(path, value) for path, value in _walk(config) if value == "GeometryKernelAttention"]
        # Check the nearest dictionaries containing the type.
        gkt_found = False
        for path, _ in attention_paths:
            parent_path = path.rsplit(".", 1)[0]
            parent = get_path(config, parent_path)
            if isinstance(parent, dict):
                gkt_found = True
                for key in ("embed_dims", "num_heads", "kernel_size", "num_levels"):
                    if key not in parent or _is_unknown(parent[key]):
                        _append(issues, "WARN", parent_path + "." + key, "GKT parameter is not explicit; class default may apply")
        if plugin_path is not None:
            op_path = plugin_path / "maptr" / "modules" / "ops" / "geometric_kernel_attn"
            if not op_path.exists():
                _append(issues, "WARN", "GKT", "custom-op source directory was not found under plugin_dir")
        _append(issues, "WARN", "GKT", "custom extension import, CUDA build, ABI, and forward/backward were not tested")

    if has_lss:
        dbound = get_path(config, "dbound")
        if not _numbers(dbound, 3) or dbound[2] <= 0 or dbound[1] <= dbound[0]:
            _append(issues, "ERROR", "dbound", "LSSTransform requires [min_depth,max_depth,positive_step]")
        if not isinstance(encoder, dict) or get_path(encoder, "voxel_size") is UNKNOWN:
            _append(issues, "ERROR", "model.pts_bbox_head.transformer.encoder.voxel_size", "LSSTransform requires voxel_size")
        if get_path(input_modality, "use_camera") is False:
            _append(issues, "ERROR", "input_modality.use_camera", "LSSTransform requires camera input")

    if fusion:
        if modality is not UNKNOWN and modality != "fusion":
            _append(issues, "ERROR", "model.modality", "LiDAR/fusion keys require model.modality='fusion'")
        if not isinstance(model, dict) or "lidar_encoder" not in model:
            _append(issues, "ERROR", "model.lidar_encoder", "fusion requires a lidar_encoder")
        if not isinstance(transformer, dict) or "fuser" not in transformer:
            _append(issues, "ERROR", "model.pts_bbox_head.transformer.fuser", "fusion requires a transformer fuser")
        if get_path(transformer, "modality") not in (UNKNOWN, "fusion"):
            _append(issues, "ERROR", "model.pts_bbox_head.transformer.modality", "must be fusion when a fuser is used")
        if use_lidar is False:
            _append(issues, "ERROR", "input_modality.use_lidar", "must be True for fusion")
        point_steps = [value for path, value in _walk(config) if path.endswith("type") and value in ("CustomLoadPointsFromFile", "CustomLoadPointsFromMultiSweeps")]
        collect_points = any(path.endswith("keys") and isinstance(value, list) and "points" in value for path, value in _walk(config))
        if not point_steps or not collect_points:
            _append(issues, "ERROR", "data", "fusion requires point-loading steps and collection of 'points'")

    queue = get_path(config, "queue_length")
    if not _is_unknown(queue) and (not isinstance(queue, int) or queue < 1):
        _append(issues, "ERROR", "queue_length", "must be a positive integer")

    return issues, {
        "family": family,
        "encoder": encoder_type,
        "plugin_path": str(plugin_path) if plugin_path is not None else None,
        "point_cloud_range": pc_range,
        "bev": [bev_h, bev_w],
        "map_classes": map_classes,
        "num_pts_per_vec": get_path(head, "num_pts_per_vec") if isinstance(head, dict) else UNKNOWN,
    }


def _display(value):
    return "<unresolved>" if _is_unknown(value) else repr(value)


def run(path, as_json=False):
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        print("ERROR: config: file does not exist: {}".format(path))
        return 2
    try:
        config, parser_name, parser_warning = load_config(path)
    except RuntimeError as exc:
        print("ERROR: config: {}".format(exc))
        return 2
    issues, summary = check_config(config, path)
    errors = [issue for issue in issues if issue.level == "ERROR"]
    warnings = [issue for issue in issues if issue.level == "WARN"]

    if as_json:
        payload = {
            "config": str(path),
            "parser": parser_name,
            "summary": {key: (None if _is_unknown(value) else value) for key, value in summary.items()},
            "issues": [{"level": item.level, "path": item.path, "message": item.message} for item in issues],
            "ok": not errors,
        }
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        print("config: {}".format(path))
        print("parser: {}".format(parser_name))
        if parser_warning:
            print("WARN: parser: {}".format(parser_warning))
        print("family: {}".format(summary["family"]))
        print("encoder: {}".format(_display(summary["encoder"])))
        print("plugin path: {}".format(summary["plugin_path"] or "<unresolved>"))
        print("geometry: range={}, bev={}, classes={}, points={}".format(
            _display(summary["point_cloud_range"]),
            "{}x{}".format(_display(summary["bev"][0]), _display(summary["bev"][1])),
            len(summary["map_classes"]) if isinstance(summary["map_classes"], (list, tuple)) else _display(summary["map_classes"]),
            _display(summary["num_pts_per_vec"])))
        for issue in issues:
            print(issue.line())
        if errors:
            print("FAIL: {} error(s), {} warning(s)".format(len(errors), len(warnings)))
        else:
            print("PASS: required MapTR configuration checks")
            print("WARN: plugin import and custom-op/CUDA ABI verification were not run")
    return 1 if errors else 0


def self_test():
    with tempfile.TemporaryDirectory(prefix="maptr-config-check-") as directory:
        path = Path(directory) / "invalid.py"
        path.write_text("model = dict(type='NotMapTR')\n", encoding="utf-8")
        result = run(path)
        if result == 0:
            print("SELF-TEST FAILED: invalid config unexpectedly passed")
            return 1
        print("SELF-TEST PASS: invalid config rejected")
        return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Parse and statically validate a MapTR config without importing or building a model.")
    parser.add_argument("config", nargs="?", help="Python config file to inspect")
    parser.add_argument("--json", action="store_true", help="emit machine-readable diagnostics")
    parser.add_argument("--self-test", action="store_true", help="run a tiny invalid-config rejection test")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.config:
        parser.error("the following arguments are required: config")
    return run(args.config, as_json=args.json)


if __name__ == "__main__":
    sys.exit(main())
