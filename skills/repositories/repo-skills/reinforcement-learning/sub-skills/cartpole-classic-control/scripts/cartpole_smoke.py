#!/usr/bin/env python3
"""Headless CartPole DQN/A2C/PPO smoke checks.

This standalone script distills the repository's CartPole model and update
contracts into safe synthetic checks. It does not import Gymnasium, create a
Pygame window, run CartPole training, or require the original checkout.
"""

from __future__ import annotations

import argparse
import os
import platform
import random
import sys
from collections import deque
from collections.abc import Mapping
from typing import Any

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
except Exception as exc:  # pragma: no cover - exercised only on missing deps
    print(
        "ERROR: cartpole_smoke.py requires PyTorch for model/update checks. "
        "Install the repository runtime dependencies, then retry.\n"
        f"Original import error: {exc}",
        file=sys.stderr,
    )
    raise SystemExit(2)


STATE_SIZE = 4
ACTION_SIZE = 2


# ---------------------------------------------------------------------------
# DQN: same architecture and update contract as the CartPole DQN workflow.
# ---------------------------------------------------------------------------


class QNetwork(nn.Module):
    def __init__(self, state_size: int = STATE_SIZE, action_size: int = ACTION_SIZE):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_size, 24),
            nn.ReLU(),
            nn.Linear(24, 24),
            nn.ReLU(),
            nn.Linear(24, action_size),
        )
        for module in self.net:
            if isinstance(module, nn.Linear):
                nn.init.kaiming_uniform_(module.weight, nonlinearity="relu")
                nn.init.zeros_(module.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class DQNAgent:
    def __init__(self, state_size: int = STATE_SIZE, action_size: int = ACTION_SIZE):
        self.state_size = state_size
        self.action_size = action_size
        self.discount_factor = 0.99
        self.learning_rate = 1e-3
        self.epsilon = 1.0
        self.epsilon_decay = 0.999
        self.epsilon_min = 0.01
        self.batch_size = 64
        self.train_start = 1000
        self.memory: deque[tuple[np.ndarray, int, float, np.ndarray, bool]] = deque(maxlen=2000)
        self.model = QNetwork(state_size, action_size)
        self.target_model = QNetwork(state_size, action_size)
        self.update_target_model()
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.loss_fn = nn.MSELoss()

    def update_target_model(self) -> None:
        self.target_model.load_state_dict(self.model.state_dict())

    def get_action(self, state: np.ndarray) -> int:
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        with torch.no_grad():
            q_values = self.model(torch.as_tensor(state, dtype=torch.float32))
        return int(torch.argmax(q_values).item())

    def append_sample(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ) -> None:
        self.memory.append((state, action, reward, next_state, done))
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def train_model(self) -> bool:
        if len(self.memory) < self.train_start:
            return False
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states_t = torch.as_tensor(np.array(states), dtype=torch.float32)
        actions_t = torch.as_tensor(actions, dtype=torch.long)
        rewards_t = torch.as_tensor(rewards, dtype=torch.float32)
        next_states_t = torch.as_tensor(np.array(next_states), dtype=torch.float32)
        dones_t = torch.as_tensor(dones, dtype=torch.float32)

        q_pred = self.model(states_t).gather(1, actions_t.unsqueeze(1)).squeeze(1)
        with torch.no_grad():
            q_next = self.target_model(next_states_t).max(dim=1).values
            target = rewards_t + (1.0 - dones_t) * self.discount_factor * q_next

        loss = self.loss_fn(q_pred, target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        return True


# ---------------------------------------------------------------------------
# A2C: same actor/critic architecture and one-step TD update contract.
# ---------------------------------------------------------------------------


class Actor(nn.Module):
    def __init__(self, state_size: int = STATE_SIZE, action_size: int = ACTION_SIZE):
        super().__init__()
        self.fc1 = nn.Linear(state_size, 24)
        self.fc2 = nn.Linear(24, action_size)
        nn.init.kaiming_uniform_(self.fc1.weight, nonlinearity="relu")
        nn.init.kaiming_uniform_(self.fc2.weight, nonlinearity="relu")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc2(torch.relu(self.fc1(x)))


class Critic(nn.Module):
    def __init__(self, state_size: int = STATE_SIZE):
        super().__init__()
        self.fc1 = nn.Linear(state_size, 24)
        self.fc2 = nn.Linear(24, 1)
        nn.init.kaiming_uniform_(self.fc1.weight, nonlinearity="relu")
        nn.init.kaiming_uniform_(self.fc2.weight, nonlinearity="relu")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc2(torch.relu(self.fc1(x))).squeeze(-1)


class A2CAgent:
    def __init__(self, state_size: int = STATE_SIZE, action_size: int = ACTION_SIZE):
        self.state_size = state_size
        self.action_size = action_size
        self.discount_factor = 0.99
        self.actor_lr = 1e-3
        self.critic_lr = 5e-3
        self.actor = Actor(state_size, action_size)
        self.critic = Critic(state_size)
        self.actor_opt = optim.Adam(self.actor.parameters(), lr=self.actor_lr)
        self.critic_opt = optim.Adam(self.critic.parameters(), lr=self.critic_lr)

    def get_action(self, state: np.ndarray) -> int:
        with torch.no_grad():
            logits = self.actor(torch.as_tensor(state, dtype=torch.float32))
            probs = torch.softmax(logits, dim=-1).numpy()
        return int(np.random.choice(self.action_size, p=probs))

    def train_model(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ) -> None:
        state_t = torch.as_tensor(state, dtype=torch.float32)
        next_state_t = torch.as_tensor(next_state, dtype=torch.float32)
        value = self.critic(state_t)
        with torch.no_grad():
            next_value = self.critic(next_state_t)
            target = torch.tensor(float(reward)) if done else reward + self.discount_factor * next_value
        advantage = (target - value).detach()

        logits = self.actor(state_t)
        log_probs = torch.log_softmax(logits, dim=-1)
        actor_loss = -log_probs[action] * advantage
        critic_loss = (value - target).pow(2)

        self.actor_opt.zero_grad()
        actor_loss.backward()
        self.actor_opt.step()

        self.critic_opt.zero_grad()
        critic_loss.backward()
        self.critic_opt.step()


# ---------------------------------------------------------------------------
# PPO: same actor-critic architecture and GAE/clipped-surrogate ingredients.
# ---------------------------------------------------------------------------


PPO_ROLLOUT_STEPS = 1024
PPO_EPOCHS = 4
PPO_MINIBATCH_SIZE = 64
PPO_CLIP_COEF = 0.2
PPO_GAMMA = 0.99
PPO_GAE_LAMBDA = 0.95
PPO_LR = 3e-4
PPO_VALUE_COEF = 0.5
PPO_ENTROPY_COEF = 0.01


def _ortho(layer: nn.Linear, gain: float) -> nn.Linear:
    nn.init.orthogonal_(layer.weight, gain)
    nn.init.zeros_(layer.bias)
    return layer


class ActorCritic(nn.Module):
    def __init__(self, state_size: int = STATE_SIZE, action_size: int = ACTION_SIZE):
        super().__init__()
        self.shared = nn.Sequential(
            _ortho(nn.Linear(state_size, 64), gain=2**0.5),
            nn.Tanh(),
            _ortho(nn.Linear(64, 64), gain=2**0.5),
            nn.Tanh(),
        )
        self.policy = _ortho(nn.Linear(64, action_size), gain=0.01)
        self.value = _ortho(nn.Linear(64, 1), gain=1.0)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        hidden = self.shared(x)
        return self.policy(hidden), self.value(hidden).squeeze(-1)


def compute_gae(
    rewards: np.ndarray,
    values: np.ndarray,
    dones: np.ndarray,
    last_value: float,
) -> tuple[np.ndarray, np.ndarray]:
    advantages = np.zeros_like(rewards, dtype=np.float32)
    gae = 0.0
    for t in reversed(range(len(rewards))):
        next_v = last_value if t == len(rewards) - 1 else values[t + 1]
        next_nonterminal = 1.0 - dones[t]
        delta = rewards[t] + PPO_GAMMA * next_v * next_nonterminal - values[t]
        gae = delta + PPO_GAMMA * PPO_GAE_LAMBDA * next_nonterminal * gae
        advantages[t] = gae
    returns = advantages + values
    return advantages, returns


# ---------------------------------------------------------------------------
# Generic assertions and diagnostics.
# ---------------------------------------------------------------------------


def _clone_params(module: nn.Module) -> dict[str, torch.Tensor]:
    return {name: tensor.detach().clone() for name, tensor in module.state_dict().items()}


def _any_param_changed(before: Mapping[str, torch.Tensor], after: Mapping[str, torch.Tensor]) -> bool:
    for name, old_value in before.items():
        new_value = after[name]
        if torch.is_floating_point(old_value) and not torch.allclose(old_value, new_value):
            return True
    return False


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _all_finite_tensors(state_dict: Mapping[str, torch.Tensor]) -> bool:
    return all(torch.isfinite(value).all().item() for value in state_dict.values() if torch.is_tensor(value))


def smoke_dqn() -> str:
    agent = DQNAgent()
    agent.train_start = 8
    agent.batch_size = 8

    state = np.array([0.0, 0.02, -0.01, 0.03], dtype=np.float32)
    q_values = agent.model(torch.as_tensor(state, dtype=torch.float32))
    _assert(tuple(q_values.shape) == (ACTION_SIZE,), f"DQN Q shape mismatch: {tuple(q_values.shape)}")

    for i in range(8):
        s = np.array([i / 10.0, 0.01 * i, -0.02 * i, 0.03], dtype=np.float32)
        ns = s + np.array([0.01, -0.01, 0.02, -0.02], dtype=np.float32)
        done = i == 7
        reward = 0.1 if not done else -1.0
        agent.append_sample(s, i % ACTION_SIZE, reward, ns, done)

    before = _clone_params(agent.model)
    trained = agent.train_model()
    after = agent.model.state_dict()
    _assert(trained, "DQN synthetic replay did not reach train_start")
    _assert(_any_param_changed(before, after), "DQN SGD step did not change model parameters")
    _assert(agent.epsilon < 1.0, "DQN epsilon did not decay after append_sample")

    agent.update_target_model()
    for key, value in agent.model.state_dict().items():
        _assert(torch.allclose(value, agent.target_model.state_dict()[key]), f"DQN target copy mismatch at {key}")

    return "DQN: Q shape, replay update, epsilon decay, and target copy OK"


def smoke_a2c() -> str:
    agent = A2CAgent()
    state = np.array([0.03, -0.01, 0.02, 0.0], dtype=np.float32)
    next_state = np.array([0.04, -0.02, 0.01, 0.01], dtype=np.float32)

    logits = agent.actor(torch.as_tensor(state, dtype=torch.float32))
    value = agent.critic(torch.as_tensor(state, dtype=torch.float32))
    probs = torch.softmax(logits, dim=-1)
    _assert(tuple(logits.shape) == (ACTION_SIZE,), f"A2C actor logits shape mismatch: {tuple(logits.shape)}")
    _assert(value.ndim == 0, f"A2C critic value should be scalar, got ndim={value.ndim}")
    _assert(torch.isfinite(probs).all().item() and torch.allclose(probs.sum(), torch.tensor(1.0), atol=1e-5), "A2C action probabilities invalid")

    actor_before = _clone_params(agent.actor)
    critic_before = _clone_params(agent.critic)
    agent.train_model(state, action=1, reward=0.1, next_state=next_state, done=False)
    _assert(_any_param_changed(actor_before, agent.actor.state_dict()), "A2C actor update did not change parameters")
    _assert(_any_param_changed(critic_before, agent.critic.state_dict()), "A2C critic update did not change parameters")
    _assert(_all_finite_tensors(agent.actor.state_dict()), "A2C actor contains non-finite parameters")
    _assert(_all_finite_tensors(agent.critic.state_dict()), "A2C critic contains non-finite parameters")

    return "A2C: actor/critic shapes, probabilities, and one-step update OK"


def smoke_ppo() -> str:
    model = ActorCritic()
    optimizer = optim.Adam(model.parameters(), lr=PPO_LR)

    obs = torch.as_tensor(
        np.array(
            [
                [0.00, 0.01, 0.02, 0.03],
                [0.03, 0.02, 0.01, 0.00],
                [0.04, -0.01, 0.01, -0.03],
                [-0.02, 0.02, -0.01, 0.01],
                [0.01, 0.00, 0.03, -0.02],
                [0.02, -0.03, 0.00, 0.04],
                [-0.04, 0.01, -0.02, 0.02],
                [0.05, -0.02, 0.01, -0.01],
            ],
            dtype=np.float32,
        )
    )
    actions = torch.as_tensor([0, 1, 0, 1, 1, 0, 1, 0], dtype=torch.long)

    logits, values = model(obs)
    _assert(tuple(logits.shape) == (8, ACTION_SIZE), f"PPO logits shape mismatch: {tuple(logits.shape)}")
    _assert(tuple(values.shape) == (8,), f"PPO values shape mismatch: {tuple(values.shape)}")

    dist = torch.distributions.Categorical(logits=logits.detach())
    old_logp = dist.log_prob(actions)

    rewards = np.array([0.1, 0.1, -1.0, 0.1, 0.1, 0.1, -1.0, 0.1], dtype=np.float32)
    dones = np.array([0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0], dtype=np.float32)
    advantages, returns = compute_gae(rewards, values.detach().numpy(), dones, last_value=0.25)
    _assert(advantages.shape == rewards.shape, "PPO GAE advantages shape mismatch")
    _assert(returns.shape == rewards.shape, "PPO GAE returns shape mismatch")
    _assert(np.isfinite(advantages).all() and np.isfinite(returns).all(), "PPO GAE produced non-finite values")

    adv_t = torch.as_tensor((advantages - advantages.mean()) / (advantages.std() + 1e-8), dtype=torch.float32)
    ret_t = torch.as_tensor(returns, dtype=torch.float32)

    before = _clone_params(model)
    new_logits, new_values = model(obs)
    new_dist = torch.distributions.Categorical(logits=new_logits)
    new_logp = new_dist.log_prob(actions)
    entropy = new_dist.entropy().mean()
    ratio = (new_logp - old_logp).exp()
    unclipped = ratio * adv_t
    clipped = torch.clamp(ratio, 1 - PPO_CLIP_COEF, 1 + PPO_CLIP_COEF) * adv_t
    policy_loss = -torch.min(unclipped, clipped).mean()
    value_loss = (new_values - ret_t).pow(2).mean()
    loss = policy_loss + PPO_VALUE_COEF * value_loss - PPO_ENTROPY_COEF * entropy
    _assert(torch.isfinite(loss).item(), "PPO synthetic loss is not finite")

    optimizer.zero_grad()
    loss.backward()
    nn.utils.clip_grad_norm_(model.parameters(), 0.5)
    optimizer.step()
    _assert(_any_param_changed(before, model.state_dict()), "PPO clipped-surrogate update did not change parameters")

    return "PPO: actor-critic shapes, finite GAE, and clipped update OK"


# ---------------------------------------------------------------------------
# Checkpoint validation.
# ---------------------------------------------------------------------------


def _is_plain_state_dict(obj: Any) -> bool:
    return isinstance(obj, Mapping) and bool(obj) and all(isinstance(k, str) and torch.is_tensor(v) for k, v in obj.items())


def validate_checkpoint_object(algorithm: str, obj: Any) -> tuple[bool, str]:
    """Validate an already-loaded checkpoint payload for one CartPole algorithm."""
    algorithm = algorithm.lower()
    if algorithm == "dqn":
        if isinstance(obj, Mapping) and ("actor" in obj or "critic" in obj):
            return False, "DQN expects a raw QNetwork state_dict, but this looks like an A2C actor/critic checkpoint."
        if not _is_plain_state_dict(obj):
            return False, "DQN expects a non-empty mapping of parameter names to tensors."
        model = QNetwork()
    elif algorithm == "ppo":
        if isinstance(obj, Mapping) and ("actor" in obj or "critic" in obj):
            return False, "PPO expects a raw ActorCritic state_dict, but this looks like an A2C actor/critic checkpoint."
        if not _is_plain_state_dict(obj):
            return False, "PPO expects a non-empty mapping of parameter names to tensors."
        model = ActorCritic()
    elif algorithm == "a2c":
        if not isinstance(obj, Mapping):
            return False, "A2C expects a dictionary with top-level 'actor' and 'critic' entries."
        if "actor" not in obj or "critic" not in obj:
            return False, "A2C checkpoint must contain both top-level 'actor' and 'critic' state_dicts."
        if not _is_plain_state_dict(obj["actor"]) or not _is_plain_state_dict(obj["critic"]):
            return False, "A2C 'actor' and 'critic' entries must each be plain state_dict mappings."
        try:
            Actor().load_state_dict(obj["actor"], strict=True)
            Critic().load_state_dict(obj["critic"], strict=True)
        except RuntimeError as exc:
            return False, f"A2C state_dict keys or tensor shapes do not match the CartPole Actor/Critic: {exc}"
        return True, "A2C checkpoint structure matches nested actor/critic state_dicts."
    else:  # pragma: no cover - argparse prevents this
        return False, f"Unknown algorithm: {algorithm}"

    try:
        model.load_state_dict(obj, strict=True)
    except RuntimeError as exc:
        return False, f"{algorithm.upper()} state_dict keys or tensor shapes do not match the expected CartPole model: {exc}"
    return True, f"{algorithm.upper()} checkpoint structure matches the expected raw state_dict."


def load_checkpoint(path: str) -> Any:
    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    except TypeError:  # Older PyTorch has no weights_only argument.
        return torch.load(path, map_location="cpu")


def smoke_checkpoint_mismatches() -> str:
    dqn_payload = QNetwork().state_dict()
    a2c_payload = {"actor": Actor().state_dict(), "critic": Critic().state_dict()}
    ppo_payload = ActorCritic().state_dict()

    expected = [
        ("dqn", dqn_payload, True),
        ("a2c", a2c_payload, True),
        ("ppo", ppo_payload, True),
        ("dqn", a2c_payload, False),
        ("a2c", dqn_payload, False),
        ("ppo", a2c_payload, False),
        ("ppo", dqn_payload, False),
    ]
    for algorithm, payload, should_pass in expected:
        ok, message = validate_checkpoint_object(algorithm, payload)
        _assert(ok is should_pass, f"Checkpoint validator expectation failed for {algorithm}: {message}")

    return "Checkpoint validators: correct formats accepted and representative mismatches rejected"


# ---------------------------------------------------------------------------
# Render/headless diagnostics.
# ---------------------------------------------------------------------------


def render_readiness() -> tuple[bool, str]:
    """Return whether human rendering is likely available without opening a window."""
    sdl_driver = os.environ.get("SDL_VIDEODRIVER", "").strip().lower()
    if sdl_driver in {"dummy", "offscreen"}:
        return (
            False,
            f"SDL_VIDEODRIVER={sdl_driver!r}; human CartPole rendering may initialize invisibly or fail. Use non-render training or a real display.",
        )

    system = platform.system().lower()
    if system == "linux" and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return (
            False,
            "No DISPLAY or WAYLAND_DISPLAY is set on Linux; --render and --test are likely to fail when Gymnasium/Pygame requests render_mode='human'.",
        )

    if os.environ.get("CI") and system == "linux":
        return (
            False,
            "CI=true on Linux; even with display variables, avoid unattended --render/--test unless the job explicitly provisions a display server.",
        )

    return (
        True,
        "Display variables do not show an obvious headless block. This is a preflight only; it does not open a Pygame window.",
    )


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run safe synthetic smoke checks for CartPole DQN/A2C/PPO models, "
            "validate algorithm-specific checkpoint formats, and diagnose headless render readiness."
        )
    )
    parser.add_argument(
        "--algorithm",
        choices=("dqn", "a2c", "ppo"),
        help="algorithm expected by --checkpoint",
    )
    parser.add_argument(
        "--checkpoint",
        help="optional checkpoint file to validate against --algorithm without running Gym training or rendering",
    )
    parser.add_argument(
        "--require-render-ready",
        action="store_true",
        help="fail if display environment variables suggest --render/--test would fail",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print only final PASS/FAIL lines",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.checkpoint and not args.algorithm:
        print("ERROR: --checkpoint requires --algorithm {dqn,a2c,ppo}", file=sys.stderr)
        return 2
    if args.algorithm and not args.checkpoint:
        print("ERROR: --algorithm is only meaningful with --checkpoint", file=sys.stderr)
        return 2

    random.seed(7)
    np.random.seed(7)
    torch.manual_seed(7)

    checks = [smoke_dqn, smoke_a2c, smoke_ppo, smoke_checkpoint_mismatches]
    messages: list[str] = []
    try:
        for check in checks:
            messages.append(check())

        render_ok, render_message = render_readiness()
        messages.append(f"Render diagnostic: {render_message}")
        if args.require_render_ready and not render_ok:
            raise AssertionError(render_message)

        if args.checkpoint:
            payload = load_checkpoint(args.checkpoint)
            ok, message = validate_checkpoint_object(args.algorithm, payload)
            if not ok:
                raise AssertionError(f"Checkpoint validation failed for {args.algorithm}: {message}")
            messages.append(f"Checkpoint file: {message}")

    except Exception as exc:
        print(f"FAIL cartpole_smoke: {exc}", file=sys.stderr)
        return 1

    if args.quiet:
        print("PASS cartpole_smoke")
    else:
        for message in messages:
            print(f"PASS {message}")
        print("PASS cartpole_smoke: synthetic DQN/A2C/PPO checks completed without Gym training or display use")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
