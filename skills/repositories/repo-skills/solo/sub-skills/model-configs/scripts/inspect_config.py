#!/usr/bin/env python3
"""Read-only summary of a legacy MMDetection-style config.

This intentionally uses a restricted AST evaluator. It does not import the
config, import project code, load checkpoints, access datasets, or evaluate
arbitrary Python calls. Expressions/calls/imports are reported as unresolved.
"""
from __future__ import print_function

import argparse
import ast
import json
import sys
from pathlib import Path


class Unresolved(object):
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return "<unresolved:{}>".format(self.text)


def safe_eval(node, env):
    if hasattr(ast, "Constant") and isinstance(node, ast.Constant):
        return node.value
    # Use node type names instead of isinstance(ast.Str/ast.Num) so current
    # Python versions do not emit deprecation warnings for legacy aliases.
    if type(node).__name__ == "Str":  # Python 3.5 compatibility
        return node.s
    if type(node).__name__ == "Num":
        return node.n
    if isinstance(node, ast.Name):
        return env.get(node.id, Unresolved(node.id))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        # Configs commonly spell dictionaries as dict(type='...'). Supporting
        # only these non-executable constructors keeps the parser read-only.
        if node.func.id == "dict":
            out = {}
            for arg in node.args:
                value = safe_eval(arg, env)
                if not isinstance(value, dict):
                    return Unresolved("dict-arg")
                out.update(value)
            for keyword in node.keywords:
                value = safe_eval(keyword.value, env)
                if keyword.arg is None:
                    if not isinstance(value, dict):
                        return Unresolved("dict-unpack")
                    out.update(value)
                else:
                    out[keyword.arg] = value
            return out
        if node.func.id == "range":
            values = [safe_eval(arg, env) for arg in node.args]
            if all(isinstance(value, int) for value in values) and 1 <= len(values) <= 3:
                return list(range(*values))
        return Unresolved(node.func.id + "(...)")
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        values = [safe_eval(item, env) for item in node.elts]
        typ = {ast.Tuple: tuple, ast.List: list, ast.Set: set}[type(node)]
        return typ(values)
    if isinstance(node, ast.Dict):
        out = {}
        for key, value in zip(node.keys, node.values):
            if key is None:
                return Unresolved("dict-unpack")
            key = safe_eval(key, env)
            value = safe_eval(value, env)
            if isinstance(key, Unresolved):
                return Unresolved("dict-key")
            out[key] = value
        return out
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        value = safe_eval(node.operand, env)
        if isinstance(value, (int, float)):
            return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub,
                                                               ast.Mult, ast.Div,
                                                               ast.FloorDiv)):
        left, right = safe_eval(node.left, env), safe_eval(node.right, env)
        if not isinstance(left, Unresolved) and not isinstance(right, Unresolved):
            try:
                return {
                    ast.Add: lambda: left + right,
                    ast.Sub: lambda: left - right,
                    ast.Mult: lambda: left * right,
                    ast.Div: lambda: left / right,
                    ast.FloorDiv: lambda: left // right,
                }[type(node.op)]()
            except (KeyError, TypeError, ZeroDivisionError):
                pass
    return Unresolved(ast.unparse(node) if hasattr(ast, "unparse") else node.__class__.__name__)


def load_assignments(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    env = {}
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
            if isinstance(target, ast.Name):
                env[target.id] = safe_eval(statement.value, env)
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            env[statement.target.id] = safe_eval(statement.value, env)
    return env


def get_path(value, *keys):
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def clean(value):
    if isinstance(value, Unresolved):
        return value.text
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [clean(v) for v in value]
    return value


def summarize(path):
    env = load_assignments(path)
    model = env.get("model", {})
    summary = {
        "config": path.name,
        "top_level_keys": sorted(env.keys()),
        "model": clean(model),
        "model_type": clean(get_path(model, "type")),
        "backbone_type": clean(get_path(model, "backbone", "type")),
        "neck_type": clean(get_path(model, "neck", "type")),
        "head_type": clean(get_path(model, "bbox_head", "type")),
        "mask_feat_head_type": clean(get_path(model, "mask_feat_head", "type")),
        "backbone_keys": sorted(get_path(model, "backbone").keys())
        if isinstance(get_path(model, "backbone"), dict) else [],
        "neck_keys": sorted(get_path(model, "neck").keys())
        if isinstance(get_path(model, "neck"), dict) else [],
        "head_keys": sorted(get_path(model, "bbox_head").keys())
        if isinstance(get_path(model, "bbox_head"), dict) else [],
        "train_cfg": clean(env.get("train_cfg")),
        "test_cfg": clean(env.get("test_cfg")),
        "unresolved": [],
    }

    def collect(value, location):
        if isinstance(value, Unresolved):
            summary["unresolved"].append({"key": location, "expression": value.text})
        elif isinstance(value, dict):
            for key, item in value.items():
                collect(item, "{}.{}".format(location, key))
        elif isinstance(value, (list, tuple, set)):
            for index, item in enumerate(value):
                collect(item, "{}[{}]".format(location, index))

    collect(model, "model")
    collect(env.get("train_cfg"), "train_cfg")
    collect(env.get("test_cfg"), "test_cfg")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="Summarize a legacy model config safely")
    parser.add_argument("config", type=Path, help="user-provided config file")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)
    if not args.config.is_file():
        parser.error("config is not a regular file: {}".format(args.config))
    try:
        result = summarize(args.config)
    except (OSError, SyntaxError, UnicodeError) as exc:
        print("inspect_config: {}".format(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("config: {}".format(result["config"]))
        for key in ("model_type", "backbone_type", "neck_type", "head_type", "mask_feat_head_type"):
            print("{}: {}".format(key, result[key]))
        print("top_level_keys: {}".format(", ".join(result["top_level_keys"])))
        for key in ("backbone_keys", "neck_keys", "head_keys"):
            print("{}: {}".format(key, ", ".join(result[key])))
        print("train_cfg: {}".format(result["train_cfg"]))
        print("test_cfg: {}".format(result["test_cfg"]))
        if result["unresolved"]:
            print("unresolved:")
            for item in result["unresolved"]:
                print("  {} = {}".format(item["key"], item["expression"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
