#!/usr/bin/env python3
"""Construct or optionally run a tiny AutoKeras export/reload lifecycle."""
from __future__ import annotations
import argparse, os, pathlib, tempfile

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); m=p.add_mutually_exclusive_group(); m.add_argument("--dry-run", action="store_true"); m.add_argument("--run-fit", action="store_true"); p.add_argument("--work-dir", default=None); p.add_argument("--model-path", default=None); args=p.parse_args(); os.environ.setdefault("KERAS_BACKEND","torch")
    import numpy as np, autokeras as ak
    from keras.models import load_model
    work=pathlib.Path(args.work_dir or tempfile.mkdtemp(prefix="ak-export-")); model_path=pathlib.Path(args.model_path) if args.model_path else work/"model_autokeras.keras"
    clf=ak.ImageClassifier(max_trials=1, overwrite=True, directory=str(work), project_name="tiny_export", seed=5)
    print(f"model={type(clf).__name__} directory={work}")
    if not args.run_fit: print(f"dry_run=ok; would export to {model_path}. Add --run-fit to execute lifecycle"); return 0
    rng=np.random.default_rng(5); x=rng.random((8,28,28), dtype=np.float32); y=np.arange(8)%2; clf.fit(x,y,epochs=1,validation_split=0.25,batch_size=2,verbose=0); exported=clf.export_model(); model_path.parent.mkdir(parents=True, exist_ok=True); exported.save(model_path); loaded=load_model(model_path, custom_objects=ak.CUSTOM_OBJECTS); pred=loaded.predict(x[:2], verbose=0); print(f"export=ok loaded={type(loaded).__name__} pred_shape={getattr(pred,'shape',None)}"); return 0
if __name__=="__main__": raise SystemExit(main())
