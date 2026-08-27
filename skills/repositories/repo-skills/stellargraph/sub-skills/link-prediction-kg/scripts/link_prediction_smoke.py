#!/usr/bin/env python3
"""Tiny StellarGraph link-prediction smoke.

Builds a small graph, creates a FullBatchLinkGenerator, wires a GCN embedding
stack to a link_classification head, and checks one prediction shape. No dataset
downloads or training are performed.
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
    args = parser.parse_args(argv)
    _add_repo_root(args.repo_root)

    import numpy as np
    import pandas as pd
    import tensorflow as tf
    from stellargraph import StellarGraph
    from stellargraph.mapper import FullBatchLinkGenerator
    from stellargraph.layer import GCN, LinkEmbedding, link_classification

    nodes = pd.DataFrame({"f0": [1.0, 0.0, 1.0], "f1": [0.0, 1.0, 1.0]}, index=["a", "b", "c"])
    edges = pd.DataFrame({"source": ["a", "b"], "target": ["b", "c"]})
    graph = StellarGraph(nodes, edges)

    link_ids = [("a", "b"), ("a", "c")]
    labels = np.array([1, 0], dtype="float32")

    generator = FullBatchLinkGenerator(graph, method="gcn", sparse=False)
    gcn = GCN(layer_sizes=[4], generator=generator, activations=["relu"], dropout=0.0)
    x_inp, x_out = gcn.in_out_tensors()
    embedding_model = tf.keras.Model(inputs=x_inp, outputs=x_out)

    seq = generator.flow(link_ids, labels)
    inputs, y = seq[0]
    embeddings = embedding_model.predict(inputs, verbose=0)
    # Verify the public link head on a standalone two-node embedding tensor.
    pair_input = tf.keras.Input(shape=(2, 4))
    pair_output = link_classification(output_dim=1, output_act="sigmoid", edge_embedding_method="ip")(pair_input)
    pair_model = tf.keras.Model(inputs=pair_input, outputs=pair_output)
    pair_pred = pair_model.predict(embeddings[0], verbose=0)
    print("input_shapes:", [getattr(x, "shape", None) for x in inputs])
    print("target_shape:", getattr(y, "shape", None))
    print("embedding_shape:", embeddings.shape)
    print("link_head_shape:", pair_pred.shape)
    if pair_pred.shape[-1] != 1:
        raise RuntimeError("unexpected link prediction final dimension")
    print("link prediction smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
