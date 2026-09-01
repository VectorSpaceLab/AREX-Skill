#!/usr/bin/env python3
"""Continuous denoising score-matching helpers for Score SDE recovery."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Callable, Sequence


Number = float | int


def as_list(values: Number | Sequence[Number]) -> list[float]:
    if isinstance(values, (int, float)):
        return [float(values)]
    return [float(v) for v in values]


def mean(values: Sequence[Number]) -> float:
    vals = as_list(values)
    return sum(vals) / len(vals)


@dataclass
class ScoreBatch:
    clean: list[float]
    time: list[float]
    noise: list[float]
    mean: list[float]
    std: list[float]
    perturbed: list[float]
    target: list[float]


@dataclass
class LinearScoreModel:
    weight: float = 0.0
    time_weight: float = 0.0
    bias: float = 0.0

    def predict_one(self, x: float, t: float) -> float:
        return self.weight * x + self.time_weight * t + self.bias

    def predict(self, xs: Sequence[Number], ts: Sequence[Number]) -> list[float]:
        return [self.predict_one(float(x), float(t)) for x, t in zip(xs, ts)]

    def params(self) -> dict[str, float]:
        return {"weight": self.weight, "time_weight": self.time_weight, "bias": self.bias}

    def with_params(self, params: dict[str, float]) -> "LinearScoreModel":
        return LinearScoreModel(weight=params["weight"], time_weight=params["time_weight"], bias=params["bias"])


def build_score_matching_batch(
    clean: Sequence[Number],
    times: Sequence[Number],
    noises: Sequence[Number],
    marginal_fn: Callable[[float, float], tuple[float, float]],
) -> ScoreBatch:
    clean_v = as_list(clean)
    time_v = as_list(times)
    noise_v = as_list(noises)
    if not (len(clean_v) == len(time_v) == len(noise_v)):
        raise ValueError("clean, times, and noises must have the same length")
    means: list[float] = []
    stds: list[float] = []
    perturbed: list[float] = []
    targets: list[float] = []
    for x0, t, z in zip(clean_v, time_v, noise_v):
        m, std = marginal_fn(x0, t)
        if std <= 0:
            raise ValueError("marginal std must be positive; use t >= eps")
        means.append(float(m))
        stds.append(float(std))
        perturbed.append(float(m) + float(std) * float(z))
        targets.append(-float(z) / float(std))
    return ScoreBatch(clean_v, time_v, noise_v, means, stds, perturbed, targets)


def score_matching_loss(
    predictions: Sequence[Number],
    batch: ScoreBatch,
    likelihood_weighting: bool = False,
    diffusion_sq_fn: Callable[[float], float] | None = None,
) -> dict:
    preds = as_list(predictions)
    if len(preds) != len(batch.target):
        raise ValueError("prediction count must match batch size")
    losses: list[float] = []
    for pred, target, t in zip(preds, batch.target, batch.time):
        err2 = (float(pred) - float(target)) ** 2
        if likelihood_weighting:
            if diffusion_sq_fn is None:
                raise ValueError("diffusion_sq_fn is required for likelihood weighting")
            err2 *= float(diffusion_sq_fn(float(t)))
        losses.append(err2)
    return {"loss": mean(losses), "per_example": losses}


def finite_difference_gradient(
    model: LinearScoreModel,
    batch: ScoreBatch,
    likelihood_weighting: bool = False,
    diffusion_sq_fn: Callable[[float], float] | None = None,
    eps: float = 1e-5,
) -> dict[str, float]:
    base = model.params()
    grads: dict[str, float] = {}
    for name in base:
        plus = dict(base)
        minus = dict(base)
        plus[name] += eps
        minus[name] -= eps
        plus_model = model.with_params(plus)
        minus_model = model.with_params(minus)
        plus_loss = score_matching_loss(
            plus_model.predict(batch.perturbed, batch.time),
            batch,
            likelihood_weighting=likelihood_weighting,
            diffusion_sq_fn=diffusion_sq_fn,
        )["loss"]
        minus_loss = score_matching_loss(
            minus_model.predict(batch.perturbed, batch.time),
            batch,
            likelihood_weighting=likelihood_weighting,
            diffusion_sq_fn=diffusion_sq_fn,
        )["loss"]
        grads[name] = (plus_loss - minus_loss) / (2.0 * eps)
    return grads


def optimizer_step(
    model: LinearScoreModel,
    batch: ScoreBatch,
    learning_rate: float = 0.05,
    likelihood_weighting: bool = False,
    diffusion_sq_fn: Callable[[float], float] | None = None,
) -> dict:
    params_before = model.params()
    predictions_before = model.predict(batch.perturbed, batch.time)
    loss_before = score_matching_loss(
        predictions_before,
        batch,
        likelihood_weighting=likelihood_weighting,
        diffusion_sq_fn=diffusion_sq_fn,
    )["loss"]
    grads = finite_difference_gradient(model, batch, likelihood_weighting, diffusion_sq_fn)
    params_after = {name: value - learning_rate * grads[name] for name, value in params_before.items()}
    updated = model.with_params(params_after)
    predictions_after = updated.predict(batch.perturbed, batch.time)
    loss_after = score_matching_loss(
        predictions_after,
        batch,
        likelihood_weighting=likelihood_weighting,
        diffusion_sq_fn=diffusion_sq_fn,
    )["loss"]
    return {
        "loss_before": loss_before,
        "loss_after": loss_after,
        "params_before": params_before,
        "params_after": params_after,
        "gradients": grads,
        "optimizer_state_changed": params_before != params_after,
        "predictions_before": predictions_before,
        "predictions_after": predictions_after,
    }


def self_test() -> dict:
    marginal = lambda x0, t: (0.8 * x0, 0.5 + 0.1 * t)
    batch = build_score_matching_batch([1.0, -1.0], [0.2, 0.4], [0.5, -0.25], marginal)
    model = LinearScoreModel(weight=-0.2, time_weight=0.0, bias=0.0)
    trace = optimizer_step(model, batch, learning_rate=0.05)
    return {
        "ok": trace["optimizer_state_changed"] and trace["loss_after"] < trace["loss_before"],
        "trace": trace,
        "target": batch.target,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = self_test()
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 2
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
