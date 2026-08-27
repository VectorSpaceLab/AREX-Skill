#!/usr/bin/env python3
"""Run tiny deterministic MNE-Python analysis smoke checks.

The helper creates synthetic EEG data, computes a PSD, runs a tiny Welch array
check, and optionally probes scikit-learn-backed decoding imports. It avoids
network, datasets, GUI, and source-modeling prerequisites.

Example:
    python analysis_smoke.py --include-decoding
"""

from __future__ import annotations

import argparse
import json

import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sfreq", type=float, default=100.0, help="Synthetic sampling frequency")
    parser.add_argument("--duration", type=float, default=4.0, help="Synthetic duration in seconds")
    parser.add_argument("--include-decoding", action="store_true", help="Also verify mne.decoding imports that require scikit-learn")
    args = parser.parse_args()

    import mne
    from mne.time_frequency import psd_array_welch

    n_times = int(round(args.sfreq * args.duration))
    times = np.arange(n_times) / args.sfreq
    data = np.vstack([
        np.sin(2 * np.pi * 10 * times),
        0.5 * np.sin(2 * np.pi * 20 * times),
    ])
    info = mne.create_info(["Fz", "Cz"], args.sfreq, ch_types="eeg")
    raw = mne.io.RawArray(data, info, verbose=False)

    spectrum = raw.compute_psd(fmin=1, fmax=40, method="welch", verbose=False)
    psds, freqs = spectrum.get_data(return_freqs=True)
    assert psds.shape[0] == 2, psds.shape
    assert freqs[0] >= 1 and freqs[-1] <= 40, (freqs[0], freqs[-1])

    arr_psd, arr_freqs = psd_array_welch(data, sfreq=args.sfreq, fmin=1, fmax=40, verbose=False)
    assert arr_psd.shape[0] == 2, arr_psd.shape
    assert len(arr_freqs) == arr_psd.shape[-1], (len(arr_freqs), arr_psd.shape)

    decoding = "not requested"
    if args.include_decoding:
        from mne.decoding import CSP, SlidingEstimator

        decoding = f"ok: {CSP.__name__}, {SlidingEstimator.__name__}"

    result = {
        "mne_version": mne.__version__,
        "raw_shape": raw.get_data().shape,
        "spectrum_shape": psds.shape,
        "freq_range": [float(freqs[0]), float(freqs[-1])],
        "array_welch_shape": arr_psd.shape,
        "decoding": decoding,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
