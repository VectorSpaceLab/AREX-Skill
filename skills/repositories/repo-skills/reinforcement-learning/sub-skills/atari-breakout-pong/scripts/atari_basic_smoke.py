#!/usr/bin/env python3
"""Synthetic smoke checks for the standard Atari Breakout/Pong workflows.

This helper is self-contained. It adapts the Atari DQN/PPO model, replay, and
GAE checks into tiny synthetic tests so agents can validate core logic without
Atari ROM downloads, ALE/Gymnasium env reset, W&B credentials, rendering, or a
10M-frame training run.

Examples:
    python scripts/atari_basic_smoke.py --help
    python scripts/atari_basic_smoke.py --device cpu
    python scripts/atari_basic_smoke.py --device auto --batch-size 2
"""
from __future__ import annotations

import argparse
import sys
from typing import Any, Tuple

np: Any = None
torch: Any = None
nn: Any = None
optim: Any = None

GAMMA = 0.99
GAE_LAMBDA = 0.95


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Run synthetic Nature-CNN, DQN replay-buffer, PPO GAE, and tiny "
            "gradient checks for standard Atari Breakout/Pong workflows."
        )
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda", "mps"],
        default="auto",
        help="Torch device selection using the workflow priority for auto: cuda, then mps, then cpu.",
    )
    parser.add_argument(
        "--n-actions",
        type=int,
        default=4,
        help="Synthetic discrete action count for model heads; must be >=2.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Synthetic batch size for model/replay checks; must be >=2.",
    )
    parser.add_argument(
        "--replay-capacity",
        type=int,
        default=16,
        help="Tiny replay capacity for the synthetic DQN buffer check; must be >=10.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Random seed for NumPy and Torch.")
    return parser.parse_args(argv)


