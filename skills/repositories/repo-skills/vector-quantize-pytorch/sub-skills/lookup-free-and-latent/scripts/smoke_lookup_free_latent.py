#!/usr/bin/env python3
"""Tiny CPU smoke checks for lookup-free and latent quantizers.

This script intentionally avoids dataset downloads, training loops, optional example
dependencies, and repository-local imports. It only requires an installed
`vector-quantize-pytorch` package plus PyTorch.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import torch
from torch import nn

from vector_quantize_pytorch import (
    BinaryMapper,
    EvoLFQ,
    GroupedResidualLFQ,
    LFQ,
    LatentQuantize,
    ResidualLFQ,
)


def assert_shape(name: str, tensor: torch.Tensor, expected: tuple[int, ...]) -> None:
    actual = tuple(tensor.shape)
    if actual != expected:
        raise AssertionError(f"{name} shape {actual} != expected {expected}")


def assert_close(name: str, actual: torch.Tensor, expected: torch.Tensor) -> None:
    if not torch.allclose(actual, expected):
        max_diff = (actual - expected).abs().max().item()
        raise AssertionError(f"{name} tensors are not close; max diff={max_diff:.6g}")


def check_lfq(device: torch.device) -> dict[str, Any]:
    lfq = LFQ(codebook_size=16, dim=4, entropy_loss_weight=0.0).to(device)
    lfq.eval()

    seq = torch.tensor(
        [
            [[-1.0, -0.1, 0.2, 0.7], [0.3, -0.4, 0.5, -0.6], [0.9, 0.8, -0.7, -0.2]],
            [[0.1, 0.2, 0.3, 0.4], [-0.5, -0.6, -0.7, -0.8], [0.2, -0.2, 0.2, -0.2]],
        ],
        device=device,
    )
    quantized, indices, aux_loss = lfq(seq)
    assert_shape("lfq.sequence.quantized", quantized, (2, 3, 4))
    assert_shape("lfq.sequence.indices", indices, (2, 3))
    assert_close("lfq.sequence.roundtrip", quantized, lfq.indices_to_codes(indices))

    multi = LFQ(codebook_size=4, dim=4, num_codebooks=2, entropy_loss_weight=0.0).to(device)
    multi.eval()
    image = torch.randn(1, 4, 2, 2, device=device)
    image_quantized, image_indices, _ = multi(image)
    assert_shape("lfq.image.quantized", image_quantized, (1, 4, 2, 2))
    assert_shape("lfq.image.indices", image_indices, (1, 2, 2, 2))
    assert_close("lfq.image.roundtrip", image_quantized, multi.indices_to_codes(image_indices))

    return {
        "sequence_indices_shape": list(indices.shape),
        "image_multicodebook_indices_shape": list(image_indices.shape),
        "aux_loss_is_scalar": aux_loss.ndim == 0,
    }


def check_residual_lfq(device: torch.device) -> dict[str, Any]:
    residual = ResidualLFQ(dim=4, codebook_size=16, num_quantizers=2).to(device)
    residual.eval()

    x = torch.randn(1, 5, 4, device=device)
    quantized, indices, losses = residual(x)
    reconstructed = residual.get_output_from_indices(indices)

    assert_shape("residual_lfq.quantized", quantized, (1, 5, 4))
    assert_shape("residual_lfq.indices", indices, (1, 5, 2))
    assert_shape("residual_lfq.losses", losses, (2,))
    assert_close("residual_lfq.roundtrip", quantized, reconstructed)

    grouped = GroupedResidualLFQ(dim=4, groups=2, codebook_size=4, num_quantizers=2).to(device)
    grouped.eval()

    grouped_quantized, grouped_indices, grouped_losses = grouped(x)
    grouped_reconstructed = grouped.get_output_from_indices(grouped_indices)

    assert_shape("grouped_residual_lfq.quantized", grouped_quantized, (1, 5, 4))
    assert_shape("grouped_residual_lfq.indices", grouped_indices, (2, 1, 5, 2))
    assert_shape("grouped_residual_lfq.losses", grouped_losses, (2, 2))
    assert_close("grouped_residual_lfq.roundtrip", grouped_quantized, grouped_reconstructed)

    return {
        "residual_indices_shape": list(indices.shape),
        "grouped_indices_shape": list(grouped_indices.shape),
    }


def check_latent_quantize(device: torch.device) -> dict[str, Any]:
    latent = LatentQuantize(levels=[3, 5], dim=4, num_codebooks=2).to(device)

    x = torch.randn(1, 4, 3, device=device)
    quantized, indices, loss = latent(x)
    reconstructed = latent.indices_to_codes(indices)

    assert_shape("latent_quantize.quantized", quantized, (1, 4, 3))
    assert_shape("latent_quantize.indices", indices, (1, 3, 2))
    assert_close("latent_quantize.roundtrip", quantized, reconstructed)
    if loss.ndim != 0:
        raise AssertionError("latent_quantize.loss is not scalar")

    latent_int = LatentQuantize(levels=5, dim=4, codebook_dim=2, num_codebooks=2).to(device)
    int_quantized, int_indices, _ = latent_int(x)
    assert_shape("latent_quantize_int.quantized", int_quantized, (1, 4, 3))
    assert_shape("latent_quantize_int.indices", int_indices, (1, 3, 2))

    return {
        "indices_shape": list(indices.shape),
        "int_levels_indices_shape": list(int_indices.shape),
        "loss_is_scalar": loss.ndim == 0,
    }


def check_binary_mapper(device: torch.device) -> dict[str, Any]:
    mapper = BinaryMapper(bits=3, deterministic_on_eval=True).to(device)
    mapper.eval()

    logits = torch.randn(2, 4, 3, device=device)
    one_hot, indices, aux_loss = mapper(
        logits,
        deterministic=True,
        calc_aux_loss=True,
        return_indices=True,
        reduce_aux_kl_loss=False,
    )

    assert_shape("binary_mapper.one_hot", one_hot, (2, 4, 8))
    assert_shape("binary_mapper.indices", indices, (2, 4))
    assert_shape("binary_mapper.aux_loss", aux_loss, (2, 4))

    log_prob_from_indices = mapper.log_prob(logits, indices=indices)
    log_prob_from_one_hot = mapper.log_prob(logits, one_hot=one_hot)
    assert_shape("binary_mapper.log_prob", log_prob_from_indices, (2, 4))
    assert_close("binary_mapper.log_prob_roundtrip", log_prob_from_indices, log_prob_from_one_hot)

    return {
        "one_hot_shape": list(one_hot.shape),
        "indices_shape": list(indices.shape),
        "aux_loss_shape": list(aux_loss.shape),
    }


def check_evo_lfq(device: torch.device) -> dict[str, Any]:
    class TinyEncoder(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.net = nn.Linear(6, 4)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.net(x)

    class TinyDecoder(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.net = nn.Linear(4, 6)

        def forward(self, codes: torch.Tensor) -> torch.Tensor:
            return self.net(codes)

    model = EvoLFQ(
        encoder=TinyEncoder(),
        decoder=TinyDecoder(),
        codebook_size=4,
        num_codebooks=2,
        pop_size=4,
        elitism_count=1,
        generations=1,
        entropy_loss_weight=0.0,
    ).to(device)
    model.eval()

    x = torch.randn(2, 6, device=device)
    reconstructed, indices, aux_loss = model(x)
    assert_shape("evo_lfq.reconstructed", reconstructed, (2, 6))
    assert_shape("evo_lfq.indices", indices, (2, 2))
    if aux_loss.ndim != 0:
        raise AssertionError("evo_lfq.aux_loss is not scalar")

    bits = model.encode(x)
    assert_shape("evo_lfq.bits", bits, (2, 4))
    decoded = model.decode_bits(bits)
    assert_shape("evo_lfq.decode_bits", decoded, (2, 6))

    return {
        "indices_shape": list(indices.shape),
        "bits_shape": list(bits.shape),
        "decoded_shape": list(decoded.shape),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run tiny CPU smoke checks for LFQ, ResidualLFQ, LatentQuantize, BinaryMapper, and EvoLFQ."
    )
    parser.add_argument("--seed", type=int, default=0, help="Torch random seed for deterministic tiny tensors.")
    parser.add_argument("--skip-evo", action="store_true", help="Skip the optional EvoLFQ wrapper forward check.")
    parser.add_argument("--quiet", action="store_true", help="Only print a compact success line.")
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    device = torch.device("cpu")

    results: dict[str, Any] = {
        "lfq": check_lfq(device),
        "residual_lfq": check_residual_lfq(device),
        "latent_quantize": check_latent_quantize(device),
        "binary_mapper": check_binary_mapper(device),
    }

    if not args.skip_evo:
        results["evo_lfq"] = check_evo_lfq(device)

    if args.quiet:
        print("lookup-free-and-latent smoke: ok")
    else:
        print(json.dumps({"status": "ok", "checks": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
