#!/usr/bin/env python3
"""Run a tiny KerasTuner search on synthetic data.

Safe by default: no network, no external datasets, no writes outside the
chosen work directory.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import tempfile

import numpy as np


def _add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    repo = pathlib.Path(repo_root).resolve()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))


def _build_model(hp):
    from tensorflow import keras

    model = keras.Sequential(
        [
            keras.layers.Input(shape=(3,)),
            keras.layers.Dense(hp.Choice("units", [4, 8]), activation=hp.Choice("activation", ["relu", "tanh"])),
            keras.layers.Dense(1, activation="sigmoid"),
        ]
    )
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    return model


def _make_tuner(algo: str, kt, workdir: str):
    common = dict(
        hypermodel=_build_model,
        objective="val_loss",
        directory=workdir,
        project_name=f"smoke-{algo}",
    )
    if algo == "randomsearch":
        return kt.RandomSearch(max_trials=2, **common)
    if algo == "gridsearch":
        return kt.GridSearch(**common)
    if algo == "hyperband":
        return kt.Hyperband(max_epochs=2, factor=2, hyperband_iterations=1, **common)
    if algo == "bayesian":
        return kt.BayesianOptimization(max_trials=2, **common)
    raise ValueError(f"Unknown algorithm: {algo}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Optional local checkout to add to sys.path.")
    parser.add_argument(
        "--algorithm",
        choices=["randomsearch", "gridsearch", "hyperband", "bayesian"],
        default="randomsearch",
        help="Which tuner to smoke test.",
    )
    parser.add_argument(
        "--workdir",
        help="Optional working directory for tuner artifacts. Defaults to a temp dir.",
    )
    args = parser.parse_args()
    _add_repo_root(args.repo_root)

    import keras_tuner as kt

    rng = np.random.default_rng(0)
    x = rng.normal(size=(16, 3)).astype("float32")
    y = (x[:, 0] + x[:, 1] > 0).astype("float32")

    workdir_ctx = None
    if args.workdir:
        workdir = str(pathlib.Path(args.workdir).resolve())
    else:
        workdir_ctx = tempfile.TemporaryDirectory(prefix="keras-tuner-smoke-")
        workdir = workdir_ctx.name

    tuner = _make_tuner(args.algorithm, kt, workdir)
    tuner.search(x, y, validation_split=0.25, epochs=1, batch_size=4, verbose=0)

    best = tuner.get_best_hyperparameters(1)[0]
    print(f"algorithm={args.algorithm}")
    print(f"trials={len(tuner.oracle.trials)}")
    print(f"best={best.values}")

    if workdir_ctx is not None:
        workdir_ctx.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
