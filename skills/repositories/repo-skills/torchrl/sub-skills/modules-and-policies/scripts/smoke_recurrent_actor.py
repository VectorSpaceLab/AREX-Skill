#!/usr/bin/env python
"""CPU-safe TorchRL recurrent policy smoke checks.

The script avoids CUDA/Triton and optional simulator dependencies. It builds a
tiny GRU policy, demonstrates a missing recurrent reset-signal failure,
manually primes hidden state for synthetic TensorDicts, and checks recurrent-
mode shapes and boundary isolation.
"""

from __future__ import annotations

import torch
from tensordict import TensorDict
from tensordict.nn import TensorDictModule, TensorDictSequential
from torch import nn

from torchrl.modules import GRUModule, set_recurrent_mode


OBS_DIM = 4
HIDDEN = 8
N_ACTIONS = 3


def assert_key(tensordict: TensorDict, key) -> None:
    if key not in tensordict.keys(True, True):
        raise AssertionError(f"missing TensorDict key {key!r}; keys={list(tensordict.keys(True, True))}")


def make_policy() -> TensorDictSequential:
    gru = GRUModule(
        input_size=OBS_DIM,
        hidden_size=HIDDEN,
        in_keys=["observation", "rs"],
        out_keys=["features", ("next", "rs")],
        recurrent_backend="pad",
    )
    head = TensorDictModule(
        nn.Linear(HIDDEN, N_ACTIONS),
        in_keys=["features"],
        out_keys=["logits"],
    )
    chooser = TensorDictModule(
        lambda logits: logits.argmax(dim=-1),
        in_keys=["logits"],
        out_keys=["action"],
    )
    return TensorDictSequential(gru, head, chooser)


def expect_missing_reset_signal_failure(policy: TensorDictSequential) -> None:
    td = TensorDict(
        {
            "observation": torch.randn(2, OBS_DIM),
            "rs": torch.zeros(2, 1, HIDDEN),
        },
        batch_size=[2],
    )
    try:
        policy(td)
    except (KeyError, RuntimeError):
        return
    raise AssertionError("policy unexpectedly succeeded without recurrent reset key 'is_init'")


def one_step_manual_primer_smoke(policy: TensorDictSequential) -> None:
    batch = 2
    td = TensorDict(
        {
            "observation": torch.randn(batch, OBS_DIM),
            "rs": torch.zeros(batch, 1, HIDDEN),
            "is_init": torch.ones(batch, 1, dtype=torch.bool),
        },
        batch_size=[batch],
    )
    with set_recurrent_mode(False):
        out = policy(td)
    for key in ["features", "logits", "action", ("next", "rs")]:
        assert_key(out, key)
    assert out["features"].shape == (batch, HIDDEN)
    assert out["logits"].shape == (batch, N_ACTIONS)
    assert out["action"].shape == (batch,)
    assert out["next", "rs"].shape == (batch, 1, HIDDEN)


def recurrent_sequence_shape_smoke(policy: TensorDictSequential) -> None:
    batch, time = 2, 5
    is_init = torch.zeros(batch, time, 1, dtype=torch.bool)
    is_init[:, 0] = True
    is_init[0, 3] = True
    td = TensorDict(
        {
            "observation": torch.randn(batch, time, OBS_DIM),
            "rs": torch.zeros(batch, time, 1, HIDDEN),
            "is_init": is_init,
        },
        batch_size=[batch, time],
    )
    with set_recurrent_mode(True), torch.no_grad():
        out = policy(td)
    for key in ["features", "logits", "action", ("next", "rs")]:
        assert_key(out, key)
    assert out["features"].shape == (batch, time, HIDDEN)
    assert out["logits"].shape == (batch, time, N_ACTIONS)
    assert out["action"].shape == (batch, time)
    assert out["next", "rs"].shape == (batch, time, 1, HIDDEN)


def recurrent_boundary_isolation_smoke(policy: TensorDictSequential) -> None:
    """A later trajectory in a packed batch should match the same trajectory alone."""

    batch, time, split = 1, 6, 3
    torch.manual_seed(123)
    obs = torch.randn(batch, time, OBS_DIM)
    noisy_hidden = torch.randn(batch, time, 1, HIDDEN)
    is_init = torch.zeros(batch, time, 1, dtype=torch.bool)
    is_init[:, 0] = True
    is_init[:, split] = True

    packed = TensorDict(
        {"observation": obs, "rs": noisy_hidden, "is_init": is_init},
        batch_size=[batch, time],
    )
    second_only_is_init = torch.zeros(batch, time - split, 1, dtype=torch.bool)
    second_only_is_init[:, 0] = True
    second_only = TensorDict(
        {
            "observation": obs[:, split:].clone(),
            "rs": noisy_hidden[:, split:].clone(),
            "is_init": second_only_is_init,
        },
        batch_size=[batch, time - split],
    )

    with set_recurrent_mode(True), torch.no_grad():
        packed_out = policy(packed.clone())
        second_out = policy(second_only.clone())

    torch.testing.assert_close(
        packed_out["features"][:, split:],
        second_out["features"],
        rtol=1e-5,
        atol=1e-6,
    )


def main() -> None:
    torch.manual_seed(0)
    policy = make_policy()
    policy.eval()
    expect_missing_reset_signal_failure(policy)
    one_step_manual_primer_smoke(policy)
    recurrent_sequence_shape_smoke(policy)
    recurrent_boundary_isolation_smoke(policy)
    print("smoke_recurrent_actor.py: ok")


if __name__ == "__main__":
    main()
