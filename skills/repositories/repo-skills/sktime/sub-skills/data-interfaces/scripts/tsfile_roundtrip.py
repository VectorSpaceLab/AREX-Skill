#!/usr/bin/env python3
"""Write/read a generated tiny .ts panel with sktime."""
from __future__ import annotations
import argparse, json, tempfile, sys
from pathlib import Path

def run(output_dir=None):
    import numpy as np
    from sktime.datasets import write_ndarray_to_tsfile, load_from_tsfile_to_dataframe
    from sktime.datatypes import check_is_mtype
    base = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="sktime-ts-"))
    X = np.array([[[1.0, 2.0, 3.0], [2.0, 3.0, 4.0]], [[4.0, 5.0, 6.0], [5.0, 6.0, 7.0]]])
    y = np.array(["a", "b"])
    write_ndarray_to_tsfile(X, path=base, problem_name="TinyPanel", class_label=["a","b"], class_value_list=y, equal_length=True, series_length=3)
    ts_path = base/"TinyPanel"/"TinyPanel.ts"
    X2, y2 = load_from_tsfile_to_dataframe(ts_path, return_separate_X_and_y=True)
    valid, msg, meta = check_is_mtype(X2, "nested_univ", scitype="Panel", return_metadata=True, msg_return_dict="list")
    return {"ok": bool(valid) and list(y2)==list(y), "ts_path": str(ts_path), "roundtrip_valid": bool(valid), "expected_mtype": "nested_univ", "message": msg, "metadata": meta, "labels_loaded": list(y2)}
def main(argv=None):
    ap=argparse.ArgumentParser(description="Write/read a generated tiny .ts panel with sktime.")
    ap.add_argument("--output-dir")
    ap.add_argument("--json", action="store_true")
    args=ap.parse_args(argv)
    try: out=run(args.output_dir)
    except Exception as exc:
        print(json.dumps({"ok":False,"error_type":type(exc).__name__,"error":str(exc)}), file=sys.stderr); return 1
    print(json.dumps(out, indent=None if args.json else 2, default=str)); return 0 if out["ok"] else 1
if __name__ == "__main__": raise SystemExit(main())
