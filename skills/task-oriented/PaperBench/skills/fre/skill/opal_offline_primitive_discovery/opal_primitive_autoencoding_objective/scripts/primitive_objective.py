#!/usr/bin/env python3
"""Reduced OPAL primitive autoencoding objective for deterministic recovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def mean(values):
    return sum(values) / len(values) if values else 0.0


def segment_action_mean(segment):
    actions = segment["actions"]
    if actions and isinstance(actions[0], list):
        return mean([mean([float(x) for x in action]) for action in actions])
    return mean([float(action) for action in actions])


def assign_latents(segments):
    assignments = []
    for segment in segments:
        assignments.append(1 if segment_action_mean(segment) >= 0 else 0)
    return assignments


def reconstruction_loss(segments, assignments, prototypes):
    errors = []
    for segment, latent in zip(segments, assignments):
        prediction = prototypes[str(latent)]
        for action in segment["actions"]:
            target = mean([float(x) for x in action]) if isinstance(action, list) else float(action)
            errors.append((target - prediction) ** 2)
    return mean(errors)


def prior_penalty(segments, assignments):
    errors = []
    for segment, latent in zip(segments, assignments):
        initial_state = segment.get("initial_state", 0.0)
        if isinstance(initial_state, list):
            initial_value = mean([float(x) for x in initial_state])
        else:
            initial_value = float(initial_state)
        prior_latent = 1 if initial_value >= 0 else 0
        errors.append(0.0 if prior_latent == latent else 1.0)
    return mean(errors)


def update_prototypes(segments, assignments, prototypes, learning_rate):
    gradients = {key: 0.0 for key in prototypes}
    counts = {key: 0 for key in prototypes}
    for segment, latent in zip(segments, assignments):
        key = str(latent)
        for action in segment["actions"]:
            target = mean([float(x) for x in action]) if isinstance(action, list) else float(action)
            gradients[key] += 2.0 * (prototypes[key] - target)
            counts[key] += 1
    updated = dict(prototypes)
    for key, gradient in gradients.items():
        if counts[key]:
            updated[key] = prototypes[key] - learning_rate * gradient / counts[key]
    return updated


def train_reduced_objective(segment_payload, beta=0.1, steps=3, learning_rate=0.5):
    segments = segment_payload.get("segments", segment_payload)
    assignments = assign_latents(segments)
    prototypes = {"0": 0.0, "1": 0.0}
    params_before = dict(prototypes)
    loss_before = reconstruction_loss(segments, assignments, prototypes)
    kl_before = prior_penalty(segments, assignments)
    trace = []
    for step in range(steps):
        prototypes = update_prototypes(segments, assignments, prototypes, learning_rate)
        recon = reconstruction_loss(segments, assignments, prototypes)
        kl = prior_penalty(segments, assignments)
        trace.append({"step": step + 1, "reconstruction_loss": recon, "prior_penalty": kl, "total_loss": recon + beta * kl, "prototypes": dict(prototypes)})
    loss_after = reconstruction_loss(segments, assignments, prototypes)
    kl_after = prior_penalty(segments, assignments)
    separation = abs(prototypes["1"] - prototypes["0"])
    return {
        "assignments": assignments,
        "params_before": params_before,
        "params_after": prototypes,
        "reconstruction_loss_before": loss_before,
        "reconstruction_loss_after": loss_after,
        "prior_penalty_before": kl_before,
        "prior_penalty_after": kl_after,
        "total_loss_before": loss_before + beta * kl_before,
        "total_loss_after": loss_after + beta * kl_after,
        "latent_separation": separation,
        "optimizer_step_executed": params_before != prototypes,
        "trace": trace,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("segments_json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--beta", type=float, default=0.1)
    parser.add_argument("--steps", type=int, default=3)
    args = parser.parse_args()
    payload = json.loads(Path(args.segments_json).read_text(encoding="utf-8"))
    result = train_reduced_objective(payload, beta=args.beta, steps=args.steps)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"loss_before": result["total_loss_before"], "loss_after": result["total_loss_after"], "latent_separation": result["latent_separation"]}, indent=2))


if __name__ == "__main__":
    main()
