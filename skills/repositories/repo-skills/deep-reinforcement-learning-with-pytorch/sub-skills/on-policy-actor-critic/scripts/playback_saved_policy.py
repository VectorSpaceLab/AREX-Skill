"""Bounded playback helper for saved on-policy policy pickles.

This helper is meant for the REINFORCE / actor-critic family that saves full
``torch.save(model, path)`` pickles. It keeps evaluation bounded and avoids any
training loop.

It intentionally does not load bare PPO ``state_dict`` checkpoints. For those,
recreate the actor / critic classes first and load the weights manually.
"""

from pathlib import Path
import argparse

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical


class Policy(nn.Module):
    """Compatibility wrapper for the source repo's pickled policy objects."""

    def __init__(self):
        super().__init__()

    def forward(self, x):
        if hasattr(self, "affine1") and hasattr(self, "affine2"):
            x = F.relu(self.affine1(x))
            logits = self.affine2(x)
            if logits.shape[-1] == 1:
                raise RuntimeError("Loaded a scalar head; playback expects a policy.")
            return F.softmax(logits, dim=1)

        if hasattr(self, "linear1") and hasattr(self, "linear2"):
            x = F.relu(self.linear1(x))
            logits = self.linear2(x)
            if logits.shape[-1] == 1:
                raise RuntimeError("Loaded a scalar head; playback expects a policy.")
            return F.softmax(logits, dim=1)

        if hasattr(self, "fc1") and hasattr(self, "fc3"):
            x = F.relu(self.fc1(x))
            logits = self.fc3(x)
            if logits.shape[-1] == 1:
                raise RuntimeError("Loaded a scalar head; playback expects a policy.")
            return F.softmax(logits, dim=1)

        if hasattr(self, "fc1") and hasattr(self, "action_head") and hasattr(self, "value_head"):
            x = F.relu(self.fc1(x))
            action_scores = self.action_head(x)
            value = self.value_head(x)
            return F.softmax(action_scores, dim=-1), value

        raise RuntimeError(
            "Unsupported pickled policy layout; this helper covers the repo's "
            "REINFORCE and actor-critic pickles."
        )


class Module(Policy):
    """Alias used by the MountainCar actor-critic pickle layout."""

    pass


def _reset_env(env, seed=None):
    if seed is not None:
        try:
            result = env.reset(seed=seed)
        except TypeError:
            if hasattr(env, "seed"):
                env.seed(seed)
            result = env.reset()
    else:
        result = env.reset()

    if isinstance(result, tuple) and len(result) == 2:
        obs, _info = result
        return obs
    return result


def _step_env(env, action):
    result = env.step(action)
    if len(result) == 5:
        obs, reward, terminated, truncated, info = result
        done = bool(terminated or truncated)
        return obs, reward, done, info

    obs, reward, done, info = result
    return obs, reward, done, info


def _choose_device(kind):
    if kind == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(kind)


def _load_policy(checkpoint, device):
    try:
        policy = torch.load(checkpoint, map_location=device, weights_only=False)
    except TypeError:
        policy = torch.load(checkpoint, map_location=device)

    if isinstance(policy, dict):
        raise TypeError(
            "Checkpoint looks like a bare state_dict. Recreate the matching "
            "model class and load weights manually instead of using the playback helper."
        )

    if hasattr(policy, "to"):
        policy = policy.to(device)
    if hasattr(policy, "eval"):
        policy.eval()
    return policy


def _sample_action(policy, state, device):
    state_tensor = torch.as_tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
    with torch.no_grad():
        output = policy(state_tensor)

    if isinstance(output, (tuple, list)):
        output = output[0]

    if output.ndim == 2 and output.shape[0] == 1:
        output = output.squeeze(0)

    if output.ndim != 1:
        raise RuntimeError(
            "Playback helper expected a 1D policy output after squeezing. "
            "This usually means the checkpoint is not a discrete policy module."
        )

    if output.numel() == 1:
        raise RuntimeError(
            "Loaded a scalar output; this looks like a value network, not a policy."
        )

    if output.ge(0).all().item() and abs(output.sum().item() - 1.0) < 1e-3:
        dist = Categorical(probs=output)
    else:
        dist = Categorical(logits=output)

    return dist.sample().item()


def _play_episode(env, policy, device, max_steps, render, seed=None):
    state = _reset_env(env, seed=seed)
    total_reward = 0.0
    for step in range(max_steps):
        action = _sample_action(policy, state, device)
        state, reward, done, _info = _step_env(env, action)
        if render:
            env.render()
        total_reward += reward
        if done:
            return total_reward, step + 1
    return total_reward, max_steps


def build_parser():
    parser = argparse.ArgumentParser(description="Play back a saved on-policy policy pickle")
    parser.add_argument(
        "--checkpoint",
        type=Path,
        required=True,
        help="Path to a torch.save(model, path) checkpoint.",
    )
    parser.add_argument(
        "--env-id",
        default="MountainCar-v0",
        help="Gym environment id for the policy playback.",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=1,
        help="Number of evaluation episodes to run.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=10000,
        help="Hard step limit per episode.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional seed passed to the environment reset.",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Render the environment while the policy acts.",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="cpu",
        help="Device used to evaluate the policy (default: cpu).",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    import gym

    device = _choose_device(args.device)
    env = gym.make(args.env_id)
    try:
        if not hasattr(env.action_space, "n"):
            raise TypeError(
                "This helper only handles discrete action spaces from the REINFORCE / actor-critic family."
            )

        policy = _load_policy(args.checkpoint, device)

        for episode in range(args.episodes):
            episode_seed = None if args.seed is None else args.seed + episode
            total_reward, steps = _play_episode(
                env,
                policy,
                device,
                max_steps=args.max_steps,
                render=args.render,
                seed=episode_seed,
            )
            print(
                f"episode={episode + 1} steps={steps} reward={total_reward:.3f} "
                f"env={args.env_id} checkpoint={args.checkpoint}"
            )
    finally:
        env.close()


if __name__ == "__main__":
    main()
