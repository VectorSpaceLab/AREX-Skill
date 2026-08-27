#!/usr/bin/env python3
"""Safe sktime panel-learning smoke checks with onboard data."""
from __future__ import annotations
import argparse, json, sys

def run(include_clustering=False, n_estimators=2):
    import numpy as np
    import sktime
    from sktime.datasets import load_arrow_head
    from sktime.classification.dummy import DummyClassifier
    from sktime.classification.interval_based import TimeSeriesForestClassifier
    from sktime.regression.dummy import DummyRegressor
    X, y = load_arrow_head(split="train", return_X_y=True, return_type="numpy3D")
    clf = DummyClassifier(strategy="most_frequent").fit(X[:20], y[:20])
    pred = clf.predict(X[20:25]); assert len(pred)==5
    tsf = TimeSeriesForestClassifier(n_estimators=n_estimators, random_state=0).fit(X[:20], y[:20])
    tsf_pred = tsf.predict(X[20:25]); assert len(tsf_pred)==5
    reg = DummyRegressor(strategy="mean").fit(X[:20], np.arange(20, dtype=float))
    rpred = reg.predict(X[20:25]); assert len(rpred)==5
    out={"status":"passed","sktime_version":sktime.__version__,"classification_pred_len":len(pred),"tsf_pred_len":len(tsf_pred),"regression_pred_len":len(rpred),"X_shape":list(X.shape)}
    if include_clustering:
        from sktime.clustering.k_means import TimeSeriesKMeans
        labels = TimeSeriesKMeans(n_clusters=2, n_init=1, max_iter=2, random_state=0).fit_predict(X[:8])
        out["cluster_labels_len"] = len(labels)
    return out

def main(argv=None):
    ap=argparse.ArgumentParser(description="Run safe sktime panel-learning smoke checks.")
    ap.add_argument("--include-clustering", action="store_true")
    ap.add_argument("--n-estimators", type=int, default=2)
    ap.add_argument("--json", action="store_true")
    args=ap.parse_args(argv)
    try: out=run(args.include_clustering,args.n_estimators)
    except Exception as exc:
        print(json.dumps({"status":"failed","error_type":type(exc).__name__,"error":str(exc)}), file=sys.stderr); return 1
    print(json.dumps(out, indent=None if args.json else 2, sort_keys=True)); return 0
if __name__ == "__main__": raise SystemExit(main())
