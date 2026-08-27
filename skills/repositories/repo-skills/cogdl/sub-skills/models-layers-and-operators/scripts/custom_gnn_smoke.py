#!/usr/bin/env python3
"""Exercise a toy CogDL GNN on CPU without downloading data."""

from __future__ import annotations

import argparse
import json
from pprint import pprint


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer", choices=["gcn", "gat"], default="gcn")
    parser.add_argument("--nodes", type=int, default=3)
    parser.add_argument("--in-feats", type=int, default=3)
    parser.add_argument("--out-feats", type=int, default=2)
    parser.add_argument("--nhead", type=int, default=2)
    parser.add_argument("--json", action="store_true", help="print JSON instead of a pretty dict")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    import torch
    from cogdl.data import Graph
    from cogdl.layers import GATLayer, GCNLayer

    x = torch.eye(args.nodes, args.in_feats, dtype=torch.float32)
    edge_index = (
        torch.tensor([0, 1, 2], dtype=torch.long),
        torch.tensor([1, 2, 0], dtype=torch.long),
    )
    graph = Graph(x=x, edge_index=edge_index)
    graph.sym_norm()

    if args.layer == "gcn":
        layer = GCNLayer(args.in_feats, args.out_feats)
        output = layer(graph, graph.x)
    else:
        layer = GATLayer(args.in_feats, args.out_feats, nhead=args.nhead)
        output = layer(graph, graph.x)

    payload = {
        "layer": args.layer,
        "input_shape": list(graph.x.shape),
        "output_shape": list(output.shape),
        "num_nodes": graph.num_nodes,
        "num_edges": graph.num_edges,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        pprint(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
