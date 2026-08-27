#!/usr/bin/env python3
"""Package-wide import and dependency check for the ML-From-Scratch repo skill.

This script performs small read-only checks. It does not load external data,
open plots, contact networks, render Gym windows, or write files.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from importlib import metadata
from typing import Any

os.environ.setdefault("MPLBACKEND", "Agg")


DISTRIBUTIONS = [
    "mlfromscratch",
    "numpy",
    "scipy",
    "pandas",
    "scikit-learn",
    "matplotlib",
    "cvxopt",
    "progressbar33",
    "terminaltables",
]

FAMILY_IMPORTS = [
    "mlfromscratch",
    "mlfromscratch.utils",
    "mlfromscratch.supervised_learning",
    "mlfromscratch.unsupervised_learning",
    "mlfromscratch.deep_learning",
]

RL_IMPORTS = [
    "gym",
    "mlfromscratch.reinforcement_learning",
]


def version_of(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def import_module(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {"module": name, "ok": True, "version": getattr(module, "__version__", None)}
    except Exception as exc:  # pragma: no cover - depends on caller environment
        return {
            "module": name,
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def smoke_core_objects() -> dict[str, Any]:
    try:
        import numpy as np
        np.random.seed(7)
        from mlfromscratch.deep_learning import NeuralNetwork
        from mlfromscratch.deep_learning.layers import Activation, Dense
        from mlfromscratch.deep_learning.loss_functions import CrossEntropy
        from mlfromscratch.deep_learning.optimizers import Adam
        from mlfromscratch.supervised_learning import LinearRegression
        from mlfromscratch.unsupervised_learning import KMeans
        from mlfromscratch.utils import to_categorical

        X = np.asarray([[0.0], [1.0], [2.0]])
        y = np.asarray([0.0, 1.0, 2.0])
        reg = LinearRegression(n_iterations=1, learning_rate=0.001)
        reg.fit(X, y)
        reg_pred = reg.predict(np.asarray([[3.0]]))

        km = KMeans(k=1, max_iterations=10)
        labels = km.predict(
            np.asarray(
                [[0.0, 0.0], [0.0, 0.1], [0.1, 0.0], [5.0, 5.0], [5.1, 5.0], [5.0, 5.1]]
            )
        )

        model = NeuralNetwork(optimizer=Adam(learning_rate=0.01), loss=CrossEntropy)
        model.progressbar = lambda iterable: iterable
        model.add(Dense(2, input_shape=(1,)))
        model.add(Activation("softmax"))
        y_cat = to_categorical(np.asarray([0, 1, 0]), n_col=2)
        loss, _ = model.fit(X, y_cat, n_epochs=1, batch_size=1)

        return {
            "ok": True,
            "linear_regression_prediction_shape": list(np.asarray(reg_pred).shape),
            "kmeans_label_shape": list(np.asarray(labels).shape),
            "tiny_nn_loss_last": float(loss[-1]),
        }
    except Exception as exc:  # pragma: no cover - diagnostic path depends on environment
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def smoke_rl() -> dict[str, Any]:
    try:
        import numpy as np

        if "bool8" not in np.__dict__:
            np.bool8 = np.bool_

        import gym
        from mlfromscratch.reinforcement_learning import DeepQNetwork

        env = gym.make("CartPole-v1")
        try:
            reset_out = env.reset()
            step_out = env.step(env.action_space.sample())
        finally:
            env.close()

        dqn = DeepQNetwork(env_name="CartPole-v1", epsilon=1.0)
        try:
            result = {
                "ok": True,
                "gym_version": getattr(gym, "__version__", None),
                "reset_returns_tuple": isinstance(reset_out, tuple),
                "step_output_length": len(step_out),
                "dqn_n_states": int(dqn.n_states),
                "dqn_n_actions": int(dqn.n_actions),
            }
        finally:
            try:
                dqn.env.close()
            except Exception:
                pass
        return result
    except Exception as exc:  # pragma: no cover - diagnostic path depends on environment
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check ML-From-Scratch package imports and dependency versions.")
    parser.add_argument("--include-rl", action="store_true", help="Also import Gym and run a small CartPole/DQN compatibility check.")
    parser.add_argument("--json", action="store_true", help="Print JSON only. Default prints the same JSON prettily.")
    args = parser.parse_args(argv)

    distributions = {dist: version_of(dist) for dist in DISTRIBUTIONS}
    if args.include_rl:
        distributions["gym"] = version_of("gym")

    modules = [import_module(name) for name in FAMILY_IMPORTS]
    if args.include_rl:
        modules.extend(import_module(name) for name in RL_IMPORTS)

    result: dict[str, Any] = {
        "distributions": distributions,
        "imports": modules,
        "core_smoke": smoke_core_objects(),
        "rl_smoke": smoke_rl() if args.include_rl else "skipped",
        "notes": [
            "Install scikit-learn explicitly when legacy sklearn metadata is insufficient.",
            "Install cvxopt for supervised package imports and SVM usage.",
            "Use gym==0.25.x with numpy<2 or a local compatibility wrapper for the DQN path.",
        ],
    }

    ok = all(item["ok"] for item in modules) and bool(result["core_smoke"].get("ok"))
    if args.include_rl:
        ok = ok and bool(result["rl_smoke"].get("ok"))
    result["ok"] = ok

    print(json.dumps(result, indent=None if args.json else 2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
