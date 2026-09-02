#!/usr/bin/env python3
"""Reduced TeCoA proxy experiment used by recovery harnesses."""

from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path
import sys


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_generated_helpers(skills_root: str | Path):
    root = Path(skills_root)
    prompt = _load_module("prompt_protocol", root / "tecoa_zeroshot_prompt_protocol" / "scripts" / "prompt_protocol.py")
    contrastive = _load_module("contrastive_objective", root / "tecoa_text_contrastive_objective" / "scripts" / "contrastive_objective.py")
    sys.modules["contrastive_objective"] = contrastive
    attack = _load_module("feature_attack", root / "tecoa_adversarial_feature_attack" / "scripts" / "feature_attack.py")
    return prompt, contrastive, attack


def _scale_rows(features, params):
    return [[value * params[col_idx] for col_idx, value in enumerate(row)] for row in features]


def _loss_for_params(contrastive, adversarial, texts, labels, params, temperature):
    return contrastive.compute_tecoa_metrics(_scale_rows(adversarial, params), texts, labels, temperature)


def _finite_difference_gradient(contrastive, adversarial, texts, labels, params, temperature, fd_eps=1e-5):
    grad = []
    for idx in range(len(params)):
        plus = params[:]
        minus = params[:]
        plus[idx] += fd_eps
        minus[idx] -= fd_eps
        loss_plus = _loss_for_params(contrastive, adversarial, texts, labels, plus, temperature)["loss"]
        loss_minus = _loss_for_params(contrastive, adversarial, texts, labels, minus, temperature)["loss"]
        grad.append((loss_plus - loss_minus) / (2 * fd_eps))
    return grad


def run_proxy_experiment(skills_root: str | Path, steps: int = 8, learning_rate: float = 0.2, temperature: float = 0.5) -> dict:
    prompt, contrastive, attack = load_generated_helpers(skills_root)
    labels_text = ["hummingbird", "tabby cat", "fire truck", "sailboat"]
    prompt_payload = prompt.build_prompts(labels_text, "a photo of a {}")
    text_embeddings = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
    image_embeddings = [[0.85, 0.15, 0.0, 0.0], [0.10, 0.82, 0.08, 0.0], [0.0, 0.12, 0.80, 0.08], [0.06, 0.0, 0.13, 0.81]]
    labels = [0, 1, 2, 3]
    baseline_clean = contrastive.compute_tecoa_metrics(image_embeddings, text_embeddings, labels, temperature)
    attacked = attack.generate_feature_attack(image_embeddings, text_embeddings, labels, epsilon=0.35, step_size=0.12, steps=4, temperature=temperature)
    baseline_adversarial = contrastive.compute_tecoa_metrics(attacked["adversarial_embeddings"], text_embeddings, labels, temperature)
    params = [1.0, 1.0, 1.0, 1.0]
    params_before = params[:]
    loss_history = []
    for _ in range(steps):
        metrics_before_step = _loss_for_params(contrastive, attacked["adversarial_embeddings"], text_embeddings, labels, params, temperature)
        loss_history.append(metrics_before_step["loss"])
        grad = _finite_difference_gradient(contrastive, attacked["adversarial_embeddings"], text_embeddings, labels, params, temperature)
        params = [value - learning_rate * g for value, g in zip(params, grad)]
    final_metrics = _loss_for_params(contrastive, attacked["adversarial_embeddings"], text_embeddings, labels, params, temperature)
    loss_history.append(final_metrics["loss"])
    parameter_l1_change = sum(abs(a - b) for a, b in zip(params_before, params))
    success_checks = {
        "prompt_protocol_invoked": True,
        "contrastive_objective_invoked": True,
        "adversarial_attack_invoked": True,
        "text_conditioned_attack_executed": True,
        "feature_level_proxy_declared": True,
        "tecoa_loss_computed": True,
        "reduced_training_executed": True,
        "optimizer_step_executed": parameter_l1_change > 1e-9,
        "params_changed": parameter_l1_change > 1e-9,
        "attack_bound_passed": bool(attacked["bound_checks"]["passed"]),
        "loss_decreased_after_adaptation": final_metrics["loss"] < baseline_adversarial["loss"],
        "margin_improved_after_adaptation": final_metrics["mean_margin"] > baseline_adversarial["mean_margin"],
        "qwen3_model_loaded": False,
        "clip_model_loaded": False,
        "imagenet_full_training_executed": False,
    }
    trace = {
        "params_before": params_before,
        "params_after": params,
        "parameters_before": params_before,
        "parameters_after": params,
        "parameter_l1_change": parameter_l1_change,
        "loss_before": baseline_adversarial["loss"],
        "loss_after": final_metrics["loss"],
        "loss_history": loss_history,
        "clean_metrics": baseline_clean,
        "adversarial_metrics_before": baseline_adversarial,
        "adversarial_metrics_after": final_metrics,
        "attack": attacked,
        "prompt_payload": prompt_payload,
        "steps": steps,
        "learning_rate": learning_rate,
        "temperature": temperature,
    }
    success_rate = sum(1 for key in ["prompt_protocol_invoked", "contrastive_objective_invoked", "adversarial_attack_invoked", "text_conditioned_attack_executed", "tecoa_loss_computed", "optimizer_step_executed", "loss_decreased_after_adaptation", "margin_improved_after_adaptation", "attack_bound_passed"] if success_checks[key]) / 9.0
    return {
        "trace": trace,
        "metrics": {
            "tecoa_proxy_success_rate": success_rate,
            "loss_before": baseline_adversarial["loss"],
            "loss_after": final_metrics["loss"],
            "mean_margin_before": baseline_adversarial["mean_margin"],
            "mean_margin_after": final_metrics["mean_margin"],
            "adversarial_accuracy_before": baseline_adversarial["accuracy"],
            "adversarial_accuracy_after": final_metrics["accuracy"],
        },
        "mechanism_checks": success_checks,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=0.2)
    args = parser.parse_args()
    result = run_proxy_experiment(args.skills_root, args.steps, args.learning_rate)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
