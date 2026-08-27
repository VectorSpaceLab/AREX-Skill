#!/usr/bin/env python3
"""Safe Fast Style Transfer environment and source-surface inspector.

This helper does not download assets, restore checkpoints, train a model, or
process images/videos. It checks optional dependencies and, when given a local
Fast Style Transfer checkout with --repo-root, imports the script modules and
builds a tiny TensorFlow graph for transform.net.

Example:
  python inspect_fast_style_transfer.py --repo-root /path/to/fast-style-transfer --json
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


def _module_status(name: str) -> Dict[str, Any]:
    try:
        mod = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(mod, "__version__", None)
    if name == "PIL":
        version = getattr(mod, "__version__", version)
    return {"name": name, "ok": True, "version": version}


def _add_repo_paths(repo_root: Path) -> None:
    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(repo_root / "src"))


def _inspect_repo(repo_root: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {"repo_root_exists": repo_root.exists(), "imports": [], "signatures": {}, "graph_smoke": None}
    if not repo_root.exists():
        result["error"] = "repo root does not exist"
        return result
    _add_repo_paths(repo_root)
    for name in ["style", "evaluate", "transform_video", "transform", "optimize", "vgg", "utils"]:
        try:
            mod = importlib.import_module(name)
            result["imports"].append({"name": name, "ok": True})
        except Exception as exc:
            result["imports"].append({"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    signature_targets = [
        ("optimize.optimize", "optimize", "optimize"),
        ("evaluate.ffwd", "evaluate", "ffwd"),
        ("evaluate.ffwd_to_img", "evaluate", "ffwd_to_img"),
        ("evaluate.ffwd_different_dimensions", "evaluate", "ffwd_different_dimensions"),
        ("evaluate.ffwd_video", "evaluate", "ffwd_video"),
        ("transform.net", "transform", "net"),
        ("vgg.net", "vgg", "net"),
        ("utils.get_img", "utils", "get_img"),
        ("utils.save_img", "utils", "save_img"),
        ("utils.scale_img", "utils", "scale_img"),
    ]
    for label, module_name, attr in signature_targets:
        try:
            obj = getattr(importlib.import_module(module_name), attr)
            result["signatures"][label] = str(inspect.signature(obj))
        except Exception as exc:
            result["signatures"][label] = f"ERROR {type(exc).__name__}: {exc}"
    try:
        import tensorflow as tf  # type: ignore
        transform = importlib.import_module("transform")
        graph = tf.Graph()
        with graph.as_default():
            x = tf.compat.v1.placeholder(tf.float32, shape=(1, 8, 8, 3), name="x")
            y = transform.net(x)
        result["graph_smoke"] = {"ok": True, "output_shape": str(y.shape)}
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["graph_smoke"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return result


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect Fast Style Transfer dependencies and optional local source modules safely.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional local Fast Style Transfer checkout to inspect.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable summary.")
    args = parser.parse_args(argv)

    report: Dict[str, Any] = {
        "dependencies": [_module_status(name) for name in ["tensorflow", "numpy", "scipy", "imageio", "PIL", "moviepy"]],
        "tensorflow_devices": None,
        "repo": None,
    }
    try:
        import tensorflow as tf  # type: ignore
        report["tensorflow_devices"] = {
            "cpu": [str(x) for x in tf.config.list_physical_devices("CPU")],
            "gpu": [str(x) for x in tf.config.list_physical_devices("GPU")],
        }
    except Exception as exc:
        report["tensorflow_devices"] = {"error": f"{type(exc).__name__}: {exc}"}

    if args.repo_root is not None:
        report["repo"] = _inspect_repo(args.repo_root.expanduser().resolve())

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Dependency status:")
        for dep in report["dependencies"]:
            suffix = f" {dep.get('version')}" if dep.get("version") else ""
            print(f"- {dep['name']}: {'ok' if dep['ok'] else 'missing'}{suffix}")
            if not dep["ok"]:
                print(f"  {dep['error']}")
        print(f"TensorFlow devices: {report['tensorflow_devices']}")
        if report["repo"] is not None:
            print("Repo inspection:")
            print(json.dumps(report["repo"], indent=2, sort_keys=True))
    failed_deps = [dep for dep in report["dependencies"] if not dep["ok"]]
    repo = report.get("repo")
    failed_repo_imports = [] if not repo else [item for item in repo.get("imports", []) if not item.get("ok")]
    return 1 if failed_deps or failed_repo_imports else 0


if __name__ == "__main__":
    raise SystemExit(main())
