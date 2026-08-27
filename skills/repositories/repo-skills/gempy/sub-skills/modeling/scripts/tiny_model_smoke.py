#!/usr/bin/env python3
"""Run a deterministic, in-memory GemPy modeling smoke test.

This helper uses only public GemPy APIs, NumPy, and the installed matching
GemPy engine. It reads no files, uses no source-checkout paths, and makes no
network requests.
"""

from __future__ import annotations

import numpy as np


def build_and_compute():
    import gempy as gp

    frame = gp.data.StructuralFrame.initialize_default_structure()
    model = gp.create_geomodel(
        project_name="tiny_model_smoke",
        extent=[0, 100, 0, 100, 0, 100],
        resolution=[8, 8, 8],
        structural_frame=frame,
    )
    gp.add_surface_points(
        model,
        x=[10.0, 90.0, 10.0, 90.0],
        y=[10.0, 10.0, 90.0, 90.0],
        z=[40.0, 40.0, 40.0, 40.0],
        elements_names="surface1",
    )
    gp.add_orientations(
        model,
        x=[50.0],
        y=[50.0],
        z=[40.0],
        elements_names=["surface1"],
        pole_vector=[[0.0, 0.0, 1.0]],
    )

    model.validate()
    config = gp.data.GemPyEngineConfig(
        backend=gp.data.AvailableBackends.numpy,
        use_gpu=False,
    )
    solutions = gp.compute_model(model, engine_config=config)
    probe = gp.compute_model_at(
        model,
        np.array([[20.0, 20.0, 20.0], [80.0, 80.0, 80.0]], dtype=float),
        engine_config=config,
    )
    if solutions is None or probe.shape[0] != 2:
        raise AssertionError("GemPy smoke test returned no solutions or wrong probe length")
    return model, solutions, probe


def main() -> int:
    try:
        model, solutions, probe = build_and_compute()
    except Exception as exc:  # noqa: BLE001 - command-line diagnostic boundary
        print(f"tiny GemPy modeling smoke failed: {type(exc).__name__}: {exc}")
        return 1

    print(
        "tiny GemPy modeling smoke passed: "
        f"groups={len(model.structural_frame.structural_groups)} "
        f"solutions={type(solutions).__name__} probe_shape={probe.shape}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
