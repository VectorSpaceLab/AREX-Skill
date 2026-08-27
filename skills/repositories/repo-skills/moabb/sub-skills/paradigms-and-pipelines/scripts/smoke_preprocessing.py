#!/usr/bin/env python3
"""Exercise MOABB's public raw-to-epoch and filter-bank contracts offline.

The fixture is an in-memory MNE RawArray with a stim channel.  No dataset
catalog, download, cache, checkout, or output file is used.
"""

from __future__ import annotations

import argparse
from typing import Sequence

import mne
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from moabb.datasets.preprocessing import RawToEpochs, RawToEvents
from moabb.pipelines import FilterBank, LogVariance


def build_raw(seed: int = 23) -> mne.io.RawArray:
    """Build a small raw recording with two event codes."""
    sfreq = 100.0
    n_times = 240
    rng = np.random.default_rng(seed)
    eeg = rng.normal(0.0, 1e-6, size=(3, n_times))
    stim = np.zeros((1, n_times))
    event_samples = [20, 100, 180]
    event_codes = [1, 2, 1]
    for sample, code in zip(event_samples, event_codes):
        stim[0, sample] = code
    info = mne.create_info(
        ["C3", "Cz", "C4", "STI 014"], sfreq, ["eeg", "eeg", "eeg", "stim"]
    )
    return mne.io.RawArray(np.vstack([eeg, stim]), info, verbose=False)


def run(tiny_fixture: bool = False) -> int:
    """Extract epochs and validate a 4-D filter-bank estimator."""
    event_id = {"left_hand": 1, "right_hand": 2}
    raw = build_raw()
    events = RawToEvents(event_id=event_id, interval=(0.0, 1.0)).transform(raw)
    if events.shape != (3, 3) or not np.array_equal(events[:, 2], [1, 2, 1]):
        raise AssertionError(f"unexpected events: {events!r}")

    epochs = RawToEpochs(
        event_id=event_id,
        tmin=0.0,
        tmax=0.5,
        baseline=None,
        channels=["C3", "Cz", "C4"],
    ).transform({"raw": raw, "events": events})
    X = epochs.get_data(copy=True)
    y = np.array(["left_hand", "right_hand", "left_hand"])
    if X.shape != (3, 3, 51) or len(y) != len(X):
        raise AssertionError(f"unexpected epochs: X={X.shape}, y={y.shape}")

    # A filter-bank tensor has bands on its final axis.  The inner estimator
    # must emit 2-D features for FilterBank to concatenate them.
    X_fb = np.stack([X, X * 0.5], axis=-1)
    bank = FilterBank(LogVariance()).fit(X_fb, y)
    features = bank.transform(X_fb)
    if features.shape != (3, 6):
        raise AssertionError(f"unexpected filter-bank features: {features.shape}")

    classifier = make_pipeline(FilterBank(LogVariance()), LogisticRegression(max_iter=100))
    classifier.fit(X_fb, y)
    predictions = classifier.predict(X_fb)
    if predictions.shape != y.shape:
        raise AssertionError("filter-bank classifier lost trial alignment")

    print(
        f"ok: events={events.shape}, epochs={X.shape}, "
        f"filter_bank_features={features.shape}, predictions={predictions.shape}"
    )
    if tiny_fixture:
        print("tiny fixture: deterministic offline preprocessing passed")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tiny-fixture",
        action="store_true",
        help="run the deterministic local fixture (the default behavior)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return run(tiny_fixture=args.tiny_fixture)


if __name__ == "__main__":
    raise SystemExit(main())
