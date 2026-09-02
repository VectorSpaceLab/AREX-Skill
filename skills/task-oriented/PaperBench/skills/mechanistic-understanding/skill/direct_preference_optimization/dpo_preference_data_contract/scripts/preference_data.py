#!/usr/bin/env python3
"""Normalize pairwise preference records for DPO."""
from __future__ import annotations
import argparse, json
ASSISTANT_MARKER = "\n\nAssistant:"

def _nonempty(value, name):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value

def normalize_explicit(record, idx=0):
    prompt = _nonempty(record.get("prompt"), "prompt")
    chosen = _nonempty(record.get("chosen"), "chosen")
    rejected = _nonempty(record.get("rejected"), "rejected")
    if chosen == rejected:
        raise ValueError("chosen and rejected responses must differ")
    return {"prompt": prompt, "chosen": chosen, "rejected": rejected,
            "pair_id": str(record.get("pair_id", f"pair_{idx}")),
            "source": str(record.get("source", "unknown"))}

def normalize_hh(record, idx=0):
    chosen_full = _nonempty(record.get("chosen"), "chosen")
    rejected_full = _nonempty(record.get("rejected"), "rejected")
    ci = chosen_full.rfind(ASSISTANT_MARKER)
    ri = rejected_full.rfind(ASSISTANT_MARKER)
    if ci < 0 or ri < 0:
        raise ValueError("HH-style records must contain the final Assistant marker")
    prompt = chosen_full[:ci + len(ASSISTANT_MARKER)]
    if rejected_full[:ri + len(ASSISTANT_MARKER)] != prompt:
        raise ValueError("chosen and rejected HH records do not share a prompt")
    return normalize_explicit({"prompt": prompt, "chosen": chosen_full[len(prompt):],
                               "rejected": rejected_full[len(prompt):],
                               "pair_id": record.get("pair_id", f"pair_{idx}"),
                               "source": record.get("source", "hh_style")}, idx)

def normalize_records(records):
    out = []
    for i, rec in enumerate(records):
        if rec.get("format") == "hh" or ("prompt" not in rec and ASSISTANT_MARKER in str(rec.get("chosen", ""))):
            out.append(normalize_hh(rec, i))
        else:
            out.append(normalize_explicit(rec, i))
    return out

def _self_test():
    ex = normalize_records([{"prompt":"p","chosen":" good","rejected":" bad"}])[0]
    assert ex["chosen"] == " good" and ex["rejected"] == " bad"
    hh = normalize_records([{"format":"hh","chosen":"\n\nHuman: hi\n\nAssistant: yes","rejected":"\n\nHuman: hi\n\nAssistant: no"}])[0]
    assert hh["prompt"].endswith("Assistant:") and hh["chosen"] == " yes"
    try:
        normalize_records([{"prompt":"p","chosen":"x","rejected":"x"}])
        raise AssertionError("expected identical response failure")
    except ValueError:
        pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?")
    ap.add_argument("--output", default="")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        _self_test(); print(json.dumps({"ok": True})); return
    data = json.load(open(args.input, encoding="utf-8"))
    result = normalize_records(data if isinstance(data, list) else data["records"])
    text = json.dumps(result, indent=2)
    if args.output: open(args.output, "w", encoding="utf-8").write(text + "\n")
    else: print(text)
if __name__ == "__main__": main()
