#!/usr/bin/env python3
"""Lightweight deterministic BAR zeroth-order optimizer."""

from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Sequence

Vector = List[float]


def softmax(logits: Sequence[float]) -> Vector:
    m = max(logits)
    exps = [math.exp(x - m) for x in logits]
    s = sum(exps)
    return [x / s for x in exps]


def normalize(v: Vector) -> Vector:
    n = math.sqrt(sum(x*x for x in v))
    return [x / n for x in v] if n else [0.0 for _ in v]


def apply_program(features: Sequence[float], w: Sequence[float], mask: Sequence[float]) -> Vector:
    return [float(x) + math.tanh(float(a) * float(m)) for x, a, m in zip(features, w, mask)]


def mapped_probs(source_probs: Sequence[float], mapping: Dict[int, Sequence[int]]) -> Vector:
    vals = []
    for target in sorted(mapping):
        group = list(mapping[target])
        vals.append(sum(source_probs[i] for i in group) / len(group))
    total = sum(vals)
    return [v / total for v in vals]


def focal_loss(probs: Sequence[Sequence[float]], labels: Sequence[int], gamma: float = 2.0) -> float:
    counts = {y: labels.count(y) for y in set(labels)}
    loss = 0.0
    for row, y in zip(probs, labels):
        p = max(1e-9, min(1.0, row[int(y)]))
        loss += (1.0 / counts[y]) * ((1.0 - p) ** gamma) * (-math.log(p))
    return loss / len(labels)


def evaluate(w: Sequence[float], features: Sequence[Sequence[float]], labels: Sequence[int], mask: Sequence[float], mapping: Dict[int, Sequence[int]], black_box: Callable[[Sequence[float]], Sequence[float]]) -> dict:
    target_probs = []
    predictions = []
    for x in features:
        source = black_box(apply_program(x, w, mask))
        probs = mapped_probs(source, mapping)
        target_probs.append(probs)
        predictions.append(max(range(len(probs)), key=lambda i: probs[i]))
    acc = sum(int(p == y) for p, y in zip(predictions, labels)) / len(labels)
    return {"loss": focal_loss(target_probs, labels), "accuracy": acc, "predictions": predictions, "target_probs": target_probs}


def train_zo(features: Sequence[Sequence[float]], labels: Sequence[int], mask: Sequence[float], mapping: Dict[int, Sequence[int]], black_box: Callable[[Sequence[float]], Sequence[float]], iterations: int = 8, q: int = 4, beta: float = 0.05, lr: float = 0.8, seed: int = 0, initial_w: Sequence[float] | None = None) -> dict:
    rng = random.Random(seed)
    dim = len(mask)
    w = list(initial_w) if initial_w is not None else [0.0] * dim
    before = list(w)
    trace = []
    queries = 0
    for step in range(iterations):
        base = evaluate(w, features, labels, mask, mapping, black_box)
        queries += len(features)
        grad = [0.0] * dim
        for _ in range(q):
            u = normalize([rng.gauss(0.0, 1.0) for _ in range(dim)])
            wp = [a + beta*b for a, b in zip(w, u)]
            pert = evaluate(wp, features, labels, mask, mapping, black_box)
            queries += len(features)
            scale = dim * (pert["loss"] - base["loss"]) / beta
            for i in range(dim):
                grad[i] += scale * u[i] / q
        w = [a - lr*g for a, g in zip(w, grad)]
        after_eval = evaluate(w, features, labels, mask, mapping, black_box)
        queries += len(features)
        trace.append({"step": step, "loss_before_step": base["loss"], "loss_after_step": after_eval["loss"], "accuracy": after_eval["accuracy"]})
    final = evaluate(w, features, labels, mask, mapping, black_box)
    queries += len(features)
    return {"params_before": before, "params_after": w, "loss_before": trace[0]["loss_before_step"] if trace else final["loss"], "loss_after": final["loss"], "accuracy": final["accuracy"], "predictions": final["predictions"], "query_count": queries, "trace": trace}


def toy_black_box(x: Sequence[float]) -> Vector:
    # Four source labels. Labels 0/1 prefer negative programmable bias; 2/3 prefer positive bias.
    signal = sum(x[2:]) + 0.5 * (x[0] - x[1])
    return softmax([-signal, -0.8*signal, signal, 0.8*signal])
