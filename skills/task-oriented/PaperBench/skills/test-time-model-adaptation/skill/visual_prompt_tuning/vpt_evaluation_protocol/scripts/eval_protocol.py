#!/usr/bin/env python3
import argparse
import json


def accuracy(predictions, labels):
    if len(predictions) != len(labels) or not labels:
        raise ValueError("predictions and labels must have the same non-zero length")
    return sum(1 for pred, label in zip(predictions, labels) if pred == label) / len(labels)


def tunable_percent(trainable, backbone):
    if backbone <= 0:
        raise ValueError("backbone parameter count must be positive")
    return 100.0 * trainable / backbone


def pooling_warnings(pooling):
    if pooling in {"prompt_pool", "global_pool"}:
        return ["pooling includes prompt tokens; paper reports this can reduce accuracy relative to CLS"]
    return []


def select_candidate(candidates):
    scored = []
    for candidate in candidates:
        val_acc = accuracy(candidate["val_predictions"], candidate["val_labels"])
        pct = tunable_percent(candidate.get("trainable_parameters", 0), candidate.get("backbone_parameters", 1))
        scored.append((candidate, val_acc, pct))
    scored.sort(key=lambda item: (-item[1], item[2], item[0].get("prompt_tokens", 0), item[0].get("name", "")))
    candidate, val_acc, pct = scored[0]
    test_acc = accuracy(candidate["test_predictions"], candidate["test_labels"])
    return {
        "selected_name": candidate.get("name", "candidate"),
        "validation_accuracy": val_acc,
        "test_accuracy": test_acc,
        "tunable_percent_backbone": pct,
        "pooling": candidate.get("pooling", "cls"),
        "warnings": pooling_warnings(candidate.get("pooling", "cls")),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    args = parser.parse_args()
    payload = json.loads(open(args.input_json, encoding="utf-8").read())
    print(json.dumps(select_candidate(payload["candidates"]), indent=2))


if __name__ == "__main__":
    main()
