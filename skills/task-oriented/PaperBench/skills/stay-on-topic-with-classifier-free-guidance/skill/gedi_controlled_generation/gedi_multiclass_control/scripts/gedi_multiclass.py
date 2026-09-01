#!/usr/bin/env python3
import argparse, json


def build_control_pairs(label, text, positive_token="true", negative_token="false", seen_labels=None):
    label = " ".join(str(label).strip().split())
    if not label:
        raise ValueError("label must be nonempty")
    text = str(text)
    seen = None
    if seen_labels is not None:
        seen = label.lower() in {str(x).lower() for x in seen_labels}
    return {
        "label": label,
        "positive_sequence": f"{positive_token} {label} {text}",
        "negative_sequence": f"{negative_token} {label} {text}",
        "positive_token": positive_token,
        "negative_token": negative_token,
        "control_passes": 2,
        "seen_label": seen,
        "zero_shot_candidate": (None if seen is None else not seen),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    json.dump(build_control_pairs(args.label, args.text), open(args.output, "w"), indent=2, sort_keys=True)

if __name__ == "__main__":
    main()
