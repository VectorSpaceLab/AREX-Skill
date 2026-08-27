#!/usr/bin/env python3
from __future__ import annotations

import argparse
import inspect
import tempfile
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

import nir
from spikingjelly.activation_based import layer, neuron, nir_exchange


def as_shape(value) -> tuple[int, ...]:
    if isinstance(value, tuple):
        return tuple(int(x) for x in value)
    if isinstance(value, list):
        return tuple(int(x) for x in value)
    arr = np.asarray(value)
    if arr.ndim == 0:
        return (int(arr.item()),)
    return tuple(int(x) for x in arr.reshape(-1).tolist())


def assert_shape(actual, expected, label: str):
    actual_shape = as_shape(actual)
    expected_shape = tuple(expected)
    if actual_shape != expected_shape:
        raise AssertionError(f"{label}: expected {expected_shape}, got {actual_shape}")


def build_stateless_model() -> nn.Sequential:
    return nn.Sequential(
        layer.Conv2d(3, 4, kernel_size=3, padding=1, bias=False, step_mode="s"),
        nn.AvgPool2d(2),
        layer.Flatten(step_mode="s"),
        nn.Linear(4 * 4 * 4, 2, bias=False),
    )


def build_optional_neuron_model() -> nn.Sequential:
    return nn.Sequential(
        layer.Linear(4, 3, bias=False, step_mode="s"),
        neuron.LIFNode(tau=2.0, decay_input=False, v_reset=0.0, step_mode="s"),
    )


def supports_shape_bearing_nir_neurons() -> bool:
    required = {"input_type", "output_type"}
    if required <= set(inspect.signature(nir.IF).parameters) and required <= set(
        inspect.signature(nir.LIF).parameters
    ):
        return True
    return False


def run_stateless_roundtrip(dt: float, atol: float, rtol: float):
    torch.manual_seed(0)
    model = build_stateless_model().eval()
    example_input = torch.randn(1, 3, 8, 8)

    with tempfile.TemporaryDirectory() as tmpdir:
        h5_path = Path(tmpdir) / "stateless_roundtrip.h5"
        graph = nir_exchange.export_to_nir(
            model,
            example_input=example_input,
            save_path=h5_path,
            dt=dt,
        )
        if not h5_path.exists():
            raise AssertionError("expected export_to_nir to write the HDF5 file")

        assert_shape(graph.input_type["input_1"], (3, 8, 8), "graph input_type")
        assert_shape(graph.nodes["_0"].input_type["input"], (3, 8, 8), "conv input")
        assert_shape(graph.nodes["_0"].output_type["output"], (4, 8, 8), "conv output")
        assert_shape(graph.nodes["_1"].input_type["input"], (4, 8, 8), "pool input")
        assert_shape(graph.nodes["_1"].output_type["output"], (4, 4, 4), "pool output")
        assert_shape(graph.nodes["_2"].input_type["input"], (4, 4, 4), "flatten input")
        assert_shape(graph.nodes["_2"].output_type["output"], (64,), "flatten output")
        assert_shape(graph.nodes["_3"].input_type["input"], (64,), "linear input")
        assert_shape(graph.nodes["_3"].output_type["output"], (2,), "linear output")
        assert_shape(graph.output_type["output"], (2,), "graph output")

        import_from_graph = nir_exchange.import_from_nir(
            graph,
            dt=dt,
            device="cpu",
            dtype=torch.float32,
            step_mode="s",
        )
        import_from_path = nir_exchange.import_from_nir(
            str(h5_path),
            dt=dt,
            device="cpu",
            dtype=torch.float32,
            step_mode="m",
        )

        x = torch.randn(2, 3, 8, 8)
        expected = model(x)

        actual_s, state_s = import_from_graph(x)
        if not isinstance(state_s, dict):
            raise AssertionError("single-step import should return a state dictionary")
        torch.testing.assert_close(actual_s, expected, rtol=rtol, atol=atol)

        x_seq = torch.randn(3, 2, 3, 8, 8)
        expected_seq = torch.stack([model(x_seq[t]) for t in range(x_seq.shape[0])], dim=0)
        actual_m, state_m = import_from_path(x_seq)
        if not isinstance(state_m, dict):
            raise AssertionError("multi-step import should return a state dictionary")
        torch.testing.assert_close(actual_m, expected_seq, rtol=rtol, atol=atol)

        print("stateless NIR round-trip: ok")


def run_optional_neuron_roundtrip(dt: float, atol: float, rtol: float):
    if not supports_shape_bearing_nir_neurons():
        print("optional neuron NIR round-trip: skipped (current nir.IF/nir.LIF signatures do not expose shape-bearing constructors)")
        return

    torch.manual_seed(1)
    model = build_optional_neuron_model().eval()
    example_input = torch.randn(1, 4)

    with tempfile.TemporaryDirectory() as tmpdir:
        h5_path = Path(tmpdir) / "neuron_roundtrip.h5"
        graph = nir_exchange.export_to_nir(
            model,
            example_input=example_input,
            save_path=h5_path,
            dt=dt,
        )
        if not h5_path.exists():
            raise AssertionError("expected neuron export_to_nir to write the HDF5 file")

        imported = nir_exchange.import_from_nir(
            graph,
            dt=dt,
            device="cpu",
            dtype=torch.float32,
            step_mode="s",
        )
        x = torch.randn(2, 4)
        expected = model(x)
        actual, state = imported(x)
        if not isinstance(state, dict):
            raise AssertionError("neuron import should return a state dictionary")
        torch.testing.assert_close(actual, expected, rtol=rtol, atol=atol)
        print("optional neuron NIR round-trip: ok")


def main():
    parser = argparse.ArgumentParser(description="Smoke-test NIR export/import round-tripping.")
    parser.add_argument("--dt", type=float, default=1e-4, help="NIR simulation dt")
    parser.add_argument("--atol", type=float, default=1e-6, help="absolute tolerance")
    parser.add_argument("--rtol", type=float, default=1e-6, help="relative tolerance")
    args = parser.parse_args()

    run_stateless_roundtrip(args.dt, args.atol, args.rtol)
    run_optional_neuron_roundtrip(args.dt, args.atol, args.rtol)
    print("nir round-trip smoke passed")


if __name__ == "__main__":
    main()
