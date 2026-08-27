#!/usr/bin/env python3
"""Tiny matrix-profile and persistence smoke checks for tslearn."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
from sklearn.exceptions import NotFittedError

from tslearn.clustering import KShape
from tslearn.matrix_profile import MatrixProfile


def build_matrix_profile_series() -> np.ndarray:
    """Return a tiny univariate series for the MatrixProfile smoke."""

    return np.array(
        [
            0.0,
            1.0,
            3.0,
            2.0,
            9.0,
            1.0,
            14.0,
            15.0,
            1.0,
            2.0,
            2.0,
            10.0,
            7.0,
        ],
        dtype=float,
    ).reshape(1, -1, 1)


def build_serialization_case() -> tuple[np.ndarray, KShape]:
    """Return a tiny fitted-model fixture for persistence checks."""

    X = np.array(
        [
            [[0.0], [1.0], [0.0], [1.0], [0.0]],
            [[0.1], [1.1], [0.1], [1.1], [0.1]],
            [[3.0], [2.0], [3.0], [2.0], [3.0]],
            [[2.9], [1.9], [2.9], [1.9], [2.9]],
        ],
        dtype=float,
    )
    init = np.array([X[0], X[2]])
    model = KShape(
        n_clusters=2,
        n_init=1,
        max_iter=5,
        random_state=0,
        init=init,
    )
    return X, model


def h5py_is_available() -> bool:
    try:
        import h5py  # noqa: F401
    except ImportError:
        return False
    return True


def assert_unfitted_raises(model_factory, fmt: str, path: Path) -> None:
    model = model_factory()
    saver = getattr(model, f"to_{fmt}")
    try:
        saver(str(path))
    except NotFittedError:
        return
    raise AssertionError(f"Expected NotFittedError for unfitted {fmt} save")


def run_matrix_profile() -> None:
    X = build_matrix_profile_series()
    numpy_mp = MatrixProfile(subsequence_length=4, implementation="numpy")
    numpy_out = numpy_mp.fit_transform(X)

    try:
        stump_out = MatrixProfile(
            subsequence_length=4,
            implementation="stump",
        ).fit_transform(X)
    except ImportError:
        print("stumpy not installed; checked MatrixProfile numpy baseline only.")
        return

    np.testing.assert_allclose(numpy_out, stump_out)
    print("MatrixProfile numpy/stump match on the tiny series.")


def run_serialization() -> None:
    X, model = build_serialization_case()
    use_hdf5 = h5py_is_available()

    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)

        def model_factory() -> KShape:
            _, fresh_model = build_serialization_case()
            return fresh_model

        for fmt in ("json", "pickle"):
            assert_unfitted_raises(model_factory, fmt, tmpdir / f"unfitted.{fmt}")

        if use_hdf5:
            assert_unfitted_raises(model_factory, "hdf5", tmpdir / "unfitted.hdf5")
        else:
            print("h5py not installed; skipping unfitted HDF5 check.")

        model.fit(X)
        baseline_pred = model.predict(X)
        baseline_centers = model.cluster_centers_.copy()

        for fmt in ("json", "pickle"):
            path = tmpdir / f"kshape.{fmt}"
            getattr(model, f"to_{fmt}")(str(path))
            loaded = getattr(KShape, f"from_{fmt}")(str(path))
            np.testing.assert_array_equal(loaded.predict(X), baseline_pred)
            np.testing.assert_allclose(loaded.cluster_centers_, baseline_centers)
            print(f"KShape {fmt} round-trip ok.")

        if use_hdf5:
            path = tmpdir / "kshape.hdf5"
            model.to_hdf5(str(path))
            loaded = KShape.from_hdf5(str(path))
            np.testing.assert_array_equal(loaded.predict(X), baseline_pred)
            np.testing.assert_allclose(loaded.cluster_centers_, baseline_centers)
            print("KShape hdf5 round-trip ok.")
        else:
            print("h5py not installed; validated JSON and Pickle only.")


def run_all() -> None:
    run_matrix_profile()
    run_serialization()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tiny matrix-profile and persistence smoke checks for tslearn."
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser(
        "matrix-profile",
        help="Compare MatrixProfile numpy and stump implementations.",
    )
    subparsers.add_parser(
        "serialization",
        help="Round-trip a tiny fitted estimator through JSON, Pickle, and HDF5.",
    )
    subparsers.add_parser(
        "all",
        help="Run both smoke checks.",
    )
    parser.set_defaults(command="all")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "matrix-profile":
        run_matrix_profile()
    elif args.command == "serialization":
        run_serialization()
    else:
        run_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
