#!/usr/bin/env python3
"""Tiny CPU smoke checks for vector-quantize-pytorch scalar quantizers.

The script intentionally uses small random tensors only. It does not download
or train datasets and does not require any source tree.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run tiny CPU smoke checks for FSQ, FSP, ResidualFSQ, and GroupedResidualFSQ.",
    )
    parser.add_argument(
        "--case",
        choices=("all", "fsq", "fsp", "residual"),
        default="all",
        help="Subset to run. Default: all.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Torch random seed for reproducible smoke tensors. Default: 0.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary instead of human-readable lines.",
    )
    return parser.parse_args()


def load_runtime():
    try:
        import torch
        from vector_quantize_pytorch import FSQ, FSP, GroupedResidualFSQ, ResidualFSQ
    except Exception as exc:  # pragma: no cover - import error path is user-facing
        message = (
            "Failed to import torch and vector_quantize_pytorch. Install the package "
            "and its base dependencies, then rerun this smoke script. "
            f"Original error: {type(exc).__name__}: {exc}"
        )
        raise SystemExit(message) from exc

    return torch, FSQ, FSP, ResidualFSQ, GroupedResidualFSQ


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def shape(tensor: Any) -> tuple[int, ...]:
    return tuple(int(dim) for dim in tensor.shape)


def check_fsq(torch, FSQ) -> dict[str, Any]:
    torch.manual_seed(11)

    fsq = FSQ([8, 5, 5, 5])
    x = torch.randn(1, 16, 4)
    quantized, indices = fsq(x)
    recovered = fsq.indices_to_codes(indices)

    require(shape(quantized) == shape(x), "FSQ sequence output shape mismatch")
    require(shape(indices) == (1, 16), "FSQ sequence index shape mismatch")
    require(indices.dtype == torch.int32, "FSQ indices should be int32 in this package version")
    require(torch.equal(quantized, recovered), "FSQ no-projection roundtrip should be exact")

    fsq_no_indices = FSQ([8, 5, 5, 5], return_indices=False)
    no_idx_quantized, no_indices = fsq_no_indices(x)
    require(shape(no_idx_quantized) == shape(x), "FSQ return_indices=False output shape mismatch")
    require(no_indices is None, "FSQ return_indices=False should return None for indices")

    projected = FSQ(levels=[4, 4], dim=6, num_codebooks=2)
    x_projected = torch.randn(2, 5, 6)
    projected_quantized, projected_indices = projected(x_projected)
    projected_recovered = projected.indices_to_codes(projected_indices)
    require(projected.has_projections, "Projected FSQ should report has_projections=True")
    require(shape(projected_quantized) == shape(x_projected), "Projected FSQ output shape mismatch")
    require(shape(projected_indices) == (2, 5, 2), "Projected multi-codebook FSQ index shape mismatch")
    require(shape(projected_recovered) == shape(x_projected), "Projected FSQ recovered shape mismatch")
    require(torch.allclose(projected_quantized, projected_recovered), "Projected FSQ roundtrip mismatch")

    image_fsq = FSQ(levels=[4, 4, 4], dim=3, channel_first=True)
    image = torch.randn(2, 3, 4, 5)
    image_quantized, image_indices = image_fsq(image)
    require(shape(image_quantized) == shape(image), "FSQ image output shape mismatch")
    require(shape(image_indices) == (2, 4, 5), "FSQ image index shape mismatch")
    require(shape(image_fsq.indices_to_codes(image_indices)) == shape(image), "FSQ image recovered shape mismatch")

    return {
        "fsq_sequence": {"quantized": shape(quantized), "indices": shape(indices)},
        "fsq_no_indices": {"indices": None},
        "fsq_projected": {"quantized": shape(projected_quantized), "indices": shape(projected_indices)},
        "fsq_image": {"quantized": shape(image_quantized), "indices": shape(image_indices)},
    }


def check_fsp(torch, FSP) -> dict[str, Any]:
    torch.manual_seed(22)

    fsp = FSP(levels=[8, 5, 5, 5], act_name="normal", vector_norm="none")
    x = torch.randn(1, 16, 4)
    quantized, indices, norm_loss, other_info = fsp(x)
    require(shape(quantized) == shape(x), "FSP sequence output shape mismatch")
    require(shape(indices) == (1, 16), "FSP sequence index shape mismatch")
    require(indices.dtype == torch.int32, "FSP indices should be int32 in this package version")
    require(float(norm_loss.item()) == 0.0, "FSP vector_norm='none' should return zero norm loss")
    require("level_indices" in other_info and "norm_info" in other_info, "FSP other_info missing expected keys")

    eval_fsp = FSP(levels=[8, 5, 5, 5], dim=8)
    eval_fsp.eval()
    x_projected = torch.randn(1, 12, 8)
    with torch.no_grad():
        projected_quantized, projected_indices, _, _ = eval_fsp(x_projected)
        projected_recovered = eval_fsp.indices_to_codes(projected_indices)
    require(eval_fsp.has_projections, "Projected FSP should report has_projections=True")
    require(shape(projected_quantized) == shape(x_projected), "Projected FSP output shape mismatch")
    require(shape(projected_indices) == (1, 12), "Projected FSP index shape mismatch")
    require(torch.allclose(projected_quantized, projected_recovered, atol=1e-4), "Projected eval FSP roundtrip mismatch")

    level_indices = torch.tensor([[[7, 4, 4, 4]]])
    flat_index = fsp.level_indices_to_indices(level_indices)
    require(int(flat_index.item()) == 999, "FSP mixed-radix encoding check failed")
    require(torch.equal(fsp.indices_to_level_indices(flat_index), level_indices), "FSP mixed-radix decode check failed")

    image_fsp = FSP(levels=[8, 5, 5, 5], dim=4, channel_first=True)
    image_fsp.eval()
    image = torch.randn(2, 4, 4, 5)
    with torch.no_grad():
        image_quantized, image_indices, _, _ = image_fsp(image)
        image_recovered = image_fsp.indices_to_codes(image_indices)
    require(shape(image_quantized) == shape(image), "FSP image output shape mismatch")
    require(shape(image_indices) == (2, 4, 5), "FSP image index shape mismatch")
    require(torch.allclose(image_quantized, image_recovered, atol=1e-5), "FSP image eval roundtrip mismatch")

    encoder = torch.nn.Linear(8, 8)
    train_fsp = FSP(levels=[4, 4], dim=8, quantize_rate=0.5, vector_norm="none")
    decoder = torch.nn.Linear(8, 8)
    train_x = torch.randn(2, 4, 8, requires_grad=True)
    hidden = encoder(train_x)
    train_quantized, train_indices, train_norm_loss, _ = train_fsp(hidden)
    train_out = decoder(train_quantized)
    loss = train_out.square().mean() + train_norm_loss
    loss.backward()
    require(train_x.grad is not None, "FSP training smoke did not produce input gradients")
    require(torch.isfinite(train_x.grad).all().item(), "FSP training smoke produced non-finite gradients")
    require((train_indices >= 0).all().item(), "FSP training smoke produced negative indices")

    return {
        "fsp_sequence": {"quantized": shape(quantized), "indices": shape(indices)},
        "fsp_projected_eval": {"quantized": shape(projected_quantized), "indices": shape(projected_indices)},
        "fsp_index_encoding_max": int(flat_index.item()),
        "fsp_image": {"quantized": shape(image_quantized), "indices": shape(image_indices)},
        "fsp_training_grad": True,
    }


def check_residual(torch, ResidualFSQ, GroupedResidualFSQ) -> dict[str, Any]:
    torch.manual_seed(33)

    residual = ResidualFSQ(dim=8, levels=[4, 4], num_quantizers=3)
    residual.eval()
    x = torch.randn(1, 10, 8)
    with torch.no_grad():
        quantized, indices = residual(x)
        recovered = residual.get_output_from_indices(indices)
        quantized_all, indices_all, all_codes = residual(x, return_all_codes=True)

    require(shape(quantized) == shape(x), "ResidualFSQ output shape mismatch")
    require(shape(indices) == (1, 10, 3), "ResidualFSQ index shape mismatch")
    require(shape(recovered) == shape(x), "ResidualFSQ recovered shape mismatch")
    require(torch.allclose(quantized, recovered), "ResidualFSQ eval reconstruction mismatch")
    require(shape(quantized_all) == shape(x), "ResidualFSQ return_all_codes output shape mismatch")
    require(shape(indices_all) == (1, 10, 3), "ResidualFSQ return_all_codes index shape mismatch")
    require(shape(all_codes) == (3, 1, 10, 2), "ResidualFSQ all_codes shape mismatch")

    grouped = GroupedResidualFSQ(dim=8, groups=2, levels=[4, 4], num_quantizers=2)
    grouped.eval()
    grouped_x = torch.randn(1, 7, 8)
    with torch.no_grad():
        grouped_quantized, grouped_indices = grouped(grouped_x)
        grouped_recovered = grouped.get_output_from_indices(grouped_indices)

    require(shape(grouped_quantized) == shape(grouped_x), "GroupedResidualFSQ output shape mismatch")
    require(shape(grouped_indices) == (2, 1, 7, 2), "GroupedResidualFSQ index shape mismatch")
    require(shape(grouped_recovered) == shape(grouped_x), "GroupedResidualFSQ recovered shape mismatch")
    require(torch.allclose(grouped_quantized, grouped_recovered), "GroupedResidualFSQ eval reconstruction mismatch")

    return {
        "residual_fsq": {"quantized": shape(quantized), "indices": shape(indices), "all_codes": shape(all_codes)},
        "grouped_residual_fsq": {"quantized": shape(grouped_quantized), "indices": shape(grouped_indices)},
    }


def main() -> int:
    args = parse_args()
    torch, FSQ, FSP, ResidualFSQ, GroupedResidualFSQ = load_runtime()
    torch.manual_seed(args.seed)

    summary: dict[str, Any] = {
        "torch_version": torch.__version__,
        "device": "cpu",
        "case": args.case,
    }

    if args.case in ("all", "fsq"):
        summary.update(check_fsq(torch, FSQ))

    if args.case in ("all", "fsp"):
        summary.update(check_fsp(torch, FSP))

    if args.case in ("all", "residual"):
        summary.update(check_residual(torch, ResidualFSQ, GroupedResidualFSQ))

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("scalar quantizer smoke checks passed")
        for key, value in summary.items():
            print(f"- {key}: {value}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"scalar quantizer smoke check failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
