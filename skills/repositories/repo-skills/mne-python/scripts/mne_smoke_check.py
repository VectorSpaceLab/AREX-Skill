#!/usr/bin/env python3
"""Run safe MNE-Python smoke checks without datasets, GUI, or repo files.

Example:
    python scripts/mne_smoke_check.py --include-decoding
"""

from __future__ import annotations

import argparse
import importlib
import json

import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-decoding", action="store_true", help="Also import scikit-learn-backed MNE decoding objects")
    parser.add_argument("--sfreq", type=float, default=100.0, help="Synthetic sampling frequency")
    parser.add_argument("--duration", type=float, default=2.0, help="Synthetic duration in seconds")
    args = parser.parse_args()

    import mne

    modules = [
        "mne.io",
        "mne.preprocessing",
        "mne.viz",
        "mne.time_frequency",
        "mne.stats",
        "mne.simulation",
        "mne.commands",
    ]
    imported = []
    for name in modules:
        importlib.import_module(name)
        imported.append(name)

    n_times = int(round(args.sfreq * args.duration))
    data = np.zeros((2, n_times), dtype=float)
    info = mne.create_info(["Fz", "Cz"], sfreq=args.sfreq, ch_types="eeg")
    raw = mne.io.RawArray(data, info, verbose=False)
    events = mne.make_fixed_length_events(raw, id=1, duration=0.5)
    epochs = mne.Epochs(raw, events, tmin=0, tmax=0.2, baseline=None, preload=True, verbose=False)
    evoked = epochs.average()
    spectrum = raw.compute_psd(fmax=min(40.0, args.sfreq / 2 - 1), verbose=False)

    decoding = "not requested"
    if args.include_decoding:
        from mne.decoding import CSP, SlidingEstimator

        decoding = [CSP.__name__, SlidingEstimator.__name__]

    result = {
        "mne_version": mne.__version__,
        "imported_modules": imported,
        "raw_shape": raw.get_data().shape,
        "events_shape": events.shape,
        "epochs_shape": epochs.get_data().shape,
        "evoked_shape": evoked.data.shape,
        "spectrum_shape": spectrum.get_data().shape,
        "decoding": decoding,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
