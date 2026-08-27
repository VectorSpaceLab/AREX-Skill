#!/usr/bin/env python3
"""Tiny synthetic smoke test for DeepCTR multitask models.

This script exercises SharedBottom, ESMM, MMOE, and PLE on a tiny synthetic
batch. It avoids external data and checks both list- and dict-style loss/target
packing.
"""

from __future__ import annotations

import argparse
import json
from typing import Dict, Iterable, List, Tuple

TASK_NAMES = ("ctr", "ctcvr")
TASK_TYPES = ("binary", "binary")
MODEL_NAMES = ("sharedbottom", "esmm", "mmoe", "ple")


def build_feature_columns() -> List[object]:
    from deepctr.feature_column import DenseFeat, SparseFeat

    return [
        SparseFeat("user_id", vocabulary_size=8, embedding_dim=4),
        SparseFeat("item_id", vocabulary_size=16, embedding_dim=4),
        DenseFeat("score", 1),
    ]


def build_inputs(num_samples: int, seed: int) -> Tuple[Dict[str, object], Dict[str, object]]:
    import numpy as np

    rng = np.random.default_rng(seed)
    x = {
        "user_id": rng.integers(0, 8, size=(num_samples, 1), dtype=np.int32),
        "item_id": rng.integers(0, 16, size=(num_samples, 1), dtype=np.int32),
        "score": rng.random((num_samples, 1)).astype("float32"),
    }
    ctr = rng.integers(0, 2, size=(num_samples, 1), dtype=np.int32).astype("float32")
    cvr = rng.integers(0, 2, size=(num_samples, 1), dtype=np.int32).astype("float32")
    labels = {
        "ctr": ctr,
        "ctcvr": (ctr * cvr).astype("float32"),
    }
    return x, labels


def build_model(name: str, feature_columns: Iterable[object]):
    from deepctr.models import ESMM, MMOE, PLE, SharedBottom

    shared_kwargs = dict(task_types=TASK_TYPES, task_names=TASK_NAMES)
    if name == "sharedbottom":
        return SharedBottom(
            feature_columns,
            bottom_dnn_hidden_units=(8,),
            tower_dnn_hidden_units=(4,),
            **shared_kwargs,
        )
    if name == "esmm":
        return ESMM(
            feature_columns,
            tower_dnn_hidden_units=(8,),
            **shared_kwargs,
        )
    if name == "mmoe":
        return MMOE(
            feature_columns,
            num_experts=2,
            expert_dnn_hidden_units=(8,),
            tower_dnn_hidden_units=(4,),
            gate_dnn_hidden_units=(),
            **shared_kwargs,
        )
    if name == "ple":
        return PLE(
            feature_columns,
            shared_expert_num=1,
            specific_expert_num=1,
            num_levels=2,
            expert_dnn_hidden_units=(8,),
            tower_dnn_hidden_units=(4,),
            gate_dnn_hidden_units=(),
            **shared_kwargs,
        )
    raise ValueError(f"unknown model: {name}")


def pack_targets(output_names: List[str], labels: Dict[str, object], style: str):
    if style == "list":
        return [labels[name] for name in output_names]
    if style == "dict":
        return {name: labels[name] for name in output_names}
    raise ValueError(f"unknown compile style: {style}")


def pack_losses(output_names: List[str], style: str):
    if style == "list":
        return ["binary_crossentropy" for _ in output_names]
    if style == "dict":
        return {name: "binary_crossentropy" for name in output_names}
    raise ValueError(f"unknown compile style: {style}")


def run_one(model_name: str, compile_style: str, num_samples: int, seed: int, epochs: int) -> dict:
    import numpy as np
    import tensorflow as tf

    tf.keras.backend.clear_session()
    np.random.seed(seed)
    tf.random.set_seed(seed)

    feature_columns = build_feature_columns()
    x, labels = build_inputs(num_samples=num_samples, seed=seed)
    model = build_model(model_name, feature_columns)

    if list(model.output_names) != list(TASK_NAMES):
        raise AssertionError(f"unexpected output order for {model_name}: {model.output_names}")

    losses = pack_losses(model.output_names, compile_style)
    targets = pack_targets(model.output_names, labels, compile_style)

    model.compile(optimizer="adam", loss=losses)
    history = model.fit(x, targets, batch_size=min(4, num_samples), epochs=epochs, verbose=0)
    eval_result = model.evaluate(x, targets, batch_size=min(4, num_samples), verbose=0)
    preds = model.predict(x, batch_size=min(4, num_samples), verbose=0)

    if not isinstance(preds, list):
        raise AssertionError(f"{model_name} predict() did not return a list")
    if len(preds) != len(model.output_names):
        raise AssertionError(f"{model_name} predict() output count mismatch: {len(preds)}")
    for pred in preds:
        if pred.shape != (num_samples, 1):
            raise AssertionError(f"{model_name} prediction shape mismatch: {pred.shape}")

    return {
        "model": model_name,
        "compile_style": compile_style,
        "output_names": list(model.output_names),
        "history_keys": sorted(history.history.keys()),
        "eval_type": type(eval_result).__name__,
        "pred_shapes": [list(pred.shape) for pred in preds],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run tiny synthetic DeepCTR multitask smoke checks.")
    parser.add_argument(
        "--model",
        choices=("all",) + MODEL_NAMES,
        default="all",
        help="Which model to smoke-test.",
    )
    parser.add_argument(
        "--compile-style",
        choices=("list", "dict", "both"),
        default="both",
        help="How to pack losses and targets.",
    )
    parser.add_argument("--samples", type=int, default=8, help="Number of synthetic rows to generate.")
    parser.add_argument("--seed", type=int, default=2024, help="Random seed for synthetic data.")
    parser.add_argument("--epochs", type=int, default=1, help="Training epochs for the smoke run.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    models = list(MODEL_NAMES) if args.model == "all" else [args.model]
    compile_styles = ["list", "dict"] if args.compile_style == "both" else [args.compile_style]

    results = []
    for model_name in models:
        for compile_style in compile_styles:
            results.append(
                run_one(
                    model_name=model_name,
                    compile_style=compile_style,
                    num_samples=args.samples,
                    seed=args.seed,
                    epochs=args.epochs,
                )
            )

    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
