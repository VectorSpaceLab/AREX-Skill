#!/usr/bin/env python3
"""No-network smoke check for Nilearn ML/connectivity workflows."""

from __future__ import annotations

import argparse
import json
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Exercise tiny synthetic Nilearn connectivity and lightweight "
            "classification paths without downloading data."
        )
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=8,
        help="Number of synthetic subjects to generate (default: 8).",
    )
    parser.add_argument(
        "--timepoints",
        type=int,
        default=24,
        help="Timepoints per synthetic subject (default: 24).",
    )
    parser.add_argument(
        "--regions",
        type=int,
        default=5,
        help="Regions/features per synthetic subject (default: 5).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducible synthetic data (default: 0).",
    )
    parser.add_argument(
        "--skip-decoder",
        action="store_true",
        help="Skip the optional tiny Decoder image path.",
    )
    return parser


def make_subject_series(np, subjects: int, timepoints: int, regions: int, seed: int):
    rng = np.random.default_rng(seed)
    labels = np.arange(subjects) % 2
    series = []
    base = rng.normal(size=(regions, regions))
    covariance = base @ base.T + np.eye(regions) * 0.5
    for label in labels:
        subject = rng.multivariate_normal(
            mean=np.zeros(regions), cov=covariance, size=timepoints
        )
        subject[:, 0] += 0.6 * label
        subject[:, 1] -= 0.3 * label
        series.append(subject)
    return series, labels


def run_connectivity_smoke(args):
    import numpy as np
    from nilearn.connectome import ConnectivityMeasure
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    if args.subjects < 4:
        raise ValueError("--subjects must be at least 4 for stratified CV")
    if args.timepoints < 3:
        raise ValueError("--timepoints must be at least 3")
    if args.regions < 2:
        raise ValueError("--regions must be at least 2")

    series, labels = make_subject_series(
        np, args.subjects, args.timepoints, args.regions, args.seed
    )

    correlation = ConnectivityMeasure(
        kind="correlation", vectorize=True, discard_diagonal=True
    )
    corr_features = correlation.fit_transform(series)

    tangent = ConnectivityMeasure(
        kind="tangent", vectorize=True, discard_diagonal=True
    )
    tangent_features = tangent.fit_transform(series)

    cv = StratifiedKFold(n_splits=2, shuffle=True, random_state=args.seed)
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500))
    scores = cross_val_score(clf, tangent_features, labels, cv=cv)

    return {
        "correlation_shape": list(corr_features.shape),
        "tangent_shape": list(tangent_features.shape),
        "cv_scores": [float(score) for score in scores],
        "labels": labels.tolist(),
    }


def run_optional_decoder_smoke(seed: int):
    import numpy as np
    from nibabel import Nifti1Image
    from nilearn.decoding import Decoder

    rng = np.random.default_rng(seed)
    labels = np.array([0, 1, 0, 1, 0, 1])
    data = rng.normal(size=(3, 3, 3, labels.size))
    data[1, 1, 1, :] += labels * 1.5
    imgs = Nifti1Image(data, affine=np.eye(4))
    mask_img = Nifti1Image(np.ones((3, 3, 3), dtype=np.uint8), affine=np.eye(4))

    decoder = Decoder(
        estimator="svc",
        mask=mask_img,
        cv=2,
        screening_percentile=100,
        scoring="accuracy",
        n_jobs=1,
    )
    decoder.fit(imgs, labels)
    return {"classes": decoder.classes_.tolist()}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = run_connectivity_smoke(args)
        if not args.skip_decoder:
            try:
                result["decoder"] = run_optional_decoder_smoke(args.seed)
            except Exception as exc:  # pragma: no cover - diagnostic path
                result["decoder_skipped"] = f"{type(exc).__name__}: {exc}"
        print(json.dumps(result, indent=2, sort_keys=True))
    except Exception as exc:
        print(f"smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
