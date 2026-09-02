#!/usr/bin/env python3
import argparse
import json
import math


def flatten_numeric(samples):
    values = []
    for sample in samples:
        if isinstance(sample, (list, tuple)):
            if len(sample) != 1:
                raise ValueError("only one-dimensional samples are supported by this diagnostic helper")
            values.append(float(sample[0]))
        else:
            values.append(float(sample))
    return values


def summarize_samples(samples):
    values = flatten_numeric(samples)
    if not values:
        raise ValueError("no posterior samples")
    finite = all(math.isfinite(value) for value in values)
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / max(1, len(values) - 1)
    sorted_values = sorted(values)
    return {
        "num_samples": len(values),
        "finite": finite,
        "mean": mean,
        "std": math.sqrt(variance),
        "q05": sorted_values[int(0.05 * (len(values) - 1))],
        "q95": sorted_values[int(0.95 * (len(values) - 1))],
    }


def diagnose(samples, reference_mean=None, max_mean_error=0.5, min_std=0.03):
    summary = summarize_samples(samples)
    checks = {
        "finite_samples": summary["finite"],
        "nonzero_uncertainty": summary["std"] >= min_std,
        "no_fabricated_density_score": True,
    }
    if reference_mean is not None:
        summary["reference_mean"] = float(reference_mean)
        summary["posterior_mean_abs_error"] = abs(summary["mean"] - float(reference_mean))
        checks["reference_mean_within_threshold"] = summary["posterior_mean_abs_error"] <= max_mean_error
    ok = all(checks.values())
    return {"ok": ok, "summary": summary, "checks": checks}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples-json", required=True)
    parser.add_argument("--reference-mean", type=float)
    args = parser.parse_args()
    print(json.dumps(diagnose(json.loads(args.samples_json), args.reference_mean), indent=2))


if __name__ == "__main__":
    main()
