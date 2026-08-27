#!/usr/bin/env python3
"""Construct and initialize a tiny public JAX PPO stack without training.

This is a bounded adaptation of the public Gymnasium Pendulum PPO construction
pattern. It uses the installed public package APIs only, performs no source
checkout import, network access, training/evaluation loop, checkpoint write, or
persistent output. The ``--backend`` flag records the example-level NumPy/JAX
choice; skrl's JAX model initialization still uses native JAX arrays.
"""

from __future__ import annotations

import argparse

import flax.linen as nn
import gymnasium as gym
import jax
import jax.numpy as jnp

from skrl import config
from skrl.agents.jax.ppo import PPO, PPO_CFG
from skrl.envs.wrappers.jax import wrap_env
from skrl.memories.jax import RandomMemory
from skrl.models.jax import DeterministicMixin, GaussianMixin, Model
from skrl.trainers.jax import SequentialTrainer
from skrl.utils import set_seed


class Policy(GaussianMixin, Model):
    """Small Flax Gaussian policy matching the Pendulum example contract."""

    def __init__(
        self,
        observation_space,
        state_space,
        action_space,
        device,
        clip_actions: bool = False,
        clip_log_std: bool = True,
        min_log_std: float = -20,
        max_log_std: float = 2,
        reduction: str = "sum",
        **kwargs,
    ):
        Model.__init__(
            self,
            observation_space=observation_space,
            state_space=state_space,
            action_space=action_space,
            device=device,
            **kwargs,
        )
        GaussianMixin.__init__(
            self,
            clip_actions=clip_actions,
            clip_log_std=clip_log_std,
            min_log_std=min_log_std,
            max_log_std=max_log_std,
            reduction=reduction,
        )

    @nn.compact
    def __call__(self, inputs, role):
        x = nn.relu(nn.Dense(16)(inputs["observations"]))
        x = nn.relu(nn.Dense(16)(x))
        x = nn.Dense(self.num_actions)(x)
        log_std = self.param("log_std", lambda _: jnp.zeros(self.num_actions))
        return 2.0 * nn.tanh(x), {"log_std": log_std}


class Value(DeterministicMixin, Model):
    """Small Flax deterministic value model matching PPO's value role."""

    def __init__(self, observation_space, state_space, action_space, device, **kwargs):
        Model.__init__(
            self,
            observation_space=observation_space,
            state_space=state_space,
            action_space=action_space,
            device=device,
            **kwargs,
        )
        DeterministicMixin.__init__(self)

    @nn.compact
    def __call__(self, inputs, role):
        x = nn.relu(nn.Dense(16)(inputs["observations"]))
        x = nn.relu(nn.Dense(16)(x))
        return nn.Dense(1)(x), {}


def _latest_pendulum_id() -> str:
    versions = [spec for spec in gym.envs.registry if spec.startswith("Pendulum-v")]
    if not versions:
        raise RuntimeError("Gymnasium does not provide a Pendulum-v environment")
    return versions[-1]


def build_components(num_envs: int, backend: str, seed: int, device: str):
    """Build, initialize, and shape-check the components; never train."""
    config.jax.backend = backend  # retained for parity with maintained examples
    config.jax.device = device
    set_seed(seed)

    env_id = _latest_pendulum_id()
    if num_envs == 1:
        raw_env = gym.make(env_id)
    else:
        raw_env = gym.make_vec(
            env_id,
            num_envs=num_envs,
            vectorization_mode="sync",
        )
    env = wrap_env(raw_env)

    try:
        device_obj = env.device
        observations, _ = env.reset()
        states = env.state()

        models = {
            "policy": Policy(
                env.observation_space,
                env.state_space,
                env.action_space,
                device_obj,
            ),
            "value": Value(
                env.observation_space,
                env.state_space,
                env.action_space,
                device_obj,
            ),
        }
        for role, model in models.items():
            model.init_state_dict(role=role)
            if not hasattr(model, "state_dict"):
                raise AssertionError(f"JAX model '{role}' has no state_dict after initialization")

        policy_actions, policy_outputs = models["policy"].act(
            {"observations": observations, "states": states}, role="policy"
        )
        values, _ = models["value"].act(
            {"observations": observations, "states": states}, role="value"
        )
        if policy_actions.shape[0] != num_envs or values.shape != (num_envs, 1):
            raise AssertionError(
                f"unexpected model shapes: actions={policy_actions.shape}, values={values.shape}"
            )
        if "log_prob" not in policy_outputs or "log_std" not in policy_outputs:
            raise AssertionError("Gaussian policy did not produce log_prob/log_std outputs")

        memory = RandomMemory(
            memory_size=4,
            num_envs=env.num_envs,
            device=device_obj,
        )
        cfg = PPO_CFG()
        cfg.rollouts = 4
        cfg.learning_epochs = 1
        cfg.mini_batches = 1
        cfg.experiment.write_interval = 0
        cfg.experiment.checkpoint_interval = 0

        agent = PPO(
            models=models,
            memory=memory,
            cfg=cfg,
            observation_space=env.observation_space,
            state_space=env.state_space,
            action_space=env.action_space,
            device=device_obj,
        )
        # Trainer construction initializes agent-owned memory tensors and JIT
        # apply functions, but no train/eval method is called here.
        trainer = SequentialTrainer(
            cfg={
                "timesteps": 1,
                "headless": True,
                "disable_progressbar": True,
                "close_environment_at_exit": False,
            },
            env=env,
            agents=agent,
        )
        expected = {
            "observations",
            "actions",
            "log_prob",
            "values",
            "returns",
            "advantages",
        }
        if env.state_space is not None:
            expected.add("states")
        missing = expected.difference(memory.get_tensor_names())
        if missing:
            raise AssertionError(f"PPO initialization did not create tensors: {sorted(missing)}")

        return {
            "backend_marker": backend,
            "jax_backend": jax.default_backend(),
            "device": str(device_obj),
            "num_envs": env.num_envs,
            "policy_shape": tuple(policy_actions.shape),
            "value_shape": tuple(values.shape),
            "memory_tensors": memory.get_tensor_names(),
            "trainer": type(trainer).__name__,
        }
    finally:
        env.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build/init a bounded CPU JAX PPO component stack; never train or write outputs."
    )
    parser.add_argument(
        "--backend",
        choices=("numpy", "jax"),
        default="numpy",
        help="Example-level backend marker; model initialization remains native JAX.",
    )
    parser.add_argument("--num-envs", type=int, default=1, help="Number of synchronous Pendulum environments.")
    parser.add_argument("--seed", type=int, default=42, help="Seed used for the bounded construction check.")
    parser.add_argument(
        "--device",
        default="cpu",
        help="JAX device specification passed to skrl (default: cpu).",
    )
    args = parser.parse_args()
    if args.num_envs < 1:
        parser.error("--num-envs must be at least 1")

    result = build_components(args.num_envs, args.backend, args.seed, args.device)
    print("JAX PPO component smoke passed")
    for key, value in result.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
