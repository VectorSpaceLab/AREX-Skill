#!/usr/bin/env python3
"""Side-effect-free Actor/Critic shape smoke for the TD3 contract.

This deliberately reimplements only the network definitions from the source;
it never imports the repository's training or ROS environment modules.
"""

from __future__ import annotations

import argparse
import copy
import sys
from typing import Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


class Actor(nn.Module):
    """The source Actor: state -> 800 -> 600 -> action with tanh output."""

    def __init__(self, state_dim: int, action_dim: int) -> None:
        super().__init__()
        self.layer_1 = nn.Linear(state_dim, 800)
        self.layer_2 = nn.Linear(800, 600)
        self.layer_3 = nn.Linear(600, action_dim)
        self.tanh = nn.Tanh()

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        state = F.relu(self.layer_1(state))
        state = F.relu(self.layer_2(state))
        return self.tanh(self.layer_3(state))


class Critic(nn.Module):
    """The source twin critic, with two independent Q branches."""

    def __init__(self, state_dim: int, action_dim: int) -> None:
        super().__init__()
        self.layer_1 = nn.Linear(state_dim, 800)
        self.layer_2_s = nn.Linear(800, 600)
        self.layer_2_a = nn.Linear(action_dim, 600)
        self.layer_3 = nn.Linear(600, 1)

        self.layer_4 = nn.Linear(state_dim, 800)
        self.layer_5_s = nn.Linear(800, 600)
        self.layer_5_a = nn.Linear(action_dim, 600)
        self.layer_6 = nn.Linear(600, 1)

    def _q1(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        state_hidden = F.relu(self.layer_1(state))
        # The source discards both Linear call results and combines their
        # weights manually, using only the action projection bias. Keep that
        # forward shape/numerical convention without its .data side effects.
        state_projection = torch.mm(state_hidden, self.layer_2_s.weight.t())
        action_projection = torch.mm(action, self.layer_2_a.weight.t())
        hidden = F.relu(state_projection + action_projection + self.layer_2_a.bias)
        return self.layer_3(hidden)

    def _q2(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        state_hidden = F.relu(self.layer_4(state))
        hidden = F.relu(self.layer_5_s(state_hidden) + self.layer_5_a(action))
        return self.layer_6(hidden)

    def forward(
        self, state: torch.Tensor, action: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        return self._q1(state, action), self._q2(state, action)


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false")
    return torch.device(requested)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test TD3 Actor/Critic shapes without ROS or Gazebo."
    )
    parser.add_argument("--state-dim", type=int, default=24)
    parser.add_argument("--action-dim", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cpu")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--check-cuda",
        action="store_true",
        help="also run a one-batch CUDA check when CUDA is available",
    )
    return parser.parse_args()


def check_once(state_dim: int, action_dim: int, batch_size: int, device: torch.device) -> None:
    actor = Actor(state_dim, action_dim).to(device)
    critic = Critic(state_dim, action_dim).to(device)
    actor_target = copy.deepcopy(actor)
    critic_target = copy.deepcopy(critic)

    states = torch.randn(batch_size, state_dim, device=device)
    actions = actor(states)
    q1, q2 = critic(states, actions)

    assert actions.shape == (batch_size, action_dim), actions.shape
    assert q1.shape == (batch_size, 1), q1.shape
    assert q2.shape == (batch_size, 1), q2.shape
    assert torch.isfinite(actions).all()
    assert torch.isfinite(q1).all() and torch.isfinite(q2).all()
    assert float(actions.detach().min()) >= -1.000001
    assert float(actions.detach().max()) <= 1.000001

    for online, target in zip(actor.parameters(), actor_target.parameters()):
        assert torch.equal(online, target)
    for online, target in zip(critic.parameters(), critic_target.parameters()):
        assert torch.equal(online, target)

    # Prove that the shape contract supports a differentiable critic loss.
    loss = (q1.square().mean() + q2.square().mean())
    loss.backward()
    assert any(parameter.grad is not None for parameter in actor.parameters())
    assert any(parameter.grad is not None for parameter in critic.parameters())
    print(
        f"PASS device={device} state_shape={tuple(states.shape)} "
        f"action_shape={tuple(actions.shape)} q_shape={tuple(q1.shape)}"
    )


def main() -> int:
    args = parse_args()
    if min(args.state_dim, args.action_dim, args.batch_size) <= 0:
        raise SystemExit("dimensions and batch size must be positive")
    torch.manual_seed(args.seed)
    device = choose_device(args.device)
    check_once(args.state_dim, args.action_dim, args.batch_size, device)

    if args.check_cuda:
        if torch.cuda.is_available():
            try:
                check_once(args.state_dim, args.action_dim, args.batch_size, torch.device("cuda"))
            except RuntimeError as error:
                # CUDA can be visible but unavailable to this process (for
                # example, due to an external allocation). CPU verification
                # remains valid; make the optional probe explicit.
                print(f"SKIP CUDA check failed: {error}")
        else:
            print("SKIP CUDA unavailable")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, RuntimeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
