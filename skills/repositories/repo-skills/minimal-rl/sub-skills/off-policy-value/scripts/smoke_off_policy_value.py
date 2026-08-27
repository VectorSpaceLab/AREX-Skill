#!/usr/bin/env python3
"""CPU-only smoke checks for minimalRL off-policy/value contracts.

The helper adapts safe tensor-shape and replay checks from the DQN, ACER, and
V-trace scripts. It does not import the original repository and does not run
full training.
"""

from __future__ import annotations

import argparse
import collections
import random

import torch
import torch.nn as nn
import torch.nn.functional as F


class ReplayBuffer:
    def __init__(self, limit: int = 100):
        self.buffer = collections.deque(maxlen=limit)

    def put(self, transition):
        self.buffer.append(transition)

    def sample(self, n: int):
        batch = random.sample(self.buffer, n)
        s, a, r, sp, done = zip(*batch)
        return (
            torch.tensor(s, dtype=torch.float32),
            torch.tensor([[x] for x in a], dtype=torch.long),
            torch.tensor([[x] for x in r], dtype=torch.float32),
            torch.tensor(sp, dtype=torch.float32),
            torch.tensor([[x] for x in done], dtype=torch.float32),
        )

    def size(self) -> int:
        return len(self.buffer)


class Qnet(nn.Module):
    def __init__(self, obs_dim: int = 4, action_dim: int = 2):
        super().__init__()
        self.fc1 = nn.Linear(obs_dim, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, action_dim)

    def forward(self, x):
        return self.fc3(F.relu(self.fc2(F.relu(self.fc1(x)))))


def check_dqn() -> None:
    memory = ReplayBuffer()
    for i in range(4):
        memory.put(([0.0, 0.0, 0.0, float(i)], i % 2, 0.01, [0.1, 0.0, 0.0, float(i)], 1.0))
    q, q_target = Qnet(), Qnet()
    s, a, r, sp, done = memory.sample(4)
    q_a = q(s).gather(1, a)
    target = r + 0.98 * q_target(sp).max(1)[0].unsqueeze(1) * done
    loss = F.smooth_l1_loss(q_a, target.detach())
    assert memory.size() == 4
    assert tuple(q_a.shape) == (4, 1)
    assert loss.ndim == 0
    print("dqn: ok")


class AcerActorCritic(nn.Module):
    def __init__(self, obs_dim: int = 4, action_dim: int = 2):
        super().__init__()
        self.fc1 = nn.Linear(obs_dim, 256)
        self.fc_pi = nn.Linear(256, action_dim)
        self.fc_q = nn.Linear(256, action_dim)

    def pi(self, x, softmax_dim=0):
        return F.softmax(self.fc_pi(F.relu(self.fc1(x))), dim=softmax_dim)

    def q(self, x):
        return self.fc_q(F.relu(self.fc1(x)))


def check_acer() -> None:
    model = AcerActorCritic()
    s = torch.zeros(6, 4)
    a = torch.tensor([[0], [1], [0], [1], [0], [1]])
    behavior_prob = torch.full((6, 2), 0.5)
    q = model.q(s)
    q_a = q.gather(1, a)
    pi = model.pi(s, softmax_dim=1)
    pi_a = pi.gather(1, a)
    v = (q * pi).sum(1).unsqueeze(1).detach()
    rho = pi.detach() / behavior_prob
    rho_a = rho.gather(1, a).clamp(max=1.0)
    correction_coeff = (1 - 1.0 / rho).clamp(min=0)
    assert tuple(q_a.shape) == (6, 1)
    assert tuple(pi_a.shape) == (6, 1)
    assert tuple(v.shape) == (6, 1)
    assert tuple(rho_a.shape) == (6, 1)
    assert tuple(correction_coeff.shape) == (6, 2)
    print("acer: ok")


def check_vtrace() -> None:
    model = AcerActorCritic()
    s = torch.zeros(5, 4)
    sp = torch.ones(5, 4) * 0.01
    a = torch.tensor([[0], [1], [0], [1], [0]])
    r = torch.ones(5, 1) / 100.0
    done = torch.ones(5, 1)
    mu_a = torch.full((5, 1), 0.5)
    with torch.no_grad():
        pi_a = model.pi(s, softmax_dim=1).gather(1, a)
        v = (model.q(s) * model.pi(s, softmax_dim=1)).sum(1).unsqueeze(1)
        v_prime = (model.q(sp) * model.pi(sp, softmax_dim=1)).sum(1).unsqueeze(1)
        ratio = torch.exp(torch.log(pi_a) - torch.log(mu_a))
        rhos = torch.minimum(torch.tensor(1.0), ratio)
        cs = torch.minimum(torch.tensor(1.0), ratio)
        td_target = r + 0.98 * v_prime * done
        delta = rhos * (td_target - v)
    assert tuple(rhos.shape) == (5, 1)
    assert tuple(cs.shape) == (5, 1)
    assert tuple(delta.shape) == (5, 1)
    print("vtrace: ok")


CHECKS = {"dqn": check_dqn, "acer": check_acer, "vtrace": check_vtrace}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run safe minimalRL off-policy/value smoke checks.")
    parser.add_argument("--algorithm", choices=["all", *CHECKS.keys()], default="all")
    args = parser.parse_args()
    names = CHECKS.keys() if args.algorithm == "all" else [args.algorithm]
    for name in names:
        CHECKS[name]()


if __name__ == "__main__":
    main()
