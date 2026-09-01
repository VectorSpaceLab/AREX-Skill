#!/usr/bin/env python3
import argparse
import json

TRAINABLE_KEYWORDS = ("prompt", "head", "classifier", "fc")
FROZEN_KEYWORDS = ("backbone", "transformer", "encoder", "patch", "position", "attn", "mlp", "norm", "block")


def classify_parameter(name, role=None):
    role_text = (role or "").lower()
    name_text = name.lower()
    if role_text in {"prompt", "head", "classifier"}:
        return "trainable"
    if role_text in {"backbone", "frozen"}:
        return "frozen"
    if any(key in name_text for key in TRAINABLE_KEYWORDS):
        return "trainable"
    if any(key in name_text for key in FROZEN_KEYWORDS):
        return "frozen"
    return "frozen"


def build_trainability(parameters):
    records = []
    total = 0
    trainable = 0
    for param in parameters:
        count = int(param.get("count", 1))
        status = classify_parameter(param["name"], param.get("role"))
        total += count
        if status == "trainable":
            trainable += count
        records.append({"name": param["name"], "count": count, "trainable": status == "trainable"})
    frozen = total - trainable
    return {
        "parameters": records,
        "optimizer_group_names": [r["name"] for r in records if r["trainable"]],
        "summary": {
            "total_parameters": total,
            "trainable_parameters": trainable,
            "frozen_parameters": frozen,
            "trainable_percent_total": 100.0 * trainable / total if total else 0.0,
            "trainable_percent_backbone": 100.0 * trainable / frozen if frozen else 0.0,
        },
    }


def verify_frozen_unchanged(parameters, tolerance=1e-12):
    violations = []
    for param in parameters:
        if classify_parameter(param["name"], param.get("role")) == "trainable":
            continue
        if "before" in param and "after" in param and abs(float(param["before"]) - float(param["after"])) > tolerance:
            violations.append(param["name"])
    return {"ok": not violations, "violations": violations}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    args = parser.parse_args()
    payload = json.loads(open(args.input_json, encoding="utf-8").read())
    result = build_trainability(payload["parameters"])
    result["freeze_check"] = verify_frozen_unchanged(payload["parameters"])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
