#!/usr/bin/env python3
"""Smoke-test TorchIO include/exclude routing on synthetic scalar and label images."""

from __future__ import annotations

import argparse
from typing import Any


def _make_subject(size: int, torch: Any, tio: Any) -> Any:
    ramp = torch.linspace(0, 1, size**3, dtype=torch.float32).reshape(1, size, size, size)
    labels = torch.zeros(1, size, size, size, dtype=torch.int16)
    labels[..., size // 2 :, :, :] = 1
    return tio.Subject(
        t1=tio.ScalarImage(ramp.clone()),
        t2=tio.ScalarImage((ramp + 10).clone()),
        seg=tio.LabelMap(labels),
    )


def run(size: int, verbose: bool) -> None:
    import torch
    import torchio as tio

    if size < 4:
        raise ValueError("--size must be at least 4 so spatial assertions are useful")

    subject = _make_subject(size, torch, tio)
    original_t1 = subject.t1.data.clone()
    original_t2 = subject.t2.data.clone()
    original_seg = subject.seg.data.clone()

    pipeline = tio.Compose(
        [
            tio.Normalize(out_min=-1, out_max=1, include=["t1"]),
            tio.Gamma(log_gamma=0.5, include=["t1"]),
            tio.Flip(axes=(0,), exclude=["t2"]),
        ]
    )

    transformed = pipeline(subject)
    names = [trace.name for trace in transformed.applied_transforms]
    assert names == ["Normalize", "Gamma", "Flip"], names

    assert transformed.t1.shape == subject.t1.shape
    assert transformed.t2.shape == subject.t2.shape
    assert transformed.seg.shape == subject.seg.shape

    assert not torch.equal(transformed.t1.data, original_t1)
    torch.testing.assert_close(transformed.t2.data, original_t2)

    expected_seg = torch.flip(original_seg, dims=(-3,))
    torch.testing.assert_close(transformed.seg.data, expected_seg)
    assert set(torch.unique(transformed.seg.data).tolist()) <= {0, 1}

    assert transformed.t1.data.min() >= -1.00001
    assert transformed.t1.data.max() <= 1.00001

    if verbose:
        print("applied history:", names)
        print("image keys:", list(transformed.images.keys()))
        print("t1 range:", float(transformed.t1.data.min()), float(transformed.t1.data.max()))
    print("include/exclude smoke passed")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate TorchIO include/exclude routing with synthetic scalar and label tensors.",
    )
    parser.add_argument("--size", type=int, default=8, help="Synthetic cubic image size, default: 8")
    parser.add_argument("--verbose", action="store_true", help="Print transform and tensor details")
    args = parser.parse_args()
    run(size=args.size, verbose=args.verbose)


if __name__ == "__main__":
    main()
