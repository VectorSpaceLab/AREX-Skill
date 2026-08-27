#!/usr/bin/env python3
"""Tiny vision-model smoke test.

Instantiates the main TensorLayer image constructors with `pretrained=False`
and, if requested, runs a tiny forward pass on a synthetic image tensor.
"""

from __future__ import annotations

import argparse

import numpy as np
import tensorflow as tf
import tensorlayer as tl


def _constructors():
    return [
        ('vgg16', lambda: tl.models.vgg16(pretrained=False, end_with='outputs', mode='dynamic')),
        ('mobilenetv1', lambda: tl.models.MobileNetV1(pretrained=False, end_with='out')),
        ('resnet50', lambda: tl.models.ResNet50(pretrained=False, end_with='fc1000', n_classes=10)),
        ('squeezenetv1', lambda: tl.models.SqueezeNetV1(pretrained=False, end_with='out')),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--forward', action='store_true', help='also run a tiny synthetic forward pass')
    args = parser.parse_args()

    dummy = tf.zeros([1, 224, 224, 3], dtype=tf.float32)
    for name, make_model in _constructors():
        model = make_model()
        print(name, len(model.all_weights))
        if args.forward:
            out = model(dummy, is_train=False)
            print(name + '-output', tuple(out.shape))

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
