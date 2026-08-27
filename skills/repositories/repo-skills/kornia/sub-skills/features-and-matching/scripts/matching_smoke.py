#!/usr/bin/env python3
"""No-download smoke test for Kornia descriptor matching."""

from __future__ import annotations

import argparse

import torch

from kornia.feature import match_mnn, match_nn, match_snn
from kornia.feature.laf import get_laf_center, laf_from_center_scale_ori


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but torch.cuda.is_available() is false")
    return torch.device(requested)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args()
    device = choose_device(args.device)

    desc1 = torch.tensor([[0.0, 0.0], [1.0, 1.0], [3.0, 3.0]], device=device)
    desc2 = torch.tensor([[1.0, 1.0], [3.0, 3.0], [0.0, 0.0]], device=device)

    d_nn, i_nn = match_nn(desc1, desc2)
    expected_idx = torch.tensor([[0, 2], [1, 0], [2, 1]], device=device)
    assert d_nn.shape == (3, 1)
    assert i_nn.shape == (3, 2)
    assert torch.equal(i_nn, expected_idx), (i_nn, expected_idx)
    assert torch.allclose(d_nn, torch.zeros_like(d_nn))

    d_mnn, i_mnn = match_mnn(desc1, desc2)
    assert d_mnn.shape == (3, 1)
    assert torch.equal(i_mnn, expected_idx), i_mnn

    # A strict ratio threshold should reject a one-candidate ambiguous case.
    d_snn, i_snn = match_snn(desc1[:1], desc2[:1], 0.8)
    assert d_snn.numel() == 0
    assert i_snn.numel() == 0

    centers = torch.tensor([[[4.0, 5.0], [8.0, 9.0]]], device=device)
    scales = torch.ones(1, 2, 1, 1, device=device)
    orientations = torch.zeros(1, 2, 1, device=device)
    lafs = laf_from_center_scale_ori(centers, scales, orientations)
    recovered = get_laf_center(lafs)
    assert recovered.shape == centers.shape
    assert torch.allclose(recovered, centers)

    print("matching-smoke-ok", f"device={device}")


if __name__ == "__main__":
    main()
