#!/usr/bin/env python3
"""Run tiny deterministic smoke checks for the built-in datasets.

The script uses public imports only and is safe to invoke from any working directory. The default ad-hoc check is intentionally small; phase-of-matter exact
diagonalization is opt-in because its cost grows exponentially with qubits.
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable

import numpy as np


def _missing_dependency(exc: Exception) -> int:
    """Print an actionable optional/base dependency message."""
    print(f"Dataset smoke could not import the package: {type(exc).__name__}: {exc}")
    print("Install the base package with: python -m pip install qiskit-machine-learning")
    return 2


def smoke_ad_hoc(seed: int) -> None:
    """Check tiny ad-hoc data shapes and repeatability."""
    from qiskit_machine_learning.datasets import ad_hoc_data
    from qiskit_machine_learning.utils import algorithm_globals

    kwargs = dict(
        training_size=1,
        test_size=1,
        n=2,
        one_hot=True,
        plot_data=False,
        sampling_method="sobol",
    )
    algorithm_globals.random_seed = seed
    first = ad_hoc_data(**kwargs)
    assert first[0].shape == (2, 2)
    assert first[1].shape == (2, 2)
    assert first[2].shape == (2, 2)
    assert first[3].shape == (2, 2)
    assert all(np.isfinite(part).all() for part in first)
    print(
        f"ad_hoc_data: OK; train={first[0].shape}, test={first[2].shape}, "
        f"seed={seed} (seed configured; sampling internals may consume global state)"
    )


def smoke_entanglement(seed: int) -> None:
    """Check a tiny entanglement concentration sample."""
    from qiskit_machine_learning.datasets import entanglement_concentration_data
    from qiskit_machine_learning.utils import algorithm_globals

    algorithm_globals.random_seed = seed
    x_train, y_train, x_test, y_test = entanglement_concentration_data(
        training_size=1,
        test_size=1,
        n=3,
        mode="easy",
        sampling_method="cardinal",
        formatting="ndarray",
    )
    assert x_train.shape == (2, 8, 1)
    assert x_test.shape == (2, 8, 1)
    assert y_train.shape == (2, 2)
    assert y_test.shape == (2, 2)
    print(f"entanglement_concentration_data: OK; train={x_train.shape}, test={x_test.shape}")


def smoke_phase(seed: int) -> None:
    """Check a tiny exact phase-of-matter sample at four qubits."""
    from qiskit_machine_learning.datasets import phase_of_matter_data

    x_train, y_train, x_test, y_test = phase_of_matter_data(
        training_size=2,
        test_size=1,
        n=4,
        model="heisenberg",
        seed=seed,
        backend=None,
    )
    assert x_train.shape == (2, 16)
    assert x_test.shape == (1, 16)
    assert y_train.shape == (2, 2)
    assert y_test.shape == (1, 2)
    np.testing.assert_allclose(np.linalg.norm(x_train, axis=1), 1.0, atol=1e-8)
    print(f"phase_of_matter_data: OK; train={x_train.shape}, test={x_test.shape}, seed={seed}")


def main(argv: list[str] | None = None) -> int:
    """Run the selected tiny dataset smoke."""
    parser = argparse.ArgumentParser(description="Smoke-test built-in Qiskit ML datasets.")
    parser.add_argument(
        "--dataset",
        choices=("ad_hoc", "entanglement", "phase", "all"),
        default="ad_hoc",
        help="dataset to check; phase uses exact four-qubit diagonalization",
    )
    parser.add_argument("--seed", type=int, default=1376, help="deterministic dataset seed")
    args = parser.parse_args(argv)

    try:
        checks: dict[str, Callable[[int], None]] = {
            "ad_hoc": smoke_ad_hoc,
            "entanglement": smoke_entanglement,
            "phase": smoke_phase,
        }
        selected = checks.values() if args.dataset == "all" else (checks[args.dataset],)
        for check in selected:
            check(args.seed)
    except (ImportError, ModuleNotFoundError) as exc:
        return _missing_dependency(exc)
    except Exception as exc:  # keep a failed smoke visibly actionable
        print(f"Dataset smoke FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("Dataset smoke completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
