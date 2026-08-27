#!/usr/bin/env python
"""Synthetic smoke check for MNE preprocessing, Epochs, and Evoked workflows.

This helper creates a tiny RawArray, extracts stim and annotation events, drops
an epoch via a BAD annotation, averages to Evoked, computes covariance/rank, and
prints assertion-backed status lines. It does not read external datasets.
"""

from __future__ import annotations

import argparse
import json

import numpy as np


def _build_raw(mne):
    rng = np.random.RandomState(13)
    sfreq = 100.0
    n_times = int(sfreq * 20.0)
    times = np.arange(n_times) / sfreq

    eeg = 1e-6 * rng.randn(4, n_times)
    # Add a small condition-locked response on EEG 001/002.
    for samp, amp in [(200, 5e-6), (600, -5e-6), (1000, 5e-6), (1400, -5e-6)]:
        width = int(0.12 * sfreq)
        window = np.hanning(width)
        eeg[0, samp : samp + width] += amp * window
        eeg[1, samp : samp + width] -= amp * window / 2

    eog = 2e-6 * rng.randn(1, n_times)
    stim = np.zeros((1, n_times))
    for samp, code in [(200, 3), (600, 7), (1000, 3), (1400, 7)]:
        stim[0, samp : samp + 3] = code

    data = np.vstack([eeg, eog, stim])
    ch_names = ["EEG 001", "EEG 002", "EEG 003", "EEG 004", "EOG 001", "STI 014"]
    ch_types = ["eeg", "eeg", "eeg", "eeg", "eog", "stim"]
    info = mne.create_info(ch_names, sfreq=sfreq, ch_types=ch_types)
    raw = mne.io.RawArray(data, info, verbose=False)

    annotations = mne.Annotations(
        onset=[2.0, 6.0, 10.0, 6.0],
        duration=[0.0, 0.0, 0.0, 0.2],
        description=["Stim/A", "Stim/B", "Stim/A", "BAD_artifact"],
    )
    raw.set_annotations(annotations)
    return raw


def run_smoke(as_json: bool = False) -> dict[str, object]:
    import mne

    mne.set_log_level("WARNING")
    raw = _build_raw(mne)

    # Safe continuous filtering/cropping on a copy.
    raw_filtered = raw.copy().crop(tmin=0.0, tmax=12.0).filter(
        l_freq=1.0,
        h_freq=30.0,
        picks="eeg",
        fir_design="firwin",
        verbose=False,
    )
    assert raw_filtered.n_times <= raw.n_times
    assert raw_filtered.info["highpass"] >= 1.0

    stim_events = mne.find_events(
        raw,
        stim_channel="STI 014",
        consecutive=False,
        shortest_event=1,
        verbose=False,
    )
    assert stim_events.shape == (4, 3)
    assert set(stim_events[:, 2]) == {3, 7}

    annotation_events, annotation_id = mne.events_from_annotations(raw, verbose=False)
    assert annotation_events.shape == (3, 3)
    assert set(annotation_id) == {"Stim/A", "Stim/B"}

    fixed_events = mne.make_fixed_length_events(
        raw, id=42, duration=2.0, overlap=0.5
    )
    assert fixed_events.shape[1] == 3
    assert len(fixed_events) > 0

    event_id = {"face": 3, "scramble": 7}
    epochs = mne.Epochs(
        raw,
        stim_events,
        event_id=event_id,
        tmin=-0.1,
        tmax=0.3,
        baseline=(None, 0),
        picks="eeg",
        preload=True,
        reject_by_annotation=True,
        event_repeated="error",
        verbose=False,
    )
    # The event at 6 s overlaps BAD_artifact and should be dropped.
    assert len(epochs) == 3
    assert any("BAD_artifact" in reason for log in epochs.drop_log for reason in log)
    assert epochs.get_data(copy=True).shape[1] == 4

    duplicate_events = np.vstack([stim_events[:2], [stim_events[0, 0], 0, 99]])
    dup_epochs = mne.Epochs(
        raw,
        duplicate_events,
        event_id={"face": 3, "scramble": 7, "duplicate": 99},
        tmin=-0.05,
        tmax=0.05,
        baseline=None,
        picks="eeg",
        preload=True,
        reject_by_annotation=False,
        event_repeated="merge",
        verbose=False,
    )
    assert any("/" in key for key in dup_epochs.event_id)

    evoked = epochs["face"].average()
    assert evoked.data.shape[0] == 4
    assert evoked.nave == len(epochs["face"])
    evoked_short = evoked.copy().crop(0.0, 0.2)
    assert evoked_short.times[0] >= 0.0

    rank = mne.compute_rank(epochs, tol="auto", verbose=False)
    cov = mne.compute_covariance(
        epochs,
        tmax=0,
        method="empirical",
        rank=rank,
        on_few_samples="ignore",
        verbose=False,
    )
    cov_names = list(cov.ch_names)
    assert cov.data.shape[0] == len(cov_names)

    summary = {
        "mne_version": mne.__version__,
        "stim_events": int(len(stim_events)),
        "annotation_events": int(len(annotation_events)),
        "fixed_events": int(len(fixed_events)),
        "epochs_kept": int(len(epochs)),
        "evoked_nave": int(evoked.nave),
        "rank": {key: int(value) for key, value in rank.items()},
        "covariance_channels": int(len(cov_names)),
        "duplicate_event_keys": sorted(dup_epochs.event_id),
    }
    if as_json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        for key, value in summary.items():
            print(f"{key}: {value}")
        print("preprocessing smoke assertions: ok")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    args = parser.parse_args()
    run_smoke(as_json=args.json)


if __name__ == "__main__":
    main()
