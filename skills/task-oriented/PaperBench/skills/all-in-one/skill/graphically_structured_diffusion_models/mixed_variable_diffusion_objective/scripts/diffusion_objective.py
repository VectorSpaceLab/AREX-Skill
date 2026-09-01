#!/usr/bin/env python3
"""Deterministic mixed-variable diffusion objective helpers."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def encoded_slices(specs: list[dict]) -> dict[str, tuple[int, int]]:
    cursor = 0
    result = {}
    for spec in specs:
        name = spec["name"]
        if spec["kind"] == "continuous":
            width = 1
        elif spec["kind"] == "categorical":
            width = int(spec["num_categories"])
            if width <= 1:
                raise ValueError("categorical num_categories must be greater than 1")
        else:
            raise ValueError(f"unknown variable kind: {spec['kind']}")
        result[name] = (cursor, cursor + width)
        cursor += width
    return result


def encode_values(specs: list[dict], values: dict) -> list[float]:
    encoded = []
    for spec in specs:
        name = spec["name"]
        if name not in values:
            raise ValueError(f"missing value for {name}")
        if spec["kind"] == "continuous":
            encoded.append(float(values[name]))
        elif spec["kind"] == "categorical":
            cats = int(spec["num_categories"])
            value = int(values[name])
            if value < 0 or value >= cats:
                raise ValueError(f"categorical value out of range for {name}")
            encoded.extend(1.0 if idx == value else 0.0 for idx in range(cats))
        else:
            raise ValueError(f"unknown variable kind: {spec['kind']}")
    return encoded


def decode_values(specs: list[dict], encoded: list[float]) -> dict:
    slices = encoded_slices(specs)
    decoded = {}
    for spec in specs:
        start, end = slices[spec["name"]]
        block = encoded[start:end]
        if spec["kind"] == "continuous":
            decoded[spec["name"]] = block[0]
        else:
            decoded[spec["name"]] = max(range(len(block)), key=lambda idx: block[idx])
    return decoded


def observation_mask(specs: list[dict], observed_names: list[str]) -> list[int]:
    observed = set(observed_names)
    slices = encoded_slices(specs)
    width = max(end for _, end in slices.values()) if slices else 0
    mask = [0] * width
    for name in observed:
        if name not in slices:
            raise ValueError(f"unknown observed variable: {name}")
        start, end = slices[name]
        for idx in range(start, end):
            mask[idx] = 1
    return mask


def alpha_bar(beta_schedule: list[float], timestep: int) -> float:
    if timestep < 0 or timestep >= len(beta_schedule):
        raise ValueError("timestep out of range")
    product = 1.0
    for beta in beta_schedule[: timestep + 1]:
        product *= 1.0 - float(beta)
    return product


def diffuse_x0(x0: list[float], noise: list[float], beta_schedule: list[float], timestep: int) -> list[float]:
    if len(x0) != len(noise):
        raise ValueError("x0 and noise lengths differ")
    abar = alpha_bar(beta_schedule, timestep)
    clean_scale = math.sqrt(abar)
    noise_scale = math.sqrt(1.0 - abar)
    return [clean_scale * float(value) + noise_scale * float(eps) for value, eps in zip(x0, noise)]


def masked_mse(prediction: list[float], target: list[float], loss_mask: list[int] | None = None) -> float:
    if len(prediction) != len(target):
        raise ValueError("prediction and target lengths differ")
    if loss_mask is None:
        loss_mask = [1] * len(target)
    if len(loss_mask) != len(target):
        raise ValueError("loss_mask length differs")
    active = [idx for idx, flag in enumerate(loss_mask) if flag]
    if not active:
        raise ValueError("loss_mask has no active entries")
    return sum((float(prediction[idx]) - float(target[idx])) ** 2 for idx in active) / len(active)


def demo_result() -> dict:
    specs = [
        {"name": "A[0,0]", "kind": "continuous"},
        {"name": "R[0,0]", "kind": "categorical", "num_categories": 2},
    ]
    values = {"A[0,0]": 0.25, "R[0,0]": 1}
    x0 = encode_values(specs, values)
    noise = [0.1, -0.2, 0.3]
    beta = [0.1, 0.2]
    xt = diffuse_x0(x0, noise, beta, 1)
    obs = observation_mask(specs, ["A[0,0]"])
    latent_mask = [0 if flag else 1 for flag in obs]
    return {
        "specs": specs,
        "values": values,
        "encoded": x0,
        "xt": xt,
        "decoded": decode_values(specs, x0),
        "observation_mask": obs,
        "loss": masked_mse([0.0, 0.0, 0.9], x0, latent_mask),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not args.demo:
        parser.error("--demo is required for the CLI smoke path")
    result = demo_result()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "loss": result["loss"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