def load_deps():
    global np, torch, nn, optim
    try:
        import numpy as _np
        import torch as _torch
        import torch.nn as _nn
        import torch.optim as _optim
    except ImportError as exc:  # pragma: no cover - exercised only in missing envs
        print(
            "Missing dependency for synthetic Atari smoke: "
            f"{exc}. Install NumPy and Torch, or run --help only.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    np, torch, nn, optim = _np, _torch, _nn, _optim


def pick_device(arg: str):
    if arg == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    if arg == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("--device cuda requested, but torch.cuda.is_available() is false")
    if arg == "mps" and not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
        raise RuntimeError("--device mps requested, but torch.backends.mps.is_available() is false")
    return torch.device(arg)


def ensure(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def make_q_network_class():
    class QNetwork(nn.Module):
        """Nature CNN Q-network for stacked uint8 Atari frames."""

        def __init__(self, n_actions: int):
            super().__init__()
            self.conv = nn.Sequential(
                nn.Conv2d(4, 32, kernel_size=8, stride=4), nn.ReLU(),
                nn.Conv2d(32, 64, kernel_size=4, stride=2), nn.ReLU(),
                nn.Conv2d(64, 64, kernel_size=3, stride=1), nn.ReLU(),
                nn.Flatten(),
            )
            self.fc = nn.Sequential(
                nn.Linear(64 * 7 * 7, 512), nn.ReLU(),
                nn.Linear(512, n_actions),
            )

        def forward(self, x):
            return self.fc(self.conv(x.float() / 255.0))

    return QNetwork


def make_replay_buffer_class():
    class ReplayBuffer:
        """Single-frame uint8 replay buffer with stack reconstruction."""

        def __init__(self, capacity: int, frame_shape: Tuple[int, int] = (84, 84), stack: int = 4):
            self.capacity = capacity
            self.stack = stack
            self.frames = np.zeros((capacity, *frame_shape), dtype=np.uint8)
            self.actions = np.zeros(capacity, dtype=np.int64)
            self.rewards = np.zeros(capacity, dtype=np.float32)
            self.dones = np.zeros(capacity, dtype=np.float32)
            self.idx = 0
            self.size = 0

        def push(self, frame, action: int, reward: float, done: bool):
            self.frames[self.idx] = frame
            self.actions[self.idx] = action
            self.rewards[self.idx] = reward
            self.dones[self.idx] = float(done)
            self.idx = (self.idx + 1) % self.capacity
            self.size = min(self.size + 1, self.capacity)

        def _stack(self, idx):
            offsets = np.arange(self.stack)
            gather = (idx[:, None] - (self.stack - 1) + offsets[None, :]) % self.capacity
            out = self.frames[gather]
            older = self.dones[gather[:, :-1]].astype(bool)
            invalid = np.cumsum(older[:, ::-1], axis=1)[:, ::-1] > 0
            mask = np.concatenate([~invalid, np.ones((idx.shape[0], 1), dtype=bool)], axis=1)
            return out * mask[:, :, None, None]

        def sample(self, batch_size: int, device):
            while True:
                if self.size < self.capacity:
                    if self.size < self.stack + 2:
                        raise RuntimeError("buffer too small to sample yet")
                    idx = np.random.randint(self.stack - 1, self.size - 1, size=batch_size)
                    break
                idx = np.random.randint(0, self.capacity, size=batch_size)
                dist = (self.idx - 1 - idx) % self.capacity
                if np.all(dist >= self.stack):
                    break
            states = self._stack(idx)
            next_states = self._stack((idx + 1) % self.capacity)
            return (
                torch.as_tensor(states, device=device),
                torch.as_tensor(self.actions[idx], device=device),
                torch.as_tensor(self.rewards[idx], device=device),
                torch.as_tensor(next_states, device=device),
                torch.as_tensor(self.dones[idx], device=device),
            )

    return ReplayBuffer


def make_actor_critic_class():
    def _ortho(layer, gain: float):
        nn.init.orthogonal_(layer.weight, gain)
        nn.init.zeros_(layer.bias)
        return layer

    class ActorCritic(nn.Module):
        """Nature CNN shared trunk with categorical policy and scalar value heads."""

        def __init__(self, n_actions: int):
            super().__init__()
            self.conv = nn.Sequential(
                _ortho(nn.Conv2d(4, 32, kernel_size=8, stride=4), 2 ** 0.5), nn.ReLU(),
                _ortho(nn.Conv2d(32, 64, kernel_size=4, stride=2), 2 ** 0.5), nn.ReLU(),
                _ortho(nn.Conv2d(64, 64, kernel_size=3, stride=1), 2 ** 0.5), nn.ReLU(),
                nn.Flatten(),
                _ortho(nn.Linear(64 * 7 * 7, 512), 2 ** 0.5), nn.ReLU(),
            )
            self.policy = _ortho(nn.Linear(512, n_actions), 0.01)
            self.value = _ortho(nn.Linear(512, 1), 1.0)

        def forward(self, x):
            h = self.conv(x.float() / 255.0)
            return self.policy(h), self.value(h).squeeze(-1)

    return ActorCritic


def compute_gae(rewards, values, dones, last_value):
    advantages = np.zeros_like(rewards, dtype=np.float32)
    gae = 0.0
    for t in reversed(range(len(rewards))):
        next_v = last_value if t == len(rewards) - 1 else values[t + 1]
        next_nonterminal = 1.0 - dones[t]
        delta = rewards[t] + GAMMA * next_v * next_nonterminal - values[t]
        gae = delta + GAMMA * GAE_LAMBDA * next_nonterminal * gae
        advantages[t] = gae
    returns = advantages + values
    return advantages, returns


def synthetic_uint8(batch_size: int):
    frames = np.random.randint(0, 256, size=(batch_size, 4, 84, 84), dtype=np.uint8)
    return frames


def check_q_network(device, n_actions: int, batch_size: int):
    QNetwork = make_q_network_class()
    model = QNetwork(n_actions).to(device)
    obs = torch.as_tensor(synthetic_uint8(batch_size), device=device)
    q_values = model(obs)
    ensure(tuple(q_values.shape) == (batch_size, n_actions), f"DQN Q shape mismatch: {tuple(q_values.shape)}")
    ensure(torch.isfinite(q_values).all().item(), "DQN Q values contain non-finite numbers")

    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    actions = torch.arange(batch_size, device=device) % n_actions
    target = torch.zeros(batch_size, device=device)
    pred = q_values.gather(1, actions.unsqueeze(1)).squeeze(1)
    loss = nn.SmoothL1Loss()(pred, target)
    optimizer.zero_grad()
    loss.backward()
    nn.utils.clip_grad_norm_(model.parameters(), 10.0)
    optimizer.step()
    ensure(torch.isfinite(loss).item(), "DQN tiny Huber loss is not finite")
    return int(sum(p.numel() for p in model.parameters()))


def check_replay_buffer(device, n_actions: int, capacity: int, batch_size: int):
    ReplayBuffer = make_replay_buffer_class()
    buffer = ReplayBuffer(capacity=capacity)
    frames_to_push = capacity - 2
    for i in range(frames_to_push):
        frame = np.full((84, 84), fill_value=(i + 1), dtype=np.uint8)
        done = (i == 5)
        buffer.push(frame, action=i % n_actions, reward=float(np.sign(i - 3)), done=done)

    terminal_stack = buffer._stack(np.array([6], dtype=np.int64))[0]
    ensure(int(terminal_stack[:3].sum()) == 0, "Replay stack did not mask frames before a terminal boundary")
    ensure(int(terminal_stack[3].sum()) > 0, "Replay stack unexpectedly masked the newest frame")

    states, actions, rewards, next_states, dones = buffer.sample(batch_size, device)
    ensure(tuple(states.shape) == (batch_size, 4, 84, 84), f"Replay states shape mismatch: {tuple(states.shape)}")
    ensure(tuple(next_states.shape) == (batch_size, 4, 84, 84), "Replay next_states shape mismatch")
    ensure(tuple(actions.shape) == (batch_size,), "Replay actions shape mismatch")
    ensure(tuple(rewards.shape) == (batch_size,), "Replay rewards shape mismatch")
    ensure(tuple(dones.shape) == (batch_size,), "Replay dones shape mismatch")
    ensure(states.dtype == torch.uint8, f"Replay states dtype should be uint8, got {states.dtype}")
    return buffer.size


def check_actor_critic(device, n_actions: int, batch_size: int):
    ActorCritic = make_actor_critic_class()
    model = ActorCritic(n_actions).to(device)
    obs = torch.as_tensor(synthetic_uint8(batch_size), device=device)
    logits, values = model(obs)
    ensure(tuple(logits.shape) == (batch_size, n_actions), f"PPO logits shape mismatch: {tuple(logits.shape)}")
    ensure(tuple(values.shape) == (batch_size,), f"PPO values shape mismatch: {tuple(values.shape)}")
    ensure(torch.isfinite(logits).all().item(), "PPO logits contain non-finite numbers")
    ensure(torch.isfinite(values).all().item(), "PPO values contain non-finite numbers")

    dist = torch.distributions.Categorical(logits=logits)
    actions = dist.sample()
    loss = -(dist.log_prob(actions).mean() + 0.01 * dist.entropy().mean()) + 0.5 * values.pow(2).mean()
    optimizer = optim.Adam(model.parameters(), lr=2.5e-4, eps=1e-5)
    optimizer.zero_grad()
    loss.backward()
    nn.utils.clip_grad_norm_(model.parameters(), 0.5)
    optimizer.step()
    ensure(torch.isfinite(loss).item(), "PPO tiny policy/value loss is not finite")
    return int(sum(p.numel() for p in model.parameters()))


def check_gae():
    rewards = np.array([[1.0, 0.0], [2.0, 1.0], [0.5, -1.0]], dtype=np.float32)
    values = np.array([[0.2, 0.1], [0.3, 0.4], [0.5, 0.6]], dtype=np.float32)
    dones = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    last_value = np.array([0.7, 0.8], dtype=np.float32)
    advantages, returns = compute_gae(rewards, values, dones, last_value)
    ensure(advantages.shape == rewards.shape, f"GAE advantages shape mismatch: {advantages.shape}")
    ensure(returns.shape == rewards.shape, f"GAE returns shape mismatch: {returns.shape}")
    ensure(np.isfinite(advantages).all(), "GAE advantages contain non-finite numbers")
    ensure(np.isfinite(returns).all(), "GAE returns contain non-finite numbers")
    ensure(np.isclose(advantages[1, 0], rewards[1, 0] - values[1, 0]), "GAE did not reset at done boundary")
    ensure(np.isclose(advantages[2, 1], rewards[2, 1] - values[2, 1]), "GAE final done boundary check failed")
    return advantages, returns


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.n_actions < 2:
        print("FAIL: --n-actions must be >= 2", file=sys.stderr)
        return 2
    if args.batch_size < 2:
        print("FAIL: --batch-size must be >= 2", file=sys.stderr)
        return 2
    if args.replay_capacity < 10:
        print("FAIL: --replay-capacity must be >= 10", file=sys.stderr)
        return 2

    load_deps()
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    try:
        device = pick_device(args.device)
        q_params = check_q_network(device, args.n_actions, args.batch_size)
        replay_size = check_replay_buffer(device, args.n_actions, args.replay_capacity, args.batch_size)
        ac_params = check_actor_critic(device, args.n_actions, args.batch_size)
        advantages, returns = check_gae()
    except Exception as exc:  # pragma: no cover - intended user-facing failure path
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("Synthetic Atari smoke passed")
    print(f"  device: {device}")
    print(f"  n_actions: {args.n_actions}")
    print(f"  DQN QNetwork parameters: {q_params:,}")
    print(f"  PPO ActorCritic parameters: {ac_params:,}")
    print(f"  replay frames checked: {replay_size}")
    print(f"  GAE mean advantage: {float(advantages.mean()):.6f}")
    print(f"  GAE mean return: {float(returns.mean()):.6f}")
    print("  ALE env reset, ROMs, rendering, W&B, and long training were intentionally skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
