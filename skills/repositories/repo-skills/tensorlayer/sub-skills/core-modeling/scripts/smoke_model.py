#!/usr/bin/env python3
"""Tiny TensorLayer model smoke test.

This script is safe to run from any working directory after installing the
package. It builds a tiny dense model, runs a forward pass, saves and reloads
weights, and can optionally instantiate the main pretrained image constructors
without downloading weights.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import h5py
import numpy as np
import tensorflow as tf
import tensorlayer as tl
from tensorlayer.layers import Dense, Input
from tensorlayer.models import Model


def roundtrip() -> None:
    x = Input([None, 4], name='input')
    y = Dense(3, act=tf.nn.relu, name='dense')(x)
    model = Model(inputs=x, outputs=y, name='tiny')
    model.eval()

    sample = np.ones((2, 4), dtype=np.float32)
    before = model(sample).numpy()

    def _normalize_hdf5_attrs(path: Path) -> None:
        with h5py.File(path, 'a') as f:
            def walk(group):
                for key, value in list(group.attrs.items()):
                    if isinstance(value, str):
                        group.attrs[key] = value.encode('utf8')
                    else:
                        try:
                            arr = np.asarray(value)
                        except Exception:
                            continue
                        if arr.dtype.kind in {'U', 'O'}:
                            group.attrs[key] = np.array([x.encode('utf8') if isinstance(x, str) else x for x in arr], dtype='S')
                for child in group.values():
                    if isinstance(child, h5py.Group):
                        walk(child)
            walk(f)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / 'tiny_weights.h5'
        tl.files.save_weights_to_hdf5(str(path), model)
        _normalize_hdf5_attrs(path)
        for weight in model.all_weights:
            weight.assign(tf.zeros_like(weight))
        tl.files.load_hdf5_to_weights_in_order(str(path), model)

    after = model(sample).numpy()
    if not np.allclose(before, after):
        raise AssertionError('save/load roundtrip changed the tiny model output')

    print('roundtrip-ok', tuple(after.shape))


def image_models() -> None:
    constructors = [
        ('vgg16', lambda: tl.models.vgg16(pretrained=False, end_with='outputs', mode='dynamic')),
        ('mobilenetv1', lambda: tl.models.MobileNetV1(pretrained=False, end_with='out')),
        ('resnet50', lambda: tl.models.ResNet50(pretrained=False, end_with='fc1000', n_classes=10)),
        ('squeezenetv1', lambda: tl.models.SqueezeNetV1(pretrained=False, end_with='out')),
    ]
    for name, make_model in constructors:
        model = make_model()
        print(name, len(model.all_weights))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image-models', action='store_true', help='also instantiate the main pretrained image constructors')
    args = parser.parse_args()

    roundtrip()
    if args.image_models:
        image_models()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
