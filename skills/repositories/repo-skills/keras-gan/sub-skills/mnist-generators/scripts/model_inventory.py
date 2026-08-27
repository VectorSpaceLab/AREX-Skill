#!/usr/bin/env python3
"""Static inventory for Keras-GAN standalone MNIST-style scripts.

This script parses source files with ast. It does not import Keras, TensorFlow,
Matplotlib, SciPy, datasets, or any repository modules.
"""
from __future__ import print_function

import argparse
import ast
import json
import os
import re
import sys

SCRIPTS = [
    "gan/gan.py",
    "dcgan/dcgan.py",
    "cgan/cgan.py",
    "acgan/acgan.py",
    "sgan/sgan.py",
    "infogan/infogan.py",
    "lsgan/lsgan.py",
    "bgan/bgan.py",
    "bigan/bigan.py",
    "aae/aae.py",
    "cogan/cogan.py",
    "dualgan/dualgan.py",
    "wgan/wgan.py",
    "wgan_gp/wgan_gp.py",
]

SPECIAL_METHODS = set([
    "wasserstein_loss",
    "gradient_penalty_loss",
    "boundary_loss",
    "mutual_info_loss",
    "sample_generator_input",
    "sample_images",
    "sample_interval",
    "save_imgs",
    "save_model",
])


def call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = call_name(node.value)
        return (parent + "." if parent else "") + node.attr
    if isinstance(node, ast.Call):
        return call_name(node.func)
    return None


def expr(node):
    """Render enough expression detail for an inventory; no ast.unparse needed."""
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        return repr(node.value)
    node_type = node.__class__.__name__
    # Python 3.7 can still emit Num/Str/NameConstant nodes. Avoid direct
    # ast.Num/ast.Str isinstance checks because newer Python versions warn.
    if node_type == "Num":
        return repr(node.n)
    if node_type == "Str":
        return repr(node.s)
    if node_type == "NameConstant":
        return repr(node.value)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = expr(node.value)
        return (base + "." if base else "") + node.attr
    if isinstance(node, ast.Tuple):
        return "(" + ", ".join(expr(x) for x in node.elts) + ("," if len(node.elts) == 1 else "") + ")"
    if isinstance(node, ast.List):
        return "[" + ", ".join(expr(x) for x in node.elts) + "]"
    if isinstance(node, ast.Dict):
        pairs = []
        for k, v in zip(node.keys, node.values):
            pairs.append("%s: %s" % (expr(k), expr(v)))
        return "{" + ", ".join(pairs) + "}"
    if isinstance(node, ast.Call):
        args = [expr(a) for a in node.args]
        args.extend("%s=%s" % (kw.arg, expr(kw.value)) for kw in node.keywords if kw.arg)
        return "%s(%s)" % (expr(node.func), ", ".join(args))
    if isinstance(node, ast.keyword):
        return "%s=%s" % (node.arg, expr(node.value))
    if isinstance(node, ast.BinOp):
        return "%s %s %s" % (expr(node.left), op_name(node.op), expr(node.right))
    if isinstance(node, ast.UnaryOp):
        return "%s%s" % (op_name(node.op), expr(node.operand))
    if isinstance(node, ast.Subscript):
        return "%s[%s]" % (expr(node.value), expr(node.slice))
    if isinstance(node, ast.Index):  # Python <3.9
        return expr(node.value)
    if isinstance(node, ast.Slice):
        return "%s:%s" % (expr(node.lower) or "", expr(node.upper) or "")
    if isinstance(node, ast.Lambda):
        return "lambda"
    return ast.dump(node)


def op_name(op):
    names = {
        ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.Pow: "**",
        ast.Mod: "%", ast.USub: "-", ast.UAdd: "+",
    }
    for cls, name in names.items():
        if isinstance(op, cls):
            return name
    return op.__class__.__name__


def target_expr(node):
    if isinstance(node, ast.Tuple):
        return "(" + ", ".join(target_expr(x) for x in node.elts) + ")"
    return expr(node)


def function_signature(fn):
    args = list(fn.args.args)
    defaults = [None] * (len(args) - len(fn.args.defaults)) + list(fn.args.defaults)
    parts = []
    for arg, default in zip(args, defaults):
        if arg.arg == "self":
            continue
        if default is None:
            parts.append(arg.arg)
        else:
            parts.append("%s=%s" % (arg.arg, expr(default)))
    if fn.args.vararg:
        parts.append("*" + fn.args.vararg.arg)
    if fn.args.kwarg:
        parts.append("**" + fn.args.kwarg.arg)
    return "%s(%s)" % (fn.name, ", ".join(parts))


def import_record(node):
    if isinstance(node, ast.Import):
        return "import " + ", ".join(a.name + ((" as " + a.asname) if a.asname else "") for a in node.names)
    if isinstance(node, ast.ImportFrom):
        module = "." * node.level + (node.module or "")
        return "from %s import %s" % (module, ", ".join(a.name + ((" as " + a.asname) if a.asname else "") for a in node.names))
    return None


def compile_call_record(call):
    record = {
        "line": getattr(call, "lineno", None),
        "target": expr(call.func.value) if isinstance(call.func, ast.Attribute) else None,
        "args": [expr(a) for a in call.args],
        "keywords": {},
    }
    for kw in call.keywords:
        if kw.arg:
            record["keywords"][kw.arg] = expr(kw.value)
    return record


