#!/usr/bin/env python3
"""Deterministic, data-free geometry and GuidanceWrapper smoke test.

Run from a Diffusion-Planner checkout with its package installed, for example:

    python skills/disco/diffusion-planner/sub-skills/guidance/scripts/synthetic_guidance_smoke.py

The helper intentionally uses B=1 because the repository's live collision gate
uses Python ``and`` on the diffusion-time tensor.  A separate test should cover
vectorized time handling in a custom implementation before using B>1.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Any, Dict

import torch

from diffusion_planner.model.guidance.collision import (
    batch_signed_distance_rect,
    center_rect_to_points,
    collision_guidance_fn,
)
from diffusion_planner.model.guidance.guidance_wrapper import GuidanceWrapper


@dataclass
class IdentityNormalizer:
    """Minimal normalizer for a wrapper-only smoke; it performs no conversion."""

    def inverse(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: tensor.clone() if torch.is_tensor(tensor) else tensor for key, tensor in value.items()}
        return value


class IdentityModel(torch.nn.Module):
    """Return the sampler state with the model's expected call signature."""

    def forward(self, x: torch.Tensor, t: torch.Tensor, **kwargs: Any) -> torch.Tensor:
        del t, kwargs
        return x


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run deterministic live Diffusion-Planner guidance geometry/autograd smoke checks."
    )
    parser.add_argument(
        "--device",
        default="cpu",
        choices=("cpu", "cuda"),
        help="Tensor device (default: cpu; cuda requires a visible GPU).",
    )
    return parser.parse_args()


def check_geometry(device: torch.device) -> None:
    # Two same-heading 4 x 2 rectangles: one separated, one overlapping.
    rects = torch.tensor(
        [
            [0.0, 0.0, 1.0, 0.0, 4.0, 2.0],
            [8.0, 0.0, 1.0, 0.0, 4.0, 2.0],
            [1.0, 0.0, 1.0, 0.0, 4.0, 2.0],
        ],
        device=device,
    )
    points = center_rect_to_points(rects)
    separated = batch_signed_distance_rect(points[0:1], points[1:2])
    overlap = batch_signed_distance_rect(points[0:1], points[2:3])
    if not (separated > 0).all():
        raise AssertionError(f"expected positive separated distance, got {separated}")
    if not (overlap < 0).all():
        raise AssertionError(f"expected negative overlap distance, got {overlap}")
    if points.shape != (3, 4, 2):
        raise AssertionError(f"unexpected rectangle points shape: {points.shape}")
    print(f"geometry: PASS (separated={separated.item():.3f}, overlap={overlap.item():.3f})")


def make_inputs(device: torch.device) -> Dict[str, torch.Tensor]:
    # P=2: ego plus one valid neighbor.  Source collision.py reads [7, 6] as
    # [width, length] from the final neighbor history row.
    neighbor_past = torch.zeros((1, 1, 1, 8), device=device)
    neighbor_past[0, 0, 0, 7] = 2.0
    neighbor_past[0, 0, 0, 6] = 4.0
    return {
        "neighbor_current_mask": torch.tensor([[False]], device=device),
        "neighbor_agents_past": neighbor_past,
    }


def make_state(device: torch.device) -> torch.Tensor:
    # Current plus two future states.  The neighbor overlaps the ego so the
    # live collision calculation traverses its differentiable geometry path.
    ego = torch.tensor(
        [[0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 1.0, 0.0]],
        device=device,
    )
    neighbor = torch.tensor(
        [[2.0, 0.0, 1.0, 0.0], [2.0, 0.0, 1.0, 0.0], [2.0, 0.0, 1.0, 0.0]],
        device=device,
    )
    return torch.stack((ego, neighbor), dim=0).unsqueeze(0)


def assert_finite(name: str, value: torch.Tensor) -> None:
    if not torch.isfinite(value).all():
        raise AssertionError(f"{name} is non-finite: {value}")


def check_live_collision(state: torch.Tensor, inputs: Dict[str, torch.Tensor]) -> None:
    state_for_fn = state.detach().clone().requires_grad_(True)
    time = torch.tensor([0.05], device=state.device)
    energy = collision_guidance_fn(state_for_fn, time, None, inputs)
    assert_finite("collision energy", energy)
    if not isinstance(energy, torch.Tensor) or not energy.requires_grad:
        raise AssertionError("collision energy is not an autograd-connected torch.Tensor")
    gradient = torch.autograd.grad(energy.sum(), state_for_fn, allow_unused=False)[0]
    assert_finite("collision gradient", gradient)
    print(
        "collision: PASS "
        f"(energy_shape={tuple(energy.shape)}, gradient_l1={gradient.abs().sum().item():.6f})"
    )


def check_wrapper(state: torch.Tensor, inputs: Dict[str, torch.Tensor]) -> None:
    sampler_state = state.reshape(1, 2, -1).detach().clone().requires_grad_(True)
    wrapper = GuidanceWrapper()
    energy = wrapper(
        sampler_state,
        torch.tensor([0.05], device=sampler_state.device),
        None,
        state_normalizer=IdentityNormalizer(),
        observation_normalizer=IdentityNormalizer(),
        model=IdentityModel().to(sampler_state.device),
        model_condition={},
        inputs=inputs,
    )
    assert_finite("wrapper energy", energy)
    if not energy.requires_grad:
        raise AssertionError("wrapper energy is not autograd-connected")
    gradient = torch.autograd.grad(energy.sum(), sampler_state, allow_unused=False)[0]
    assert_finite("wrapper gradient", gradient)
    if gradient.shape != sampler_state.shape:
        raise AssertionError(f"unexpected wrapper gradient shape: {gradient.shape}")
    print(
        "wrapper: PASS "
        f"(energy_shape={tuple(energy.shape)}, gradient_l1={gradient.abs().sum().item():.6f})"
    )


def main() -> int:
    args = parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        print("requested CUDA but torch.cuda.is_available() is false", file=sys.stderr)
        return 2

    torch.manual_seed(0)
    device = torch.device(args.device)
    print(f"device: {device}; torch: {torch.__version__}")
    check_geometry(device)
    inputs = make_inputs(device)
    state = make_state(device)
    check_live_collision(state, inputs)
    check_wrapper(state, inputs)
    print("synthetic guidance smoke: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
