#!/usr/bin/env python3
"""CPU-only smoke checks for minimalRL on-policy discrete algorithm contracts.

This helper adapts the safe tensor-shape parts of the minimalRL on-policy
CartPole scripts. It does not import the original repository and does not run
training episodes.

Examples:
  python sub-skills/on-policy-discrete/scripts/smoke_on_policy_discrete.py --algorithm all
  python sub-skills/on-policy-discrete/scripts/smoke_on_policy_discrete.py --algorithm ppo-lstm
"""

from __future__ import annotations

import argparse

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical


class ReinforcePolicy(nn.Module):
    def __init__(self, obs_dim: int = 4, action_dim: int = 2):
        super().__init__()
        self.fc1 = nn.Linear(obs_dim, 128)
        self.fc2 = nn.Linear(128, action_dim)
        self.data = []

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.softmax(self.fc2(F.relu(self.fc1(x))), dim=0)


def check_reinforce() -> None:
    policy = ReinforcePolicy()
    prob = policy(torch.zeros(4))
    assert tuple(prob.shape) == (2,)
    action = Categorical(prob).sample()
    policy.data.append((1.0, prob[action]))
    assert policy.data[0][1].requires_grad
    print("reinforce: ok")


class ActorCritic(nn.Module):
    def __init__(self, obs_dim: int = 4, action_dim: int = 2):
        super().__init__()
        self.fc1 = nn.Linear(obs_dim, 256)
        self.fc_pi = nn.Linear(256, action_dim)
        self.fc_v = nn.Linear(256, 1)

    def pi(self, x: torch.Tensor, softmax_dim: int = 0) -> torch.Tensor:
        return F.softmax(self.fc_pi(F.relu(self.fc1(x))), dim=softmax_dim)

    def v(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc_v(F.relu(self.fc1(x)))


def check_actor_critic() -> None:
    model = ActorCritic()
    one_prob = model.pi(torch.zeros(4))
    batch_prob = model.pi(torch.zeros(3, 4), softmax_dim=1)
    value = model.v(torch.zeros(3, 4))
    actions = torch.tensor([[0], [1], [0]])
    selected = batch_prob.gather(1, actions)
    td_target = torch.zeros(3, 1) + 0.98 * value.detach()
    loss = -torch.log(selected) * (td_target - value).detach() + F.smooth_l1_loss(value, td_target)
    assert tuple(one_prob.shape) == (2,)
    assert tuple(batch_prob.shape) == (3, 2)
    assert tuple(selected.shape) == (3, 1)
    assert loss.mean().ndim == 0
    print("actor-critic: ok")


def check_ppo() -> None:
    model = ActorCritic()
    s = torch.zeros(5, 4)
    a = torch.tensor([[0], [1], [0], [1], [0]])
    r = torch.ones(5, 1) / 100.0
    s_prime = torch.ones(5, 4) * 0.01
    done_mask = torch.ones(5, 1)
    old_prob_a = torch.full((5, 1), 0.5)
    td_target = r + 0.98 * model.v(s_prime) * done_mask
    delta = (td_target - model.v(s)).detach()
    advantage_values = []
    advantage = 0.0
    for delta_t in reversed(delta.numpy()):
        advantage = 0.98 * 0.95 * advantage + float(delta_t[0])
        advantage_values.append([advantage])
    advantage_values.reverse()
    advantage_t = torch.tensor(advantage_values, dtype=torch.float32)
    pi_a = model.pi(s, softmax_dim=1).gather(1, a)
    ratio = torch.exp(torch.log(pi_a) - torch.log(old_prob_a))
    clipped = torch.clamp(ratio, 1 - 0.1, 1 + 0.1) * advantage_t
    assert tuple(ratio.shape) == (5, 1)
    assert tuple(clipped.shape) == (5, 1)
    print("ppo: ok")


class PpoLstm(nn.Module):
    def __init__(self, obs_dim: int = 4, action_dim: int = 2):
        super().__init__()
        self.fc1 = nn.Linear(obs_dim, 64)
        self.lstm = nn.LSTM(64, 32)
        self.fc_pi = nn.Linear(32, action_dim)
        self.fc_v = nn.Linear(32, 1)

    def pi(self, x: torch.Tensor, hidden):
        x = F.relu(self.fc1(x)).view(-1, 1, 64)
        x, hidden_out = self.lstm(x, hidden)
        return F.softmax(self.fc_pi(x), dim=2), hidden_out

    def v(self, x: torch.Tensor, hidden):
        x = F.relu(self.fc1(x)).view(-1, 1, 64)
        x, _ = self.lstm(x, hidden)
        return self.fc_v(x)


def check_ppo_lstm() -> None:
    model = PpoLstm()
    hidden = (torch.zeros([1, 1, 32]), torch.zeros([1, 1, 32]))
    prob, hidden_out = model.pi(torch.zeros(4), hidden)
    value = model.v(torch.zeros(4), hidden)
    detached = (hidden_out[0].detach(), hidden_out[1].detach())
    assert tuple(prob.shape) == (1, 1, 2)
    assert tuple(value.shape) == (1, 1, 1)
    assert not detached[0].requires_grad
    print("ppo-lstm: ok")


def check_vtrace() -> None:
    model = ActorCritic()
    s = torch.zeros(4, 4)
    s_prime = torch.ones(4, 4) * 0.01
    a = torch.tensor([[0], [1], [0], [1]])
    r = torch.ones(4, 1) / 100.0
    done_mask = torch.ones(4, 1)
    mu_a = torch.full((4, 1), 0.5)
    with torch.no_grad():
        pi_a = model.pi(s, softmax_dim=1).gather(1, a)
        ratio = torch.exp(torch.log(pi_a) - torch.log(mu_a))
        rho = torch.minimum(torch.tensor(1.0), ratio)
        td_target = r + 0.98 * model.v(s_prime) * done_mask
        delta = rho * (td_target - model.v(s))
    assert tuple(rho.shape) == (4, 1)
    assert tuple(delta.shape) == (4, 1)
    print("vtrace: ok")


CHECKS = {
    "reinforce": check_reinforce,
    "actor-critic": check_actor_critic,
    "ppo": check_ppo,
    "ppo-lstm": check_ppo_lstm,
    "vtrace": check_vtrace,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run safe minimalRL on-policy discrete smoke checks.")
    parser.add_argument("--algorithm", choices=["all", *CHECKS.keys()], default="all")
    args = parser.parse_args()
    names = CHECKS.keys() if args.algorithm == "all" else [args.algorithm]
    for name in names:
        CHECKS[name]()


if __name__ == "__main__":
    main()
