#!/usr/bin/env python3
"""Check a local tensorflow-yolov3 working copy without running training/inference.

This skill-owned helper validates the common legacy environment prerequisites:
TensorFlow 1.x API availability, relative config path visibility, class/anchor
files, optional imports, and optional YOLOV3 graph construction.

Example:
  python scripts/check_environment.py --repo-root /path/to/tensorflow-yolov3 --build-graph
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import os
from pathlib import Path
import sys


def status(ok: bool, label: str, detail: str = "") -> bool:
    prefix = "PASS" if ok else "FAIL"
    print(f"[{prefix}] {label}" + (f": {detail}" if detail else ""))
    return ok


@contextlib.contextmanager
def repo_context(repo_root: Path):
    old_cwd = Path.cwd()
    old_path = list(sys.path)
    sys.path.insert(0, str(repo_root))
    os.chdir(str(repo_root))
    try:
        yield
    finally:
        os.chdir(str(old_cwd))
        sys.path[:] = old_path


def check_file(path: Path, label: str, required: bool = True) -> bool:
    exists = path.exists()
    if required:
        return status(exists, label, str(path) if exists else f"missing: {path}")
    return status(True, label, str(path) if exists else f"optional missing: {path}")


def parse_anchors(path: Path) -> bool:
    try:
        raw = path.read_text().strip().splitlines()[0]
        vals = [float(x.strip()) for x in raw.split(",") if x.strip()]
    except Exception as exc:  # noqa: BLE001 - friendly CLI diagnostic
        return status(False, "anchor file parse", str(exc))
    return status(len(vals) == 18, "anchor file has 18 numeric values", f"found {len(vals)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check TensorFlow 1.x and config prerequisites for tensorflow-yolov3.")
    parser.add_argument("--repo-root", default=".", help="Path to a tensorflow-yolov3 working copy")
    parser.add_argument("--classes", default="data/classes/coco.names", help="Class-name file relative to repo root or absolute")
    parser.add_argument("--anchors", default="data/anchors/basline_anchors.txt", help="Anchor file relative to repo root or absolute")
    parser.add_argument("--build-graph", action="store_true", help="Build a YOLOV3 graph for a 416x416 input without running a session")
    parser.add_argument("--skip-tensorflow", action="store_true", help="Skip TensorFlow/core imports and only check files")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).expanduser().resolve()
    ok = True
    ok &= check_file(repo_root / "core" / "config.py", "core/config.py")
    ok &= check_file(repo_root / "core" / "yolov3.py", "core/yolov3.py")

    classes = Path(args.classes).expanduser()
    if not classes.is_absolute():
        classes = repo_root / classes
    anchors = Path(args.anchors).expanduser()
    if not anchors.is_absolute():
        anchors = repo_root / anchors
    ok &= check_file(classes, "class-name file")
    ok &= check_file(anchors, "anchor file")
    if anchors.exists():
        ok &= parse_anchors(anchors)
    if classes.exists():
        names = [line.strip() for line in classes.read_text().splitlines() if line.strip()]
        ok &= status(bool(names), "class file non-empty", f"{len(names)} classes")

    optional_imports = ["numpy", "cv2", "PIL", "easydict"]
    for module in optional_imports:
        try:
            imported = importlib.import_module(module)
            detail = getattr(imported, "__version__", "imported")
            ok &= status(True, f"import {module}", str(detail))
        except Exception as exc:  # noqa: BLE001
            ok &= status(False, f"import {module}", str(exc))

    if args.skip_tensorflow:
        return 0 if ok else 2

    try:
        import tensorflow as tf  # type: ignore
        ok &= status(True, "import tensorflow", getattr(tf, "__version__", "unknown"))
        ok &= status(hasattr(tf, "Session"), "TensorFlow has tf.Session")
        ok &= status(hasattr(tf, "placeholder"), "TensorFlow has tf.placeholder")
        ok &= status(hasattr(tf, "layers"), "TensorFlow has tf.layers")
    except Exception as exc:  # noqa: BLE001
        status(False, "import tensorflow", str(exc))
        return 2

    try:
        with repo_context(repo_root):
            from core.config import cfg  # type: ignore
            import core.utils as utils  # type: ignore

            ok &= status(True, "import core.config/core.utils from repo root")
            ok &= status(Path(cfg.YOLO.CLASSES).exists(), "cfg.YOLO.CLASSES resolves from repo root", cfg.YOLO.CLASSES)
            ok &= status(Path(cfg.YOLO.ANCHORS).exists(), "cfg.YOLO.ANCHORS resolves from repo root", cfg.YOLO.ANCHORS)
            ok &= status(len(utils.read_class_names(str(classes))) == len([line for line in classes.read_text().splitlines() if line.strip()]), "read_class_names returns expected count")
            ok &= status(tuple(utils.get_anchors(str(anchors)).shape) == (3, 3, 2), "get_anchors shape is (3,3,2)")

            if args.build_graph:
                from core.yolov3 import YOLOV3  # type: ignore
                tf.reset_default_graph()
                input_data = tf.placeholder(dtype=tf.float32, shape=(1, 416, 416, 3), name="input_data")
                model = YOLOV3(input_data, trainable=False)
                expected = ([1, 52, 52, 3, 85], [1, 26, 26, 3, 85], [1, 13, 13, 3, 85])
                actual = (
                    model.pred_sbbox.shape.as_list(),
                    model.pred_mbbox.shape.as_list(),
                    model.pred_lbbox.shape.as_list(),
                )
                ok &= status(actual == expected, "YOLOV3 default COCO graph shapes", str(actual))
    except Exception as exc:  # noqa: BLE001
        ok &= status(False, "repo core smoke", str(exc))

    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
