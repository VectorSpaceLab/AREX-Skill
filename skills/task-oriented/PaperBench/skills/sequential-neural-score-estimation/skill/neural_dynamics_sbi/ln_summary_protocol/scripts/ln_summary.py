#!/usr/bin/env python3
import argparse
import json
import math
import random


def dot(left, right):
    return sum(a * b for a, b in zip(left, right))


def sigmoid(value):
    value = max(-30.0, min(30.0, value))
    return 1.0 / (1.0 + math.exp(-value))


def compute_summary(stimuli, spikes):
    if not stimuli:
        raise ValueError("stimuli must not be empty")
    if len(stimuli) != len(spikes):
        raise ValueError("stimuli and spikes length mismatch")
    dimension = len(stimuli[0])
    spike_count = sum(spikes)
    if spike_count:
        sta = [sum(row[index] for row, spike in zip(stimuli, spikes) if spike) / spike_count for index in range(dimension)]
    else:
        sta = [0.0] * dimension
    firing_rate = spike_count / len(spikes)
    return sta + [firing_rate], sta, firing_rate


def simulate_ln(theta, n_stimuli=128, seed=0, bias=-1.0, gain=1.5):
    if not theta:
        raise ValueError("theta must not be empty")
    rng = random.Random(seed)
    dimension = len(theta)
    stimuli = [[rng.gauss(0.0, 1.0) for _ in range(dimension)] for _ in range(n_stimuli)]
    spikes = []
    for row in stimuli:
        probability = sigmoid(bias + gain * dot(row, theta))
        spikes.append(1 if rng.random() < probability else 0)
    summary, sta, firing_rate = compute_summary(stimuli, spikes)
    return {
        "theta": list(theta),
        "stimuli": stimuli,
        "spikes": spikes,
        "summary": summary,
        "sta": sta,
        "firing_rate": firing_rate,
        "metadata": {"seed": seed, "n_stimuli": n_stimuli, "dimension": dimension, "bias": bias, "gain": gain},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--theta", required=True, help="JSON list of filter parameters")
    parser.add_argument("--n-stimuli", type=int, default=128)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    item = simulate_ln(json.loads(args.theta), n_stimuli=args.n_stimuli, seed=args.seed)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(item, handle, indent=2)


if __name__ == "__main__":
    main()
