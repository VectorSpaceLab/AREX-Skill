#!/usr/bin/env python3
"""Tiny StellarGraph GCN node-classification wiring smoke.

The script builds a tiny graph, creates a FullBatchNodeGenerator, wires a GCN
stack to a Keras Dense classification head, and verifies one prediction shape.
It avoids public dataset downloads and long training.

Examples:
  python sub-skills/node-classification-gnns/scripts/gcn_node_smoke.py
  python sub-skills/node-classification-gnns/scripts/gcn_node_smoke.py --repo-root /path/to/checkout
"""

from __future__ import print_function

import argparse
import sys
from pathlib import Path


def _add_repo_root(path):
    if path:
        sys.path.insert(0, str(Path(path).expanduser().resolve()))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Optional local checkout root to prepend to sys.path.")
    parser.add_argument("--sparse", action="store_true", help="Use sparse full-batch adjacency inputs instead of dense inputs.")
    args = parser.parse_args(argv)
    _add_repo_root(args.repo_root)

    import numpy as np
    import pandas as pd
    import tensorflow as tf
    from stellargraph import StellarGraph
    from stellargraph.mapper import FullBatchNodeGenerator
    from stellargraph.layer import GCN

    nodes = pd.DataFrame(
        {"f0": [1.0, 0.0, 1.0, 0.5], "f1": [0.0, 1.0, 1.0, 0.5]},
        index=["a", "b", "c", "d"],
    )
    edges = pd.DataFrame({"source": ["a", "b", "c", "d"], "target": ["b", "c", "d", "a"]})
    graph = StellarGraph(nodes, edges)

    train_ids = ["a", "b"]
    train_targets = np.array([[1.0, 0.0], [0.0, 1.0]], dtype="float32")

    generator = FullBatchNodeGenerator(graph, method="gcn", sparse=args.sparse)
    gcn = GCN(layer_sizes=[4], generator=generator, activations=["relu"], dropout=0.0)
    x_inp, x_out = gcn.in_out_tensors()
    predictions = tf.keras.layers.Dense(units=2, activation="softmax")(x_out)
    model = tf.keras.Model(inputs=x_inp, outputs=predictions)
    model.compile(optimizer="adam", loss="categorical_crossentropy")

    sequence = generator.flow(train_ids, train_targets)
    batch_inputs, batch_targets = sequence[0]
    output = model.predict(batch_inputs, verbose=0)

    print("graph:", graph.number_of_nodes(), "nodes", graph.number_of_edges(), "edges")
    print("input_shapes:", [getattr(x, "shape", None) for x in batch_inputs])
    print("target_shape:", getattr(batch_targets, "shape", None))
    print("prediction_shape:", output.shape)
    if output.shape[-1] != 2:
        raise RuntimeError("unexpected prediction final dimension")
    print("gcn node smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
