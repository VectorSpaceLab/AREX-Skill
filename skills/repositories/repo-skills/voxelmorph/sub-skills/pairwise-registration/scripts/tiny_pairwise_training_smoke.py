#!/usr/bin/env python3
"""Tiny synthetic smoke training for VoxelMorph VxmPairwise.

This helper verifies the current PyTorch VoxelMorph pairwise-registration path
without downloading data, reading checkpoints, or depending on repository-local
example datasets. By default it runs one CPU optimizer step on random 2D tensors.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

import torch


def _features(values: Sequence[int]) -> tuple[int, ...]:
    if not values:
        raise argparse.ArgumentTypeError("at least one feature value is required")
    if any(v <= 0 for v in values):
        raise argparse.ArgumentTypeError("feature values must be positive")
    return tuple(int(v) for v in values)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny synthetic VoxelMorph VxmPairwise training smoke. "
            "No data download or real medical image is required."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dim", type=int, choices=(2, 3), default=2,
                        help="Spatial dimensionality to test.")
    parser.add_argument("--spatial-size", type=int, default=16,
                        help="Uniform spatial size for synthetic tensors.")
    parser.add_argument("--batch-size", type=int, default=1,
                        help="Synthetic batch size.")
    parser.add_argument("--source-channels", type=int, default=1,
                        help="Source image channel count.")
    parser.add_argument("--target-channels", type=int, default=1,
                        help="Target image channel count.")
    parser.add_argument("--features", type=int, nargs="+", default=[4, 4, 4],
                        help="UNet feature sequence for the tiny model.")
    parser.add_argument("--integration-steps", type=int, default=1,
                        help="Scaling-and-squaring integration steps in the model.")
    parser.add_argument("--steps", type=int, default=1,
                        help="Number of optimizer steps to run.")
    parser.add_argument("--lr", type=float, default=1e-3,
                        help="Adam learning rate for the tiny smoke.")
    parser.add_argument("--lambda-grad", type=float, default=0.01,
                        help="Weight for Neurite SpatialGradient regularization.")
    parser.add_argument("--image-loss", choices=("mse", "ncc"), default="mse",
                        help="Synthetic image-matching loss.")
    parser.add_argument("--grad-penalty", choices=("l1", "l2"), default="l2",
                        help="Neurite SpatialGradient penalty.")
    parser.add_argument("--device", default="cpu",
                        help="Torch device: cpu, cuda, or auto.")
    parser.add_argument("--seed", type=int, default=11,
                        help="Torch random seed.")
    parser.add_argument("--checkpoint-out", type=Path,
                        help="Optional path for a checkpoint round-trip payload.")
    parser.add_argument("--json", action="store_true",
                        help="Emit a JSON summary instead of one-line text.")
    return parser.parse_args(argv)


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(requested)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("--device cuda requested, but torch.cuda.is_available() is false")
    return device


def build_image_loss(name: str):
    import neurite as ne

    if name == "mse":
        return ne.nn.modules.MSE()
    if name == "ncc":
        return ne.nn.modules.NCC(window_size=3)
    raise ValueError(name)


def run(args: argparse.Namespace) -> dict:
    import neurite as ne
    import voxelmorph as vxm

    if args.spatial_size < 8:
        raise SystemExit("--spatial-size should be at least 8 for the tiny UNet smoke")
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be positive")
    if args.integration_steps < 0:
        raise SystemExit("--integration-steps must be nonnegative")
    if args.steps <= 0:
        raise SystemExit("--steps must be positive")

    features = _features(args.features)
    device = choose_device(args.device)
    torch.manual_seed(args.seed)

    spatial = (args.spatial_size,) * args.dim
    source_shape = (args.batch_size, args.source_channels, *spatial)
    target_shape = (args.batch_size, args.target_channels, *spatial)

    model_config = {
        "ndim": args.dim,
        "source_channels": args.source_channels,
        "target_channels": args.target_channels,
        "nb_features": features,
        "integration_steps": args.integration_steps,
        "device": str(device),
    }
    model = vxm.nn.models.VxmPairwise(**model_config).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    image_loss_fn = build_image_loss(args.image_loss)
    grad_loss_fn = ne.nn.modules.SpatialGradient(args.grad_penalty)

    losses: list[float] = []
    final_field_shape: tuple[int, ...] | None = None
    final_warped_shape: tuple[int, ...] | None = None
    for _ in range(args.steps):
        source = torch.rand(source_shape, device=device)
        target = torch.rand(target_shape, device=device)
        optimizer.zero_grad(set_to_none=True)
        field, warped_source = model(
            source,
            target,
            return_warped_source=True,
            return_field_type="displacement",
        )
        image_loss = image_loss_fn(target, warped_source).mean()
        grad_loss = grad_loss_fn(field).mean()
        loss = image_loss + args.lambda_grad * grad_loss
        if not torch.isfinite(loss):
            raise AssertionError(f"loss is not finite: {loss.item()}")
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu().item()))
        final_field_shape = tuple(field.shape)
        final_warped_shape = tuple(warped_source.shape)

    # Exercise the target-warp path only when integration is enabled.
    target_warp_ok = False
    if args.integration_steps > 0:
        with torch.no_grad():
            outputs = model(
                torch.rand(source_shape, device=device),
                torch.rand(target_shape, device=device),
                return_warped_source=True,
                return_warped_target=True,
                return_field_type="velocity",
            )
        if len(outputs) != 3:
            raise AssertionError("expected field, warped_source, warped_target tuple")
        target_warp_ok = True

    checkpoint_round_trip = False
    if args.checkpoint_out is not None:
        args.checkpoint_out.parent.mkdir(parents=True, exist_ok=True)
        public_config = dict(model_config)
        public_config["device"] = "cpu"
        payload = {
            "model_config": public_config,
            "state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
        }
        torch.save(payload, args.checkpoint_out)
        loaded_payload = torch.load(args.checkpoint_out, map_location="cpu")
        reloaded = vxm.nn.models.VxmPairwise(**loaded_payload["model_config"])
        reloaded.load_state_dict(loaded_payload["state_dict"])
        reloaded.eval()
        checkpoint_round_trip = True

    return {
        "status": "pass",
        "voxelmorph_version": getattr(vxm, "__version__", "unknown"),
        "torch_version": torch.__version__,
        "device": str(device),
        "dim": args.dim,
        "spatial": spatial,
        "features": features,
        "integration_steps": args.integration_steps,
        "steps": args.steps,
        "losses": losses,
        "field_shape": final_field_shape,
        "warped_source_shape": final_warped_shape,
        "target_warp_checked": target_warp_ok,
        "checkpoint_round_trip": checkpoint_round_trip,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001 - command-line smoke should stay concise.
        print(f"FAIL tiny_pairwise_training_smoke: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            "PASS tiny_pairwise_training_smoke",
            f"dim={result['dim']}",
            f"spatial={result['spatial']}",
            f"device={result['device']}",
            f"steps={result['steps']}",
            f"final_loss={result['losses'][-1]:.6f}",
            f"field_shape={result['field_shape']}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
