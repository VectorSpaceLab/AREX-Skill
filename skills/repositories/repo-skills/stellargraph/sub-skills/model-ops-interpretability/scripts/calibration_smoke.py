#!/usr/bin/env python3
"""Tiny StellarGraph calibration smoke."""
from __future__ import print_function
import argparse, sys
from pathlib import Path

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--repo-root'); a=p.parse_args(argv)
    if a.repo_root: sys.path.insert(0, str(Path(a.repo_root).expanduser().resolve()))
    import numpy as np
    from stellargraph.calibration import expected_calibration_error, IsotonicCalibration, TemperatureCalibration
    probs=np.array([0.1,0.4,0.8,0.9])
    acc=np.array([0.5,1.0])
    conf=np.array([0.25,0.85])
    ece=expected_calibration_error(probs, acc, conf)
    iso=IsotonicCalibration()
    temp=TemperatureCalibration(epochs=1)
    print('ece:', float(ece)); print('classes:', type(iso).__name__, type(temp).__name__); print('calibration smoke: ok')
    return 0
if __name__=='__main__': raise SystemExit(main())
