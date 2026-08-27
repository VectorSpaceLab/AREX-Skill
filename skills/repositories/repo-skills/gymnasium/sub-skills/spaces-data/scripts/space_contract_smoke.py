#!/usr/bin/env python3
"""Smoke-test core Gymnasium space contracts.

This helper is intentionally self-contained for the generated Gymnasium skill. It
builds representative fundamental and composite spaces, verifies sample/contains,
checks flatten/unflatten for a nested numpy-flattenable space, demonstrates
JSONable round trips for simple spaces, and reports expected dynamic-space limits.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def _load_runtime_dependencies():
    try:
        import numpy as np
        from gymnasium import spaces
        from gymnasium.spaces import utils as space_utils
        from gymnasium.utils.env_checker import data_equivalence
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing runtime dependency for space checks: "
            f"{exc.name}. Install Gymnasium with its base dependencies first."
        ) from exc
    return np, spaces, space_utils, data_equivalence


def _json_default(value: Any) -> Any:
    np = sys.modules.get("numpy")
    if np is not None and isinstance(value, np.generic):
        return value.item()
    if np is not None and isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _build_nested_space(seed: int, np: Any, spaces: Any) -> Any:
    nested_space = spaces.Dict(
        {
            "agent": spaces.Tuple(
                (
                    spaces.Box(-1.0, 1.0, shape=(2,), dtype=np.float32),
                    spaces.Discrete(3, start=1, dtype=np.int64),
                )
            ),
            "inventory": spaces.MultiBinary(4),
            "controller": spaces.MultiDiscrete([5, 2], dtype=np.int64),
        },
        seed=seed,
    )
    return nested_space


def _check_nested_flatten(seed: int, verbose: bool, np: Any, spaces: Any, space_utils: Any, data_equivalence: Any) -> dict[str, Any]:
    nested_space = _build_nested_space(seed, np, spaces)
    sample = nested_space.sample()
    assert nested_space.contains(sample), "Nested sample should satisfy contains"

    flat = space_utils.flatten(nested_space, sample)
    flat_space = space_utils.flatten_space(nested_space)
    restored = space_utils.unflatten(nested_space, flat)

    assert isinstance(flat, np.ndarray), "Nested fixed space should flatten to ndarray"
    assert flat.shape == (space_utils.flatdim(nested_space),)
    assert flat in flat_space, "Flattened sample should be contained in flatten_space"
    assert nested_space.contains(restored), "Restored sample should satisfy contains"
    assert data_equivalence(sample, restored), "Flatten/unflatten should round-trip"
    assert restored["agent"][0].dtype == np.float32, "Box dtype should be preserved"

    if verbose:
        print("nested sample:")
        print(json.dumps(sample, default=_json_default, indent=2, sort_keys=True))
        print("flat sample:", flat.tolist())

    return {
        "nested_flatdim": int(space_utils.flatdim(nested_space)),
        "flat_dtype": str(flat.dtype),
        "restored_box_dtype": str(restored["agent"][0].dtype),
    }


def _check_jsonable(seed: int, verbose: bool, np: Any, spaces: Any) -> dict[str, Any]:
    simple_spaces = {
        "box": spaces.Box(0.0, 1.0, shape=(2,), dtype=np.float32, seed=seed),
        "discrete": spaces.Discrete(4, start=2, dtype=np.int64, seed=seed),
        "multibinary": spaces.MultiBinary(3, seed=seed),
        "multidiscrete": spaces.MultiDiscrete([2, 3], dtype=np.int64, seed=seed),
        "text": spaces.Text(5, min_length=0, charset="abc", seed=seed),
    }

    summary: dict[str, Any] = {}
    for name, space in simple_spaces.items():
        samples = [space.sample() for _ in range(3)]
        payload = space.to_jsonable(samples)
        restored = space.from_jsonable(payload)
        assert all(space.contains(item) for item in restored), f"{name} JSON round-trip failed"
        summary[name] = {
            "sample_count": len(restored),
            "first_restored_type": type(restored[0]).__name__,
        }
        if verbose:
            print(f"{name} jsonable:", json.dumps(payload, default=_json_default))

    return summary


def _check_dynamic_limits(seed: int, np: Any, spaces: Any, space_utils: Any) -> dict[str, Any]:
    sequence_space = spaces.Sequence(spaces.Box(0.0, 1.0, shape=(2,), dtype=np.float32), seed=seed)
    graph_space = spaces.Graph(
        node_space=spaces.Box(-1.0, 1.0, shape=(2,), dtype=np.float32),
        edge_space=spaces.Discrete(2),
        seed=seed,
    )
    oneof_space = spaces.OneOf(
        (
            spaces.Discrete(2),
            spaces.Box(-1.0, 1.0, shape=(3,), dtype=np.float32),
        ),
        seed=seed,
    )

    sequence_sample = sequence_space.sample(mask=(2, None))
    graph_sample = graph_space.sample(num_nodes=3, num_edges=2)
    oneof_sample = oneof_space.sample()

    assert sequence_space.contains(sequence_sample)
    assert graph_space.contains(graph_sample)
    assert oneof_space.contains(oneof_sample)

    for dynamic_space in (sequence_space, graph_space):
        try:
            space_utils.flatdim(dynamic_space)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected flatdim to fail for {dynamic_space}")

    flat_oneof = space_utils.flatten(oneof_space, oneof_sample)
    restored_oneof = space_utils.unflatten(oneof_space, flat_oneof)
    assert oneof_space.contains(restored_oneof)

    return {
        "sequence_length": len(sequence_sample),
        "graph_nodes": int(len(graph_sample.nodes)),
        "graph_edges": 0 if graph_sample.edges is None else int(len(graph_sample.edges)),
        "oneof_flatdim": int(space_utils.flatdim(oneof_space)),
    }


def _check_contains_diagnostics(np: Any, spaces: Any) -> dict[str, Any]:
    box = spaces.Box(
        low=np.array([-1.0, 0.0], dtype=np.float32),
        high=np.array([1.0, 2.0], dtype=np.float32),
        dtype=np.float32,
    )
    good_value = np.array([0.25, 1.5], dtype=np.float32)
    wrong_shape = np.array([[0.25, 1.5]], dtype=np.float32)
    out_of_bounds = np.array([0.25, 2.5], dtype=np.float32)
    nan_value = np.array([0.25, np.nan], dtype=np.float32)

    assert box.contains(good_value)
    assert not box.contains(wrong_shape)
    assert not box.contains(out_of_bounds)
    assert not box.contains(nan_value)

    discrete = spaces.Discrete(3, start=5)
    assert not discrete.contains(0)
    assert discrete.contains(5)
    assert discrete.contains(7)
    assert not discrete.contains(8)

    multidiscrete = spaces.MultiDiscrete([2, 3], start=[1, 10])
    assert multidiscrete.contains(np.array([1, 12], dtype=np.int64))
    assert not multidiscrete.contains(np.array([0, 12], dtype=np.int64))

    return {
        "box_shape": box.shape,
        "box_dtype": str(box.dtype),
        "discrete_valid_values": [5, 6, 7],
        "multidiscrete_start": multidiscrete.start.tolist(),
        "multidiscrete_nvec": multidiscrete.nvec.tolist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate Gymnasium space sample/contains, flatten/unflatten, and JSONable contracts."
    )
    parser.add_argument("--seed", type=int, default=123, help="Seed used for deterministic samples.")
    parser.add_argument(
        "--skip-json",
        action="store_true",
        help="Skip simple-space JSONable round-trip checks.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print representative samples and JSONable payloads.",
    )
    args = parser.parse_args()

    np, spaces, space_utils, data_equivalence = _load_runtime_dependencies()

    summary: dict[str, Any] = {
        "nested": _check_nested_flatten(args.seed, args.verbose, np, spaces, space_utils, data_equivalence),
        "dynamic_limits": _check_dynamic_limits(args.seed, np, spaces, space_utils),
        "contains_diagnostics": _check_contains_diagnostics(np, spaces),
    }
    if not args.skip_json:
        summary["jsonable"] = _check_jsonable(args.seed, args.verbose, np, spaces)

    print(json.dumps(summary, default=_json_default, indent=2, sort_keys=True))
    print("SPACE_CONTRACT_SMOKE_OK")


if __name__ == "__main__":
    main()
