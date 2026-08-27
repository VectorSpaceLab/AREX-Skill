#!/usr/bin/env python3
"""Safe DGL graph API smoke checks for the graph-apis sub-skill."""

import argparse
import json
import tempfile
from pathlib import Path


def _assert(condition, message):
    if not condition:
        raise AssertionError(message)


def check_homogeneous(dgl, torch):
    src = torch.tensor([0, 0, 1, 2], dtype=torch.int64)
    dst = torch.tensor([1, 2, 2, 3], dtype=torch.int64)
    graph = dgl.graph((src, dst), num_nodes=5, idtype=torch.int64, device=torch.device("cpu"))
    graph.ndata["feat"] = torch.arange(graph.num_nodes() * 2, dtype=torch.float32).reshape(graph.num_nodes(), 2)
    graph.edata["weight"] = torch.ones(graph.num_edges(), 1)

    _assert(graph.num_nodes() == 5, "homogeneous node count mismatch")
    _assert(graph.num_edges() == 4, "homogeneous edge count mismatch")
    _assert(graph.idtype == torch.int64, "homogeneous idtype mismatch")
    _assert(str(graph.device) == "cpu", "homogeneous graph should be on CPU")
    _assert(tuple(graph.ndata["feat"].shape) == (5, 2), "node feature shape mismatch")
    _assert(tuple(graph.edata["weight"].shape) == (4, 1), "edge feature shape mismatch")

    nodes = torch.tensor([0, 1, 2], dtype=graph.idtype, device=graph.device)
    subgraph = dgl.node_subgraph(graph, nodes)
    _assert(dgl.NID in subgraph.ndata, "node_subgraph missing original node IDs")
    _assert(dgl.EID in subgraph.edata, "node_subgraph missing original edge IDs")

    block_dst = torch.tensor([2, 3], dtype=graph.idtype, device=graph.device)
    block = dgl.to_block(graph, dst_nodes=block_dst)
    _assert(block.is_block, "to_block did not produce a block")
    _assert(dgl.NID in block.srcdata, "block missing source original node IDs")
    _assert(dgl.NID in block.dstdata, "block missing destination original node IDs")
    _assert(dgl.EID in block.edata, "block missing original edge IDs")
    return graph


def check_heterograph(dgl, torch):
    heterograph = dgl.heterograph(
        {
            ("user", "rates", "movie"): (torch.tensor([0, 1, 1]), torch.tensor([0, 0, 1])),
            ("critic", "rates", "movie"): (torch.tensor([0]), torch.tensor([1])),
            ("user", "follows", "user"): (torch.tensor([0]), torch.tensor([1])),
        },
        num_nodes_dict={"user": 3, "critic": 1, "movie": 2},
        idtype=torch.int64,
        device=torch.device("cpu"),
    )

    heterograph.nodes["user"].data["feat"] = torch.ones(heterograph.num_nodes("user"), 3)
    heterograph.nodes["critic"].data["feat"] = torch.zeros(heterograph.num_nodes("critic"), 3)
    heterograph.nodes["movie"].data["feat"] = torch.arange(heterograph.num_nodes("movie") * 3, dtype=torch.float32).reshape(heterograph.num_nodes("movie"), 3)

    user_rates = ("user", "rates", "movie")
    critic_rates = ("critic", "rates", "movie")
    heterograph.edges[user_rates].data["score"] = torch.ones(heterograph.num_edges(user_rates), 1)
    heterograph.edges[critic_rates].data["score"] = torch.zeros(heterograph.num_edges(critic_rates), 1)

    _assert(user_rates in heterograph.canonical_etypes, "missing user rates canonical etype")
    _assert(critic_rates in heterograph.canonical_etypes, "missing critic rates canonical etype")
    _assert(heterograph.etypes.count("rates") == 2, "expected duplicate relation name")

    ambiguous_failed = False
    try:
        heterograph.edges(etype="rates")
    except Exception:
        ambiguous_failed = True
    _assert(ambiguous_failed, "bare duplicate etype unexpectedly succeeded")

    src, dst, eid = heterograph.edges(form="all", etype=user_rates)
    _assert(len(src) == len(dst) == len(eid) == 3, "canonical etype edge query mismatch")

    homogeneous = dgl.to_homogeneous(heterograph, ndata=["feat"], edata=None)
    _assert(dgl.NTYPE in homogeneous.ndata, "homogeneous graph missing node type IDs")
    _assert(dgl.NID in homogeneous.ndata, "homogeneous graph missing original node IDs")
    _assert(dgl.ETYPE in homogeneous.edata, "homogeneous graph missing edge type IDs")
    _assert(dgl.EID in homogeneous.edata, "homogeneous graph missing original edge IDs")
    _assert(tuple(homogeneous.ndata["feat"].shape) == (6, 3), "merged node feature shape mismatch")

    roundtrip = dgl.to_heterogeneous(homogeneous, heterograph.ntypes, heterograph.etypes)
    _assert(set(roundtrip.ntypes) == set(heterograph.ntypes), "roundtrip ntype mismatch")
    _assert(set(roundtrip.canonical_etypes) == set(heterograph.canonical_etypes), "roundtrip canonical etype mismatch")
    return heterograph


