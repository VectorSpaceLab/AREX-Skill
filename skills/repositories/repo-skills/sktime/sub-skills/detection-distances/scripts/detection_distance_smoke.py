#!/usr/bin/env python3
"""Tiny CPU smoke for sktime detection and distance workflows."""
from __future__ import annotations
import argparse, json, sys

def run():
    import numpy as np, pandas as pd
    from sktime.detection.naive import ThresholdDetector
    from sktime.dists_kernels.scipy_dist import ScipyDist
    y = pd.Series([0.0,1.0,5.0,6.0,1.0,0.0,7.0,0.0])
    seg = ThresholdDetector(upper=4.0, mode="segments").fit(y).predict(y)
    D = ScipyDist(metric="euclidean").transform(np.array([[0.,0.],[3.,4.],[6.,8.]]))
    assert D.shape == (3,3) and np.allclose(np.diag(D), 0.0)
    return {"status":"passed","detector_rows":len(seg),"distance_shape":list(D.shape),"distance_diag":[float(x) for x in np.diag(D)]}
def main(argv=None):
    ap=argparse.ArgumentParser(description="Tiny CPU smoke for detection and distance workflows.")
    ap.add_argument("--json", action="store_true")
    args=ap.parse_args(argv)
    try: out=run()
    except Exception as exc:
        print(json.dumps({"status":"failed","error_type":type(exc).__name__,"error":str(exc)}), file=sys.stderr); return 1
    print(json.dumps(out, indent=None if args.json else 2, sort_keys=True)); return 0
if __name__ == "__main__": raise SystemExit(main())
