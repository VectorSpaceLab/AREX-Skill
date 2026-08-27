#!/usr/bin/env python3
"""Create and validate a tiny deterministic MNE RawArray.

The helper is intentionally self-contained and safe: by default it writes
nothing and only prints a compact summary. Pass ``--output`` to save a FIF file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def _build_raw(sfreq: float, duration: float):
    import mne

    if sfreq <= 0:
        raise ValueError("sfreq must be positive")
    if duration <= 0:
        raise ValueError("duration must be positive")

    n_times = int(round(sfreq * duration))
    if n_times < 10:
        raise ValueError("duration * sfreq must yield at least 10 samples")

    times = np.arange(n_times, dtype=float) / sfreq
    data = np.zeros((4, n_times), dtype=float)
    data[0] = 20e-6 * np.sin(2 * np.pi * 10.0 * times)  # EEG in volts
    data[1] = 15e-6 * np.cos(2 * np.pi * 12.0 * times)  # EEG in volts
    data[2] = 80e-6 * np.exp(-0.5 * ((times - duration / 2) / 0.05) ** 2)  # EOG V

    # Stim/misc channels are arbitrary units. Put two deterministic triggers in range.
    event_samples = sorted({max(1, n_times // 4), min(n_times - 2, n_times // 2)})
    for code, sample in enumerate(event_samples, start=1):
        data[3, sample] = code

    info = mne.create_info(
        ch_names=["EEG Fz", "EEG Cz", "EOG blink", "STI 014"],
        sfreq=sfreq,
        ch_types=["eeg", "eeg", "eog", "stim"],
    )
    raw = mne.io.RawArray(data, info, verbose="ERROR")
    raw.set_annotations(mne.Annotations([duration / 3], [0.1], ["BAD_synthetic_blink"]))
    return raw, event_samples


def _validate_raw(raw, event_samples: list[int]) -> dict:
    data, times = raw.get_data(return_times=True)
    expected_shape = (4, raw.n_times)
    if data.shape != expected_shape:
        raise AssertionError(f"data shape {data.shape} != expected {expected_shape}")
    if times.shape != (raw.n_times,):
        raise AssertionError(f"times shape {times.shape} != ({raw.n_times},)")
    if raw.info["nchan"] != 4 or len(raw.ch_names) != 4:
        raise AssertionError("channel metadata count mismatch")
    if raw.get_channel_types() != ["eeg", "eeg", "eog", "stim"]:
        raise AssertionError(f"unexpected channel types: {raw.get_channel_types()}")
    if raw.info["sfreq"] <= 0:
        raise AssertionError("non-positive sampling frequency")
    stim = raw.get_data(picks=["STI 014"])[0]
    observed = np.flatnonzero(stim).tolist()
    if observed != event_samples:
        raise AssertionError(f"stim samples {observed} != expected {event_samples}")
    if len(raw.annotations) != 1 or not raw.annotations.description[0].startswith("BAD"):
        raise AssertionError("expected one BAD annotation")

    return {
        "n_channels": int(raw.info["nchan"]),
        "n_times": int(raw.n_times),
        "sfreq": float(raw.info["sfreq"]),
        "duration_sec": float(raw.n_times / raw.info["sfreq"]),
        "channel_names": [str(name) for name in raw.ch_names],
        "channel_types": [str(kind) for kind in raw.get_channel_types()],
        "stim_event_samples": [int(sample) for sample in observed],
        "annotations": [
            {
                "onset": float(raw.annotations.onset[idx]),
                "duration": float(raw.annotations.duration[idx]),
                "description": str(raw.annotations.description[idx]),
            }
            for idx in range(len(raw.annotations))
        ],
        "preload": bool(raw.preload),
    }


def _check_raw_fif_name(path: Path) -> None:
    allowed = (
        "raw.fif",
        "raw_sss.fif",
        "raw_tsss.fif",
        "_meg.fif",
        "_eeg.fif",
        "_ieeg.fif",
        "raw.fif.gz",
        "raw_sss.fif.gz",
        "raw_tsss.fif.gz",
        "_meg.fif.gz",
        "_eeg.fif.gz",
        "_ieeg.fif.gz",
    )
    name = path.name
    if not name.endswith(allowed):
        raise SystemExit(
            "--output must use an MNE Raw FIF filename ending such as "
            "'synthetic_raw.fif' or 'synthetic_eeg.fif'"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sfreq", type=float, default=100.0, help="Sampling frequency in Hz.")
    parser.add_argument("--duration", type=float, default=2.0, help="Duration in seconds.")
    parser.add_argument("--output", type=Path, help="Optional Raw FIF output path.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite --output if it exists.")
    parser.add_argument(
        "--summary-json",
        action="store_true",
        help="Print machine-readable JSON instead of key=value lines.",
    )
    args = parser.parse_args()

    raw, event_samples = _build_raw(args.sfreq, args.duration)
    summary = _validate_raw(raw, event_samples)

    if args.output is not None:
        _check_raw_fif_name(args.output)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        saved = raw.save(args.output, overwrite=args.overwrite, verbose="ERROR")
        summary["saved"] = [str(path) for path in saved]

    if args.summary_json:
        print(json.dumps(summary, sort_keys=True))
    else:
        for key, value in summary.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
