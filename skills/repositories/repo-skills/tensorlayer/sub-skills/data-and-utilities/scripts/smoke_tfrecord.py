#!/usr/bin/env python3
"""Tiny TFRecord round-trip smoke test.

Writes a temporary TFRecord file containing two tiny RGB images and reads the
records back with TensorFlow. The script avoids repo sample data and network
access so it can run as a self-contained data workflow smoke.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
import tensorflow as tf


def _example(image: np.ndarray, label: int) -> tf.train.Example:
    return tf.train.Example(
        features=tf.train.Features(
            feature={
                'label': tf.train.Feature(int64_list=tf.train.Int64List(value=[label])),
                'img_raw': tf.train.Feature(bytes_list=tf.train.BytesList(value=[image.tobytes()])),
            }
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--visualize', action='store_true', help='print a note after decoding to show the optional visualization branch')
    args = parser.parse_args()

    images = [np.zeros((4, 4, 3), dtype=np.uint8), np.full((4, 4, 3), 255, dtype=np.uint8)]
    labels = [0, 1]

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / 'tiny.tfrecord'
        with tf.io.TFRecordWriter(str(path)) as writer:
            for image, label in zip(images, labels):
                writer.write(_example(image, label).SerializeToString())

        decoded_labels = []
        decoded_shapes = []
        for raw in tf.data.TFRecordDataset([str(path)]):
            ex = tf.train.Example()
            ex.ParseFromString(raw.numpy())
            label = int(ex.features.feature['label'].int64_list.value[0])
            image = np.frombuffer(ex.features.feature['img_raw'].bytes_list.value[0], dtype=np.uint8).reshape(4, 4, 3)
            decoded_labels.append(label)
            decoded_shapes.append(image.shape)

    if decoded_labels != labels:
        raise AssertionError(f'label mismatch: {decoded_labels} != {labels}')
    if decoded_shapes != [img.shape for img in images]:
        raise AssertionError(f'shape mismatch: {decoded_shapes}')

    if args.visualize:
        print('visualize-note: decoded arrays are available for tl.visualize or matplotlib rendering')

    print('tfrecord-ok', decoded_labels, decoded_shapes)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
