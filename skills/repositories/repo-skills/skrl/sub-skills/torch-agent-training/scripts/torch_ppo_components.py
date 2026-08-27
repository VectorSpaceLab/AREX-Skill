#!/usr/bin/env python3
"""Bounded public-component smoke for a small skrl Torch PPO composition.

This intentionally does not create a trainer, step an environment, train, export
memory, write TensorBoard data, or save checkpoints. It only checks public
component construction and one policy/value inference pass.
"""

from __future__ import annotations

import argparse

import gymnasium as gym
import torch
import torch.nn as nn

from skrl.agents.torch.ppo import PPO, PPO_CFG
from skrl.memories.torch import RandomMemory
from skrl.models.torch import DeterministicMixin, GaussianMixin, Model
from skrl import config


class PendulumPolicy(GaussianMixin, Model):
    """Small continuous stochastic policy matching Pendulum-v1."""

    def __init__(self, observation_space, state_space, action_space, device):
        Model.__init__(
            self,
            observation_space=observation_space,
            state_space=state_space,
            action_space=action_space,
            device=device,
        )
        GaussianMixin.__init__(self, clip_actions=True, clip_log_std=True)
        self.net = nn.Sequential(
            nn.Linear(self.num_observations, 16),
            nn.Tanh(),
            nn.Linear(16, self.num_actions),
            nn.Tanh(),
        )
        self.log_std_parameter = nn.Parameter(torch.zeros(self.num_actions))

    def compute(self, inputs, role=""):
        # Pendulum-v1 has an action interval of [-2, 2].
        return 2.0 * self.net(inputs["observations"]), {"log_std": self.log_std_parameter}


class PendulumValue(DeterministicMixin, Model):
    """Small deterministic value function for PPO."""

    def __init__(self, observation_space, state_space, action_space, device):
        Model.__init__(
            self,
            observation_space=observation_space,
            state_space=state_space,
            action_space=action_space,
            device=device,
        )
        DeterministicMixin.__init__(self)
        self.net = nn.Sequential(
            nn.Linear(self.num_observations, 16),
            nn.Tanh(),
            nn.Linear(16, 1),
        )

    def compute(self, inputs, role=""):
        return self.net(inputs["observations"]), {}


def build_component_smoke(device: str) -> dict[str, object]:
    """Build and exercise public Torch components without a training loop."""

    env = gym.make("Pendulum-v1")
    try:
        resolved = config.torch.parse_device(device)
        observation_space = env.observation_space
        state_space = observation_space
        action_space = env.action_space

        memory = RandomMemory(memory_size=4, num_envs=1, device=resolved)
        models = {
            "policy": PendulumPolicy(observation_space, state_space, action_space, resolved),
            "value": PendulumValue(observation_space, state_space, action_space, resolved),
        }
        cfg = PPO_CFG()
        cfg.rollouts = 4
        cfg.mini_batches = 1
        cfg.experiment.write_interval = 0
        cfg.experiment.checkpoint_interval = 0
        agent = PPO(
            models=models,
            memory=memory,
            cfg=cfg,
            observation_space=observation_space,
            state_space=state_space,
            action_space=action_space,
            device=resolved,
        )
        # init allocates agent-owned memory tensors but does not write artifacts
        # because both experiment intervals are disabled.
        agent.init()

        observation, _ = env.reset(seed=0)
        observations = torch.as_tensor(observation, dtype=torch.float32, device=resolved).unsqueeze(0)
        states = observations.clone()
        with torch.no_grad():
            actions, outputs = agent.act(observations, states, timestep=0, timesteps=4)
            values, _ = models["value"].act({"observations": observations, "states": states}, role="value")

        expected_action_shape = (1, action_space.shape[0])
        if tuple(actions.shape) != expected_action_shape:
            raise AssertionError(f"unexpected action shape: {tuple(actions.shape)}")
        if tuple(values.shape) != (1, 1):
            raise AssertionError(f"unexpected value shape: {tuple(values.shape)}")
        if "log_prob" not in outputs:
            raise AssertionError("policy output did not contain log_prob")

        return {
            "resolved_device": str(resolved),
            "memory_tensors": memory.get_tensor_names(),
            "action_shape": tuple(actions.shape),
            "value_shape": tuple(values.shape),
        }
    finally:
        env.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test public skrl Torch PPO components without training")
    parser.add_argument(
        "--device",
        default="cpu",
        help="Torch device passed through config.torch.parse_device (default: cpu)",
    )
    args = parser.parse_args()
    result = build_component_smoke(args.device)
    print("Torch PPO component smoke passed")
    for key, value in result.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
