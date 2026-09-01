#!/usr/bin/env python3
import argparse
import json
import math
import sys
from pathlib import Path


def softmax(values, temperature):
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    scaled = [value / temperature for value in values]
    max_value = max(scaled)
    exps = [math.exp(value - max_value) for value in scaled]
    total = sum(exps)
    return [value / total for value in exps]


def _validate_teacher_policy(policy, action_count):
    if len(policy) != action_count:
        raise ValueError("teacher_policy length must match action count")
    if any(prob < 0 for prob in policy):
        raise ValueError("teacher_policy probabilities must be nonnegative")
    total = sum(policy)
    if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
        raise ValueError("teacher_policy must sum to 1")


def compute_qdagger_loss(q_values, transitions, temperature=1.0, lambda_t=1.0):
    if lambda_t < 0:
        raise ValueError("lambda_t must be nonnegative")
    if not transitions:
        raise ValueError("transitions must be nonempty")

    examples = []
    td_terms = []
    distillation_terms = []
    for transition in transitions:
        state = str(transition["state"])
        if state not in q_values:
            raise ValueError(f"missing q_values for state {state}")
        action_values = [float(value) for value in q_values[state]]
        action = int(transition["action"])
        if action < 0 or action >= len(action_values):
            raise ValueError("action index out of range")
        teacher_policy = [float(value) for value in transition["teacher_policy"]]
        _validate_teacher_policy(teacher_policy, len(action_values))

        target = float(transition["n_step_return"]) + float(transition["discount"]) * float(transition["next_max_q"])
        prediction = action_values[action]
        td_error = target - prediction
        td_loss = td_error * td_error
        student_policy = softmax(action_values, temperature)
        cross_entropy = -sum(prob * math.log(max(student_policy[index], 1e-12)) for index, prob in enumerate(teacher_policy))

        td_terms.append(td_loss)
        distillation_terms.append(cross_entropy)
        examples.append({
            "state": state,
            "action": action,
            "target": target,
            "prediction": prediction,
            "td_error": td_error,
            "td_loss": td_loss,
            "student_policy": student_policy,
            "teacher_policy": teacher_policy,
            "distillation_loss": cross_entropy,
        })

    td_loss = sum(td_terms) / len(td_terms)
    distillation_loss = sum(distillation_terms) / len(distillation_terms)
    combined_loss = td_loss + lambda_t * distillation_loss
    return {
        "td_loss": td_loss,
        "distillation_loss": distillation_loss,
        "combined_loss": combined_loss,
        "lambda_t": lambda_t,
        "temperature": temperature,
        "examples": examples,
    }


def _self_test():
    q_values = {"s0": [0.2, 1.0], "s1": [0.8, 0.1]}
    transitions = [
        {"state": "s0", "action": 1, "n_step_return": 1.0, "discount": 0.9, "next_max_q": 0.8, "teacher_policy": [0.05, 0.95]},
        {"state": "s1", "action": 0, "n_step_return": 0.4, "discount": 0.0, "next_max_q": 0.0, "teacher_policy": [0.9, 0.1]},
    ]
    result = compute_qdagger_loss(q_values, transitions, temperature=0.5, lambda_t=1.5)
    assert result["td_loss"] > 0
    assert result["distillation_loss"] > 0
    assert result["combined_loss"] > result["td_loss"]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        result = _self_test()
    else:
        if not args.input:
            parser.error("--input is required unless --self-test is used")
        payload = json.loads(args.input.read_text())
        result = compute_qdagger_loss(
            payload["q_values"],
            payload["transitions"],
            float(payload.get("temperature", 1.0)),
            float(payload.get("lambda_t", 1.0)),
        )
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
