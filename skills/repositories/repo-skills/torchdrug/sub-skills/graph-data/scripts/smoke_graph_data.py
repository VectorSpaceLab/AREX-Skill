#!/usr/bin/env python
"""No-network smoke checks for TorchDrug graph and molecule data objects."""

import argparse
import sys

import torch
from torchdrug import data


def check_graph_data():
    edge_list = torch.tensor([[0, 1], [1, 2], [2, 0], [2, 3]])
    node_feature = torch.eye(4)
    edge_feature = torch.arange(len(edge_list), dtype=torch.float).unsqueeze(-1)
    graph = data.Graph(edge_list, num_node=4, node_feature=node_feature, edge_feature=edge_feature)

    with graph.graph():
        graph.graph_feature = torch.tensor([1.0, 0.0])

    subgraph = graph.subgraph([0, 1, 2])
    assert subgraph.num_node == 3
    assert subgraph.node_feature.shape[0] == 3

    edge_masked = graph.edge_mask([0, 2])
    assert edge_masked.num_node == graph.num_node
    assert edge_masked.num_edge == 2
    assert edge_masked.edge_feature.shape[0] == 2

    packed = data.Graph.pack([graph, subgraph])
    assert packed.batch_size == 2
    assert packed.graph_feature.shape[0] == 2
    assert len(packed.unpack()) == 2

    subbatch = packed.subbatch([1, 0])
    assert subbatch.batch_size == 2
    assert subbatch.num_nodes.tolist() == [int(subgraph.num_node), int(graph.num_node)]

    local_nodes = torch.tensor([0, 2])
    graph_id = 1
    packed_nodes = local_nodes + packed.num_cum_nodes[graph_id] - packed.num_nodes[graph_id]
    node_masked = packed.node_mask(packed_nodes, compact=True)
    assert int(node_masked.num_nodes[graph_id]) == 2

    collated = data.graph_collate([
        {"graph": graph, "label": 0},
        {"graph": subgraph, "label": 1},
    ])
    assert collated["graph"].batch_size == 2
    assert collated["label"].tolist() == [0, 1]


def check_molecule_data():
    smiles_list = ["CCO", "c1ccccc1"]
    molecule = data.Molecule.from_smiles(smiles_list[0])
    assert molecule.num_node > 0
    assert molecule.num_edge > 0
    assert molecule.node_feature.shape[0] == molecule.num_node
    assert molecule.edge_feature.shape[0] == molecule.num_edge

    packed = data.PackedMolecule.from_smiles(smiles_list)
    assert packed.batch_size == len(smiles_list)
    assert packed.num_nodes.shape[0] == len(smiles_list)
    assert len(packed.unpack()) == len(smiles_list)

    molecule_dataset = data.MoleculeDataset()
    molecule_dataset.load_smiles(smiles_list, {"label": [0, 1]}, lazy=False)
    train_set, test_set = data.scaffold_split(molecule_dataset, [1, 1])
    assert len(train_set) + len(test_set) == len(molecule_dataset)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Smoke-check TorchDrug graph data objects without network access.")
    parser.add_argument(
        "--skip-rdkit",
        action="store_true",
        help="Skip molecule / RDKit-dependent checks and run only generic graph checks.",
    )
    args = parser.parse_args(argv)

    check_graph_data()
    if not args.skip_rdkit:
        try:
            check_molecule_data()
        except Exception as exc:
            print("Molecule checks failed. Re-run with --skip-rdkit to isolate generic graph behavior.", file=sys.stderr)
            raise exc

    mode = "graph-only" if args.skip_rdkit else "graph+molecule"
    print(f"TorchDrug graph-data smoke checks passed ({mode}).")


if __name__ == "__main__":
    main()
