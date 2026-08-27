#!/usr/bin/env python3
"""Tiny smoke checks for cuML data-pipeline utilities.

This script is self-contained and only imports cuML when a real run is
requested. `--help` therefore works even when cuML is not installed.
"""

from __future__ import annotations

import argparse
import sys
import warnings


class SmokeError(RuntimeError):
    pass


class MissingDependency(SmokeError):
    pass


class BackendUnavailable(SmokeError):
    pass


def _fail(message: str, code: int = 1) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return code


def _skip(message: str) -> int:
    print(f"SKIP: {message}", file=sys.stderr)
    return 2


def _require_gpu(cp):
    try:
        count = cp.cuda.runtime.getDeviceCount()
    except Exception as exc:  # pragma: no cover - backend specific
        raise BackendUnavailable(f"CUDA runtime probe failed: {exc}") from exc
    if count < 1:
        raise BackendUnavailable("no CUDA devices are visible")
    print(f"CUDA devices visible: {count}")


def _as_float(value, cp):
    try:
        return float(value)
    except TypeError:
        return float(cp.asnumpy(value))


def run_core(cp):
    from cuml.datasets import make_blobs, make_classification, make_regression
    from cuml.metrics import accuracy_score, mean_squared_error, pairwise_distances
    from cuml.metrics.cluster import adjusted_rand_score
    from cuml.model_selection import KFold, train_test_split
    from cuml.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler

    X, y = make_classification(
        n_samples=64,
        n_features=8,
        n_informative=4,
        n_redundant=0,
        n_classes=2,
        random_state=7,
        order="F",
        dtype="float32",
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=7,
        shuffle=True,
        stratify=y,
    )
    X_scaled = StandardScaler().fit_transform(X_train)
    X_minmax = MinMaxScaler().fit_transform(X_train)
    y_encoded = LabelEncoder().fit_transform(y_train)

    if X_scaled.shape != X_train.shape or X_minmax.shape != X_train.shape:
        raise SmokeError("preprocessing returned unexpected shapes")
    if y_encoded.shape != y_train.shape:
        raise SmokeError("label encoding returned unexpected shape")

    if _as_float(accuracy_score(y_test, y_test), cp) != 1.0:
        raise SmokeError("accuracy_score self-check failed")

    X_reg, y_reg = make_regression(
        n_samples=48,
        n_features=6,
        n_informative=4,
        noise=0.0,
        random_state=11,
    )
    if _as_float(mean_squared_error(y_reg, y_reg), cp) != 0.0:
        raise SmokeError("mean_squared_error self-check failed")

    X_blob, labels = make_blobs(
        n_samples=48,
        centers=3,
        n_features=4,
        random_state=5,
    )
    if _as_float(adjusted_rand_score(labels, labels), cp) != 1.0:
        raise SmokeError("adjusted_rand_score self-check failed")

    distances = pairwise_distances(X_scaled[:3], metric="euclidean")
    if distances.shape != (3, 3):
        raise SmokeError("pairwise_distances returned unexpected shape")

    kfold = KFold(n_splits=4, shuffle=True, random_state=3)
    folds = list(kfold.split(X))
    if len(folds) != 4:
        raise SmokeError("KFold produced the wrong number of splits")

    print("CORE: synthetic generation, split, preprocess, and metric checks passed")
    print(f"CORE: make_classification -> {X.shape}, make_regression -> {X_reg.shape}, make_blobs -> {X_blob.shape}")


def run_target(cp):
    import cudf
    from cuml.preprocessing import TargetEncoder

    train = cudf.DataFrame(
        {
            "city": ["a", "b", "b", "a", "c", "c"],
            "device": ["m", "m", "w", "w", "m", "w"],
        }
    )
    y = cudf.Series([1, 0, 1, 1, 0, 0])
    valid = cudf.DataFrame({"city": ["a", "d"], "device": ["m", "w"]})

    encoder = TargetEncoder(
        n_folds=3,
        smooth=1,
        split_method="interleaved",
        stat="mean",
        multi_feature_mode="combination",
        output_type="numpy",
    )
    train_encoded = encoder.fit_transform(train[["city", "device"]], y)
    valid_encoded = encoder.transform(valid[["city", "device"]])
    if train_encoded.shape != (len(train), 1) or valid_encoded.shape != (len(valid), 1):
        raise SmokeError("TargetEncoder returned unexpected shapes")
    print("TARGET: leakage-aware target encoding passed")


def run_text(cp):
    import cudf
    from cuml.feature_extraction.text import CountVectorizer, HashingVectorizer, TfidfVectorizer

    corpus = cudf.Series(["gpu text gpu", "cuml text vector", "gpu vector"])

    count = CountVectorizer(lowercase=True, ngram_range=(1, 1), min_df=1)
    X_count = count.fit_transform(corpus)
    if X_count.shape[0] != len(corpus):
        raise SmokeError("CountVectorizer returned unexpected shape")

    hashing = HashingVectorizer(n_features=2**8, norm="l2")
    X_hash = hashing.fit_transform(corpus)
    if X_hash.shape[0] != len(corpus):
        raise SmokeError("HashingVectorizer returned unexpected shape")

    tfidf = TfidfVectorizer(lowercase=True, use_idf=True, smooth_idf=True)
    X_tfidf = tfidf.fit_transform(corpus)
    if X_tfidf.shape[0] != len(corpus):
        raise SmokeError("TfidfVectorizer returned unexpected shape")

    vocab = list(count.get_feature_names().to_pandas())
    if not vocab:
        raise SmokeError("CountVectorizer did not learn a vocabulary")
    print("TEXT: vectorization checks passed")


def run_tsa(cp):
    import warnings
    from cuml.datasets import make_arima

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        y = make_arima(
            batch_size=2,
            n_obs=24,
            order=(1, 0, 0),
            seasonal_order=(0, 0, 0, 0),
            intercept=True,
            random_state=5,
            dtype="float32",
        )
    if y.shape != (24, 2):
        raise SmokeError("make_arima returned unexpected shape")
    print("TSA: ARIMA utility shape check passed")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tiny smoke checks for cuML data-pipeline utilities."
    )
    parser.add_argument(
        "--case",
        choices=["core", "target", "text", "tsa", "all"],
        default="core",
        help="Select which utility smoke bundle to run.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        import cupy as cp
    except Exception as exc:
        return _skip(f"cupy is unavailable: {exc}")

    try:
        _require_gpu(cp)
    except BackendUnavailable as exc:
        return _skip(str(exc))

    try:
        if args.case in ("core", "all"):
            run_core(cp)
        if args.case in ("target", "all"):
            run_target(cp)
        if args.case in ("text", "all"):
            run_text(cp)
        if args.case in ("tsa", "all"):
            run_tsa(cp)
    except (MissingDependency, ModuleNotFoundError, ImportError) as exc:
        return _skip(str(exc))
    except SmokeError as exc:
        return _fail(str(exc), code=1)
    except Exception as exc:  # pragma: no cover - unexpected runtime failure
        return _fail(f"unexpected runtime failure: {exc}", code=1)

    print(f"DONE: case={args.case}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
