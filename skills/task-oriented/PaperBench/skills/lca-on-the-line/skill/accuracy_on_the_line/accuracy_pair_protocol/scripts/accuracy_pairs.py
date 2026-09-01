#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

REQUIRED = ("model_id", "id_accuracy", "ood_accuracy")

def validate_records(records, provenance=""):
    if not isinstance(records, list) or len(records) < 2:
        raise ValueError("at least two paired records are required")
    seen=set(); clean=[]
    for idx, rec in enumerate(records):
        if not isinstance(rec, dict):
            raise ValueError(f"record {idx} is not an object")
        for field in REQUIRED:
            if field not in rec:
                raise ValueError(f"record {idx} missing {field}")
        model_id=str(rec["model_id"])
        if model_id in seen:
            raise ValueError(f"duplicate model_id: {model_id}")
        seen.add(model_id)
        try:
            id_acc=float(rec["id_accuracy"]); ood_acc=float(rec["ood_accuracy"])
        except Exception as exc:
            raise ValueError(f"record {idx} has nonnumeric accuracy") from exc
        if not (0.0 <= id_acc <= 1.0 and 0.0 <= ood_acc <= 1.0):
            raise ValueError(f"record {idx} accuracies must be in [0, 1]")
        item=dict(rec); item["model_id"]=model_id; item["id_accuracy"]=id_acc; item["ood_accuracy"]=ood_acc
        clean.append(item)
    clean.sort(key=lambda item: item["model_id"])
    ids=[r["id_accuracy"] for r in clean]; oods=[r["ood_accuracy"] for r in clean]
    return {"records":clean,"count":len(clean),"id_range":[min(ids),max(ids)],"ood_range":[min(oods),max(oods)],"provenance":provenance}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', default='')
    ap.add_argument('--provenance', default='')
    args=ap.parse_args()
    data=json.loads(Path(args.input).read_text())
    result=validate_records(data, args.provenance)
    text=json.dumps(result, indent=2)
    if args.output: Path(args.output).write_text(text + chr(10))
    print(text)
if __name__ == '__main__': main()
