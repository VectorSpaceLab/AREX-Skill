#!/usr/bin/env python3
import argparse
import json


def predict_from_distances(d0, d1):
    return 1 if float(d1) < float(d0) else 0


def evaluate_precomputed(items):
    if not items:
        raise ValueError("items must be non-empty")
    records = []
    correct = 0
    for index, item in enumerate(items):
        judge = item.get("judge")
        if judge not in (0, 1):
            raise ValueError("judge must be 0 or 1")
        if "d0" not in item or "d1" not in item:
            raise ValueError("each item must include d0 and d1")
        prediction = predict_from_distances(item["d0"], item["d1"])
        is_correct = prediction == judge
        correct += int(is_correct)
        records.append({
            "id": item.get("id", str(index)),
            "d0": float(item["d0"]),
            "d1": float(item["d1"]),
            "judge": judge,
            "prediction": prediction,
            "correct": is_correct,
        })
    return {"metric": "2afc_accuracy", "sample_count": len(items), "accuracy": correct / float(len(items)), "items": records}


def _self_test():
    result = evaluate_precomputed([
        {"id": "a", "d0": 0.1, "d1": 0.5, "judge": 0},
        {"id": "b", "d0": 0.8, "d1": 0.2, "judge": 1},
        {"id": "tie", "d0": 0.4, "d1": 0.4, "judge": 0},
    ])
    assert result["accuracy"] == 1.0
    assert result["items"][2]["prediction"] == 0
    try:
        evaluate_precomputed([{"d0": 0.1, "d1": 0.2, "judge": 2}])
    except ValueError:
        pass
    else:
        raise AssertionError("bad labels should fail")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="JSON list or object with items containing d0, d1, judge")
    parser.add_argument("--output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"ok": True}))
        return
    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    items = payload["items"] if isinstance(payload, dict) else payload
    result = evaluate_precomputed(items)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
