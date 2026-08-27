#!/usr/bin/env python
"""Small MLAlgorithms neural-stack smoke checks.

This helper adapts the repository's MLP/RBM/DQN example ideas into short
checks that use synthetic data, avoid display/rendering, and avoid long RL
training runs.

Examples:
  python run_neural_smoke.py --workflow mlp
  python run_neural_smoke.py --workflow all
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split

from mla.metrics.metrics import mean_squared_error
from mla.neuralnet import NeuralNet
from mla.neuralnet.layers import Activation, Dense
from mla.neuralnet.optimizers import Adam
from mla.rbm import RBM
from mla.rl.dqn import DQN


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def smoke_mlp() -> None:
    X, y = make_regression(n_samples=120, n_features=5, n_informative=5, noise=0.05, random_state=1111)
    y = y * 0.01
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=1111)
    model = NeuralNet(
        layers=[Dense(12), Activation("linear"), Dense(1)],
        loss="mse",
        optimizer=Adam(),
        metric="mse",
        batch_size=16,
        max_epochs=4,
        verbose=False,
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test).flatten()
    mse = float(mean_squared_error(y_test, pred))
    _check(np.isfinite(mse), f"MLP MSE is not finite: {mse}")
    _check(pred.shape == y_test.shape, f"unexpected MLP prediction shape: {pred.shape}")
    print(f"mlp pred_shape={pred.shape} mse={mse:.6f}")


def smoke_rbm() -> None:
    X = np.random.RandomState(42).uniform(0, 1, (40, 6))
    model = RBM(n_hidden=3, learning_rate=0.05, batch_size=10, max_epochs=2)
    model.fit(X)
    features = model.predict(X)
    _check(features.shape == (40, 3), f"unexpected RBM feature shape: {features.shape}")
    _check(len(model.errors) == 2, f"unexpected RBM error history length: {len(model.errors)}")
    print(f"rbm features={features.shape} errors={model.errors}")


def model_factory(n_actions, batch_size=8):
    return NeuralNet(
        layers=[Dense(8), Activation("relu"), Dense(n_actions)],
        loss="mse",
        optimizer=Adam(),
        metric="mse",
        batch_size=batch_size,
        max_epochs=1,
        verbose=False,
    )


def smoke_dqn_init() -> None:
    agent = DQN(n_episodes=1, batch_size=8, memory_limit=10)
    model = model_factory(n_actions=2, batch_size=agent.batch_size)
    probe = np.zeros((agent.batch_size, 4))
    # NeuralNet has fit_required=False, but BaseEstimator.predict still expects
    # an X attribute to exist. Set it explicitly so this remains a no-training
    # model-factory smoke rather than a full fit/train step.
    model.X = None
    pred = model.predict(probe)
    _check(pred.shape == (agent.batch_size, 2), f"unexpected DQN model prediction shape: {pred.shape}")
    _check(agent.n_episodes == 1 and agent.batch_size == 8, "unexpected DQN config")
    print(f"dqn-init q_shape={pred.shape} episodes={agent.n_episodes}")


WORKFLOWS = {
    "mlp": smoke_mlp,
    "rbm": smoke_rbm,
    "dqn-init": smoke_dqn_init,
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run small MLAlgorithms neural-stack smoke checks.")
    parser.add_argument("--workflow", choices=sorted(WORKFLOWS) + ["all"], default="all")
    args = parser.parse_args(argv)

    selected = WORKFLOWS.keys() if args.workflow == "all" else [args.workflow]
    for name in selected:
        print(f"== {name} ==")
        WORKFLOWS[name]()
    print("neural smoke checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"neural smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
