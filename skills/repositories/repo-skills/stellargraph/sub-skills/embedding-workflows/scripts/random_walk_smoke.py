#!/usr/bin/env python3
"""Tiny StellarGraph random-walk smoke for embedding workflows.

Generates uniform, biased, and heterogeneous metapath walks on small in-memory
graphs. It does not train Word2Vec/Gensim or neural embedding models.
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
    from stellargraph import IndexedArray, StellarGraph
    from stellargraph.data import BiasedRandomWalk, UniformRandomMetaPathWalk, UniformRandomWalk

    nodes = pd.DataFrame({"x": [1.0, 0.0, 1.0]}, index=["a", "b", "c"])
    edges = pd.DataFrame({"source": ["a", "b", "c"], "target": ["b", "c", "a"]})
    graph = StellarGraph(nodes, edges)
    print("uniform:", UniformRandomWalk(graph, seed=1).run(["a"], n=2, length=4))
    print("biased:", BiasedRandomWalk(graph, seed=2).run(["a"], n=1, length=4, p=1.0, q=1.0))

    h_nodes = {
        "user": IndexedArray(np.empty((2, 0), dtype="float32"), index=["u1", "u2"]),
        "group": IndexedArray(np.empty((1, 0), dtype="float32"), index=["g1"]),
    }
    h_edges = {
        "belongs": pd.DataFrame({"source": ["u1", "u2"], "target": ["g1", "g1"]})
    }
    h_graph = StellarGraph(h_nodes, h_edges)
    metapath = UniformRandomMetaPathWalk(h_graph, seed=3).run(
        nodes=["u1"], n=1, length=3, metapaths=[["user", "group", "user"]]
    )
    print("metapath:", metapath)
    print("random walk smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
