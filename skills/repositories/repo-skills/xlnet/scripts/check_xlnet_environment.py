#!/usr/bin/env python3
"""Check whether a Python runtime can inspect or run legacy XLNet source code.

This diagnostic is safe: it imports modules, reports versions, optionally adds a
caller-supplied XLNet checkout to sys.path, and validates a config JSON if one is
provided. It never downloads models, opens checkpoints, starts training, or
contacts GPU/TPU services.
"""

from __future__ import annotations

import argparse
import importlib
import json
import pathlib
import sys
from typing import Iterable, List, Optional

REQUIRED_CONFIG_KEYS = (
    "n_layer",
    "d_model",
    "n_head",
    "d_head",
    "d_inner",
    "ff_activation",
    "untie_r",
    "n_token",
)


def status(ok: bool, label: str, detail: str) -> bool:
    mark = "OK" if ok else "FAIL"
    print(f"[{mark}] {label}: {detail}")
    return ok


def add_repo_root(repo_root: Optional[str]) -> None:
    if not repo_root:
        return
    root = pathlib.Path(repo_root).expanduser().resolve()
    sys.path.insert(0, str(root))
    print(f"Using repo root for imports: {root}")


def import_one(name: str) -> bool:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic should report raw symptom.
        return status(False, f"import {name}", f"{type(exc).__name__}: {exc}")
    version = getattr(module, "__version__", "unknown")
    detail = f"loaded from {getattr(module, '__file__', 'built-in')}"
    if version != "unknown":
        detail += f" (version {version})"
    return status(True, f"import {name}", detail)


def check_tensorflow() -> bool:
    try:
        import tensorflow as tf  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return status(False, "TensorFlow", f"{type(exc).__name__}: {exc}")
    ok = True
    version = getattr(tf, "__version__", "unknown")
    ok &= status(True, "TensorFlow version", str(version))
    ok &= status(hasattr(tf, "contrib"), "tf.contrib", "present" if hasattr(tf, "contrib") else "missing; XLNet source is TensorFlow 1.x code")
    if version.startswith("2"):
        status(False, "TensorFlow major version", "TensorFlow 2.x lacks several tf.contrib APIs used by this repo")
        ok = False
    return ok


def check_cuda() -> bool:
    try:
        import tensorflow as tf  # type: ignore
        devices = tf.config.list_physical_devices("GPU") if hasattr(tf, "config") else []
    except Exception as exc:  # noqa: BLE001
        return status(False, "CUDA/GPU probe", f"TensorFlow probe failed: {type(exc).__name__}: {exc}")
    return status(True, "CUDA/GPU probe", f"TensorFlow sees {len(devices)} GPU device(s); XLNet GPU training still requires a compatible TF1.x GPU build")


def check_config(path: str) -> bool:
    p = pathlib.Path(path)
    try:
        data = json.loads(p.read_text())
    except Exception as exc:  # noqa: BLE001
        return status(False, "XLNet config JSON", f"cannot read {path}: {type(exc).__name__}: {exc}")
    missing = [key for key in REQUIRED_CONFIG_KEYS if key not in data]
    if missing:
        return status(False, "XLNet config JSON", "missing keys: " + ", ".join(missing))
    summary = ", ".join(f"{key}={data[key]!r}" for key in REQUIRED_CONFIG_KEYS)
    return status(True, "XLNet config JSON", summary)


def check_imports(names: Iterable[str]) -> bool:
    ok = True
    for name in names:
        ok &= import_one(name)
    return ok


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Diagnose a legacy XLNet TensorFlow 1.x runtime.")
    parser.add_argument("--repo-root", help="Optional XLNet source checkout to add to sys.path for source-script imports.")
    parser.add_argument("--config", help="Optional xlnet_config.json to validate.")
    parser.add_argument("--check-cuda", action="store_true", help="Also ask TensorFlow whether GPUs are visible. This is not a full training check.")
    parser.add_argument("--import", dest="imports", action="append", default=[], help="Additional module to import. Repeat as needed.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    add_repo_root(args.repo_root)
    ok = True
    ok &= check_tensorflow()
    ok &= import_one("sentencepiece")
    ok &= check_imports(["prepro_utils", "xlnet", "modeling", "function_builder", "model_utils"])
    if args.imports:
        ok &= check_imports(args.imports)
    if args.config:
        ok &= check_config(args.config)
    if args.check_cuda:
        ok &= check_cuda()
    if not ok:
        print("\nOne or more checks failed. Read the generated skill troubleshooting references before launching XLNet jobs.")
        return 1
    print("\nEnvironment checks passed for CPU/API inspection. Full GPU/TPU training still needs compatible hardware, data, and checkpoints.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
