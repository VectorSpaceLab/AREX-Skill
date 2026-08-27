#!/usr/bin/env python3
"""Deterministic smoke helper for tslearn data-preparation workflows.

Default mode runs tiny checks for:
- cached dataset loading
- synthetic generation
- formatting and text I/O
- preprocessing and feature synchronization
- piecewise transforms
- interop conversions, including optional pandas-backed formats when available

Use --malformed-conversion to raise a clear ValueError for a bad conversion
input. That mode is meant as a negative-path check, not as a passing smoke run.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np

from tslearn.datasets import CachedDatasets
from tslearn.generators import random_walk_blobs, random_walks
from tslearn.piecewise import (
    OneD_SymbolicAggregateApproximation,
    PiecewiseAggregateApproximation,
    SymbolicAggregateApproximation,
)
from tslearn.preprocessing import (
    TimeSeriesFeatureSynchronizer,
    TimeSeriesImputer,
    TimeSeriesResampler,
    TimeSeriesScalerMeanVariance,
    TimeSeriesScalerMinMax,
)
from tslearn.utils import (
    check_equal_size,
    from_cesium_dataset,
    from_pyflux_dataset,
    from_pyts_dataset,
    from_seglearn_dataset,
    from_sktime_dataset,
    from_stumpy_dataset,
    from_tsfresh_dataset,
    load_time_series_txt,
    save_time_series_txt,
    str_to_time_series,
    time_series_to_str,
    to_cesium_dataset,
    to_pyflux_dataset,
    to_pyts_dataset,
    to_sklearn_dataset,
    to_seglearn_dataset,
    to_sktime_dataset,
    to_stumpy_dataset,
    to_tsfresh_dataset,
    to_time_series,
    to_time_series_dataset,
)


def _assert_allclose(actual, expected, *, label):
    np.testing.assert_allclose(actual, expected, equal_nan=True, err_msg=label)


def _sort_by_first_value(X):
    return X[np.argsort(X[:, 0, 0])]


def _check_cached_datasets():
    cached = CachedDatasets()
    names = cached.list_datasets()
    if "Trace" not in names:
        raise AssertionError("Trace should be present in CachedDatasets().list_datasets().")

    X_train, y_train, X_test, y_test = cached.load_dataset("Trace")
    if X_train.shape != (100, 275, 1):
        raise AssertionError(f"Unexpected Trace train shape: {X_train.shape}")
    if X_test.shape != (100, 275, 1):
        raise AssertionError(f"Unexpected Trace test shape: {X_test.shape}")
    if y_train.shape != (100,) or y_test.shape != (100,):
        raise AssertionError("Unexpected Trace label shape.")

    if not check_equal_size(X_train):
        raise AssertionError("Trace should be equal-length after loading.")

    print("[ok] cached datasets")


def _check_generators_and_scalers():
    walks = random_walks(n_ts=2, sz=8, d=2, random_state=0)
    if walks.shape != (2, 8, 2):
        raise AssertionError(f"Unexpected random_walks shape: {walks.shape}")

    blob_X, blob_y = random_walk_blobs(
        n_ts_per_blob=2,
        sz=8,
        d=1,
        n_blobs=2,
        random_state=0,
    )
    if blob_X.shape != (4, 8, 1) or blob_y.shape != (4,):
        raise AssertionError("Unexpected random_walk_blobs output shape.")

    scaled_minmax = TimeSeriesScalerMinMax().fit_transform(walks)
    scaled_meanvar = TimeSeriesScalerMeanVariance().fit_transform(walks)
    if scaled_minmax.shape != walks.shape or scaled_meanvar.shape != walks.shape:
        raise AssertionError("Scaling changed the expected shape.")

    if not np.isfinite(scaled_minmax).all():
        raise AssertionError("Min-max scaling should not introduce non-finite values here.")
    if not np.isfinite(scaled_meanvar).all():
        raise AssertionError("Mean-variance scaling should not introduce non-finite values here.")

    print("[ok] generators and scalers")


def _check_variable_length_chain():
    raw = [
        [[1.0, 10.0], [2.0, np.nan]],
        [[3.0, 30.0], [np.nan, 31.0], [5.0, 32.0]],
    ]
    X = to_time_series_dataset(raw)
    if X.shape != (2, 3, 2):
        raise AssertionError(f"Unexpected normalized shape: {X.shape}")

    imputed = TimeSeriesImputer(method="linear", keep_trailing_nans=True).fit_transform(X)
    timestamps = np.array(
        [
            [
                [np.datetime64("2024-01-01"), np.datetime64("2024-01-01")],
                [np.datetime64("2024-01-02"), np.datetime64("2024-01-03")],
                [np.datetime64("NaT"), np.datetime64("NaT")],
            ],
            [
                [np.datetime64("2024-02-01"), np.datetime64("2024-02-01")],
                [np.datetime64("2024-02-02"), np.datetime64("2024-02-03")],
                [np.datetime64("2024-02-04"), np.datetime64("2024-02-05")],
            ],
        ],
        dtype="datetime64[ns]",
    )
    synchronized = TimeSeriesFeatureSynchronizer(reference_feature_index=0).fit_transform(
        imputed,
        timestamps=timestamps,
    )
    if synchronized.shape != (2, 3, 2):
        raise AssertionError(f"Unexpected synchronized shape: {synchronized.shape}")

    resampled = TimeSeriesResampler(sz=2).fit_transform(synchronized)
    if resampled.shape != (2, 2, 2):
        raise AssertionError(f"Unexpected resampled shape: {resampled.shape}")

    if check_equal_size(X):
        raise AssertionError("Ragged input should not report equal size.")

    print("[ok] variable-length repair chain")


def _check_text_io():
    series = to_time_series([1, 2, np.nan])
    trimmed = to_time_series([1, 2, np.nan], remove_nans=True)
    if series.shape != (3, 1) or trimmed.shape != (2, 1):
        raise AssertionError("Unexpected time-series formatting shape.")

    round_trip = str_to_time_series(time_series_to_str([[1.0, 3.0], [2.0, 4.0]], fmt="%.1f"))
    _assert_allclose(round_trip, np.array([[1.0, 3.0], [2.0, 4.0]]), label="text round-trip")

    dataset = to_time_series_dataset([[1, 2, 3], [1, 2]])
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "series.txt"
        save_time_series_txt(path, dataset)
        restored = load_time_series_txt(path)
    _assert_allclose(restored, dataset, label="dataset text round-trip")

    print("[ok] text I/O")


def _check_piecewise():
    source = TimeSeriesScalerMeanVariance().fit_transform(
        random_walks(n_ts=2, sz=12, d=1, random_state=0)
    )

    paa = PiecewiseAggregateApproximation(n_segments=3)
    paa_repr = paa.fit_transform(source)
    if paa_repr.shape != (2, 3, 1):
        raise AssertionError(f"Unexpected PAA shape: {paa_repr.shape}")
    if paa.inverse_transform(paa_repr).shape != source.shape:
        raise AssertionError("PAA inverse_transform should restore the original shape.")

    sax = SymbolicAggregateApproximation(n_segments=3, alphabet_size_avg=4)
    sax_repr = sax.fit_transform(source)
    if sax_repr.shape != (2, 3, 1):
        raise AssertionError(f"Unexpected SAX shape: {sax_repr.shape}")
    if not np.issubdtype(sax_repr.dtype, np.integer):
        raise AssertionError("SAX output should be integer-coded.")
    if sax.inverse_transform(sax_repr).shape != source.shape:
        raise AssertionError("SAX inverse_transform should restore the original shape.")

    one_d = OneD_SymbolicAggregateApproximation(
        n_segments=3,
        alphabet_size_avg=4,
        alphabet_size_slope=3,
    )
    one_d_repr = one_d.fit_transform(source)
    if one_d_repr.shape != (2, 3, 2):
        raise AssertionError(f"Unexpected 1d-SAX shape: {one_d_repr.shape}")
    if not np.issubdtype(one_d_repr.dtype, np.integer):
        raise AssertionError("1d-SAX output should be integer-coded.")
    if one_d.inverse_transform(one_d_repr).shape != source.shape:
        raise AssertionError("1d-SAX inverse_transform should restore the original shape.")

    print("[ok] piecewise transforms")


def _check_pure_numpy_interop():
    base = np.array(
        [
            [[1.0, 10.0], [2.0, 11.0], [3.0, 12.0]],
            [[4.0, 20.0], [5.0, 21.0], [6.0, 22.0]],
        ]
    )
    single = base[:1]

    flat, dim = to_sklearn_dataset(base, return_dim=True)
    if flat.shape != (2, 6) or dim != 2:
        raise AssertionError("Unexpected sklearn conversion shape.")

    _assert_allclose(from_pyts_dataset(to_pyts_dataset(base)), base, label="pyts round-trip")
    _assert_allclose(from_seglearn_dataset(to_seglearn_dataset(base)), base, label="seglearn round-trip")
    _assert_allclose(from_stumpy_dataset(to_stumpy_dataset(base)), base, label="stumpy round-trip")

    print("[ok] pure NumPy interop")
    return base, single


def _check_pandas_interop(base, single):
    try:
        import pandas as pd  # noqa: F401
    except ImportError:
        print("[skip] pandas-backed interop (pandas not installed)")
        return

    sktime_df = to_sktime_dataset(base)
    if sktime_df.shape != (2, 2):
        raise AssertionError(f"Unexpected sktime shape: {sktime_df.shape}")
    _assert_allclose(from_sktime_dataset(sktime_df), base, label="sktime round-trip")

    pyflux_df = to_pyflux_dataset(single)
    if pyflux_df.shape != (3, 2):
        raise AssertionError(f"Unexpected pyflux shape: {pyflux_df.shape}")
    _assert_allclose(from_pyflux_dataset(pyflux_df), single, label="pyflux round-trip")

    tsfresh_df = to_tsfresh_dataset(base)
    expected_columns = {"id", "time", "dim_0", "dim_1"}
    if set(tsfresh_df.columns) != expected_columns:
        raise AssertionError(f"Unexpected tsfresh columns: {list(tsfresh_df.columns)}")
    tsfresh_back = from_tsfresh_dataset(tsfresh_df)
    _assert_allclose(
        _sort_by_first_value(tsfresh_back),
        _sort_by_first_value(base),
        label="tsfresh round-trip",
    )

    print("[ok] pandas-backed interop")


def _check_cesium_interop(base):
    try:
        from cesium.time_series import TimeSeries  # noqa: F401
    except ImportError:
        print("[skip] cesium interop (cesium not installed)")
        return

    cesium_ds = to_cesium_dataset(base)
    if len(cesium_ds) != base.shape[0]:
        raise AssertionError("Unexpected cesium conversion length.")
    _assert_allclose(from_cesium_dataset(cesium_ds), base, label="cesium round-trip")

    print("[ok] cesium interop")


def _run_smoke():
    _check_cached_datasets()
    _check_generators_and_scalers()
    _check_variable_length_chain()
    _check_text_io()
    _check_piecewise()
    base, single = _check_pure_numpy_interop()
    _check_pandas_interop(base, single)
    _check_cesium_interop(base)
    print("[ok] data-preparation smoke checks passed")


def _run_malformed_conversion():
    try:
        to_pyts_dataset([np.array([1, 2, 3]), np.array([1, 2])])
    except ValueError as exc:
        raise ValueError(
            "Malformed conversion input: pyts conversion requires equal-length time series."
        ) from exc
    raise AssertionError("Expected to_pyts_dataset to reject ragged input.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run tiny deterministic checks for tslearn data preparation."
    )
    parser.add_argument(
        "--malformed-conversion",
        action="store_true",
        help="raise a clear ValueError for a malformed conversion input",
    )
    args = parser.parse_args(argv)

    if args.malformed_conversion:
        _run_malformed_conversion()
        return 0

    _run_smoke()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
