#!/usr/bin/env python3
"""Verify the seq2seq-couplet runtime environment.

By default this checks the self-contained runtime bundled inside the skill. If
``--repo-root`` is supplied, it also inspects a live checkout's flat modules and
legacy server routes.
"""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import sys
from pathlib import Path

try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:  # Python 3.7
    from importlib_metadata import PackageNotFoundError, version

import tensorflow as tf

import couplet_runtime


class FakeModel:
    def infer(self, text):
        import numpy as np

        return ["风云"], np.array([1.0])


def parse_server_routes(server_file: Path):
    module = ast.parse(server_file.read_text(encoding="utf-8"))
    routes = []
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr == "route"
                    and decorator.args
                    and isinstance(decorator.args[0], ast.Str)
                ):
                    routes.append((node.name, decorator.args[0].s))
    return routes


def module_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "not-installed"


def bundled_routes():
    app = couplet_runtime.build_flask_app(FakeModel(), enable_cors=False)
    return sorted(str(rule) for rule in app.url_map.iter_rules() if rule.endpoint != "static")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check the seq2seq-couplet runtime.")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional repository checkout to compare against the bundled runtime copy.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary after the human-readable smoke output.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else None
    modules = couplet_runtime.import_repo_modules(repo_root)
    reader = modules["reader"]
    model = modules["model"]

    print("Python:", sys.version.split()[0])
    print("TensorFlow:", module_version("tensorflow"))
    print("Flask:", module_version("Flask"))
    print("gevent:", module_version("gevent"))
    print("greenlet:", module_version("greenlet"))
    print("protobuf:", module_version("protobuf"))
    print("TensorFlow built with CUDA:", tf.test.is_built_with_cuda())
    print("TensorFlow GPU available:", tf.test.is_gpu_available())

    signatures = {
        "Model.__init__": str(inspect.signature(model.Model.__init__)),
        "Model.train": str(inspect.signature(model.Model.train)),
        "Model.eval": str(inspect.signature(model.Model.eval)),
        "Model.infer": str(inspect.signature(model.Model.infer)),
        "SeqReader.__init__": str(inspect.signature(reader.SeqReader.__init__)),
    }
    for name, sig in signatures.items():
        print(f"{name}: {sig}")

    with tf.Graph().as_default():
        tensor = tf.constant([1.0, 2.0, 3.0])
        with tf.Session() as sess:
            smoke_value = sess.run(tf.reduce_sum(tensor))
    print("TensorFlow smoke:", smoke_value)

    routes = [("bundled", route) for route in bundled_routes()]
    if repo_root and (repo_root / "server.py").exists():
        routes.extend(parse_server_routes(repo_root / "server.py"))
    print("Service routes:")
    for func_name, route in routes:
        print(f"  {func_name}: {route}")

    summary = {
        "repo_root": str(repo_root) if repo_root else None,
        "tensorflow_version": module_version("tensorflow"),
        "tf_cuda": tf.test.is_built_with_cuda(),
        "tf_gpu_available": tf.test.is_gpu_available(),
        "signatures": signatures,
        "routes": routes,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
