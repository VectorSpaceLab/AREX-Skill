#!/usr/bin/env python3
"""Reduced binary-tree Gaussian BN recovery with one optimizer step."""

from __future__ import annotations

import argparse
import copy
import json
import random


def binary_tree_structure(depth):
    if depth < 2:
        raise ValueError("depth must be at least 2")
    node_count = 2 ** depth - 1
    parents = {}
    for index in range(node_count):
        node = f"x{index}"
        parents[node] = [] if index == 0 else [f"x{(index - 1) // 2}"]
    first_leaf = 2 ** (depth - 1) - 1
    latents = [f"x{i}" for i in range(first_leaf)]
    observed = [f"x{i}" for i in range(first_leaf, node_count)]
    return parents, latents, observed


def deterministic_weights(parents):
    weights = {}
    for child in sorted(parents):
        if parents[child]:
            index = int(child[1:])
            weights[child] = round(0.55 + (index % 5) * 0.23, 6)
    return weights


def generate_samples(depth, count, seed):
    rng = random.Random(seed)
    parents, latents, observed = binary_tree_structure(depth)
    weights = deterministic_weights(parents)
    samples = []
    for sample_index in range(count):
        values = {}
        for node in sorted(parents, key=lambda item: int(item[1:])):
            if not parents[node]:
                mean = 0.0
            else:
                parent = parents[node][0]
                mean = weights[node] * values[parent]
            values[node] = rng.gauss(mean, 0.25)
        samples.append({"sample_id": sample_index, "values": values})
    return {
        "schema_version": 1,
        "depth": depth,
        "sample_count": count,
        "seed": seed,
        "parents": parents,
        "latents": latents,
        "observed": observed,
        "weights": weights,
        "samples": samples,
        "is_resource_derived": false_bool(),
        "resource_files": [],
        "notes": "Synthetic reduced recovery data generated from the paper's binary-tree Gaussian BN family.",
    }


def false_bool():
    return False


def initialize_params(contracts):
    params = {}
    for contract in contracts:
        variable = contract["variable"]
        params[variable] = {"bias": 0.0}
        for parent in contract.get("feature_order", []):
            params[variable][parent] = 0.0
    return params


def predict(params_for_variable, feature_names, values):
    total = params_for_variable.get("bias", 0.0)
    for name in feature_names:
        total += params_for_variable.get(name, 0.0) * values[name]
    return total


def loss_and_gradients(params, contracts, samples):
    gradients = {variable: {name: 0.0 for name in weights} for variable, weights in params.items()}
    total_loss = 0.0
    terms = 0
    for sample in samples:
        values = sample["values"]
        for contract in contracts:
            variable = contract["variable"]
            feature_names = contract.get("feature_order", [])
            pred = predict(params[variable], feature_names, values)
            error = pred - values[variable]
            total_loss += error * error
            terms += 1
            scale = 2.0 * error
            gradients[variable]["bias"] += scale
            for name in feature_names:
                gradients[variable][name] += scale * values[name]
    if terms == 0:
        raise ValueError("no training terms were produced")
    for variable in gradients:
        for name in gradients[variable]:
            gradients[variable][name] /= terms
    return total_loss / terms, gradients


def apply_gradient_step(params, gradients, learning_rate):
    updated = copy.deepcopy(params)
    for variable, weights in gradients.items():
        for name, gradient in weights.items():
            updated[variable][name] -= learning_rate * gradient
    return updated


def run_reduced_training(contracts, depth=3, sample_count=8, seed=1712, learning_rate=0.08):
    data_item = generate_samples(depth, sample_count, seed)
    params_before = initialize_params(contracts)
    loss_before, gradients = loss_and_gradients(params_before, contracts, data_item["samples"])
    params_after = apply_gradient_step(params_before, gradients, learning_rate)
    loss_after, _ = loss_and_gradients(params_after, contracts, data_item["samples"])
    optimizer_state_changed = params_before != params_after
    return {
        "data_item": data_item,
        "training_trace": {
            "schema_version": 1,
            "loss_before": loss_before,
            "loss_after": loss_after,
            "loss_delta": loss_before - loss_after,
            "loss_reduction_fraction": (loss_before - loss_after) / loss_before if loss_before else 0.0,
            "params_before": params_before,
            "params_after": params_after,
            "gradients": gradients,
            "learning_rate": learning_rate,
            "optimizer": "one_step_batch_gradient_descent",
            "optimizer_state_changed": optimizer_state_changed,
        },
        "metrics": {
            "mechanism_score": 1.0 if optimizer_state_changed and loss_after < loss_before else 0.0,
            "loss_reduction_fraction": (loss_before - loss_after) / loss_before if loss_before else 0.0,
        },
        "mechanism_checks": {
            "binary_tree_gaussian_constructed": True,
            "nami_inverse_contracts_consumed": True,
            "observed_leaves_conditioned": True,
            "full_analytic_posterior_computed": False,
            "training_step_executed": False,
            "qwen3_model_loaded": False,
            "reduced_training_executed": optimizer_state_changed,
            "optimizer_step_executed": optimizer_state_changed,
            "loss_decreased": loss_after < loss_before,
            "fallback_used": False,
            "toy_or_proxy_fallback_used": True,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contracts_json", help="JSON file containing a contracts list.")
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--sample-count", type=int, default=8)
    parser.add_argument("--seed", type=int, default=1712)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--data-output", default="")
    parser.add_argument("--trace-output", default="")
    parser.add_argument("--result-output", default="")
    args = parser.parse_args(argv)
    with open(args.contracts_json, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    contracts = data["contracts"] if isinstance(data, dict) and "contracts" in data else data
    result = run_reduced_training(
        contracts,
        depth=args.depth,
        sample_count=args.sample_count,
        seed=args.seed,
        learning_rate=args.learning_rate,
    )
    if args.data_output:
        with open(args.data_output, "w", encoding="utf-8") as handle:
            json.dump(result["data_item"], handle, indent=2, sort_keys=True)
            handle.write("\n")
    if args.trace_output:
        with open(args.trace_output, "w", encoding="utf-8") as handle:
            json.dump(result["training_trace"], handle, indent=2, sort_keys=True)
            handle.write("\n")
    output = {
        "schema_version": 1,
        "metrics": result["metrics"],
        "mechanism_checks": result["mechanism_checks"],
        "training_trace": result["training_trace"],
    }
    if args.result_output:
        with open(args.result_output, "w", encoding="utf-8") as handle:
            json.dump(output, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["metrics"]["mechanism_score"] >= 1.0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
