#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path


def _validate_records(records):
    if not records:
        raise ValueError("records must be non-empty")
    ids = []
    for index, record in enumerate(records):
        if "id" not in record or "score" not in record:
            raise ValueError(f"record {index} must contain id and score")
        if not isinstance(record["score"], (int, float)) or not math.isfinite(record["score"]):
            raise ValueError(f"record {index} has invalid score")
        ids.append(str(record["id"]))
    if len(set(ids)) != len(ids):
        raise ValueError("example ids must be unique")


def _retain_count(total, retain_fraction=None, retain_count=None):
    if retain_count is not None:
        count = int(retain_count)
    elif retain_fraction is not None:
        fraction = float(retain_fraction)
        if fraction <= 0 or fraction > 1:
            raise ValueError("retain_fraction must be in (0, 1]")
        count = max(1, int(total * fraction))
    else:
        raise ValueError("retain_fraction or retain_count is required")
    if count < 1 or count > total:
        raise ValueError("retain_count must be within [1, n_examples]")
    return count


def select_high_score(records, retain_fraction=None, retain_count=None):
    _validate_records(records)
    count = _retain_count(len(records), retain_fraction, retain_count)
    ranked = sorted(records, key=lambda item: (-float(item["score"]), str(item["id"])))
    selected = ranked[:count]
    pruned = ranked[count:]
    return _result(selected, pruned, "high_score")


def select_offset_window(records, retain_fraction=None, retain_count=None, offset_fraction=0.0):
    _validate_records(records)
    count = _retain_count(len(records), retain_fraction, retain_count)
    offset = float(offset_fraction)
    if offset < 0 or offset >= 1:
        raise ValueError("offset_fraction must be in [0, 1)")
    ascending = sorted(records, key=lambda item: (float(item["score"]), str(item["id"])))
    start = int(len(records) * offset)
    end = min(len(records), start + count)
    if end - start < count:
        start = len(records) - count
        end = len(records)
    selected = ascending[start:end]
    selected_ids = {str(item["id"]) for item in selected}
    pruned = [item for item in records if str(item["id"]) not in selected_ids]
    return _result(selected, pruned, "offset_window", offset_fraction=offset)


def _result(selected, pruned, mode, offset_fraction=None):
    selected_ids = [str(item["id"]) for item in selected]
    pruned_ids = [str(item["id"]) for item in pruned]
    stats = {
        "mode": mode,
        "tie_policy": "score descending, id ascending" if mode == "high_score" else "score ascending window, id ascending",
        "selected_count": len(selected_ids),
        "pruned_count": len(pruned_ids),
        "min_selected_score": min(float(item["score"]) for item in selected),
        "max_pruned_score": max([float(item["score"]) for item in pruned], default=None),
    }
    if offset_fraction is not None:
        stats["offset_fraction"] = offset_fraction
    return {"ok": True, "selected_ids": selected_ids, "pruned_ids": pruned_ids, "stats": stats}


def fixture_payload():
    return {
        "records": [
            {"id": "easy_a", "score": 0.1},
            {"id": "hard_a", "score": 0.9},
            {"id": "mid", "score": 0.5},
            {"id": "hard_b", "score": 0.8},
        ],
        "retain_fraction": 0.5,
        "mode": "high_score",
    }


def run_payload(payload):
    mode = payload.get("mode", "high_score")
    if mode == "high_score":
        return select_high_score(payload["records"], payload.get("retain_fraction"), payload.get("retain_count"))
    if mode == "offset_window":
        return select_offset_window(payload["records"], payload.get("retain_fraction"), payload.get("retain_count"), payload.get("offset_fraction", 0.0))
    raise ValueError(f"unknown mode: {mode}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fixture", action="store_true")
    args = parser.parse_args()
    payload = fixture_payload() if args.fixture else json.loads(args.input.read_text())
    result = run_payload(payload)
    text = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
