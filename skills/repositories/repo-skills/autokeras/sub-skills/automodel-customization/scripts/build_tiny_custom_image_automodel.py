#!/usr/bin/env python3
"""Construct or run a tiny custom AutoKeras image AutoModel graph."""
from __future__ import annotations
import argparse, os, tempfile

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); m=p.add_mutually_exclusive_group(); m.add_argument("--dry-run", action="store_true"); m.add_argument("--run-fit", action="store_true"); p.add_argument("--work-dir", default=None); args=p.parse_args(); os.environ.setdefault("KERAS_BACKEND","torch")
    import numpy as np, autokeras as ak
    inp=ak.ImageInput(); out=ak.Normalization()(inp); out=ak.ConvBlock(num_blocks=1,num_layers=1,filters=8)(out); out=ak.SpatialReduction(reduction_type="flatten")(out); out=ak.ClassificationHead(num_classes=2,dropout=0.0)(out)
    work=args.work_dir or tempfile.mkdtemp(prefix="ak-custom-image-"); model=ak.AutoModel(inputs=inp, outputs=out, max_trials=1, overwrite=True, directory=work, seed=5)
    print(f"graph=custom-image model={type(model).__name__} directory={work}")
    if not args.run_fit: print("dry_run=ok; add --run-fit for tiny fit"); return 0
    rng=np.random.default_rng(5); x=rng.random((8,28,28), dtype=np.float32); y=np.arange(8)%2; model.fit(x,y,validation_split=0.25,epochs=1,batch_size=2,verbose=0); print("fit=ok"); return 0
if __name__=="__main__": raise SystemExit(main())
