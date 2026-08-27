#!/usr/bin/env python3
"""Validate a small offline NetworkX -> CompilerISA topology conversion.

This helper is deterministic and intentionally does not import QCS clients,
read credentials, contact a service, start a process, or write files. It emits
one JSON-safe summary to stdout. The reverse graph transformer is edge-based,
so the isolated node is checked in the ISA and then restored explicitly for the
round-trip topology invariant.

Examples:
    python topology_isa_smoke.py
    python topology_isa_smoke.py --help
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any

import networkx as nx

from pyquil.external.rpcq import CompilerISA
from pyquil.quantum_processor import NxQuantumProcessor
from pyquil.quantum_processor.transformers import compiler_isa_to_graph


ONE_QUBIT_GATES = ["RX", "RZ", "MEASURE"]
TWO_QUBIT_GATES = ["CZ"]


def _sorted_edges(graph: nx.Graph) -> list[list[int]]:
    """Return canonical integer edges suitable for JSON."""
    return [list(edge) for edge in sorted(tuple(sorted((int(a), int(b)))) for a, b in graph.edges)]


def _isa_summary(isa: CompilerISA) -> dict[str, Any]:
    """Return only JSON-compatible CompilerISA facts relevant to this smoke."""
    return {
        "qubits": [
            {
                "id": int(qubit.id),
                "dead": bool(qubit.dead),
                "gates": sorted({str(gate.operator) for gate in qubit.gates}),
            }
            for _, qubit in sorted(isa.qubits.items(), key=lambda item: int(item[0]))
        ],
        "edges": [
            {
                "id": str(edge_id),
                "ids": [int(node_id) for node_id in edge.ids],
                "dead": bool(edge.dead),
                "gates": sorted({str(gate.operator) for gate in edge.gates}),
            }
            for edge_id, edge in sorted(isa.edges.items())
        ],
    }


def build_summary() -> dict[str, Any]:
    """Build the topology, assert invariants, and return a JSON-safe summary."""
    topology = nx.Graph()
    topology.add_nodes_from([0, 1, 2])
    topology.add_edge(0, 1)

    processor = NxQuantumProcessor(
        topology=topology,
        gates_1q=ONE_QUBIT_GATES,
        gates_2q=TWO_QUBIT_GATES,
    )
    isa = processor.to_compiler_isa()

    assert processor.qubits() == [0, 1, 2]
    assert processor.edges() == [(0, 1)]
    assert sorted(isa.qubits) == ["0", "1", "2"]
    assert sorted(isa.edges) == ["0-1"]
    assert all(not isa.qubits[str(node)].dead for node in topology.nodes)
    assert {gate.operator for gate in isa.qubits["0"].gates} == set(ONE_QUBIT_GATES)
    assert {gate.operator for gate in isa.qubits["2"].gates} == set(ONE_QUBIT_GATES)
    assert not isa.edges["0-1"].dead
    assert {gate.operator for gate in isa.edges["0-1"].gates} == set(TWO_QUBIT_GATES)

    edge_round_trip = compiler_isa_to_graph(isa)
    assert _sorted_edges(edge_round_trip) == [[0, 1]]
    assert set(edge_round_trip.nodes) == {0, 1}

    # The reverse transformer intentionally omits isolated ISA qubits. Restore
    # them only after checking that limitation, then validate full topology.
    full_round_trip = edge_round_trip.copy()
    full_round_trip.add_nodes_from(processor.qubits())
    assert sorted(full_round_trip.nodes) == [0, 1, 2]
    assert _sorted_edges(full_round_trip) == _sorted_edges(topology)

    return {
        "networkx": {
            "type": type(topology).__name__,
            "nodes": [int(node) for node in sorted(topology.nodes)],
            "edges": _sorted_edges(topology),
        },
        "processor": {
            "type": type(processor).__name__,
            "qubits": processor.qubits(),
            "edges": [list(edge) for edge in processor.edges()],
        },
        "compiler_isa": _isa_summary(isa),
        "round_trip": {
            "edge_transform_nodes": [int(node) for node in sorted(edge_round_trip.nodes)],
            "edge_transform_edges": _sorted_edges(edge_round_trip),
            "restored_nodes": [int(node) for node in sorted(full_round_trip.nodes)],
            "restored_edges": _sorted_edges(full_round_trip),
            "isolated_node_preserved_in_isa": not isa.qubits["2"].dead,
            "isolated_node_requires_explicit_restore": 2 not in edge_round_trip.nodes,
        },
        "network_contacted": False,
    }


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, run assertions, and print one JSON summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="run the same assertions and emit the JSON summary (the default)",
    )
    args = parser.parse_args(argv)
    del args

    summary = build_summary()
    # A final encoder check guards against accidentally adding a model object.
    encoded = json.dumps(summary, sort_keys=True, allow_nan=False)
    assert math.isfinite(float(len(encoded)))
    print(encoded)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"topology_isa_smoke: invariant failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
