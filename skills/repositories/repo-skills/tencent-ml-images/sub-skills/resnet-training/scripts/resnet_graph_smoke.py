#!/usr/bin/env python3
"""Smoke-check Tencent ML-Images ResNet graph construction.

The helper imports `flags` and `models.resnet` from a user-provided checkout,
sets the key graph flags, and builds a tiny placeholder graph. It is safe and
does not train, read checkpoints, or touch data files.
"""

import argparse
import pathlib
import sys


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", required=True, help="Tencent ML-Images checkout root to add to sys.path.")
    p.add_argument("--resnet-size", type=int, default=101, choices=[50, 101, 152], help="Supported ResNet depth.")
    p.add_argument("--class-num", type=int, default=1000, help="Number of output classes for the smoke graph.")
    p.add_argument("--image-size", type=int, default=224, help="Input crop size.")
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
    repo_root = pathlib.Path(a.repo_root).resolve()
    if not repo_root.exists():
        print(f"repo root does not exist: {repo_root}", file=sys.stderr)
        return 2
    sys.path.insert(0, str(repo_root))

    import tensorflow as tf  # type: ignore
    import flags  # type: ignore
    from models import resnet  # type: ignore

    # Configure the repo's flag registry before constructing the model.
    setattr(flags.FLAGS, "resnet_size", a.resnet_size)
    setattr(flags.FLAGS, "class_num", a.class_num)
    setattr(flags.FLAGS, "image_size", a.image_size)
    setattr(flags.FLAGS, "data_format", a.data_format)

    v1 = tf_v1_module(tf)
    if hasattr(v1, "disable_eager_execution"):
        v1.disable_eager_execution()
    v1.reset_default_graph()
    images = v1.placeholder(tf.float32, shape=[1, a.image_size, a.image_size, 3], name="images")
    net = resnet.ResNet(images, is_training=False)
    logits = net.build_model()
    print(f"resnet_size={a.resnet_size} data_format={a.data_format}")
    print(f"logits_shape={logits.shape.as_list()}")
    print(f"feat_shape={net.feat.shape.as_list()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
