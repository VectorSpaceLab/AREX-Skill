#!/usr/bin/env python3
"""Tiny StellarGraph generator shape smoke.

Builds small in-memory graphs and inspects representative generator batches.
The script avoids dataset downloads, training, GPU requirements, and services.

Examples:
  python sub-skills/sampling-generators/scripts/generator_shape_smoke.py
  python sub-skills/sampling-generators/scripts/generator_shape_smoke.py --repo-root /path/to/checkout
"""

from __future__ import print_function

import argparse
import sys
from pathlib import Path


def _add_repo_root(path):
    if path:
        sys.path.insert(0, str(Path(path).expanduser().resolve()))


def _shape(x):
    return getattr(x, "shape", None)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Optional local checkout root to prepend to sys.path.")
    args = parser.parse_args(argv)
    _add_repo_root(args.repo_root)

    import numpy as np
    import pandas as pd
    from stellargraph import StellarGraph
    from stellargraph.data import BiasedRandomWalk, UniformRandomWalk
    from stellargraph.mapper import FullBatchNodeGenerator, GraphSAGENodeGenerator, FullBatchLinkGenerator

    nodes = pd.DataFrame({"x": [1.0, 0.0, 1.0, 0.5], "y": [0.0, 1.0, 1.0, 0.5]}, index=["a", "b", "c", "d"])
    edges = pd.DataFrame({"source": ["a", "b", "c", "d"], "target": ["b", "c", "d", "a"]})
    graph = StellarGraph(nodes, edges)

    walks = UniformRandomWalk(graph, seed=1).run(nodes=["a"], n=2, length=3)
    biased = BiasedRandomWalk(graph, seed=2).run(nodes=["a"], n=1, length=4, p=1.0, q=1.0)
    print("uniform_walks:", walks)
    print("biased_walks:", biased)

    full = FullBatchNodeGenerator(graph, method="gcn", sparse=False)
    full_seq = full.flow(["a", "b"], np.eye(2, dtype="float32"))
    full_inputs, full_y = full_seq[0]
    print("full_batch_node input_shapes:", [_shape(x) for x in full_inputs], "target_shape:", _shape(full_y))

    link = FullBatchLinkGenerator(graph, method="gcn", sparse=False)
    link_seq = link.flow([("a", "b"), ("b", "d")], np.array([1, 0]))
    link_inputs, link_y = link_seq[0]
    print("full_batch_link input_shapes:", [_shape(x) for x in link_inputs], "target_shape:", _shape(link_y))

    sage = GraphSAGENodeGenerator(graph, batch_size=2, num_samples=[2])
    sage_seq = sage.flow(["a", "b"], np.array([[1.0], [0.0]]))
    sage_inputs, sage_y = sage_seq[0]
    print("graphsage_node input_shapes:", [_shape(x) for x in sage_inputs], "target_shape:", _shape(sage_y))

    print("generator shape smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
