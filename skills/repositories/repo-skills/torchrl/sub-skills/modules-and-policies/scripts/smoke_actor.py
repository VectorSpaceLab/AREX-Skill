#!/usr/bin/env python
"""CPU-safe TorchRL actor/module smoke checks.

This script is intentionally self-contained: it imports installed packages only,
constructs tiny TensorDict inputs, and asserts key/shape/spec behaviour.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from tensordict import TensorDict
from tensordict.nn import CompositeDistribution, TensorDictModule
from tensordict.nn.distributions import NormalParamExtractor
from torch import distributions as d, nn

from torchrl.data import Bounded, OneHot
from torchrl.modules import (
    Actor,
    MLP,
    ProbabilisticActor,
    QValueActor,
    SafeModule,
    TanhNormal,
    ValueOperator,
)


def assert_key(tensordict: TensorDict, key) -> None:
    if key not in tensordict.keys(True, True):
        raise AssertionError(f"missing TensorDict key {key!r}; keys={list(tensordict.keys(True, True))}")


class ActionCritic(nn.Module):
    def __init__(self, obs_dim: int, action_dim: int) -> None:
        super().__init__()
        self.net = nn.Linear(obs_dim + action_dim, 1)

    def forward(self, obs: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        return self.net(torch.cat([obs, action], dim=-1))


class CompositeParamModule(nn.Module):
    """Split a vector into parameters for a normal and a categorical head."""

    def forward(self, x: torch.Tensor):
        loc = x[..., :2]
        scale = F.softplus(x[..., 2:4]) + 1e-4
        logits = x[..., 4:]
        return loc, scale, logits


def deterministic_actor_and_critic_smoke() -> None:
    torch.manual_seed(0)
    batch, obs_dim, action_dim = 5, 4, 2
    action_spec = Bounded(low=-1.0, high=1.0, shape=(action_dim,))

    actor = Actor(
        MLP(in_features=obs_dim, out_features=action_dim, num_cells=[16]),
        in_keys=[("obs", "state")],
        out_keys=["action"],
        spec=action_spec,
        safe=True,
    )
    td = TensorDict(
        {("obs", "state"): torch.randn(batch, obs_dim)},
        batch_size=[batch],
    )
    out = actor(td.clone())
    assert_key(out, "action")
    assert out["action"].shape == (batch, action_dim)
    assert torch.isfinite(out["action"]).all()
    assert (out["action"] <= 1.0 + 1e-6).all()
    assert (out["action"] >= -1.0 - 1e-6).all()

    critic = ValueOperator(
        ActionCritic(obs_dim=obs_dim, action_dim=action_dim),
        in_keys=[("obs", "state"), "action"],
    )
    out = critic(out)
    assert_key(out, "state_action_value")
    assert out["state_action_value"].shape == (batch, 1)


def probabilistic_actor_smoke() -> None:
    torch.manual_seed(1)
    batch, obs_dim, action_dim = 6, 3, 2
    action_spec = Bounded(low=-1.0, high=1.0, shape=(action_dim,))

    param_module = TensorDictModule(
        nn.Sequential(nn.Linear(obs_dim, 2 * action_dim), NormalParamExtractor()),
        in_keys=[("obs", "state")],
        out_keys=["loc", "scale"],
    )
    actor = ProbabilisticActor(
        module=param_module,
        in_keys=["loc", "scale"],
        out_keys=["action"],
        spec=action_spec,
        distribution_class=TanhNormal,
        distribution_kwargs={"low": -1.0, "high": 1.0},
        return_log_prob=True,
        log_prob_key="sample_log_prob",
    )
    td = TensorDict(
        {("obs", "state"): torch.randn(batch, obs_dim)},
        batch_size=[batch],
    )
    out = actor(td)
    for key in ["loc", "scale", "action", "sample_log_prob"]:
        assert_key(out, key)
    assert out["loc"].shape == (batch, action_dim)
    assert out["scale"].shape == (batch, action_dim)
    assert out["action"].shape == (batch, action_dim)
    assert out["sample_log_prob"].shape[0] == batch
    assert torch.isfinite(out["sample_log_prob"]).all()
    assert (out["action"] <= 1.0 + 1e-6).all()
    assert (out["action"] >= -1.0 - 1e-6).all()


def composite_distribution_smoke() -> None:
    torch.manual_seed(2)
    batch = 4
    param_module = TensorDictModule(
        CompositeParamModule(),
        in_keys=["x"],
        out_keys=[
            ("params", "normal", "loc"),
            ("params", "normal", "scale"),
            ("params", "categ", "logits"),
        ],
    )
    actor = ProbabilisticActor(
        param_module,
        in_keys=["params"],
        distribution_class=CompositeDistribution,
        distribution_kwargs={
            "distribution_map": {"normal": d.Normal, "categ": d.Categorical},
            "name_map": {
                "normal": ("action", "normal"),
                "categ": ("action", "categ"),
            },
        },
    )
    td = TensorDict({"x": torch.randn(batch, 7)}, batch_size=[batch])
    out = actor(td)
    assert_key(out, ("action", "normal"))
    assert_key(out, ("action", "categ"))
    assert out["action", "normal"].shape == (batch, 2)
    assert out["action", "categ"].shape == (batch,)


def qvalue_actor_with_mask_smoke() -> None:
    torch.manual_seed(3)
    batch, obs_dim, n_actions = 7, 4, 5
    actor = QValueActor(
        module=MLP(in_features=obs_dim, out_features=n_actions, num_cells=[12]),
        spec=OneHot(n_actions),
        action_mask_key="action_mask",
    )
    mask = torch.ones(batch, n_actions, dtype=torch.bool)
    mask[:, 0] = False
    td = TensorDict(
        {"observation": torch.randn(batch, obs_dim), "action_mask": mask},
        batch_size=[batch],
    )
    out = actor(td)
    for key in ["action", "action_value", "chosen_action_value"]:
        assert_key(out, key)
    assert out["action"].shape == (batch, n_actions)
    assert out["action_value"].shape == (batch, n_actions)
    assert out["chosen_action_value"].shape == (batch, 1)
    assert (out["action"].sum(-1) == 1).all()
    assert not out["action"][:, 0].any(), "masked action 0 was selected"


def safe_module_projection_smoke() -> None:
    batch, action_dim = 3, 2
    projector = SafeModule(
        nn.Identity(),
        in_keys=["raw_action"],
        out_keys=["projected_action"],
        spec=Bounded(low=-1.0, high=1.0, shape=(action_dim,)),
        safe=True,
    )
    td = TensorDict(
        {"raw_action": torch.full((batch, action_dim), 5.0)},
        batch_size=[batch],
    )
    out = projector(td)
    assert_key(out, "projected_action")
    assert out["projected_action"].shape == (batch, action_dim)
    assert (out["projected_action"] <= 1.0 + 1e-6).all()
    assert (out["projected_action"] >= -1.0 - 1e-6).all()


def main() -> None:
    deterministic_actor_and_critic_smoke()
    probabilistic_actor_smoke()
    composite_distribution_smoke()
    qvalue_actor_with_mask_smoke()
    safe_module_projection_smoke()
    print("smoke_actor.py: ok")


if __name__ == "__main__":
    main()
