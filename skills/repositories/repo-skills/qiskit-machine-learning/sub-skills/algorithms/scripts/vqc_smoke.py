#!/usr/bin/env python3
"""Run a tiny deterministic VQC/ad_hoc_data smoke using public APIs.

The script imports the package lazily so ``--help`` works even before the base
package is installed. It never reads the current directory or a source tree.
"""

from __future__ import annotations

import argparse
import sys


def run_smoke(seed: int, maxiter: int) -> int:
    """Fit a bounded two-qubit VQC and report its shapes and score."""
    try:
        from qiskit.circuit.library import real_amplitudes, zz_feature_map
        from qiskit.primitives import StatevectorSampler
        from qiskit_machine_learning.algorithms import VQC
        from qiskit_machine_learning.datasets import ad_hoc_data
        from qiskit_machine_learning.optimizers import COBYLA
        from qiskit_machine_learning.utils import algorithm_globals
    except (ImportError, ModuleNotFoundError) as exc:
        print(f"VQC smoke could not import the public package: {exc}", file=sys.stderr)
        print(
            "Install it with: python -m pip install qiskit-machine-learning",
            file=sys.stderr,
        )
        return 2

    algorithm_globals.random_seed = seed
    x_train, y_train, x_test, y_test = ad_hoc_data(
        training_size=2,
        test_size=1,
        n=2,
        gap=0.3,
        one_hot=True,
        plot_data=False,
        sampling_method="sobol",
    )
    feature_map = zz_feature_map(feature_dimension=2, reps=1, entanglement="linear")
    ansatz = real_amplitudes(num_qubits=2, reps=1)
    sampler = StatevectorSampler(seed=seed)
    model = VQC(
        feature_map=feature_map,
        ansatz=ansatz,
        sampler=sampler,
        optimizer=COBYLA(maxiter=maxiter),
    )
    model.fit(x_train, y_train)
    score = model.score(x_test, y_test)
    predictions = model.predict(x_test)
    print(f"train={x_train.shape}, labels={y_train.shape}, test={x_test.shape}")
    print(f"predictions={predictions.shape}, score={score:.3f}, maxiter={maxiter}, seed={seed}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse options and run the smoke."""
    parser = argparse.ArgumentParser(description="Run a tiny public-API VQC smoke check.")
    parser.add_argument("--seed", type=int, default=1376, help="deterministic seed")
    parser.add_argument(
        "--maxiter",
        type=int,
        default=3,
        help="COBYLA iteration bound (1-20; default: 3)",
    )
    args = parser.parse_args(argv)
    if not 1 <= args.maxiter <= 20:
        parser.error("--maxiter must be between 1 and 20")
    try:
        return run_smoke(args.seed, args.maxiter)
    except Exception as exc:  # keep runtime failures concise and actionable
        print(f"VQC smoke FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
