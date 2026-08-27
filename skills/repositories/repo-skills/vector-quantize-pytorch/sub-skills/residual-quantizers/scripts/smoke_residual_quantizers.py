#!/usr/bin/env python3
"""Tiny CPU smoke checks for vector-quantize-pytorch residual quantizers."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

import torch
from vector_quantize_pytorch import GroupedResidualVQ, ResidualVQ


@dataclass
class CheckResult:
    name: str
    details: str


def _assert_shape(name: str, actual: torch.Size | tuple[int, ...], expected: tuple[int, ...]) -> None:
    actual_tuple = tuple(actual)
    if actual_tuple != expected:
        raise AssertionError(f"{name} shape {actual_tuple} != expected {expected}")


def _assert_close(name: str, left: torch.Tensor, right: torch.Tensor, atol: float = 1e-5) -> None:
    if not torch.allclose(left, right, atol=atol):
        max_diff = (left - right).abs().max().item()
        raise AssertionError(f"{name} mismatch; max absolute diff={max_diff:.6g}")


def check_residual(seed: int) -> list[CheckResult]:
    torch.manual_seed(seed)
    results: list[CheckResult] = []

    x = torch.randn(2, 5, 8, device="cpu")
    residual_vq = ResidualVQ(
        dim=8,
        num_quantizers=3,
        codebook_size=16,
        shared_codebook=True,
        stochastic_sample_codes=True,
        sample_codebook_temp=0.0,
    )
    residual_vq.eval()

    with torch.no_grad():
        quantized, indices, commit_loss, all_codes = residual_vq(x, return_all_codes=True)
        reconstructed = residual_vq.get_output_from_indices(indices)

    _assert_shape("ResidualVQ quantized", quantized.shape, (2, 5, 8))
    _assert_shape("ResidualVQ indices", indices.shape, (2, 5, 3))
    _assert_shape("ResidualVQ commit_loss", commit_loss.shape, (3,))
    _assert_shape("ResidualVQ all_codes", all_codes.shape, (3, 2, 5, 8))
    _assert_close("ResidualVQ eval reconstruction", quantized, reconstructed)
    results.append(CheckResult("residual_eval_reconstruction", "ResidualVQ eval indices reconstruct quantized output"))

    tuple_vq = ResidualVQ(dim=4, codebook_size=(4, 8))
    tuple_vq.eval()
    with torch.no_grad():
        tuple_quantized, tuple_indices, tuple_loss = tuple_vq(torch.randn(1, 3, 4, device="cpu"))
    _assert_shape("tuple ResidualVQ quantized", tuple_quantized.shape, (1, 3, 4))
    _assert_shape("tuple ResidualVQ indices", tuple_indices.shape, (1, 3, 2))
    _assert_shape("tuple ResidualVQ commit_loss", tuple_loss.shape, (2,))
    results.append(CheckResult("tuple_codebook_size", "Tuple codebook_size infers residual depth"))

    dropout_vq = ResidualVQ(
        dim=8,
        num_quantizers=4,
        codebook_size=8,
        quantize_dropout=True,
        quantize_dropout_cutoff_index=1,
    )
    dropout_vq.train()
    dropout_quantized, dropout_indices, dropout_loss = dropout_vq(
        torch.randn(1, 4, 8, device="cpu"),
        freeze_codebook=True,
        rand_quantize_dropout_fixed_seed=0,
    )
    _assert_shape("dropout ResidualVQ quantized", dropout_quantized.shape, (1, 4, 8))
    _assert_shape("dropout ResidualVQ indices", dropout_indices.shape, (1, 4, 4))
    _assert_shape("dropout ResidualVQ commit_loss", dropout_loss.shape, (4,))
    if not bool((dropout_indices == -1).any().item()):
        raise AssertionError("expected quantize_dropout training indices to contain at least one -1 marker")
    results.append(CheckResult("quantize_dropout_marker", "Training quantize_dropout emitted -1 skipped-layer markers"))

    return results


def check_grouped(seed: int) -> list[CheckResult]:
    torch.manual_seed(seed + 1)
    results: list[CheckResult] = []

    grouped_vq = GroupedResidualVQ(
        dim=8,
        groups=2,
        num_quantizers=2,
        codebook_size=8,
    )
    grouped_vq.eval()
    x = torch.randn(1, 4, 8, device="cpu")

    with torch.no_grad():
        quantized, indices, commit_loss, per_group_all_codes = grouped_vq(x, return_all_codes=True)
        reconstructed = grouped_vq.get_output_from_indices(indices)

    _assert_shape("GroupedResidualVQ quantized", quantized.shape, (1, 4, 8))
    _assert_shape("GroupedResidualVQ indices", indices.shape, (2, 1, 4, 2))
    _assert_shape("GroupedResidualVQ commit_loss", commit_loss.shape, (2, 2))
    if not isinstance(per_group_all_codes, tuple) or len(per_group_all_codes) != 2:
        raise AssertionError("GroupedResidualVQ return_all_codes should return a tuple with one tensor per group")
    for group_index, group_codes in enumerate(per_group_all_codes):
        _assert_shape(f"GroupedResidualVQ all_codes group {group_index}", group_codes.shape, (2, 1, 4, 4))
    _assert_close("GroupedResidualVQ eval reconstruction", quantized, reconstructed)
    results.append(CheckResult("grouped_eval_reconstruction", "GroupedResidualVQ grouped indices reconstruct quantized output"))

    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run tiny CPU smoke checks for ResidualVQ and GroupedResidualVQ. "
            "The checks validate eval reconstruction, tuple codebook_size depth, "
            "training dropout -1 markers, and grouped index shapes."
        )
    )
    parser.add_argument(
        "--case",
        choices=("all", "residual", "grouped"),
        default="all",
        help="subset of checks to run (default: all)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="torch random seed for deterministic tiny tensors (default: 0)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print each passed check instead of only the final summary",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    torch.set_num_threads(max(1, min(torch.get_num_threads(), 2)))

    results: list[CheckResult] = []
    if args.case in ("all", "residual"):
        results.extend(check_residual(args.seed))
    if args.case in ("all", "grouped"):
        results.extend(check_grouped(args.seed))

    if args.verbose:
        for result in results:
            print(f"PASS {result.name}: {result.details}")
    print(f"PASS residual quantizer smoke checks ({len(results)} checks)")


if __name__ == "__main__":
    main()
