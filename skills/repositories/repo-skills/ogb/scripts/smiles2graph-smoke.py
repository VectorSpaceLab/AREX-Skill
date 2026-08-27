#!/usr/bin/env python3
"""Run a tiny rdkit-backed OGB molecule-to-graph smoke test."""

from __future__ import annotations

from ogb.utils import smiles2graph


def main() -> None:
    graph = smiles2graph("CCO")
    print("num_nodes:", graph["num_nodes"])
    print("edge_index_shape:", graph["edge_index"].shape)
    print("node_feat_shape:", graph["node_feat"].shape)
    print("edge_feat_shape:", graph["edge_feat"].shape)


if __name__ == "__main__":
    main()
