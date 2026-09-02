#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


def normalize_objects(objects):
    seen = []
    for obj in objects:
        value = str(obj).strip().lower()
        if value and value not in seen:
            seen.append(value)
    return seen


def normalize_records(records):
    normalized = []
    for record in records:
        normalized.append({"image": record["image"], "objects": normalize_objects(record.get("objects", []))})
    return normalized


def object_frequencies(records):
    counter = Counter()
    for record in normalize_records(records):
        counter.update(record["objects"])
    return dict(counter)


def co_occurrence_rankings(records):
    counts = defaultdict(Counter)
    for record in normalize_records(records):
        objects = record["objects"]
        for obj in objects:
            for other in objects:
                if other != obj:
                    counts[obj][other] += 1
    return {obj: [name for name, _ in counter.most_common()] for obj, counter in counts.items()}


def eligible_objects(records, current_objects, history):
    vocab = set(object_frequencies(records))
    blocked = set(normalize_objects(current_objects)) | set(normalize_objects(history))
    return sorted(vocab - blocked)


def select_negative(records, current_objects, history=None, strategy="random", anchor=None, seed=0):
    history = history or []
    records = normalize_records(records)
    eligible = set(eligible_objects(records, current_objects, history))
    if not eligible:
        raise ValueError("no eligible absent object is available")
    if strategy == "random":
        return random.Random(seed).choice(sorted(eligible))
    if strategy == "popular":
        frequencies = object_frequencies(records)
        return sorted(eligible, key=lambda obj: (-frequencies[obj], obj))[0]
    if strategy == "adversarial":
        rankings = co_occurrence_rankings(records)
        for candidate in rankings.get(str(anchor).strip().lower(), []):
            if candidate in eligible:
                return candidate
        frequencies = object_frequencies(records)
        return sorted(eligible, key=lambda obj: (-frequencies[obj], obj))[0]
    raise ValueError(f"unknown strategy: {strategy}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records")
    parser.add_argument("--current-objects", default="[]")
    parser.add_argument("--history", default="[]")
    parser.add_argument("--strategy", default="random")
    parser.add_argument("--anchor", default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        records = [{"image": "a", "objects": ["cat", "sofa"]}, {"image": "b", "objects": ["cat", "dog"]}]
        assert select_negative(records, ["cat"], strategy="popular") in {"sofa", "dog"}
        assert select_negative(records, ["cat"], strategy="adversarial", anchor="cat") in {"sofa", "dog"}
        print(json.dumps({"ok": True}))
        return
    records = json.loads(Path(args.records).read_text(encoding="utf-8"))
    result = {
        "negative": select_negative(records, json.loads(args.current_objects), json.loads(args.history), args.strategy, args.anchor, args.seed),
        "frequencies": object_frequencies(records),
        "co_occurrence": co_occurrence_rankings(records),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
