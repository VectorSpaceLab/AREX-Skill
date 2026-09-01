#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _records(values, prefix):
    records = []
    seen = set()
    for index, value in enumerate(values):
        if isinstance(value, dict):
            item_id = str(value.get("id", f"{prefix}_{index}"))
            text = str(value.get("text", "")).strip()
            category = str(value.get("category", "default"))
        else:
            item_id = f"{prefix}_{index}"
            text = str(value).strip()
            category = "default"
        if not text:
            raise ValueError(f"{item_id} has empty text")
        if item_id in seen:
            raise ValueError(f"duplicate id: {item_id}")
        seen.add(item_id)
        records.append({"id": item_id, "text": text, "category": category})
    return records


def build_protocol(train_targets, heldout_prompts, disallowed_markers=None):
    disallowed_markers = list(disallowed_markers or [])
    train = _records(train_targets, "train")
    heldout = _records(heldout_prompts, "heldout")
    train_texts = {item["text"] for item in train}
    heldout_texts = {item["text"] for item in heldout}
    overlap = sorted(train_texts & heldout_texts)
    if overlap:
        raise ValueError(f"train/heldout overlap: {overlap}")
    for marker in disallowed_markers:
        if not marker:
            continue
        for item in train + heldout:
            if marker in item["text"]:
                raise ValueError(f"disallowed marker {marker!r} in {item['id']}")
    categories = sorted({item["category"] for item in heldout})
    return {
        "schema_version": 1,
        "train_targets": train,
        "heldout_prompts": heldout,
        "categories": categories,
        "safety": {"proxy_only": True, "disallowed_markers": disallowed_markers},
        "split_checks": {
            "train_count": len(train),
            "heldout_count": len(heldout),
            "overlap_count": 0,
            "heldout_distinct": True,
        },
    }


def _self_test():
    protocol = build_protocol(["alpha"], [{"id": "h0", "text": "beta", "category": "c"}])
    assert protocol["split_checks"]["heldout_distinct"] is True
    try:
        build_protocol(["same"], ["same"])
    except ValueError:
        pass
    else:
        raise AssertionError("overlap was not rejected")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="JSON file with train_targets and heldout_prompts")
    parser.add_argument("--output", help="Where to write validated protocol JSON")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"ok": True}))
        return 0
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    protocol = build_protocol(data.get("train_targets", []), data.get("heldout_prompts", []), data.get("disallowed_markers", []))
    if args.output:
        Path(args.output).write_text(json.dumps(protocol, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "train_count": len(protocol["train_targets"]), "heldout_count": len(protocol["heldout_prompts"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
