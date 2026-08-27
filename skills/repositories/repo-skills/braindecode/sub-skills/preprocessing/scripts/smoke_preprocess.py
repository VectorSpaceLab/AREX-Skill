#!/usr/bin/env python3
"""Apply bounded local preprocessing operations to a synthetic RawArray."""
from __future__ import annotations
import argparse
import numpy as np
import mne
from braindecode.datasets import RawDataset, BaseConcatDataset
from braindecode.preprocessing import Preprocessor, preprocess

def double_array(data):
    return data * 2.0

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sfreq", type=float, default=100.0)
    p.add_argument("--samples", type=int, default=200)
    args = p.parse_args()
    if args.sfreq <= 0 or args.samples < 20:
        p.error("sfreq must be positive and samples must be >= 20")
    rng = np.random.default_rng(0)
    info = mne.create_info(["C3", "C4"], args.sfreq, ["eeg", "eeg"])
    raw = mne.io.RawArray(rng.normal(size=(2, args.samples)).astype("float64"), info)
    before = raw.get_data().copy()
    ds = BaseConcatDataset([RawDataset(raw, description={"subject": 1})])
    preprocess(ds, [Preprocessor("resample", apply_on_array=False, sfreq=args.sfreq),
                    Preprocessor(double_array, apply_on_array=True)])
    after = ds.datasets[0].raw.get_data()
    assert after.shape == (2, args.samples)
    assert np.allclose(after, 2 * before)
    print(f"preprocessed_shape={after.shape}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
