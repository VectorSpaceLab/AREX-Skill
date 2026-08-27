#!/usr/bin/env python3
"""Run a deterministic, CPU-only NeuroMANCER signal and Node/System smoke.

The smoke deliberately uses only in-memory data. It never downloads data,
trains a model, plots, writes files, or imports a repository checkout.
"""

from __future__ import annotations

import argparse


def run_smoke() -> dict[str, object]:
    """Generate a tiny signal and verify a two-node closed-loop rollout."""
    import numpy as np
    import torch

    from neuromancer.psl.signals import step
    from neuromancer.system import Node, System

    # Explicit values make the fixture deterministic; the local generator keeps
    # the signal call compatible with the public signal API.
    rng = np.random.default_rng(7)
    signal = step(
        nsim=4,
        d=1,
        min=0.0,
        max=1.0,
        values=np.asarray([[0.0], [0.5], [1.0], [0.25]], dtype=np.float64),
        rng=rng,
    )
    reference = torch.tensor(signal, dtype=torch.float32).reshape(1, 4, 1)

    def policy(x: torch.Tensor, r: torch.Tensor) -> torch.Tensor:
        return 0.5 * x + r

    def plant(x: torch.Tensor, u: torch.Tensor) -> torch.Tensor:
        return x + u

    def make_system() -> System:
        return System(
            [
                Node(policy, ["X", "R"], ["U"], name="policy"),
                Node(plant, ["X", "U"], ["X"], name="plant"),
            ],
            nstep_key="R",
            nsteps=None,
            name="tiny_closed_loop",
        )

    def rollout() -> dict[str, torch.Tensor]:
        return make_system()(
            {
                "X": torch.zeros(1, 1, 1, dtype=torch.float32),
                "R": reference.clone(),
            }
        )

    first = rollout()
    second = rollout()
    assert signal.shape == (4, 1)
    assert np.isfinite(signal).all()
    assert first["X"].shape == (1, 5, 1)
    assert first["U"].shape == (1, 4, 1)
    assert first["R"].shape == (1, 4, 1)
    assert torch.isfinite(first["X"]).all()
    assert torch.allclose(first["X"], second["X"])
    assert torch.allclose(first["U"], second["U"])

    return {
        "signal_shape": list(signal.shape),
        "signal": signal[:, 0].tolist(),
        "output_shapes": {key: list(value.shape) for key, value in first.items()},
        "final_state": float(first["X"][0, -1, 0]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic in-memory PSL signal and CPU Node/System "
            "rollout; no network, training, plotting, or file writes."
        )
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="execute the four-step smoke (otherwise print usage guidance)",
    )
    args = parser.parse_args()
    if not args.run:
        parser.print_help()
        return 0

    try:
        result = run_smoke()
    except ImportError as exc:
        parser.error(
            "--run requires a working neuromancer CPU environment "
            f"({exc})"
        )
    print("simulation smoke passed")
    for key, value in result.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
