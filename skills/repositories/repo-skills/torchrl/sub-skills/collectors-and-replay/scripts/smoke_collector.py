#!/usr/bin/env python3
"""CPU-only TorchRL collector, replay integration, and Evaluator smoke test.

This helper is deterministic, uses TorchRL's native Pendulum environment, and
performs no downloads, distributed service startup, or model training.
"""

from __future__ import annotations

import logging
import warnings

try:
    import torch
    from torchrl.collectors import Collector, Evaluator, RandomPolicy
    from torchrl.data import LazyTensorStorage, TensorDictReplayBuffer
    from torchrl.envs import PendulumEnv
except Exception as exc:  # pragma: no cover - user-facing script guard
    raise SystemExit(
        "smoke_collector.py requires importable torch, tensordict, and "
        f"torchrl packages; import failed with: {exc}"
    ) from exc


def _make_env() -> PendulumEnv:
    env = PendulumEnv(device="cpu")
    env.set_seed(0)
    return env


def _make_policy() -> RandomPolicy:
    env = _make_env()
    try:
        return RandomPolicy(env.action_spec)
    finally:
        close = getattr(env, "close", None)
        if close is not None:
            close()


def _check_direct_collector() -> None:
    env = _make_env()
    collector = Collector(
        env,
        policy=_make_policy(),
        backend="direct",
        frames_per_batch=8,
        total_frames=16,
        device="cpu",
        storing_device="cpu",
        policy_device="cpu",
        env_device="cpu",
    )
    try:
        batch = next(iter(collector))
        assert batch.numel() == 8
        assert batch.device is None or str(batch.device) == "cpu"
        assert "action" in batch.keys()
        assert ("next", "reward") in batch.keys(
            include_nested=True,
            leaves_only=True,
        )
        assert ("collector", "traj_ids") in batch.keys(
            include_nested=True,
            leaves_only=True,
        )
    finally:
        collector.shutdown()


def _check_direct_collector_to_replay() -> None:
    rb = TensorDictReplayBuffer(storage=LazyTensorStorage(32), batch_size=4)
    collector = Collector(
        _make_env,
        policy=_make_policy(),
        backend="direct",
        replay_buffer=rb,
        frames_per_batch=8,
        total_frames=8,
        device="cpu",
        storing_device="cpu",
        policy_device="cpu",
        env_device="cpu",
    )
    try:
        for _ in collector:
            pass
        assert len(rb) == 8
        sample = rb.sample()
        assert sample.batch_size == torch.Size([4])
        assert sample["action"].device.type == "cpu"
        assert "index" in sample.keys()
    finally:
        collector.shutdown()


def _check_evaluator() -> None:
    evaluator = Evaluator(
        _make_env,
        _make_policy(),
        num_trajectories=1,
        max_steps=3,
        device="cpu",
        dump_video=False,
    )
    try:
        metrics = evaluator.evaluate()
        assert "eval/reward" in metrics.keys()
        assert "eval/episode_length" in metrics.keys()
        assert metrics["eval/num_episodes"] >= 1
    finally:
        evaluator.shutdown()


def main() -> None:
    logging.getLogger("torchrl").setLevel(logging.WARNING)
    warnings.filterwarnings(
        "ignore",
        message="trajs_per_batch is set but traj_format is not.*",
        category=FutureWarning,
    )
    torch.manual_seed(0)
    _check_direct_collector()
    _check_direct_collector_to_replay()
    _check_evaluator()
    print("success: smoke_collector")


if __name__ == "__main__":
    main()
