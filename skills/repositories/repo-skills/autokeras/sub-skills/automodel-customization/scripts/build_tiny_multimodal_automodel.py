#!/usr/bin/env python3
"""Construct or run a tiny multimodal/multitask AutoKeras AutoModel."""
from __future__ import annotations
import argparse, os, tempfile

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); m=p.add_mutually_exclusive_group(); m.add_argument("--dry-run", action="store_true"); m.add_argument("--run-fit", action="store_true"); p.add_argument("--work-dir", default=None); args=p.parse_args(); os.environ.setdefault("KERAS_BACKEND","torch")
    import numpy as np, autokeras as ak
    img=ak.ImageInput(); tab=ak.StructuredDataInput(column_names=["age","fare"], column_types={"age":"numerical","fare":"numerical"})
    ib=ak.ImageBlock(block_type="vanilla", normalize=True, augment=False)(img); tb=ak.DenseBlock(num_layers=1, num_units=8)(tab); merged=ak.Merge()([ib,tb]); reg=ak.RegressionHead(output_dim=1, metrics=["mae"], dropout=0.0)(merged); cls=ak.ClassificationHead(num_classes=2, metrics=["accuracy"], dropout=0.0)(merged)
    work=args.work_dir or tempfile.mkdtemp(prefix="ak-multimodal-"); model=ak.AutoModel(inputs=[img,tab], outputs=[reg,cls], max_trials=1, overwrite=True, directory=work, seed=5)
    print(f"graph=multimodal model={type(model).__name__} directory={work}")
    if not args.run_fit: print("dry_run=ok; add --run-fit for tiny fit"); return 0
    rng=np.random.default_rng(5); image_x=rng.random((8,28,28), dtype=np.float32); tab_x=np.array([[20.,7.5],[30.,20.],[40.,40.],[50.,80.],[25.,10.],[35.,30.],[45.,60.],[55.,90.]], dtype=np.float32); reg_y=rng.random((8,1), dtype=np.float32); cls_y=np.arange(8)%2; model.fit([image_x,tab_x],[reg_y,cls_y],validation_split=0.25,epochs=1,batch_size=2,verbose=0); print("fit=ok"); return 0
if __name__=="__main__": raise SystemExit(main())