def check_batching(dgl, torch):
    graph_one = dgl.graph((torch.tensor([0, 1]), torch.tensor([1, 2])), num_nodes=3)
    graph_two = dgl.graph((torch.tensor([0]), torch.tensor([1])), num_nodes=2)
    graph_one.ndata["feat"] = torch.zeros(graph_one.num_nodes(), 4)
    graph_two.ndata["feat"] = torch.ones(graph_two.num_nodes(), 4)

    batched = dgl.batch([graph_one, graph_two], ndata=["feat"], edata=None)
    _assert(batched.batch_size == 2, "batch size mismatch")
    _assert(batched.batch_num_nodes().tolist() == [3, 2], "batch node splits mismatch")
    _assert(tuple(batched.ndata["feat"].shape) == (5, 4), "batched feature shape mismatch")

    pieces = dgl.unbatch(batched)
    _assert(len(pieces) == 2, "unbatch count mismatch")
    _assert(pieces[0].num_nodes() == 3 and pieces[1].num_nodes() == 2, "unbatch node count mismatch")
    return batched


def check_save_load(dgl, torch, graph):
    with tempfile.TemporaryDirectory(prefix="dgl-graph-smoke-") as directory:
        path = Path(directory) / "graphs.bin"
        labels = {"target": torch.tensor([1])}
        dgl.save_graphs(str(path), [graph], labels=labels)
        loaded_graphs, loaded_labels = dgl.load_graphs(str(path))

    _assert(len(loaded_graphs) == 1, "load_graphs count mismatch")
    loaded = loaded_graphs[0]
    _assert(loaded.num_nodes() == graph.num_nodes(), "loaded node count mismatch")
    _assert(loaded.num_edges() == graph.num_edges(), "loaded edge count mismatch")
    _assert("target" in loaded_labels, "loaded labels missing target")
    _assert(loaded_labels["target"].tolist() == [1], "loaded label mismatch")


def run_smoke():
    import dgl
    import torch

    graph = check_homogeneous(dgl, torch)
    heterograph = check_heterograph(dgl, torch)
    batched = check_batching(dgl, torch)
    check_save_load(dgl, torch, graph)

    return {
        "ok": True,
        "dgl_version": getattr(dgl, "__version__", "unknown"),
        "torch_version": getattr(torch, "__version__", "unknown"),
        "homogeneous": {"nodes": graph.num_nodes(), "edges": graph.num_edges()},
        "heterograph": {"ntypes": heterograph.ntypes, "canonical_etypes": [list(item) for item in heterograph.canonical_etypes]},
        "batch": {"batch_size": batched.batch_size, "node_splits": batched.batch_num_nodes().tolist()},
    }


def main():
    parser = argparse.ArgumentParser(description="Run safe DGL graph API smoke checks.")
    parser.add_argument("--quiet", action="store_true", help="Only print failures; exit silently on success.")
    args = parser.parse_args()

    result = run_smoke()
    if not args.quiet:
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
