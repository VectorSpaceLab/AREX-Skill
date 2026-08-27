#!/usr/bin/env python3
"""Check a TensorFlow 1.x/OpenCV runtime for Tencent ML-Images workflows.

This script is safe: it imports dependencies, optionally imports `flags` and
`models.resnet` from a user-provided checkout, and optionally builds a tiny graph.
It does not train, download data, or restore checkpoints.
"""

import argparse
import pathlib
import sys


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", help="Optional Tencent ML-Images checkout root to inspect.")
    p.add_argument("--smoke-graph", action="store_true", help="Build a tiny ResNet graph after importing the checkout.")
    p.add_argument("--resnet-size", type=int, default=101, choices=[50, 101, 152], help="ResNet depth for graph smoke.")
    p.add_argument("--class-num", type=int, default=1000, help="Class count for graph smoke.")
    p.add_argument("--image-size", type=int, default=224, help="Input image size for graph smoke.")
    p.add_argument("--data-format", default="NCHW", choices=["NCHW", "NHWC"], help="TensorFlow data format string.")
    return p.parse_args()


def tf_v1_module(tf):
    compat = getattr(tf, "compat", None)
    try:
        return getattr(compat, "v1") if compat is not None else tf
    except Exception:
        return tf


def main() -> int:
    a = parse_args()
    # Prevent TensorFlow/absl flag parsing from seeing this helper's argparse flags.
    sys.argv = [sys.argv[0]]
    errors = []
    try:
        import tensorflow as tf  # type: ignore
        print(f"tensorflow={getattr(tf, '__version__', 'unknown')}")
        for name in ["app", "contrib", "gfile", "python_io", "layers"]:
            print(f"has_tf_{name}={hasattr(tf, name)}")
    except Exception as exc:
        print(f"ERROR importing tensorflow: {exc}", file=sys.stderr)
        return 1

    try:
        import cv2  # type: ignore
        print(f"opencv={getattr(cv2, '__version__', 'unknown')}")
    except Exception as exc:
        errors.append(f"OpenCV/cv2 import failed: {exc}")

    if a.repo_root:
        repo_root = pathlib.Path(a.repo_root).resolve()
        if not repo_root.exists():
            errors.append(f"repo root does not exist: {repo_root}")
        else:
            sys.path.insert(0, str(repo_root))
            try:
                import flags  # type: ignore
                print("repo_flags_import=ok")
            except Exception as exc:
                errors.append(f"repo flags import failed: {exc}")
                flags = None  # type: ignore
            try:
                from models import resnet  # type: ignore
                print("repo_models_resnet_import=ok")
            except Exception as exc:
                errors.append(f"repo models.resnet import failed: {exc}")
                resnet = None  # type: ignore
            try:
                from data_processing import dataset  # noqa: F401
                print("repo_data_processing_dataset_import=ok")
            except Exception as exc:
                errors.append(f"repo data_processing.dataset import failed: {exc}")
            if a.smoke_graph and not errors:
                setattr(flags.FLAGS, "resnet_size", a.resnet_size)
                setattr(flags.FLAGS, "class_num", a.class_num)
                setattr(flags.FLAGS, "image_size", a.image_size)
                setattr(flags.FLAGS, "data_format", a.data_format)
                v1 = tf_v1_module(tf)
                if hasattr(v1, "disable_eager_execution"):
                    v1.disable_eager_execution()
                v1.reset_default_graph()
                placeholder = v1.placeholder
                images = placeholder(tf.float32, shape=[1, a.image_size, a.image_size, 3], name="images")
                net = resnet.ResNet(images, is_training=False)
                logits = net.build_model()
                print(f"graph_logits_shape={logits.shape.as_list()}")
                print(f"graph_feat_shape={net.feat.shape.as_list()}")

    for msg in errors:
        print(f"ERROR: {msg}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
