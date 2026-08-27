#!/usr/bin/env python3
"""Check a learning-to-learn TensorFlow/Sonnet environment.

This helper is safe by default: it imports dependencies, optionally imports a
local source checkout, and optionally builds a tiny graph for the simple problem.
It does not download data, run long training, or mutate external state.

Examples:
  python check_l2l_environment.py
  python check_l2l_environment.py --repo-root /path/to/learning-to-learn --graph-smoke
"""
from __future__ import print_function

import argparse
import contextlib
import io
import json
import pathlib
import sys


def version_or_none(module):
    return getattr(module, "__version__", None)


def import_dependency(name, import_name=None):
    import importlib
    import_name = import_name or name
    try:
        module = importlib.import_module(import_name)
        return {"name": name, "ok": True, "version": version_or_none(module), "error": None}
    except Exception as exc:  # noqa: broad for diagnostic helper
        return {"name": name, "ok": False, "version": None, "error": str(exc)}


def add_repo_root(repo_root):
    root = pathlib.Path(repo_root).expanduser().resolve()
    required = ["meta.py", "networks.py", "problems.py", "preprocess.py", "util.py"]
    missing = [name for name in required if not (root / name).exists()]
    if missing:
        raise SystemExit("repo root is missing required source files: {}".format(", ".join(missing)))
    sys.path.insert(0, str(root))
    return root


def source_imports(repo_root):
    add_repo_root(repo_root)
    import importlib
    results = []
    for name in ["preprocess", "networks", "problems", "meta", "util"]:
        try:
            importlib.import_module(name)
            results.append({"module": name, "ok": True, "error": None})
        except Exception as exc:  # noqa: broad for diagnostic helper
            results.append({"module": name, "ok": False, "error": str(exc)})
    return results


def graph_smoke(repo_root):
    add_repo_root(repo_root)
    try:
        import tensorflow as tf
        import meta
        import problems
        import networks
    except Exception as exc:  # noqa: broad for diagnostic helper
        return {"ok": False, "error": "import failed: {}".format(exc)}
    try:
        tf.reset_default_graph()
        problem = problems.simple()
        optimizer = meta.MetaOptimizer(net={
            "net": "CoordinateWiseDeepLSTM",
            "net_options": {"layers": (), "initializer": "zeros"},
        })
        build_log = io.StringIO()
        with contextlib.redirect_stdout(build_log):
            info = optimizer.meta_loss(problem, 2)
        for op in getattr(info, "reset", []):
            mark_used = getattr(op, "mark_used", None)
            if mark_used is not None:
                mark_used()
        net = networks.Sgd(learning_rate=0.1)
        gradient = tf.constant([1.0, -2.0])
        update, _ = net(gradient, net.initial_state_for_inputs(gradient))
        with tf.Session() as sess:
            update_value = sess.run(update).tolist()
        return {
            "ok": True,
            "meta_loss_shape": info.loss.get_shape().as_list(),
            "fx_shape": info.fx.get_shape().as_list(),
            "sgd_update": update_value,
            "meta_build_log_lines": len(build_log.getvalue().splitlines()),
        }
    except Exception as exc:  # noqa: broad for diagnostic helper
        return {"ok": False, "error": str(exc)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None, help="source checkout containing root learning-to-learn modules")
    parser.add_argument("--graph-smoke", action="store_true", help="build and run a tiny CPU graph smoke; requires --repo-root")
    args = parser.parse_args(argv)

    deps = [
        import_dependency("tensorflow"),
        import_dependency("sonnet"),
        import_dependency("numpy"),
        import_dependency("dill"),
        import_dependency("mock"),
    ]
    result = {"dependencies": deps}
    try:
        import tensorflow as tf
        result["tensorflow_has_contrib"] = hasattr(tf, "contrib")
    except Exception:
        result["tensorflow_has_contrib"] = False

    if args.repo_root:
        result["source_imports"] = source_imports(args.repo_root)
    if args.graph_smoke:
        if not args.repo_root:
            raise SystemExit("--graph-smoke requires --repo-root")
        result["graph_smoke"] = graph_smoke(args.repo_root)

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
