#!/usr/bin/env python3
"""Construct or run a tiny offline AutoKeras text task."""
from __future__ import annotations
import argparse, os, tempfile

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--task", choices=["classifier","regressor"], default="classifier")
    m=p.add_mutually_exclusive_group(); m.add_argument("--dry-run", action="store_true"); m.add_argument("--run-fit", action="store_true")
    p.add_argument("--work-dir", default=None)
    args=p.parse_args(); os.environ.setdefault("KERAS_BACKEND","torch")
    import numpy as np, autokeras as ak
    x=np.array(["bright calm movie", "dull noisy movie", "happy useful text", "sad weak text"]*2); work=args.work_dir or tempfile.mkdtemp(prefix="ak-text-")
    if args.task=="classifier": y=np.arange(len(x))%2; model=ak.TextClassifier(max_trials=1, overwrite=True, directory=work, seed=5)
    else: y=np.arange(len(x), dtype="float32").reshape(-1,1); model=ak.TextRegressor(max_trials=1, overwrite=True, directory=work, seed=5)
    print(f"task={args.task} x_shape={x.shape} y_shape={y.shape} model={type(model).__name__}")
    if not args.run_fit: print("dry_run=ok; add --run-fit for tiny training smoke"); return 0
    model.fit(x,y,epochs=1,validation_split=0.25,batch_size=2,verbose=0); pred=model.predict(x[:2],verbose=0); print(f"fit=ok pred_shape={getattr(pred,'shape',None)}"); return 0
if __name__=="__main__": raise SystemExit(main())
