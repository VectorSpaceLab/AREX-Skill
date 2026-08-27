#!/usr/bin/env python3
"""CPU-only smoke checks for minimalRL continuous-control contracts.

This helper adapts safe tensor-shape parts of the DDPG, PPO-Continuous, and SAC
scripts. It does not import the original repository and does not run training.
"""

from __future__ import annotations

import argparse
import copy
import math
import random
import collections

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Normal


class MuNet(nn.Module):
    def __init__(self, obs_dim: int = 3, action_dim: int = 1, action_scale: float = 2.0):
        super().__init__()
        self.fc1 = nn.Linear(obs_dim, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc_mu = nn.Linear(64, action_dim)
        self.action_scale = action_scale

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return torch.tanh(self.fc_mu(x)) * self.action_scale


class QNet(nn.Module):
    def __init__(self, obs_dim: int = 3, action_dim: int = 1):
        super().__init__()
        self.fc_s = nn.Linear(obs_dim, 64)
        self.fc_a = nn.Linear(action_dim, 64)
        self.fc_q = nn.Linear(128, 32)
        self.fc_out = nn.Linear(32, 1)

    def forward(self, x, a):
        h1 = F.relu(self.fc_s(x))
        h2 = F.relu(self.fc_a(a))
        return self.fc_out(F.relu(self.fc_q(torch.cat([h1, h2], dim=1))))


def soft_update(source: nn.Module, target: nn.Module, tau: float = 0.005) -> None:
    for target_param, source_param in zip(target.parameters(), source.parameters()):
        target_param.data.copy_(target_param.data * (1.0 - tau) + source_param.data * tau)


class OrnsteinUhlenbeckNoise:
    def __init__(self, mu):
        self.theta, self.dt, self.sigma = 0.1, 0.01, 0.1
        self.mu = mu
        self.x_prev = np.zeros_like(self.mu)

    def __call__(self):
        x = self.x_prev + self.theta * (self.mu - self.x_prev) * self.dt + self.sigma * math.sqrt(self.dt) * np.random.normal(size=self.mu.shape)
        self.x_prev = x
        return x


def check_ddpg() -> None:
    mu = MuNet()
    q = QNet()
    target = copy.deepcopy(mu)
    state = torch.zeros(1, 3)
    action = mu(state)
    q_value = q(state, action)
    before = next(target.parameters()).detach().clone()
    with torch.no_grad():
        for p in mu.parameters():
            p.add_(0.01)
    soft_update(mu, target, tau=0.005)
    after = next(target.parameters()).detach()
    noise = OrnsteinUhlenbeckNoise(np.zeros(1))()
    assert tuple(action.shape) == (1, 1)
    assert tuple(q_value.shape) == (1, 1)
    assert tuple(noise.shape) == (1,)
    assert not torch.equal(before, after)
    print("ddpg: ok")


class ContinuousPPO(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(3, 128)
        self.fc_mu = nn.Linear(128, 1)
        self.fc_std = nn.Linear(128, 1)
        self.fc_v = nn.Linear(128, 1)

    def pi(self, x):
        x = F.relu(self.fc1(x))
        return 2.0 * torch.tanh(self.fc_mu(x)), F.softplus(self.fc_std(x))

    def v(self, x):
        return self.fc_v(F.relu(self.fc1(x)))


def check_ppo_continuous() -> None:
    model = ContinuousPPO()
    s = torch.zeros(6, 3)
    mu, std = model.pi(s)
    dist = Normal(mu, std)
    a = dist.sample()
    log_prob = dist.log_prob(a)
    value = model.v(s)
    ratio = torch.exp(log_prob - log_prob.detach())
    assert tuple(mu.shape) == (6, 1)
    assert tuple(std.shape) == (6, 1)
    assert tuple(a.shape) == (6, 1)
    assert tuple(value.shape) == (6, 1)
    assert tuple(ratio.shape) == (6, 1)
    print("ppo-continuous: ok")


class PolicyNet(nn.Module):
    def __init__(self, init_alpha: float = 0.01):
        super().__init__()
        self.fc1 = nn.Linear(3, 128)
        self.fc_mu = nn.Linear(128, 1)
        self.fc_std = nn.Linear(128, 1)
        self.log_alpha = torch.tensor(np.log(init_alpha), requires_grad=True)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        mu = self.fc_mu(x)
        std = F.softplus(self.fc_std(x))
        dist = Normal(mu, std)
        raw_action = dist.rsample()
        log_prob = dist.log_prob(raw_action)
        action = torch.tanh(raw_action)
        corrected = log_prob - torch.log(1 - action.pow(2) + 1e-7)
        return action, corrected


def calc_target(pi: PolicyNet, q1: QNet, q2: QNet, mini_batch, gamma: float = 0.98):
    _s, _a, r, s_prime, done = mini_batch
    with torch.no_grad():
        a_prime, log_prob = pi(s_prime)
        entropy = -pi.log_alpha.exp() * log_prob
        min_q = torch.min(torch.cat([q1(s_prime, a_prime), q2(s_prime, a_prime)], dim=1), dim=1, keepdim=True)[0]
        return r + gamma * done * (min_q + entropy)


def check_sac() -> None:
    pi = PolicyNet()
    q1, q2 = QNet(), QNet()
    s = torch.zeros(5, 3)
    a, log_prob = pi(s)
    batch = (s, a.detach(), torch.ones(5, 1) / 10.0, torch.ones(5, 3) * 0.01, torch.ones(5, 1))
    target = calc_target(pi, q1, q2, batch)
    assert tuple(a.shape) == (5, 1)
    assert tuple(log_prob.shape) == (5, 1)
    assert tuple(q1(s, a).shape) == (5, 1)
    assert tuple(target.shape) == (5, 1)
    print("sac: ok")


CHECKS = {"ddpg": check_ddpg, "ppo-continuous": check_ppo_continuous, "sac": check_sac}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run safe minimalRL continuous-control smoke checks.")
    parser.add_argument("--algorithm", choices=["all", *CHECKS.keys()], default="all")
    args = parser.parse_args()
    names = CHECKS.keys() if args.algorithm == "all" else [args.algorithm]
    for name in names:
        CHECKS[name]()


if __name__ == "__main__":
    main()
