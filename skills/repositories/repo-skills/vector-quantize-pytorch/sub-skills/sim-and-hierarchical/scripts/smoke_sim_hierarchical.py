#!/usr/bin/env python3
"""Tiny CPU smoke checks for SimVQ, ResidualSimVQ, and HierarchicalVQ.

The script imports vector-quantize-pytorch only when checks are executed, so
`--help` remains usable even in an environment that has not installed the
package yet.
"""

from __future__ import annotations

import argparse
import sys


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _shape(tensor) -> tuple[int, ...]:
    return tuple(int(dim) for dim in tensor.shape)


def run_checks(seed: int, device: str, quiet: bool) -> None:
    import torch
    from torch import nn
    from vector_quantize_pytorch import HierarchicalVQ, ResidualSimVQ, SimVQ

    torch.manual_seed(seed)
    dev = torch.device(device)

    def log(message: str) -> None:
        if not quiet:
            print(message)

    # SimVQ: sequence layout, custom transform, explicit frozen_codebook_dim.
    def init_uniform(codes):
        return codes.uniform_(-0.25, 0.25)

    sim_vq = SimVQ(
        dim=8,
        codebook_size=16,
        frozen_codebook_dim=4,
        codebook_transform=nn.Sequential(
            nn.Linear(4, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
        ),
        init_fn=init_uniform,
        rotation_trick=True,
    ).to(dev)

    x = torch.randn(2, 5, 8, device=dev)
    quantized, indices, commit_loss = sim_vq(x)
    decoded = sim_vq.indices_to_codes(indices)

    _check(_shape(quantized) == _shape(x), f"SimVQ quantized shape {_shape(quantized)} != input {_shape(x)}")
    _check(_shape(indices) == (2, 5), f"SimVQ indices shape {_shape(indices)} != (2, 5)")
    _check(torch.isfinite(commit_loss).all().item(), "SimVQ commit_loss is not finite")
    _check(torch.allclose(quantized, decoded, atol=1e-5), "SimVQ indices_to_codes did not reconstruct quantized values")
    log(f"[ok] SimVQ: quantized={_shape(quantized)} indices={_shape(indices)} loss={float(commit_loss.detach()):.6f}")

    # ResidualSimVQ: channel-first image feature maps and reconstruction helper.
    residual_sim_vq = ResidualSimVQ(
        dim=6,
        num_quantizers=3,
        codebook_size=12,
        channel_first=True,
        rotation_trick=True,
    ).to(dev)

    image_features = torch.randn(2, 6, 4, 4, device=dev)
    res_quantized, res_indices, res_losses, all_codes = residual_sim_vq(image_features, return_all_codes=True)
    res_reconstructed = residual_sim_vq.get_output_from_indices(res_indices)

    _check(_shape(res_quantized) == _shape(image_features), "ResidualSimVQ quantized shape mismatch")
    _check(_shape(res_indices) == (2, 4, 4, 3), f"ResidualSimVQ indices shape {_shape(res_indices)} != (2, 4, 4, 3)")
    _check(_shape(res_losses) == (3,), f"ResidualSimVQ losses shape {_shape(res_losses)} != (3,)")
    _check(_shape(all_codes) == (3, 2, 6, 4, 4), f"ResidualSimVQ all_codes shape {_shape(all_codes)} != (3, 2, 6, 4, 4)")
    _check(torch.isfinite(res_losses).all().item(), "ResidualSimVQ losses are not finite")
    _check(torch.allclose(res_quantized, res_reconstructed, atol=1e-5), "ResidualSimVQ get_output_from_indices did not reconstruct quantized values")
    log(f"[ok] ResidualSimVQ: quantized={_shape(res_quantized)} indices={_shape(res_indices)} losses={_shape(res_losses)}")

    # HierarchicalVQ: small square feature map, full scale last, index-list check.
    hq = HierarchicalVQ(
        dim=4,
        codebook_size=8,
        accept_image_fmap=True,
        scales=(1, 2, 4),
        quant_resi=0.25,
        share_quant_resi=2,
        kmeans_init=False,
        threshold_ema_dead_code=0,
    ).to(dev)
    hq.eval()

    hq_features = torch.randn(2, 4, 4, 4, device=dev)
    hq_quantized, hq_indices, hq_commit_loss = hq(hq_features)
    hq_reconstructed = hq.get_output_from_indices(hq_indices)
    expected_index_shapes = [(2, 1, 1), (2, 2, 2), (2, 4, 4)]

    _check(_shape(hq_quantized) == _shape(hq_features), "HierarchicalVQ quantized shape mismatch")
    _check(isinstance(hq_indices, (tuple, list)), "HierarchicalVQ indices must be a tuple/list")
    _check(len(hq_indices) == 3, f"HierarchicalVQ index-list length {len(hq_indices)} != 3")
    _check([_shape(ind) for ind in hq_indices] == expected_index_shapes, f"HierarchicalVQ index shapes {[ _shape(ind) for ind in hq_indices ]} != {expected_index_shapes}")
    _check(_shape(hq_reconstructed) == _shape(hq_features), "HierarchicalVQ reconstructed shape mismatch; ensure scales[-1] equals feature-map size")
    _check(torch.isfinite(hq_commit_loss).all().item(), "HierarchicalVQ commit_loss is not finite")
    log(f"[ok] HierarchicalVQ: quantized={_shape(hq_quantized)} indices={[ _shape(ind) for ind in hq_indices ]} loss={float(hq_commit_loss.detach()):.6f}")

    log("All sim-and-hierarchical smoke checks passed.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run tiny tensor-only smoke checks for vector-quantize-pytorch SimVQ, ResidualSimVQ, and HierarchicalVQ.",
    )
    parser.add_argument("--seed", type=int, default=1234, help="Torch random seed for reproducible tiny tensors. Default: 1234.")
    parser.add_argument("--device", default="cpu", help="Torch device for checks. Default: cpu.")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-check success messages.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    run_checks(seed=args.seed, device=args.device, quiet=args.quiet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
