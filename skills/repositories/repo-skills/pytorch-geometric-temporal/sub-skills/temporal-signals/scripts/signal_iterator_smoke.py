#!/usr/bin/env python3
"""Deterministic smoke checks for PyTorch Geometric Temporal signal iterators."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple


def ensure_package_path() -> None:
    """Make the local package importable even when the cwd is arbitrary."""

    try:
        import torch_geometric_temporal.signal  # noqa: F401
        return
    except Exception:
        pass

    script_path = Path(__file__).resolve()
    for parent in script_path.parents:
        candidate = parent / "torch_geometric_temporal"
        if (candidate / "__init__.py").is_file() and (candidate / "signal" / "__init__.py").is_file():
            sys.path.insert(0, str(parent))
            return

    raise RuntimeError("Unable to locate an importable torch_geometric_temporal package.")


ensure_package_path()

import numpy as np
import torch
from torch_geometric.data import Batch, Data, HeteroData
from torch_geometric_temporal.signal import (
    DynamicGraphStaticSignal,
    DynamicGraphStaticSignalBatch,
    DynamicGraphTemporalSignal,
    DynamicGraphTemporalSignalBatch,
    DynamicHeteroGraphStaticSignal,
    DynamicHeteroGraphStaticSignalBatch,
    DynamicHeteroGraphTemporalSignal,
    DynamicHeteroGraphTemporalSignalBatch,
    StaticGraphTemporalSignal,
    StaticGraphTemporalSignalBatch,
    StaticHeteroGraphTemporalSignal,
    StaticHeteroGraphTemporalSignalBatch,
    temporal_signal_split,
)

RELATION = ("author", "writes", "paper")
SNAPSHOT_COUNT = 4


def cycle_edge_index(num_nodes: int) -> np.ndarray:
    src = np.arange(num_nodes, dtype=np.int64)
    dst = np.roll(src, -1)
    return np.stack([src, dst], axis=0)


def homogeneous_batch_edge_index() -> np.ndarray:
    return np.array([[0, 1, 2, 3], [1, 0, 3, 2]], dtype=np.int64)


def hetero_relation_edge_index() -> np.ndarray:
    return np.array([[0, 1], [0, 2]], dtype=np.int64)


def hetero_batch_relation_edge_index() -> np.ndarray:
    return np.array([[0, 1, 2, 3], [0, 2, 3, 5]], dtype=np.int64)


def matrix(time: int, rows: int, cols: int, offset: float = 0.0) -> np.ndarray:
    base = np.arange(rows * cols, dtype=np.float32).reshape(rows, cols)
    return base + np.float32(time + offset)


def labels(time: int, rows: int, offset: int = 0) -> np.ndarray:
    return np.arange(rows, dtype=np.int64) + time + offset


def edge_weights(length: int, base: float = 1.0, time: int = 0) -> np.ndarray:
    return np.asarray([base + time + idx * 0.25 for idx in range(length)], dtype=np.float32)


def repeated_edge_index_list(edge_index: np.ndarray) -> List[np.ndarray]:
    return [edge_index.copy() for _ in range(SNAPSHOT_COUNT)]


def repeated_weight_list(length: int, base: float = 1.0) -> List[np.ndarray]:
    return [edge_weights(length, base=base, time=t) for t in range(SNAPSHOT_COUNT)]


def repeated_batch_list(batch: np.ndarray) -> List[np.ndarray]:
    return [batch.copy() for _ in range(SNAPSHOT_COUNT)]


def repeated_hetero_dict_list(payload: Dict[str, np.ndarray]) -> List[Dict[str, np.ndarray]]:
    return [{key: value.copy() for key, value in payload.items()} for _ in range(SNAPSHOT_COUNT)]


def repeated_hetero_relation_dict_list(payload: Dict[Tuple[str, str, str], np.ndarray]) -> List[Dict[Tuple[str, str, str], np.ndarray]]:
    return [{key: value.copy() for key, value in payload.items()} for _ in range(SNAPSHOT_COUNT)]


def repeated_hetero_batch_dict_list(payload: Dict[str, np.ndarray]) -> List[Dict[str, np.ndarray]]:
    return [{key: value.copy() for key, value in payload.items()} for _ in range(SNAPSHOT_COUNT)]


def assert_shape(actual: Sequence[int], expected: Tuple[int, ...], label: str) -> None:
    assert tuple(actual) == expected, f"{label} shape mismatch: expected {expected}, got {tuple(actual)}"


def assert_reiterable(iterator: Any, expected_count: int, label: str) -> Dict[str, int]:
    first_pass = sum(1 for _ in iterator)
    second_pass = sum(1 for _ in iterator)
    assert first_pass == expected_count, f"{label} first pass expected {expected_count}, got {first_pass}"
    assert second_pass == expected_count, f"{label} second pass expected {expected_count}, got {second_pass}"
    return {"first_pass": int(first_pass), "second_pass": int(second_pass)}


def assert_window(iterator: Any, label: str, expected_count: int = 2) -> Dict[str, int]:
    window = iterator[1:3]
    assert window.snapshot_count == expected_count, f"{label} slice count expected {expected_count}, got {window.snapshot_count}"
    counts = assert_reiterable(window, expected_count, f"{label} slice")
    counts["slice_count"] = int(window.snapshot_count)
    return counts


def static_signal() -> StaticGraphTemporalSignal:
    edge_index = cycle_edge_index(3)
    features = [matrix(t, 3, 2) for t in range(SNAPSHOT_COUNT)]
    targets = [labels(t, 3) for t in range(SNAPSHOT_COUNT)]
    aux = [matrix(t, 3, 1) for t in range(SNAPSHOT_COUNT)]
    return StaticGraphTemporalSignal(edge_index, np.array([1.0, 0.5, 0.25], dtype=np.float32), features, targets, aux=aux)


def dynamic_signal() -> DynamicGraphTemporalSignal:
    edge_index = cycle_edge_index(3)
    return DynamicGraphTemporalSignal(
        repeated_edge_index_list(edge_index),
        repeated_weight_list(3, base=1.0),
        [matrix(t, 3, 2) for t in range(SNAPSHOT_COUNT)],
        [labels(t, 3) for t in range(SNAPSHOT_COUNT)],
        aux=[matrix(t, 3, 1) for t in range(SNAPSHOT_COUNT)],
    )


def dynamic_static_signal() -> DynamicGraphStaticSignal:
    edge_index = cycle_edge_index(3)
    return DynamicGraphStaticSignal(
        repeated_edge_index_list(edge_index),
        repeated_weight_list(3, base=2.0),
        matrix(0, 3, 2),
        [labels(t, 3) for t in range(SNAPSHOT_COUNT)],
        aux=[matrix(t, 3, 1) for t in range(SNAPSHOT_COUNT)],
    )


def batch_signal() -> StaticGraphTemporalSignalBatch:
    edge_index = homogeneous_batch_edge_index()
    batch = np.array([0, 0, 1, 1], dtype=np.int64)
    return StaticGraphTemporalSignalBatch(
        edge_index,
        np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
        [matrix(t, 4, 2) for t in range(SNAPSHOT_COUNT)],
        [labels(t, 4) for t in range(SNAPSHOT_COUNT)],
        batch,
        aux=[matrix(t, 4, 1) for t in range(SNAPSHOT_COUNT)],
    )


def dynamic_batch_signal() -> DynamicGraphTemporalSignalBatch:
    edge_index = homogeneous_batch_edge_index()
    batch = np.array([0, 0, 1, 1], dtype=np.int64)
    return DynamicGraphTemporalSignalBatch(
        repeated_edge_index_list(edge_index),
        repeated_weight_list(4, base=1.5),
        [matrix(t, 4, 2) for t in range(SNAPSHOT_COUNT)],
        [labels(t, 4) for t in range(SNAPSHOT_COUNT)],
        repeated_batch_list(batch),
        aux=[matrix(t, 4, 1) for t in range(SNAPSHOT_COUNT)],
    )


def dynamic_static_batch_signal() -> DynamicGraphStaticSignalBatch:
    edge_index = homogeneous_batch_edge_index()
    batch = np.array([0, 0, 1, 1], dtype=np.int64)
    return DynamicGraphStaticSignalBatch(
        repeated_edge_index_list(edge_index),
        repeated_weight_list(4, base=2.0),
        matrix(0, 4, 2),
        [labels(t, 4) for t in range(SNAPSHOT_COUNT)],
        repeated_batch_list(batch),
        aux=[matrix(t, 4, 1) for t in range(SNAPSHOT_COUNT)],
    )


def static_hetero_signal() -> StaticHeteroGraphTemporalSignal:
    edge_index_dict = {RELATION: hetero_relation_edge_index()}
    edge_weight_dict = {RELATION: np.array([1.0, 0.5], dtype=np.float32)}
    feature_dicts = [
        {"author": matrix(t, 2, 2), "paper": matrix(t + 10, 3, 2)}
        for t in range(SNAPSHOT_COUNT)
    ]
    target_dicts = [
        {"author": labels(t, 2), "paper": labels(t + 10, 3)}
        for t in range(SNAPSHOT_COUNT)
    ]
    aux = [
        {"author": matrix(t, 2, 1), "paper": matrix(t + 10, 3, 1)}
        for t in range(SNAPSHOT_COUNT)
    ]
    return StaticHeteroGraphTemporalSignal(edge_index_dict, edge_weight_dict, feature_dicts, target_dicts, aux=aux)


def dynamic_hetero_signal() -> DynamicHeteroGraphTemporalSignal:
    edge_index_dict = {RELATION: hetero_relation_edge_index()}
    return DynamicHeteroGraphTemporalSignal(
        repeated_hetero_relation_dict_list(edge_index_dict),
        repeated_hetero_relation_dict_list({RELATION: np.array([1.0, 0.5], dtype=np.float32)}),
        repeated_hetero_dict_list({"author": matrix(0, 2, 2), "paper": matrix(10, 3, 2)}),
        repeated_hetero_dict_list({"author": labels(0, 2), "paper": labels(10, 3)}),
        aux=repeated_hetero_dict_list({"author": matrix(0, 2, 1), "paper": matrix(10, 3, 1)}),
    )


def dynamic_static_hetero_signal() -> DynamicHeteroGraphStaticSignal:
    edge_index_dict = {RELATION: hetero_relation_edge_index()}
    return DynamicHeteroGraphStaticSignal(
        repeated_hetero_relation_dict_list(edge_index_dict),
        repeated_hetero_relation_dict_list({RELATION: np.array([1.0, 0.5], dtype=np.float32)}),
        {"author": matrix(0, 2, 2), "paper": matrix(10, 3, 2)},
        repeated_hetero_dict_list({"author": labels(0, 2), "paper": labels(10, 3)}),
        aux=repeated_hetero_dict_list({"author": matrix(0, 2, 1), "paper": matrix(10, 3, 1)}),
    )


def static_hetero_batch_signal() -> StaticHeteroGraphTemporalSignalBatch:
    edge_index_dict = {RELATION: hetero_batch_relation_edge_index()}
    edge_weight_dict = {RELATION: np.array([1.0, 0.5, 1.5, 0.75], dtype=np.float32)}
    batch_dict = {
        "author": np.array([0, 0, 1, 1], dtype=np.int64),
        "paper": np.array([0, 0, 0, 1, 1, 1], dtype=np.int64),
    }
    feature_dicts = [
        {"author": matrix(t, 4, 2), "paper": matrix(t + 10, 6, 2)}
        for t in range(SNAPSHOT_COUNT)
    ]
    target_dicts = [
        {"author": labels(t, 4), "paper": labels(t + 10, 6)}
        for t in range(SNAPSHOT_COUNT)
    ]
    aux = [
        {"author": matrix(t, 4, 1), "paper": matrix(t + 10, 6, 1)}
        for t in range(SNAPSHOT_COUNT)
    ]
    return StaticHeteroGraphTemporalSignalBatch(edge_index_dict, edge_weight_dict, feature_dicts, target_dicts, batch_dict, aux=aux)


def dynamic_hetero_batch_signal() -> DynamicHeteroGraphTemporalSignalBatch:
    edge_index_dict = {RELATION: hetero_batch_relation_edge_index()}
    batch_dict = {
        "author": np.array([0, 0, 1, 1], dtype=np.int64),
        "paper": np.array([0, 0, 0, 1, 1, 1], dtype=np.int64),
    }
    return DynamicHeteroGraphTemporalSignalBatch(
        repeated_hetero_relation_dict_list(edge_index_dict),
        repeated_hetero_relation_dict_list({RELATION: np.array([1.0, 0.5, 1.5, 0.75], dtype=np.float32)}),
        repeated_hetero_dict_list({"author": matrix(0, 4, 2), "paper": matrix(10, 6, 2)}),
        repeated_hetero_dict_list({"author": labels(0, 4), "paper": labels(10, 6)}),
        repeated_hetero_batch_dict_list(batch_dict),
        aux=repeated_hetero_dict_list({"author": matrix(0, 4, 1), "paper": matrix(10, 6, 1)}),
    )


def dynamic_static_hetero_batch_signal() -> DynamicHeteroGraphStaticSignalBatch:
    edge_index_dict = {RELATION: hetero_batch_relation_edge_index()}
    batch_dict = {
        "author": np.array([0, 0, 1, 1], dtype=np.int64),
        "paper": np.array([0, 0, 0, 1, 1, 1], dtype=np.int64),
    }
    return DynamicHeteroGraphStaticSignalBatch(
        repeated_hetero_relation_dict_list(edge_index_dict),
        repeated_hetero_relation_dict_list({RELATION: np.array([1.0, 0.5, 1.5, 0.75], dtype=np.float32)}),
        {"author": matrix(0, 4, 2), "paper": matrix(10, 6, 2)},
        repeated_hetero_dict_list({"author": labels(0, 4), "paper": labels(10, 6)}),
        repeated_hetero_batch_dict_list(batch_dict),
        aux=repeated_hetero_dict_list({"author": matrix(0, 4, 1), "paper": matrix(10, 6, 1)}),
    )


def probe_homogeneous_snapshot(snapshot: Any, num_nodes: int, num_edges: int, aux_nodes: int) -> None:
    assert isinstance(snapshot, Data)
    assert_shape(snapshot.x.shape, (num_nodes, 2), "x")
    assert_shape(snapshot.edge_index.shape, (2, num_edges), "edge_index")
    assert_shape(snapshot.edge_attr.shape, (num_edges,), "edge_attr")
    assert_shape(snapshot.y.shape, (num_nodes,), "y")
    assert snapshot.x.dtype == torch.float32
    assert snapshot.edge_index.dtype == torch.long
    assert snapshot.edge_attr.dtype == torch.float32
    assert snapshot.y.dtype == torch.long
    aux = getattr(snapshot, "aux")
    assert_shape(aux.shape, (aux_nodes, 1), "aux")
    assert aux.dtype == torch.float32


def probe_homogeneous_batch_snapshot(snapshot: Any, num_nodes: int, num_edges: int) -> None:
    assert isinstance(snapshot, Batch)
    assert_shape(snapshot.x.shape, (num_nodes, 2), "x")
    assert_shape(snapshot.edge_index.shape, (2, num_edges), "edge_index")
    assert_shape(snapshot.edge_attr.shape, (num_edges,), "edge_attr")
    assert_shape(snapshot.y.shape, (num_nodes,), "y")
    assert_shape(snapshot.batch.shape, (num_nodes,), "batch")
    assert snapshot.x.dtype == torch.float32
    assert snapshot.edge_index.dtype == torch.long
    assert snapshot.edge_attr.dtype == torch.float32
    assert snapshot.y.dtype == torch.long
    assert snapshot.batch.dtype == torch.long
    assert getattr(snapshot, "aux").dtype == torch.float32


def probe_hetero_snapshot(snapshot: Any, author_nodes: int, paper_nodes: int, num_edges: int) -> None:
    assert isinstance(snapshot, HeteroData)
    assert set(snapshot.node_types) == {"author", "paper"}
    assert set(snapshot.edge_types) == {RELATION}
    assert_shape(snapshot["author"].x.shape, (author_nodes, 2), "author.x")
    assert_shape(snapshot["paper"].x.shape, (paper_nodes, 2), "paper.x")
    assert_shape(snapshot["author"].y.shape, (author_nodes,), "author.y")
    assert_shape(snapshot["paper"].y.shape, (paper_nodes,), "paper.y")
    assert_shape(snapshot[RELATION].edge_index.shape, (2, num_edges), "relation.edge_index")
    assert_shape(snapshot[RELATION].edge_attr.shape, (num_edges,), "relation.edge_attr")
    assert snapshot["author"].x.dtype == torch.float32
    assert snapshot["paper"].x.dtype == torch.float32
    assert snapshot["author"].y.dtype == torch.long
    assert snapshot["paper"].y.dtype == torch.long
    assert snapshot[RELATION].edge_index.dtype == torch.long
    assert snapshot[RELATION].edge_attr.dtype == torch.float32
    assert getattr(snapshot["author"], "aux").dtype == torch.float32
    assert getattr(snapshot["paper"], "aux").dtype == torch.float32


def probe_hetero_batch_snapshot(snapshot: Any, author_nodes: int, paper_nodes: int, num_edges: int) -> None:
    assert isinstance(snapshot, HeteroData)
    assert set(snapshot.node_types) == {"author", "paper"}
    assert set(snapshot.edge_types) == {RELATION}
    assert_shape(snapshot["author"].x.shape, (author_nodes, 2), "author.x")
    assert_shape(snapshot["paper"].x.shape, (paper_nodes, 2), "paper.x")
    assert_shape(snapshot["author"].batch.shape, (author_nodes,), "author.batch")
    assert_shape(snapshot["paper"].batch.shape, (paper_nodes,), "paper.batch")
    assert_shape(snapshot[RELATION].edge_index.shape, (2, num_edges), "relation.edge_index")
    assert_shape(snapshot[RELATION].edge_attr.shape, (num_edges,), "relation.edge_attr")
    assert snapshot["author"].batch.dtype == torch.long
    assert snapshot["paper"].batch.dtype == torch.long
    assert snapshot[RELATION].edge_index.dtype == torch.long
    assert snapshot[RELATION].edge_attr.dtype == torch.float32
    assert getattr(snapshot["author"], "aux").dtype == torch.float32
    assert getattr(snapshot["paper"], "aux").dtype == torch.float32


def run_static() -> Dict[str, Any]:
    signal = static_signal()
    snapshot = signal[0]
    probe_homogeneous_snapshot(snapshot, num_nodes=3, num_edges=3, aux_nodes=3)
    slice_counts = assert_window(signal, "static")
    iter_counts = assert_reiterable(signal, SNAPSHOT_COUNT, "static")
    return {"case": "static", "snapshot_count": int(signal.snapshot_count), **slice_counts, **iter_counts}


def run_dynamic() -> Dict[str, Any]:
    signal = dynamic_signal()
    snapshot = signal[1]
    probe_homogeneous_snapshot(snapshot, num_nodes=3, num_edges=3, aux_nodes=3)
    slice_counts = assert_window(signal, "dynamic")
    iter_counts = assert_reiterable(signal, SNAPSHOT_COUNT, "dynamic")
    return {"case": "dynamic", "snapshot_count": int(signal.snapshot_count), **slice_counts, **iter_counts}


def run_dynamic_static() -> Dict[str, Any]:
    signal = dynamic_static_signal()
    snapshot = signal[2]
    probe_homogeneous_snapshot(snapshot, num_nodes=3, num_edges=3, aux_nodes=3)
    slice_counts = assert_window(signal, "dynamic-static")
    iter_counts = assert_reiterable(signal, SNAPSHOT_COUNT, "dynamic-static")
    return {"case": "dynamic-static", "snapshot_count": int(signal.snapshot_count), **slice_counts, **iter_counts}


def run_batch() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    static = batch_signal()
    probe_homogeneous_batch_snapshot(static[0], num_nodes=4, num_edges=4)
    results.append({"case": "batch-static", "snapshot_count": int(static.snapshot_count), **assert_window(static, "batch-static"), **assert_reiterable(static, SNAPSHOT_COUNT, "batch-static")})

    dynamic = dynamic_batch_signal()
    probe_homogeneous_batch_snapshot(dynamic[1], num_nodes=4, num_edges=4)
    results.append({"case": "batch-dynamic", "snapshot_count": int(dynamic.snapshot_count), **assert_window(dynamic, "batch-dynamic"), **assert_reiterable(dynamic, SNAPSHOT_COUNT, "batch-dynamic")})

    dynamic_static = dynamic_static_batch_signal()
    probe_homogeneous_batch_snapshot(dynamic_static[2], num_nodes=4, num_edges=4)
    results.append({"case": "batch-dynamic-static", "snapshot_count": int(dynamic_static.snapshot_count), **assert_window(dynamic_static, "batch-dynamic-static"), **assert_reiterable(dynamic_static, SNAPSHOT_COUNT, "batch-dynamic-static")})

    return results


def run_hetero() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    static = static_hetero_signal()
    probe_hetero_snapshot(static[0], author_nodes=2, paper_nodes=3, num_edges=2)
    results.append({"case": "hetero-static", "snapshot_count": int(static.snapshot_count), **assert_window(static, "hetero-static"), **assert_reiterable(static, SNAPSHOT_COUNT, "hetero-static")})

    dynamic = dynamic_hetero_signal()
    probe_hetero_snapshot(dynamic[1], author_nodes=2, paper_nodes=3, num_edges=2)
    results.append({"case": "hetero-dynamic", "snapshot_count": int(dynamic.snapshot_count), **assert_window(dynamic, "hetero-dynamic"), **assert_reiterable(dynamic, SNAPSHOT_COUNT, "hetero-dynamic")})

    dynamic_static = dynamic_static_hetero_signal()
    probe_hetero_snapshot(dynamic_static[2], author_nodes=2, paper_nodes=3, num_edges=2)
    results.append({"case": "hetero-dynamic-static", "snapshot_count": int(dynamic_static.snapshot_count), **assert_window(dynamic_static, "hetero-dynamic-static"), **assert_reiterable(dynamic_static, SNAPSHOT_COUNT, "hetero-dynamic-static")})

    return results


def run_hetero_batch() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    static = static_hetero_batch_signal()
    probe_hetero_batch_snapshot(static[0], author_nodes=4, paper_nodes=6, num_edges=4)
    results.append({"case": "hetero-batch-static", "snapshot_count": int(static.snapshot_count), **assert_window(static, "hetero-batch-static"), **assert_reiterable(static, SNAPSHOT_COUNT, "hetero-batch-static")})

    dynamic = dynamic_hetero_batch_signal()
    probe_hetero_batch_snapshot(dynamic[1], author_nodes=4, paper_nodes=6, num_edges=4)
    results.append({"case": "hetero-batch-dynamic", "snapshot_count": int(dynamic.snapshot_count), **assert_window(dynamic, "hetero-batch-dynamic"), **assert_reiterable(dynamic, SNAPSHOT_COUNT, "hetero-batch-dynamic")})

    dynamic_static = dynamic_static_hetero_batch_signal()
    probe_hetero_batch_snapshot(dynamic_static[2], author_nodes=4, paper_nodes=6, num_edges=4)
    results.append({"case": "hetero-batch-dynamic-static", "snapshot_count": int(dynamic_static.snapshot_count), **assert_window(dynamic_static, "hetero-batch-dynamic-static"), **assert_reiterable(dynamic_static, SNAPSHOT_COUNT, "hetero-batch-dynamic-static")})

    return results


def run_split() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    representative_signals = [
        ("split-static", static_signal()),
        ("split-dynamic", dynamic_signal()),
        ("split-dynamic-static", dynamic_static_signal()),
        ("split-batch", batch_signal()),
        ("split-hetero", static_hetero_signal()),
        ("split-hetero-batch", static_hetero_batch_signal()),
    ]

    for name, signal in representative_signals:
        train, test = temporal_signal_split(signal, train_ratio=0.5)
        expected_train = signal.snapshot_count // 2
        expected_test = signal.snapshot_count - expected_train
        assert train.snapshot_count == expected_train, f"{name} train count expected {expected_train}, got {train.snapshot_count}"
        assert test.snapshot_count == expected_test, f"{name} test count expected {expected_test}, got {test.snapshot_count}"
        assert expected_train > 0 and expected_test > 0, f"{name} split should not be empty"
        assert_reiterable(train, expected_train, f"{name} train")
        assert_reiterable(test, expected_test, f"{name} test")
        results.append({"case": name, "train": int(expected_train), "test": int(expected_test)})

    return results


def run_mode(mode: str) -> Dict[str, Any]:
    if mode == "static":
        results = [run_static()]
    elif mode == "dynamic":
        results = [run_dynamic()]
    elif mode == "dynamic-static":
        results = [run_dynamic_static()]
    elif mode == "batch":
        results = run_batch()
    elif mode == "hetero":
        results = run_hetero()
    elif mode == "hetero-batch":
        results = run_hetero_batch()
    elif mode == "split":
        results = run_split()
    elif mode == "all":
        results = [
            run_static(),
            run_dynamic(),
            run_dynamic_static(),
            *run_batch(),
            *run_hetero(),
            *run_hetero_batch(),
            *run_split(),
        ]
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return {"mode": mode, "results": results, "cases": len(results)}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        default="all",
        choices=["all", "static", "dynamic", "dynamic-static", "batch", "hetero", "hetero-batch", "split"],
        help="Which smoke-check group to run.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run_mode(args.mode)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"ok: mode={summary['mode']} cases={summary['cases']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
