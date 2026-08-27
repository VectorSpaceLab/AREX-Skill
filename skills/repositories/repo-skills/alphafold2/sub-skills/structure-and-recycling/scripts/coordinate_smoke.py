#!/usr/bin/env python3
"""Download-free tiny coordinate, confidence, and recycling smoke test."""

from __future__ import annotations

import argparse
import sys
from typing import Any


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny Alphafold2 coordinate/confidence/recycling smoke."
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Torch device, for example cpu or cuda:0 (default: cpu).",
    )
    return parser.parse_args()


def _require_finite(name: str, value: Any) -> None:
    import torch

    if not torch.is_tensor(value):
        raise AssertionError(f"{name} is not a tensor: {type(value).__name__}")
    if not torch.isfinite(value).all().item():
        raise AssertionError(f"{name} contains non-finite values")


def run(device_name: str) -> None:
    try:
        import torch
        from alphafold2_pytorch import Alphafold2
    except Exception as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "cannot import alphafold2_pytorch and its structure dependencies; "
            "install a compatible torch, pytorch3d, and "
            "invariant-point-attention environment"
        ) from exc

    device = torch.device(device_name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(
            f"CUDA device {device_name!r} was requested, but CUDA is not available"
        )

    # Keep the fixture small enough for a shared CPU or GPU and avoid any data
    # or checkpoint access. The model is intentionally untrained.
    torch.manual_seed(1729)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(1729)
    try:
        torch.set_num_threads(1)
    except RuntimeError:
        pass

    model = Alphafold2(
        dim=32,
        depth=1,
        heads=1,
        dim_head=8,
        predict_coords=True,
        structure_module_depth=1,
        structure_module_heads=1,
        structure_module_dim_head=1,
    ).to(device).eval()

    seq = torch.tensor([[0, 4, 7, 12]], dtype=torch.long, device=device)
    msa = torch.tensor(
        [[[0, 4, 7, 12], [1, 5, 8, 13]]], dtype=torch.long, device=device
    )
    mask = torch.ones((1, 4), dtype=torch.bool, device=device)
    msa_mask = torch.ones((1, 2, 4), dtype=torch.bool, device=device)

    with torch.no_grad():
        coords, confidence = model(
            seq,
            msa,
            mask=mask,
            msa_mask=msa_mask,
            return_confidence=True,
        )
        assert coords.shape == (1, 4, 3), (
            f"unexpected coordinate shape: {tuple(coords.shape)}"
        )
        assert confidence.shape == (1, 4, 1), (
            f"unexpected confidence shape: {tuple(confidence.shape)}"
        )
        _require_finite("coords", coords)
        _require_finite("confidence", confidence)

        # Auxiliary output takes precedence when confidence is requested at
        # the same time: the result is (coords, ReturnValues), not a
        # three-item tuple. This is also the recyclable capture pass.
        first_result = model(
            seq,
            msa,
            mask=mask,
            msa_mask=msa_mask,
            return_aux_logits=True,
            return_confidence=True,
            return_recyclables=True,
        )
        assert isinstance(first_result, tuple) and len(first_result) == 2
        first_coords, first_ret = first_result
        assert first_coords.shape == (1, 4, 3)
        assert not hasattr(first_ret, "confidence")
        recycle = first_ret.recyclables
        assert recycle is not None, "return_recyclables did not populate ret.recyclables"
        assert recycle.coords.shape == (1, 4, 3)
        assert recycle.single_msa_repr_row.shape[:2] == (1, 4)
        assert recycle.pairwise_repr.shape[:3] == (1, 4, 4)
        for name in ("recycle.coords", "recycle.single_msa_repr_row", "recycle.pairwise_repr"):
            value = getattr(recycle, name.split(".", 1)[1])
            assert value.device == device, f"{name} is on {value.device}, expected {device}"
            _require_finite(name, value)
            assert not value.requires_grad, f"{name} must be detached"

        second_coords, second_ret = model(
            seq,
            msa,
            mask=mask,
            msa_mask=msa_mask,
            recyclables=recycle,
            return_aux_logits=True,
            return_recyclables=True,
        )
        assert second_coords.shape == first_coords.shape
        _require_finite("second_coords", second_coords)
        assert second_ret.recyclables is not None

    print(
        "structure smoke passed: "
        f"device={device} coords={tuple(coords.shape)} "
        f"confidence={tuple(confidence.shape)} aux_precedence=true recycled=2"
    )


def main() -> int:
    args = _parse_args()
    try:
        run(args.device)
    except Exception as exc:
        print(
            f"structure smoke failed on device={args.device!r}: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        if args.device.startswith("cuda"):
            print(
                "CUDA was requested but not verified; retry with the default "
                "--device cpu after checking shared-device memory.",
                file=sys.stderr,
            )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
