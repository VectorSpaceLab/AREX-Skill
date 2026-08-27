#!/usr/bin/env python3
"""Safely summarize a UniAD config file.

The script evaluates a restricted subset of Python config syntax without
executing the config file. It is intended for quick inspection of the public
UniAD configs and other similar OpenMMLab-style config files that mostly use
literal dict/list expressions.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional


UNRESOLVED = object()
SAFE_NAME_BINDINGS: Dict[str, Any] = {
    "None": None,
    "True": True,
    "False": False,
}


class SafeConfigEvaluator:
    """Evaluate a small, safe subset of Python expressions."""

    def __init__(self) -> None:
        self.env: Dict[str, Any] = dict(SAFE_NAME_BINDINGS)
        self.unresolved_assignments: List[str] = []
        self.base_files: List[str] = []

    def eval(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return self.env.get(node.id, UNRESOLVED)
        if isinstance(node, ast.List):
            return self._eval_sequence(node.elts, list)
        if isinstance(node, ast.Tuple):
            return self._eval_sequence(node.elts, tuple)
        if isinstance(node, ast.Set):
            return self._eval_sequence(node.elts, set)
        if isinstance(node, ast.Dict):
            keys = [self.eval(key) for key in node.keys]
            values = [self.eval(value) for value in node.values]
            if any(item is UNRESOLVED for item in keys + values):
                return UNRESOLVED
            return dict(zip(keys, values))
        if isinstance(node, ast.UnaryOp):
            value = self.eval(node.operand)
            if value is UNRESOLVED:
                return UNRESOLVED
            if isinstance(node.op, ast.UAdd):
                return +value
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.Not):
                return not value
            if isinstance(node.op, ast.Invert):
                return ~value
            return UNRESOLVED
        if isinstance(node, ast.BinOp):
            left = self.eval(node.left)
            right = self.eval(node.right)
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
            values = [self.eval(value) for value in node.values]
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
            left = self.eval(node.left)
            if left is UNRESOLVED:
                return UNRESOLVED
            current = left
            for op, comparator in zip(node.ops, node.comparators):
                right = self.eval(comparator)
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
                elif isinstance(op, ast.In):
                    ok = current in right
                elif isinstance(op, ast.NotIn):
                    ok = current not in right
                else:
                    return UNRESOLVED
                if not ok:
                    return False
                current = right
            return True
        if isinstance(node, ast.IfExp):
            test = self.eval(node.test)
            if test is UNRESOLVED:
                return UNRESOLVED
            return self.eval(node.body if test else node.orelse)
        if isinstance(node, ast.JoinedStr):
            pieces: List[str] = []
            for part in node.values:
                if isinstance(part, ast.Constant):
                    pieces.append(str(part.value))
                elif isinstance(part, ast.FormattedValue):
                    value = self.eval(part.value)
                    if value is UNRESOLVED:
                        return UNRESOLVED
                    pieces.append(str(value))
                else:
                    return UNRESOLVED
            return "".join(pieces)
        if isinstance(node, ast.Call):
            return self._eval_call(node)
        if isinstance(node, ast.Subscript):
            value = self.eval(node.value)
            if value is UNRESOLVED:
                return UNRESOLVED
            index = self._eval_slice(node.slice)
            if index is UNRESOLVED:
                return UNRESOLVED
            try:
                return value[index]
            except Exception:
                return UNRESOLVED
        return UNRESOLVED

    def _eval_sequence(self, elements: Iterable[ast.AST], factory):
        values = [self.eval(element) for element in elements]
        if any(value is UNRESOLVED for value in values):
            return UNRESOLVED
        return factory(values)

    def _eval_slice(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Index):  # pragma: no cover - Python <3.9 compatibility
            return self.eval(node.value)
        if isinstance(node, ast.Slice):
            lower = self.eval(node.lower) if node.lower else None
            upper = self.eval(node.upper) if node.upper else None
            step = self.eval(node.step) if node.step else None
            if UNRESOLVED in {lower, upper, step}:
                return UNRESOLVED
            return slice(lower, upper, step)
        return self.eval(node)

    def _eval_call(self, node: ast.Call) -> Any:
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name == "dict":
                return self._eval_dict_call(node)
            if name in {"list", "tuple", "set"}:
                if len(node.args) != 1 or node.keywords:
                    return UNRESOLVED
                value = self.eval(node.args[0])
                if value is UNRESOLVED:
                    return UNRESOLVED
                try:
                    return {"list": list, "tuple": tuple, "set": set}[name](value)
                except Exception:
                    return UNRESOLVED
            if name in {"max", "min", "len", "sum", "sorted", "str", "int", "float", "bool", "abs"}:
                args = [self.eval(arg) for arg in node.args]
                if any(arg is UNRESOLVED for arg in args):
                    return UNRESOLVED
                kwargs = {kw.arg: self.eval(kw.value) for kw in node.keywords if kw.arg is not None}
                if any(value is UNRESOLVED for value in kwargs.values()):
                    return UNRESOLVED
                try:
                    return self._call_safe_builtin(name, args, kwargs)
                except Exception:
                    return UNRESOLVED
        return UNRESOLVED

    def _eval_dict_call(self, node: ast.Call) -> Any:
        result: Dict[Any, Any] = {}
        for keyword in node.keywords:
            if keyword.arg is None:
                extra = self.eval(keyword.value)
                if extra is UNRESOLVED or not isinstance(extra, Mapping):
                    return UNRESOLVED
                result.update(extra)
            else:
                value = self.eval(keyword.value)
                if value is UNRESOLVED:
                    return UNRESOLVED
                result[keyword.arg] = value
        if node.args:
            if len(node.args) != 1:
                return UNRESOLVED
            positional = self.eval(node.args[0])
            if positional is UNRESOLVED:
                return UNRESOLVED
            if isinstance(positional, Mapping):
                result.update(positional)
            else:
                try:
                    result.update(dict(positional))
                except Exception:
                    return UNRESOLVED
        return result

    def _call_safe_builtin(self, name: str, args: List[Any], kwargs: Dict[str, Any]) -> Any:
        if name == "max":
            return max(*args, **kwargs)
        if name == "min":
            return min(*args, **kwargs)
        if name == "len":
            return len(*args)
        if name == "sum":
            return sum(*args, **kwargs)
        if name == "sorted":
            return sorted(*args, **kwargs)
        if name == "str":
            return str(*args, **kwargs)
        if name == "int":
            return int(*args, **kwargs)
        if name == "float":
            return float(*args, **kwargs)
        if name == "bool":
            return bool(*args, **kwargs)
        if name == "abs":
            return abs(*args, **kwargs)
        return UNRESOLVED

    def record_assignment(self, target: str, value: Any) -> None:
        if value is UNRESOLVED:
            self.unresolved_assignments.append(target)
        else:
            self.env[target] = value
            if target == "_base_":
                if isinstance(value, str):
                    self.base_files = [value]
                elif isinstance(value, list):
                    self.base_files = [str(item) for item in value]


def parse_config(path: Path) -> Dict[str, Any]:
    text = path.read_text()
    tree = ast.parse(text, filename=str(path))
    evaluator = SafeConfigEvaluator()

    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            if len(stmt.targets) != 1:
                continue
            target = stmt.targets[0]
            if isinstance(target, ast.Name):
                evaluator.record_assignment(target.id, evaluator.eval(stmt.value))
        elif isinstance(stmt, ast.AnnAssign):
            if isinstance(stmt.target, ast.Name) and stmt.value is not None:
                evaluator.record_assignment(stmt.target.id, evaluator.eval(stmt.value))

    return build_summary(path, evaluator)


def build_summary(path: Path, evaluator: SafeConfigEvaluator) -> Dict[str, Any]:
    env = evaluator.env
    model = env.get("model") if isinstance(env.get("model"), Mapping) else {}
    data = env.get("data") if isinstance(env.get("data"), Mapping) else {}
    train = data.get("train") if isinstance(data.get("train"), Mapping) else {}
    val = data.get("val") if isinstance(data.get("val"), Mapping) else {}
    test = data.get("test") if isinstance(data.get("test"), Mapping) else {}

    def head_type(name: str) -> Optional[str]:
        value = model.get(name)
        if isinstance(value, Mapping):
            maybe = value.get("type")
            return str(maybe) if maybe is not None else None
        return None

    head_types = {
        "pts_bbox_head": head_type("pts_bbox_head"),
        "seg_head": head_type("seg_head"),
        "motion_head": head_type("motion_head"),
        "occ_head": head_type("occ_head"),
        "planning_head": head_type("planning_head"),
    }

    motion_head = model.get("motion_head") if isinstance(model.get("motion_head"), Mapping) else {}
    warnings: List[str] = []
    if env.get("plugin") is not True:
        warnings.append("plugin flag is not enabled")
    plugin_dir = env.get("plugin_dir")
    if plugin_dir not in {"projects/mmdet3d_plugin/", "projects/mmdet3d_plugin"}:
        warnings.append("plugin_dir does not point at the public UniAD plugin package")
    if env.get("queue_length") is not None and model.get("queue_length") is not None:
        if env.get("queue_length") != model.get("queue_length"):
            warnings.append("top-level queue_length and model.queue_length differ")
    if env.get("queue_length") is not None and train.get("queue_length") is not None:
        if env.get("queue_length") != train.get("queue_length"):
            warnings.append("top-level queue_length and data.train.queue_length differ")
    if model and "motion_head" in model and isinstance(motion_head, Mapping):
        if not motion_head.get("anchor_info_path"):
            warnings.append("motion head is present but anchor_info_path is missing")
    planning_strategy = env.get("planning_evaluation_strategy")
    if planning_strategy not in {None, "uniad", "stp3"}:
        warnings.append("planning_evaluation_strategy is not one of the known public values")

    return {
        "path": str(path),
        "base_files": evaluator.base_files,
        "plugin": env.get("plugin"),
        "plugin_dir": plugin_dir,
        "dataset_type": env.get("dataset_type"),
        "data_root": env.get("data_root"),
        "info_root": env.get("info_root"),
        "load_from": env.get("load_from"),
        "queue_length": env.get("queue_length"),
        "model_type": model.get("type") if isinstance(model, Mapping) else None,
        "model_queue_length": model.get("queue_length") if isinstance(model, Mapping) else None,
        "train_queue_length": train.get("queue_length") if isinstance(train, Mapping) else None,
        "val_queue_length": val.get("queue_length") if isinstance(val, Mapping) else None,
        "test_queue_length": test.get("queue_length") if isinstance(test, Mapping) else None,
        "head_types": head_types,
        "freeze_flags": {
            "freeze_img_backbone": model.get("freeze_img_backbone") if isinstance(model, Mapping) else None,
            "freeze_img_neck": model.get("freeze_img_neck") if isinstance(model, Mapping) else None,
            "freeze_bn": model.get("freeze_bn") if isinstance(model, Mapping) else None,
            "freeze_bev_encoder": model.get("freeze_bev_encoder") if isinstance(model, Mapping) else None,
        },
        "planning_evaluation_strategy": planning_strategy,
        "motion_anchor_path": motion_head.get("anchor_info_path") if isinstance(motion_head, Mapping) else None,
        "task_loss_weight": model.get("task_loss_weight") if isinstance(model, Mapping) else None,
        "warnings": warnings,
        "unresolved_assignments": evaluator.unresolved_assignments,
    }


def format_summary(summary: Mapping[str, Any]) -> str:
    lines: List[str] = []
    lines.append("UniAD config summary")
    lines.append(f"- path: {summary.get('path')}")
    if summary.get("base_files"):
        lines.append(f"- bases: {', '.join(str(item) for item in summary['base_files'])}")
    lines.append(f"- plugin: {summary.get('plugin')}")
    lines.append(f"- plugin_dir: {summary.get('plugin_dir')}")
    lines.append(f"- model.type: {summary.get('model_type')}")
    lines.append(f"- queue_length: {summary.get('queue_length')}")
    if summary.get("model_queue_length") is not None:
        lines.append(f"- model.queue_length: {summary.get('model_queue_length')}")
    if summary.get("train_queue_length") is not None:
        lines.append(f"- data.train.queue_length: {summary.get('train_queue_length')}")
    if summary.get("val_queue_length") is not None:
        lines.append(f"- data.val.queue_length: {summary.get('val_queue_length')}")
    if summary.get("test_queue_length") is not None:
        lines.append(f"- data.test.queue_length: {summary.get('test_queue_length')}")
    lines.append(f"- dataset_type: {summary.get('dataset_type')}")
    lines.append(f"- data_root: {summary.get('data_root')}")
    lines.append(f"- info_root: {summary.get('info_root')}")
    lines.append(f"- load_from: {summary.get('load_from')}")
    lines.append("- heads:")
    head_types = summary.get("head_types") or {}
    for key in ["pts_bbox_head", "seg_head", "motion_head", "occ_head", "planning_head"]:
        lines.append(f"  - {key}: {head_types.get(key)}")
    lines.append("- freeze flags:")
    freeze_flags = summary.get("freeze_flags") or {}
    for key in ["freeze_img_backbone", "freeze_img_neck", "freeze_bn", "freeze_bev_encoder"]:
        lines.append(f"  - {key}: {freeze_flags.get(key)}")
    lines.append(f"- planning_evaluation_strategy: {summary.get('planning_evaluation_strategy')}")
    lines.append(f"- motion_anchor_path: {summary.get('motion_anchor_path')}")
    lines.append(f"- task_loss_weight: {summary.get('task_loss_weight')}")
    if summary.get("warnings"):
        lines.append("- warnings:")
        for warning in summary["warnings"]:
            lines.append(f"  - {warning}")
    if summary.get("unresolved_assignments"):
        lines.append("- unresolved assignments:")
        for name in summary["unresolved_assignments"]:
            lines.append(f"  - {name}")
    return "\n".join(lines)


def to_jsonable(value: Any) -> Any:
    if value is UNRESOLVED:
        return "<unresolved>"
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, set):
        return [to_jsonable(item) for item in sorted(value, key=repr)]
    return value


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Path to a UniAD config file")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    args = parser.parse_args(argv)

    config_path = args.config
    if not config_path.is_file():
        print(f"error: config file not found: {config_path}", file=sys.stderr)
        return 2

    try:
        summary = parse_config(config_path)
    except SyntaxError as exc:
        print(f"error: could not parse {config_path}: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - defensive boundary
        print(f"error: failed to summarize {config_path}: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(to_jsonable(summary), indent=2, sort_keys=True))
    else:
        print(format_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
