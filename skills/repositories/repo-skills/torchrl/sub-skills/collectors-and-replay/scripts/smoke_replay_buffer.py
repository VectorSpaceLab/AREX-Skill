#!/usr/bin/env python3
"""CPU-only TorchRL replay-buffer smoke test.

This helper is deterministic, uses tiny in-memory and temporary memmap storage,
and performs no downloads, distributed service startup, or model training.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

try:
    import torch
    from tensordict import TensorDict
    from torchrl.data import (
        LazyMemmapStorage,
        LazyTensorStorage,
        TensorDictPrioritizedReplayBuffer,
        TensorDictReplayBuffer,
        TensorDictRoundRobinWriter,
    )
    from torchrl.data.replay_buffers import Sequence
except Exception as exc:  # pragma: no cover - user-facing script guard
    raise SystemExit(
        "smoke_replay_buffer.py requires importable torch, tensordict, and "
        f"torchrl packages; import failed with: {exc}"
    ) from exc


def _make_transition_td(n: int = 20, *, with_priority: bool = False) -> TensorDict:
    fields = {
        "obs": torch.arange(n, dtype=torch.float32).unsqueeze(-1),
        "action": (torch.arange(n, dtype=torch.long).unsqueeze(-1) % 3),
        ("next", "obs"): torch.arange(1, n + 1, dtype=torch.float32).unsqueeze(-1),
        ("next", "reward"): torch.ones(n, 1),
        ("next", "done"): torch.zeros(n, 1, dtype=torch.bool),
    }
    if with_priority:
        fields["td_error"] = torch.linspace(1.0, 2.0, n)
    td = TensorDict(fields, batch_size=[n])
    td["next", "done"][9] = True
    td["next", "done"][-1] = True
    return td


def _check_basic_tensordict_replay(data: TensorDict) -> None:
    rb = TensorDictReplayBuffer(storage=LazyTensorStorage(64), batch_size=5)
    index = rb.extend(data, update_priority=False)
    assert index.shape == torch.Size([20])
    assert len(rb) == 20
    sample = rb.sample()
    assert sample.batch_size == torch.Size([5])
    assert "index" in sample.keys()
    assert ("next", "reward") in sample.keys(include_nested=True, leaves_only=True)


def _check_memmap_checkpoint(data: TensorDict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        rb = TensorDictReplayBuffer(
            storage=LazyMemmapStorage(64, scratch_dir=root / "source"),
            batch_size=4,
        )
        rb.extend(data[:8], update_priority=False)
        checkpoint_dir = root / "checkpoint"
        rb.dumps(checkpoint_dir)

        restored = TensorDictReplayBuffer(
            storage=LazyMemmapStorage(
                64,
                scratch_dir=root / "restored",
                existsok=True,
            ),
            batch_size=4,
        )
        restored.loads(checkpoint_dir)
        assert len(restored) == len(rb)
        assert restored.sample().batch_size == torch.Size([4])


def _check_prioritized_replay(priority_data: TensorDict) -> None:
    rb = TensorDictPrioritizedReplayBuffer(
        alpha=0.7,
        beta=0.5,
        storage=LazyTensorStorage(64),
        batch_size=6,
        priority_key="td_error",
    )
    rb.extend(priority_data)
    sample = rb.sample()
    assert sample.batch_size == torch.Size([6])
    assert "index" in sample.keys()
    assert "priority_weight" in sample.keys()
    sample.set("td_error", torch.full(sample.batch_size, 3.0))
    rb.update_tensordict_priority(sample)


def _check_sequence_sample_unit(data: TensorDict) -> None:
    rb = TensorDictReplayBuffer(
        storage=LazyTensorStorage(64),
        batch_size=3,
        sample_unit=Sequence(
            length=4,
            burn_in=2,
            bootstrap=1,
            episode_boundary="pad",
        ),
    )
    rb.extend(data, update_priority=False)
    sample = rb.sample()
    assert "learning_mask" in sample.keys()
    assert "validity_mask" in sample.keys()
    assert "anchor_index" in sample.keys()
    assert sample["learning_mask"].dtype is torch.bool
    assert sample["validity_mask"].dtype is torch.bool
    assert (sample["learning_mask"] & sample["validity_mask"]).any()


def _check_generation_safe_update(data: TensorDict) -> None:
    rb = TensorDictReplayBuffer(
        storage=LazyTensorStorage(8),
        writer=TensorDictRoundRobinWriter(track_generations=True),
        batch_size=4,
    )
    rb.extend(data[:8], update_priority=False)
    sample = rb.sample()
    assert "index_generation" in sample.keys()
    patch = TensorDict({"obs": sample["obs"] + 100.0}, batch_size=sample.batch_size)
    result = rb.update_if_present(
        index=sample["index"],
        generation=sample["index_generation"],
        patch=patch,
    )
    assert result.updated_count >= 0


def main() -> None:
    logging.getLogger("torchrl").setLevel(logging.WARNING)
    torch.manual_seed(0)
    data = _make_transition_td(with_priority=False)
    priority_data = _make_transition_td(with_priority=True)
    _check_basic_tensordict_replay(data)
    _check_memmap_checkpoint(data)
    _check_prioritized_replay(priority_data)
    _check_sequence_sample_unit(data)
    _check_generation_safe_update(data)
    print("success: smoke_replay_buffer")


if __name__ == "__main__":
    main()
