#!/usr/bin/env python3
"""ImageNet-P prediction stability metrics."""
from __future__ import annotations

import argparse
import json
from typing import Mapping, Sequence


def sequence_flip_stats(sequence: Sequence[object]) -> dict:
    if len(sequence) < 2:
        raise ValueError("prediction sequence must contain at least two labels")
    flips = sum(1 for prev, cur in zip(sequence, sequence[1:]) if cur != prev)
    transitions = len(sequence) - 1
    return {"flips": flips, "transitions": transitions, "flip_probability": flips / transitions}


def compute_flip_probabilities(grouped_sequences: Mapping[str, Sequence[Sequence[object]]], baseline: Mapping[str, float] | None = None) -> dict:
    if not grouped_sequences:
        raise ValueError("at least one perturbation group is required")
    by_group = {}
    for group, sequences in sorted(grouped_sequences.items()):
        if not sequences:
            raise ValueError(f"{group}: at least one sequence is required")
        sequence_stats = [sequence_flip_stats(sequence) for sequence in sequences]
        flips = sum(item["flips"] for item in sequence_stats)
        transitions = sum(item["transitions"] for item in sequence_stats)
        flip_probability = flips / transitions
        entry = {"flips": flips, "transitions": transitions, "flip_probability": flip_probability, "sequences": sequence_stats}
        if baseline and group in baseline:
            if baseline[group] == 0:
                raise ValueError(f"{group}: baseline flip probability is zero")
            entry["normalized_flip_probability"] = flip_probability / float(baseline[group])
        by_group[group] = entry
    mean_fp = sum(item["flip_probability"] for item in by_group.values()) / len(by_group)
    return {"flip_probability_by_group": by_group, "mean_flip_probability": mean_fp}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON with grouped_sequences and optional baseline")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    result = compute_flip_probabilities(payload["grouped_sequences"], payload.get("baseline"))
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
