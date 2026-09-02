#!/usr/bin/env python3
import argparse, json
REQUIRED = {"candidate_id", "class_id", "label", "selection_frequency", "predictions"}

def normalize_records(records):
    if not isinstance(records, list) or not records:
        raise ValueError("candidate pool must be a non-empty list")
    out=[]
    for i, rec in enumerate(records):
        missing=REQUIRED-set(rec)
        if missing:
            raise ValueError(f"record {i} missing {sorted(missing)}")
        freq=float(rec["selection_frequency"])
        if not 0.0 <= freq <= 1.0:
            raise ValueError(f"record {i} selection_frequency outside [0,1]")
        preds=rec["predictions"]
        if not isinstance(preds, list) or not preds:
            raise ValueError(f"record {i} predictions must be non-empty list")
        out.append({"candidate_id":str(rec["candidate_id"]),"class_id":str(rec["class_id"]),"label":str(rec["label"]),"selection_frequency":freq,"predictions":[str(p) for p in preds]})
    return sorted(out, key=lambda r:(r["class_id"], r["candidate_id"]))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--output', required=True)
    args=ap.parse_args(); records=json.load(open(args.input)); norm=normalize_records(records)
    json.dump({"schema_version":1,"records":norm,"class_count":len({r['class_id'] for r in norm}),"candidate_count":len(norm)}, open(args.output,'w'), indent=2)
if __name__=='__main__': main()
