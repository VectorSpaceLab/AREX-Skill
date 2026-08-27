#!/usr/bin/env python3
"""Validate tiny sktime data containers."""
from __future__ import annotations
import argparse, json, sys

def tiny_series():
    import pandas as pd
    return pd.Series([1.0,2.0,3.0], name="target")
def tiny_panel():
    import pandas as pd
    idx = pd.MultiIndex.from_product([[0,1],[0,1,2]], names=["instance","time"])
    return pd.DataFrame({"var_0":[1,2,3,1.5,2.5,3.5],"var_1":[10,11,12,10.5,11.5,12.5]}, index=idx)
def run(example="tiny-panel"):
    from sktime.datatypes import check_is_mtype
    obj = tiny_series() if example == "tiny-series" else tiny_panel()
    mtype, scitype = ("pd.Series","Series") if example == "tiny-series" else ("pd-multiindex","Panel")
    valid, msg, meta = check_is_mtype(obj, mtype, scitype=scitype, return_metadata=True, msg_return_dict="list")
    return {"ok": bool(valid), "example": example, "expected_mtype": mtype, "expected_scitype": scitype, "shape": list(getattr(obj,"shape",[])), "message": msg, "metadata": meta}
def main(argv=None):
    ap=argparse.ArgumentParser(description="Validate tiny sktime Series/Panel examples.")
    ap.add_argument("--example", choices=["tiny-series","tiny-panel"], default="tiny-panel")
    ap.add_argument("--pretty", action="store_true")
    args=ap.parse_args(argv)
    try: out=run(args.example)
    except Exception as exc:
        print(json.dumps({"ok":False,"error_type":type(exc).__name__,"error":str(exc)}), file=sys.stderr); return 1
    print(json.dumps(out, indent=2 if args.pretty else None, default=str)); return 0 if out["ok"] else 1
if __name__ == "__main__": raise SystemExit(main())
