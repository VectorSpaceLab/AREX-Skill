#!/usr/bin/env python3
"""No-training smoke checks for DRL-Pytorch value-based algorithms.

The script imports modules from a user-supplied DRL-Pytorch checkout, isolates
per-directory import names, and runs tiny API/network/buffer probes. It does not
create Gym environments, download assets, launch training, render, or write
checkpoints.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Callable, Iterable

COLLIDING_MODULES = {
    "Q_learning",
    "DQN",
    "utils",
    "LPRB",
    "PriorDQN",
    "Categorical_DQN",
    "NoisyNetDQN",
}

ALGORITHM_DIRS = {
    "q-learning": Path("1.Q-learning"),
    "dqn": Path("2.1_Duel-Double-DQN"),
    "per-light": Path("2.3 Prioritized-Experience-Replay-DDQN-DQN") / "LightPriorDQN_gym0.2x",
    "per-sumtree": Path("2.3 Prioritized-Experience-Replay-DDQN-DQN") / "PriorDQN_gym0.2x",
    "c51": Path("2.4_Categorical-DQN_C51"),
    "noisynet": Path("2.5_NoisyNet-DQN"),
}

RUN_ORDER = ["q-learning", "dqn", "per-light", "per-sumtree", "c51", "noisynet"]


class SmokeFailure(RuntimeError):
    """Raised when a smoke check has a clear diagnostic failure."""


def _purge_modules(names: Iterable[str] = COLLIDING_MODULES) -> None:
    for name in names:
        sys.modules.pop(name, None)


@contextlib.contextmanager
def _algorithm_import_context(repo_root: Path, algorithm: str):
    """Temporarily import from exactly one standalone algorithm directory."""

    algorithm_dir = repo_root / ALGORITHM_DIRS[algorithm]
    if not algorithm_dir.is_dir():
        raise SmokeFailure(f"missing expected directory for {algorithm}: {ALGORITHM_DIRS[algorithm]}")

    previous_cwd = Path.cwd()
    previous_sys_path = list(sys.path)
    _purge_modules()
    try:
        os.chdir(algorithm_dir)
        sys.path.insert(0, str(algorithm_dir))
        yield algorithm_dir
    finally:
        os.chdir(previous_cwd)
        sys.path[:] = previous_sys_path
        _purge_modules()


def _import_required(module_name: str):
    try:
        return importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic tool should surface import cause
        raise SmokeFailure(f"failed to import {module_name}: {exc}") from exc


def _require_torch():
    try:
        import torch  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise SmokeFailure(f"PyTorch import failed: {exc}") from exc
    return torch


def _require_numpy():
    try:
        import numpy as np  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise SmokeFailure(f"NumPy import failed: {exc}") from exc
    return np


def smoke_q_learning(repo_root: Path) -> str:
    np = _require_numpy()
    with _algorithm_import_context(repo_root, "q-learning"):
        q_learning = _import_required("Q_learning")
        agent = q_learning.QLearningAgent(s_dim=4, a_dim=2, lr=0.5, gamma=0.9, exp_noise=0.0)
        before = float(agent.Q[0, 1])
        agent.train(s=0, a=1, r=1.0, s_next=2, dw=False)
        after = float(agent.Q[0, 1])
        action = agent.select_action(0, deterministic=True)
        if agent.Q.shape != (4, 2):
            raise SmokeFailure(f"unexpected Q-table shape: {agent.Q.shape}")
        if not after > before:
            raise SmokeFailure("Q-learning update did not increase the trained Q entry")
        if not isinstance(action, (int, np.integer)):
            raise SmokeFailure(f"select_action returned non-integer action: {type(action)!r}")
    return "QLearningAgent import, action, and one-table update passed"


def smoke_dqn(repo_root: Path) -> str:
    torch = _require_torch()
    with _algorithm_import_context(repo_root, "dqn"):
        dqn = _import_required("DQN")
        x = torch.zeros((3, 4), dtype=torch.float32)
        q_net = dqn.Q_Net(state_dim=4, action_dim=2, hid_shape=(8,))
        duel_net = dqn.Duel_Q_Net(state_dim=4, action_dim=2, hid_shape=(8,))
        q = q_net(x)
        duel_q = duel_net(x)
        if tuple(q.shape) != (3, 2):
            raise SmokeFailure(f"Q_Net output shape mismatch: {tuple(q.shape)}")
        if tuple(duel_q.shape) != (3, 2):
            raise SmokeFailure(f"Duel_Q_Net output shape mismatch: {tuple(duel_q.shape)}")
    return "DQN and Dueling DQN network imports/forwards passed"


def smoke_per_light(repo_root: Path) -> str:
    np = _require_numpy()
    torch = _require_torch()
    with _algorithm_import_context(repo_root, "per-light"):
        lprb = _import_required("LPRB")
        dqn = _import_required("DQN")
        opt = SimpleNamespace(
            state_dim=4,
            action_dim=2,
            net_width=8,
            lr_init=1e-4,
            gamma=0.99,
            batch_size=2,
            exp_noise_init=0.1,
            DDQN=True,
            env_with_dw=True,
            buffer_size=8,
            alpha=0.6,
            beta_init=0.4,
            replacement=False,
        )
        agent = dqn.DQN_Agent(opt)
        y = agent.q_net(torch.zeros((2, 4), dtype=torch.float32, device=lprb.device))
        if tuple(y.shape) != (2, 2):
            raise SmokeFailure(f"LightPrior Q network output shape mismatch: {tuple(y.shape)}")
        buffer = lprb.LightPriorReplayBuffer(opt)
        for idx in range(5):
            state = np.full(4, float(idx), dtype=np.float32)
            priority = torch.tensor(1.0 + idx, dtype=torch.float32, device=lprb.device)
            buffer.add(state, idx % 2, float(idx), False, False, priority)
        sample = buffer.sample(batch_size=2)
        if len(sample) != 8:
            raise SmokeFailure(f"LightPrior sample returned {len(sample)} fields, expected 8")
        if tuple(sample[0].shape) != (2, 4):
            raise SmokeFailure(f"LightPrior sampled state shape mismatch: {tuple(sample[0].shape)}")
    return "LightPrior PER import, network forward, and tiny buffer sample passed"


def smoke_per_sumtree(repo_root: Path) -> str:
    np = _require_numpy()
    torch = _require_torch()
    with _algorithm_import_context(repo_root, "per-sumtree"):
        prior = _import_required("PriorDQN")
        opt = SimpleNamespace(
            state_dim=4,
            action_dim=2,
            net_width=8,
            lr=1e-4,
            gamma=0.99,
            batch_size=2,
            exp_noise_init=0.1,
            DDQN=True,
            buffer_size=8,
            alpha=0.6,
            beta_init=0.4,
        )
        q_net = prior.Q_Net(4, 2, (8,))
        y = q_net(torch.zeros((2, 4), dtype=torch.float32))
        if tuple(y.shape) != (2, 2):
            raise SmokeFailure(f"sum-tree Q network output shape mismatch: {tuple(y.shape)}")
        buffer = prior.PrioritizedReplayBuffer(opt)
        for idx in range(4):
            state = np.full(4, float(idx), dtype=np.float32)
            next_state = state + 1.0
            buffer.add(state, idx % 2, float(idx), next_state, False)
        sample = buffer.sample(batch_size=2)
        if len(sample) != 7:
            raise SmokeFailure(f"sum-tree sample returned {len(sample)} fields, expected 7")
        indices = sample[5]
        buffer.update_batch_priorities(indices, np.ones_like(indices, dtype=np.float32))
    return "sum-tree PER import, network forward, sample, and priority update passed"


def smoke_c51(repo_root: Path) -> str:
    torch = _require_torch()
    with _algorithm_import_context(repo_root, "c51"):
        c51 = _import_required("Categorical_DQN")
        atoms = torch.linspace(-1.0, 1.0, steps=5)
        net = c51.Categorical_Q_Net(state_dim=4, action_dim=2, hid_shape=(8,), atoms=atoms)
        action, distribution = net(torch.zeros((3, 4), dtype=torch.float32))
        if tuple(action.shape) != (3,):
            raise SmokeFailure(f"C51 action shape mismatch: {tuple(action.shape)}")
        if tuple(distribution.shape) != (3, 5):
            raise SmokeFailure(f"C51 distribution shape mismatch: {tuple(distribution.shape)}")
        row_sums = distribution.sum(dim=1)
        if not torch.allclose(row_sums, torch.ones_like(row_sums), atol=1e-5):
            raise SmokeFailure("C51 distributions do not sum to one")
    return "C51 categorical network import and distribution forward passed"


def smoke_noisynet(repo_root: Path) -> str:
    torch = _require_torch()
    with _algorithm_import_context(repo_root, "noisynet"):
        noisy = _import_required("NoisyNetDQN")
        net = noisy.Noisy_Q_Net(state_dim=4, action_dim=2, hid_shape=(8,))
        x = torch.zeros((3, 4), dtype=torch.float32)
        net.train()
        y_train = net(x)
        net.eval()
        y_eval = net(x)
        if tuple(y_train.shape) != (3, 2):
            raise SmokeFailure(f"NoisyNet train output shape mismatch: {tuple(y_train.shape)}")
        if tuple(y_eval.shape) != (3, 2):
            raise SmokeFailure(f"NoisyNet eval output shape mismatch: {tuple(y_eval.shape)}")
    return "NoisyNet network import and train/eval forwards passed"


SMOKE_FUNCTIONS: dict[str, Callable[[Path], str]] = {
    "q-learning": smoke_q_learning,
    "dqn": smoke_dqn,
    "per-light": smoke_per_light,
    "per-sumtree": smoke_per_sumtree,
    "c51": smoke_c51,
    "noisynet": smoke_noisynet,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run no-training diagnostics for DRL-Pytorch value-based algorithms "
            "against a user-supplied checkout."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Path to the DRL-Pytorch checkout; defaults to the current directory.",
    )
    parser.add_argument(
        "--algorithm",
        choices=["all", *RUN_ORDER],
        default="all",
        help="Which value-based diagnostic to run.",
    )
    parser.add_argument(
        "--allow-cuda",
        action="store_true",
        help=(
            "Do not hide CUDA from PER modules. By default the script sets "
            "CUDA_VISIBLE_DEVICES='' before importing torch-backed modules so "
            "diagnostics stay CPU-safe."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()
    if not repo_root.is_dir():
        print(f"ERROR: --repo-root is not a directory: {repo_root}", file=sys.stderr)
        return 2

    if not args.allow_cuda:
        # Force CPU visibility for PER modules that pick a device at import time.
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    selected = RUN_ORDER if args.algorithm == "all" else [args.algorithm]
    failures: list[tuple[str, str]] = []
    for algorithm in selected:
        try:
            message = SMOKE_FUNCTIONS[algorithm](repo_root)
            print(f"PASS {algorithm}: {message}")
        except SmokeFailure as exc:
            failures.append((algorithm, str(exc)))
            print(f"FAIL {algorithm}: {exc}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001 - top-level diagnostic guard
            failures.append((algorithm, repr(exc)))
            print(f"FAIL {algorithm}: unexpected {exc!r}", file=sys.stderr)

    if failures:
        print("\nOne or more value-based smoke checks failed:", file=sys.stderr)
        for algorithm, message in failures:
            print(f"- {algorithm}: {message}", file=sys.stderr)
        return 1

    print("All selected value-based smoke checks passed without training.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
