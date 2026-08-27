#!/usr/bin/env python3
"""Deterministic CPU smoke check for core model components.

The script imports the installed package, creates a small vector-observation
Policy with a Discrete action space, calls Policy.act, constructs RolloutStorage,
computes returns, and prints a PASS line. It does not create Gym environments,
download data, train, or require simulator assets.
"""

from __future__ import annotations

import math
import sys

import torch

try:  # Prefer Gym because this repository depends on Gym spaces.
    from gym import spaces
except Exception:  # pragma: no cover - optional compatibility fallback
    try:
        from gymnasium import spaces  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Install gym or gymnasium to provide action spaces") from exc

from a2c_ppo_acktr.model import Policy
from a2c_ppo_acktr.storage import RolloutStorage


def assert_shape(name: str, tensor: torch.Tensor, expected: tuple[int, ...]) -> None:
    actual = tuple(tensor.shape)
    if actual != expected:
        raise AssertionError(f"{name} shape {actual} != expected {expected}")


def main() -> int:
    torch.manual_seed(0)
    device = torch.device("cpu")

    obs_shape = (4,)
    action_space = spaces.Discrete(2)

    policy = Policy(obs_shape, action_space).to(device)
    policy.eval()

    obs = torch.zeros(1, *obs_shape, device=device)
    rnn_hxs = torch.zeros(1, policy.recurrent_hidden_state_size, device=device)
    masks = torch.ones(1, 1, device=device)

    with torch.no_grad():
        value, action, action_log_prob, next_hxs = policy.act(
            obs, rnn_hxs, masks, deterministic=True
        )

    assert_shape("value", value, (1, 1))
    assert_shape("action", action, (1, 1))
    assert action.dtype == torch.long, f"Discrete action dtype {action.dtype} is not long"
    assert_shape("action_log_prob", action_log_prob, (1, 1))
    assert_shape("next_hxs", next_hxs, (1, policy.recurrent_hidden_state_size))

    num_steps = 3
    num_processes = 1
    rollouts = RolloutStorage(
        num_steps,
        num_processes,
        obs_shape,
        action_space,
        policy.recurrent_hidden_state_size,
    )
    rollouts.to(device)
    rollouts.obs[0].copy_(obs)

    for step in range(num_steps):
        step_obs = torch.full((num_processes, *obs_shape), float(step + 1), device=device)
        reward = torch.full((num_processes, 1), 0.25 * (step + 1), device=device)
        masks = torch.ones(num_processes, 1, device=device)
        bad_masks = torch.ones(num_processes, 1, device=device)
        with torch.no_grad():
            value, action, action_log_prob, next_hxs = policy.act(
                rollouts.obs[step], rollouts.recurrent_hidden_states[step], rollouts.masks[step], deterministic=True
            )
        rollouts.insert(step_obs, next_hxs, action, action_log_prob, value, reward, masks, bad_masks)

    next_value = torch.zeros(num_processes, 1, device=device)
    rollouts.compute_returns(
        next_value,
        use_gae=False,
        gamma=0.99,
        gae_lambda=0.95,
        use_proper_time_limits=True,
    )

    assert_shape("returns", rollouts.returns, (num_steps + 1, num_processes, 1))
    if not torch.isfinite(rollouts.returns).all():
        raise AssertionError("rollout returns contain non-finite values")

    expected_return0 = 0.25 + 0.99 * 0.50 + (0.99 ** 2) * 0.75
    actual_return0 = float(rollouts.returns[0, 0, 0].item())
    if not math.isclose(actual_return0, expected_return0, rel_tol=1e-5, abs_tol=1e-5):
        raise AssertionError(
            f"unexpected first return {actual_return0:.6f}; expected {expected_return0:.6f}"
        )

    print("PASS model-components smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
