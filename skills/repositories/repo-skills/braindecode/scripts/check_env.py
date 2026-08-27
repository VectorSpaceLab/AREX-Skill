#!/usr/bin/env python3
"""Run a safe braindecode import, API, and tiny CPU model smoke check.

This helper never downloads data or touches model hubs. Use ``--help`` for
options and run it from any working directory after installing braindecode.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-model", action="store_true", help="skip the tiny model forward")
    args = parser.parse_args()
    try:
        import torch
        import braindecode
        from braindecode import EEGClassifier, EEGRegressor
        from braindecode.datasets import create_from_X_y
    except Exception as exc:
        print(f"braindecode smoke failed during import: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(f"braindecode={braindecode.__version__}")
    print(f"torch={torch.__version__}; cuda_available={torch.cuda.is_available()}")
    print(f"distribution={importlib.metadata.version('braindecode')}")
    print(f"wrappers={EEGClassifier.__name__},{EEGRegressor.__name__}")
    if not args.no_model:
        import numpy as np
        from braindecode.models import ShallowFBCSPNet
        X = np.zeros((2, 4, 128), dtype="float32")
        ds = create_from_X_y(X, np.array([0, 1]), drop_last_window=False,
                             sfreq=128, window_size_samples=128,
                             window_stride_samples=128)
        model = ShallowFBCSPNet(n_chans=4, n_outputs=2, n_times=128,
                                final_conv_length="auto")
        with torch.no_grad():
            out = model(torch.from_numpy(X))
        assert tuple(out.shape[:2]) == (2, 2)
        assert len(ds) == 2
        print(f"cpu_forward_shape={tuple(out.shape)}; windows={len(ds)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