def collect_class(cls):
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)]
    method_records = []
    init_assignments = []
    compile_calls = []
    for method in methods:
        method_records.append({
            "name": method.name,
            "line": getattr(method, "lineno", None),
            "signature": function_signature(method),
            "special": method.name in SPECIAL_METHODS,
        })
        if method.name == "__init__":
            for node in ast.walk(method):
                if isinstance(node, ast.Assign):
                    targets = [target_expr(t) for t in node.targets]
                    if any(t.startswith("self.") or t == "optimizer" or t == "losses" or t.startswith("(self.") for t in targets):
                        init_assignments.append({"line": getattr(node, "lineno", None), "targets": targets, "value": expr(node.value)})
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "compile":
                    compile_calls.append(compile_call_record(node))
    return {
        "name": cls.name,
        "line": getattr(cls, "lineno", None),
        "bases": [expr(b) for b in cls.bases],
        "methods": method_records,
        "initAssignments": init_assignments,
        "compileCalls": compile_calls,
    }


def collect_main_train_calls(tree):
    calls = []
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test_text = expr(node.test)
        # Python 3.7 renders Compare as ast.dump; use source-independent structural check.
        looks_like_main = False
        if isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__":
            looks_like_main = True
        if not looks_like_main and "__name__" not in str(test_text):
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr == "train":
                calls.append({
                    "line": getattr(sub, "lineno", None),
                    "call": expr(sub),
                    "args": [expr(a) for a in sub.args],
                    "keywords": dict((kw.arg, expr(kw.value)) for kw in sub.keywords if kw.arg),
                })
    return calls


def regex_savefigs(text):
    found = []
    for match in re.finditer(r"fig\.savefig\((.*?)\)", text):
        found.append(match.group(1).strip())
    return found


def inventory_file(repo_root, rel_path):
    full_path = os.path.join(repo_root, rel_path)
    record = {"path": rel_path, "exists": os.path.exists(full_path)}
    if not record["exists"]:
        record["error"] = "missing"
        return record
    try:
        with open(full_path, "r") as handle:
            text = handle.read()
        tree = ast.parse(text, filename=full_path)
    except Exception as exc:  # SyntaxError or read problems
        record["error"] = "%s: %s" % (exc.__class__.__name__, exc)
        return record
    record.update({
        "imports": [import_record(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))],
        "classes": [collect_class(n) for n in tree.body if isinstance(n, ast.ClassDef)],
        "mainTrainCalls": collect_main_train_calls(tree),
        "savefigTargets": regex_savefigs(text),
    })
    return record


def print_human(inventory):
    print("Keras-GAN standalone MNIST-generator inventory")
    print("Repo root: %s" % inventory["repoRoot"])
    print("Scripts inspected: %d" % len(inventory["scripts"]))
    for script in inventory["scripts"]:
        print("\n- %s" % script["path"])
        if not script.get("exists"):
            print("  MISSING")
            continue
        if script.get("error"):
            print("  ERROR: %s" % script["error"])
            continue
        print("  imports: %s" % "; ".join(script.get("imports") or []))
        for cls in script.get("classes", []):
            method_names = [m["name"] for m in cls.get("methods", [])]
            print("  class %s(line %s): methods=%s" % (cls["name"], cls.get("line"), ", ".join(method_names)))
            train_methods = [m["signature"] for m in cls.get("methods", []) if m["name"] == "train"]
            special_methods = [m["signature"] for m in cls.get("methods", []) if m.get("special")]
            if train_methods:
                print("    train: %s" % "; ".join(train_methods))
            if special_methods:
                print("    special: %s" % "; ".join(special_methods))
            interesting = []
            for item in cls.get("initAssignments", []):
                targets = ", ".join(item["targets"])
                if any(key in targets for key in ["img_shape", "img_dim", "latent_dim", "num_classes", "n_critic", "clip_value"]):
                    interesting.append("%s=%s" % (targets, item["value"]))
            if interesting:
                print("    init facts: %s" % "; ".join(interesting))
            for compile_call in cls.get("compileCalls", []):
                pieces = []
                for key in sorted(compile_call.get("keywords", {})):
                    if key in ("loss", "optimizer", "metrics", "loss_weights"):
                        pieces.append("%s=%s" % (key, compile_call["keywords"][key]))
                print("    compile: %s.compile(%s)" % (compile_call.get("target"), ", ".join(pieces)))
        if script.get("mainTrainCalls"):
            print("  __main__ train calls:")
            for call in script["mainTrainCalls"]:
                print("    line %s: %s" % (call.get("line"), call.get("call")))
        if script.get("savefigTargets"):
            print("  savefig targets: %s" % "; ".join(script["savefigTargets"]))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Static AST inventory for Keras-GAN standalone MNIST-style generator scripts.")
    parser.add_argument("--repo-root", required=True, help="Path to a Keras-GAN checkout to inspect.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable report.")
    args = parser.parse_args(argv)

    repo_root = os.path.abspath(args.repo_root)
    inventory = {
        "schemaVersion": 1,
        "repoRoot": repo_root,
        "safeMode": "static-ast-no-import",
        "scripts": [inventory_file(repo_root, rel) for rel in SCRIPTS],
    }
    if args.json:
        print(json.dumps(inventory, indent=2, sort_keys=True))
    else:
        print_human(inventory)
    return 0


if __name__ == "__main__":
    sys.exit(main())
