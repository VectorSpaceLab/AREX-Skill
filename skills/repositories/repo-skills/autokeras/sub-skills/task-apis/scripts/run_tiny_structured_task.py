#!/usr/bin/env python3
"""Construct or run a tiny offline AutoKeras structured-data task."""
from __future__ import annotations
import argparse, os, tempfile

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--task", choices=["classifier","regressor"], default="classifier")
    m=p.add_mutually_exclusive_group(); m.add_argument("--dry-run", action="store_true"); m.add_argument("--run-fit", action="store_true")
    p.add_argument("--work-dir", default=None)
    args=p.parse_args(); os.environ.setdefault("KERAS_BACKEND","torch")
    import numpy as np, autokeras as ak
    names=["age","fare","ticket_class","embark_town"]; types={"age":"numerical","fare":"numerical","ticket_class":"categorical","embark_town":"categorical"}
    x=np.array([[22.0,7.25,"third","S"],[38.0,71.28,"first","C"],[26.0,7.93,"third","S"],[35.0,53.10,"first","S"]]*2, dtype=object); work=args.work_dir or tempfile.mkdtemp(prefix="ak-structured-")
    if args.task=="classifier": y=np.array([0,1,1,1]*2); model=ak.StructuredDataClassifier(column_names=names,column_types=types,max_trials=1,overwrite=True,directory=work,seed=5)
    else: y=np.array([[100.0],[200.0],[150.0],[250.0]]*2, dtype="float32"); model=ak.StructuredDataRegressor(column_names=names,column_types=types,max_trials=1,overwrite=True,directory=work,seed=5)
    print(f"task={args.task} x_shape={x.shape} y_shape={y.shape} columns={names} model={type(model).__name__}")
    if not args.run_fit: print("dry_run=ok; add --run-fit for tiny training smoke"); return 0
    model.fit(x,y,epochs=1,validation_split=0.25,batch_size=2,verbose=0); pred=model.predict(x[:2],verbose=0); print(f"fit=ok pred_shape={getattr(pred,'shape',None)}"); return 0
if __name__=="__main__": raise SystemExit(main())
