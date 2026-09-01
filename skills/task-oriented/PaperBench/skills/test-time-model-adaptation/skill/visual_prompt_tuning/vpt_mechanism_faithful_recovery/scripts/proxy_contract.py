#!/usr/bin/env python3
import argparse
import json


def mechanism_checks(trace, invocations, result):
    called = {entry.get("skill_name") for entry in invocations}
    required = {"vpt_prompt_token_insertion", "vpt_frozen_prompt_training", "vpt_evaluation_protocol"}
    params_before = trace.get("params_before", {})
    params_after = trace.get("params_after", {})
    changed_trainable = any(params_before.get(name) != params_after.get(name) for name in params_before if name.startswith(("prompt", "head", "classifier")))
    frozen_unchanged = all(params_before.get(name) == params_after.get(name) for name in params_before if name.startswith("backbone"))
    return {
        "required_skills_invoked": required.issubset(called),
        "prompt_insertion_executed": trace.get("prompted_sequence_length", 0) > trace.get("base_sequence_length", 0),
        "deep_prompt_path_checked": bool(trace.get("deep_prompt_path_checked")),
        "optimizer_step_executed": bool(trace.get("optimizer_step_executed")),
        "trainable_params_changed": changed_trainable,
        "frozen_backbone_unchanged": frozen_unchanged,
        "numeric_metric_present": isinstance(result.get("metrics", {}).get("accuracy_after_one_step"), (int, float)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trace_json")
    parser.add_argument("invocations_json")
    parser.add_argument("result_json")
    args = parser.parse_args()
    trace = json.loads(open(args.trace_json, encoding="utf-8").read())
    invocations = json.loads(open(args.invocations_json, encoding="utf-8").read()).get("invocations", [])
    result = json.loads(open(args.result_json, encoding="utf-8").read())
    print(json.dumps(mechanism_checks(trace, invocations, result), indent=2))


if __name__ == "__main__":
    main()
