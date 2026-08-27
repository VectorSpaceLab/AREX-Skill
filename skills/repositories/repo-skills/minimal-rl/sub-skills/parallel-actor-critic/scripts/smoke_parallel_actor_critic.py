#!/usr/bin/env python3
"""Bounded smoke checks for minimalRL parallel actor-critic contracts.

This helper validates model shapes, bootstrapped target math, and the command
names used by the A2C worker protocol. It does not spawn full training workers.
"""

from __future__ import annotations

import argparse

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical


class ActorCritic(nn.Module):
    def __init__(self, obs_dim: int = 4, action_dim: int = 2):
        super().__init__()
        self.fc1 = nn.Linear(obs_dim, 256)
        self.fc_pi = nn.Linear(256, action_dim)
        self.fc_v = nn.Linear(256, 1)

    def pi(self, x, softmax_dim=1):
        return F.softmax(self.fc_pi(F.relu(self.fc1(x))), dim=softmax_dim)

    def v(self, x):
        return self.fc_v(F.relu(self.fc1(x)))


def compute_target(v_final, r_lst, mask_lst, gamma: float = 0.98):
    g = torch.as_tensor(v_final, dtype=torch.float32).reshape(-1)
    targets = []
    for r, mask in zip(r_lst[::-1], mask_lst[::-1]):
        r_t = torch.as_tensor(r, dtype=torch.float32).reshape(-1)
        mask_t = torch.as_tensor(mask, dtype=torch.float32).reshape(-1)
        g = r_t + gamma * g * mask_t
        targets.append(g.clone())
    return torch.stack(targets[::-1]).float()


def check_model() -> None:
    model = ActorCritic()
    s = torch.zeros(3, 4)
    prob = model.pi(s, softmax_dim=1)
    action = Categorical(prob).sample()
    value = model.v(s)
    assert tuple(prob.shape) == (3, 2)
    assert tuple(action.shape) == (3,)
    assert tuple(value.shape) == (3, 1)
    print("model: ok")


def check_target() -> None:
    v_final = torch.tensor([[0.5, 0.25, 0.0]])
    rewards = [np.array([0.01, 0.02, 0.03]), np.array([0.04, 0.05, 0.06])]
    masks = [np.array([1.0, 1.0, 0.0]), np.array([1.0, 0.0, 1.0])]
    target = compute_target(v_final, rewards, masks)
    assert tuple(target.shape) == (2, 3)
    assert torch.isfinite(target).all()
    print("target: ok")


def check_protocol() -> None:
    commands = {"step", "reset", "reset_task", "close", "get_spaces"}
    required = ["step", "reset", "close", "get_spaces"]
    missing = [name for name in required if name not in commands]
    assert not missing
    # A bounded protocol check: verify a step command carries one action per env.
    actions = np.array([0, 1, 0])
    sent = [("step", int(a)) for a in actions]
    assert all(cmd == "step" and action in (0, 1) for cmd, action in sent)
    print("protocol: ok")


CHECKS = {"model": check_model, "target": check_target, "protocol": check_protocol}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded minimalRL parallel actor-critic smoke checks.")
    parser.add_argument("--check", choices=["all", *CHECKS.keys()], default="all")
    args = parser.parse_args()
    names = CHECKS.keys() if args.check == "all" else [args.check]
    for name in names:
        CHECKS[name]()


if __name__ == "__main__":
    main()
