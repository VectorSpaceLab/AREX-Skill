#!/usr/bin/env python3
"""Self-contained NIR export/import smoke for snnTorch."""

from __future__ import annotations

import argparse
from pathlib import Path

import nir
import torch
import snntorch as snn
from snntorch.export_nir import export_to_nir
from snntorch.import_nir import import_from_nir


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "references" / "fixtures"


def unwrap_output(result):
    if isinstance(result, tuple):
        return result[0]
    return result


def assert_graph(graph, expected_nodes, expected_edges, label):
    actual_nodes = set(graph.nodes)
    actual_edges = set(graph.edges)
    assert actual_nodes == expected_nodes, (
        f"{label}: node mismatch\n"
        f"expected: {sorted(expected_nodes)}\n"
        f"actual:   {sorted(actual_nodes)}"
    )
    assert actual_edges == expected_edges, (
        f"{label}: edge mismatch\n"
        f"expected: {sorted(expected_edges)}\n"
        f"actual:   {sorted(actual_edges)}"
    )


def build_sequential_model():
    return torch.nn.Sequential(
        torch.nn.Linear(8, 4),
        snn.Leaky(
            beta=0.9 * torch.ones(4),
            threshold=torch.ones(4),
            init_hidden=True,
        ),
        torch.nn.Linear(4, 2),
        snn.Leaky(
            beta=0.9 * torch.ones(2),
            threshold=torch.ones(2),
            init_hidden=True,
            output=True,
        ),
    ).eval()


def build_recurrent_model():
    return torch.nn.Sequential(
        torch.nn.Linear(6, 4),
        snn.RLeaky(
            beta=0.9 * torch.ones(4),
            threshold=torch.ones(4),
            V=torch.ones(4),
            all_to_all=False,
            init_hidden=True,
        ),
        torch.nn.Linear(4, 3),
        snn.Leaky(
            beta=0.9 * torch.ones(3),
            threshold=torch.ones(3),
            init_hidden=True,
            output=True,
        ),
    ).eval()


def check_sequential_round_trip():
    model = build_sequential_model()
    sample_data = torch.ones(3, 8)
    graph = export_to_nir(model, sample_data, ignore_dims=[0])

    expected_nodes = {"input", "output", "0", "1", "2", "3"}
    expected_edges = {
        ("input", "0"),
        ("0", "1"),
        ("1", "2"),
        ("2", "3"),
        ("3", "output"),
    }
    assert_graph(graph, expected_nodes, expected_edges, "sequential export")
    assert graph.nodes["input"].input_type["input"].tolist() == [8]
    assert graph.nodes["output"].output_type["output"].tolist() == [2]

    restored = import_from_nir(graph).eval()
    output = unwrap_output(restored(torch.randn(3, 8)))
    assert output.shape == (3, 2), output.shape


def check_recurrent_round_trip():
    model = build_recurrent_model()
    sample_data = torch.ones(2, 6)
    graph = export_to_nir(model, sample_data, ignore_dims=[0])

    expected_nodes = {"input", "output", "0", "1.lif", "1.w_rec", "2", "3"}
    expected_edges = {
        ("input", "0"),
        ("0", "1.lif"),
        ("1.lif", "1.w_rec"),
        ("1.w_rec", "1.lif"),
        ("1.lif", "2"),
        ("2", "3"),
        ("3", "output"),
    }
    assert_graph(graph, expected_nodes, expected_edges, "recurrent export")
    assert graph.nodes["input"].input_type["input"].tolist() == [6]
    assert graph.nodes["output"].output_type["output"].tolist() == [3]

    restored = import_from_nir(graph).eval()
    output = unwrap_output(restored(torch.randn(2, 6)))
    assert output.shape == (2, 3), output.shape


def check_fixture_import():
    fixture_path = FIXTURE_DIR / "lif.nir"
    assert fixture_path.is_file(), fixture_path
    graph = nir.read(fixture_path)
    restored = import_from_nir(graph).eval()
    output = unwrap_output(restored(torch.ones(1, 1)))
    assert output.shape == (1, 1), output.shape


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-fixture",
        action="store_true",
        help="Skip the bundled fixture import check.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    torch.manual_seed(0)

    check_sequential_round_trip()
    check_recurrent_round_trip()
    if not args.skip_fixture:
        check_fixture_import()

    print("nir round-trip smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
