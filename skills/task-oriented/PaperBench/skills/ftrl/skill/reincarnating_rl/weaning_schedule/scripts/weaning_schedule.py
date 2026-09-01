#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def _check_lambda(lambda_0):
    lambda_0 = float(lambda_0)
    if lambda_0 < 0:
        raise ValueError("lambda_0 must be nonnegative")
    return lambda_0


def linear_decay(lambda_0, step, decay_steps):
    lambda_0 = _check_lambda(lambda_0)
    if decay_steps <= 0:
        raise ValueError("decay_steps must be positive")
    progress = min(max(float(step) / float(decay_steps), 0.0), 1.0)
    return {"schedule": "linear_decay", "lambda_t": lambda_0 * (1.0 - progress), "progress": progress}


def performance_decay(lambda_0, student_score, teacher_score):
    lambda_0 = _check_lambda(lambda_0)
    if teacher_score <= 0:
        raise ValueError("teacher_score must be positive")
    ratio = min(max(float(student_score) / float(teacher_score), 0.0), 1.0)
    return {"schedule": "performance_decay", "lambda_t": lambda_0 * (1.0 - ratio), "progress": ratio}


def _self_test():
    start = linear_decay(3.0, 0, 10)
    mid = linear_decay(3.0, 5, 10)
    end = linear_decay(3.0, 20, 10)
    perf = performance_decay(2.0, 0.5, 1.0)
    assert start["lambda_t"] == 3.0
    assert mid["lambda_t"] == 1.5
    assert end["lambda_t"] == 0.0
    assert perf["lambda_t"] == 1.0
    return {"linear_start": start, "linear_mid": mid, "linear_end": end, "performance": perf}


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
        schedule = payload.get("schedule", "linear_decay")
        if schedule == "linear_decay":
            result = linear_decay(payload["lambda_0"], payload["step"], payload["decay_steps"])
        elif schedule == "performance_decay":
            result = performance_decay(payload["lambda_0"], payload["student_score"], payload["teacher_score"])
        else:
            raise ValueError(f"unknown schedule {schedule}")
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
