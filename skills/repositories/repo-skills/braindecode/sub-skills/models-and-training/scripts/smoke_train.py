#!/usr/bin/env python3
"""Run a bounded local braindecode model forward and optional one-epoch fit."""
from __future__ import annotations
import argparse
import numpy as np
import torch
from braindecode import EEGClassifier
from braindecode.datasets import create_from_X_y
from braindecode.models import ShallowFBCSPNet

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fit", action="store_true", help="run one tiny CPU epoch after the forward check")
    p.add_argument("--epochs", type=int, default=1)
    args = p.parse_args()
    if args.epochs < 1:
        p.error("--epochs must be positive")
    rng = np.random.default_rng(0)
    X = rng.normal(size=(8, 4, 128)).astype("float32")
    y = np.arange(8, dtype="int64") % 2
    ds = create_from_X_y(X, y, drop_last_window=False, sfreq=128,
                         window_size_samples=128, window_stride_samples=128)
    model = ShallowFBCSPNet(n_chans=4, n_outputs=2, n_times=128,
                            final_conv_length="auto")
    with torch.no_grad():
        output = model(torch.from_numpy(X))
    assert tuple(output.shape[:2]) == (8, 2)
    print(f"forward_shape={tuple(output.shape)} windows={len(ds)}")
    if args.fit:
        clf = EEGClassifier(model, max_epochs=args.epochs, batch_size=4,
                            train_split=None, verbose=0, device="cpu")
        clf.fit(ds, y=None)
        pred = clf.predict(ds)
        assert len(pred) == len(ds)
        print(f"fit_ok predictions={len(pred)}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
