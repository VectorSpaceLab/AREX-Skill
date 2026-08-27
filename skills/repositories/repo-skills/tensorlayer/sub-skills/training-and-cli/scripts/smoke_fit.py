#!/usr/bin/env python3
"""Tiny TensorLayer training-loop smoke test.

Creates a synthetic two-class dataset, trains a small classifier with
`tl.utils.fit`, then checks `tl.utils.test` and `tl.utils.predict`.
"""

from __future__ import annotations

import argparse

import numpy as np
import tensorflow as tf
import tensorlayer as tl


def make_data():
    X = np.array(
        [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [0.1, 0.1],
            [0.1, 0.9],
            [0.9, 0.1],
            [0.9, 0.9],
        ],
        dtype=np.float32,
    )
    y = np.array([0, 1, 1, 1, 0, 1, 1, 1], dtype=np.int64)
    return X, y


def acc(logits, labels):
    return tf.reduce_mean(
        tf.cast(tf.equal(tf.argmax(logits, 1), tf.convert_to_tensor(labels, tf.int64)), tf.float32),
        name='accuracy',
    )


def build_network():
    ni = tl.layers.Input([None, 2], name='input')
    nn = tl.layers.Dense(4, act=tf.nn.relu, name='hidden')(ni)
    nn = tl.layers.Dense(2, name='logits')(nn)
    return tl.models.Model(inputs=ni, outputs=nn, name='tiny_classifier')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--epochs', type=int, default=2, help='number of tiny training epochs')
    args = parser.parse_args()

    X, y = make_data()
    network = build_network()

    tl.utils.fit(
        network,
        train_op=tf.optimizers.Adam(learning_rate=0.05),
        cost=tl.cost.cross_entropy,
        X_train=X,
        y_train=y,
        acc=acc,
        batch_size=4,
        n_epoch=args.epochs,
        print_freq=1,
        eval_train=False,
    )

    tl.utils.test(network, acc, X, y, batch_size=None, cost=tl.cost.cross_entropy)
    logits = tl.utils.predict(network, X)
    predictions = np.argmax(logits, axis=1)

    if len(predictions) != len(y):
        raise AssertionError('prediction length mismatch')

    print('test-results', 'see tl.utils.test output above')
    print('predictions', predictions.tolist())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
