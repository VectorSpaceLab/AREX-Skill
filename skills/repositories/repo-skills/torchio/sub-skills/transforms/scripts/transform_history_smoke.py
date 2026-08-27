#!/usr/bin/env python3
"""Smoke-test TorchIO transform history and inverse behavior on synthetic data."""

from __future__ import annotations

import argparse
import warnings
from typing import Any


def _make_subject(size: int, torch: Any, tio: Any) -> tuple[Any, Any]:
    values = torch.arange(size**3, dtype=torch.float32).reshape(1, size, size, size)
    subject = tio.Subject(
        image=tio.ScalarImage(values.clone()),
        label=tio.LabelMap((values.remainder(3)).to(torch.int16)),
    )
    return subject, values


def run(size: int, verbose: bool) -> None:
    import torch
    import torchio as tio

    if size < 4:
        raise ValueError("--size must be at least 4 so spatial assertions are useful")

    subject, original = _make_subject(size, torch, tio)
    pipeline = tio.Compose(
        [
            tio.Flip(axes=(0,), p=1),
            tio.Normalize(out_min=-1, out_max=1, include=["image"]),
        ]
    )

    transformed = pipeline(subject)
    names = [trace.name for trace in transformed.applied_transforms]
    assert names == ["Flip", "Normalize"], names
    assert transformed.image.shape == subject.image.shape
    assert transformed.label.shape == subject.label.shape
    assert transformed.image.data.min() >= -1.00001
    assert transformed.image.data.max() <= 1.00001

    inverse_transform = transformed.get_inverse_transform(ignore_intensity=True)
    assert isinstance(inverse_transform, tio.Compose)
    assert len(inverse_transform.transforms) >= 1

    restored_spatial = transformed.apply_inverse_transform(ignore_intensity=True)
    assert restored_spatial.image.data.shape == original.shape
    torch.testing.assert_close(restored_spatial.label.data, subject.label.data)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        restored_all = transformed.apply_inverse_transform()
    assert restored_all.image.shape == subject.image.shape
    assert not any("Unknown transform" in str(w.message) for w in caught)

    if verbose:
        print("applied history:", names)
        print("inverse repr:", inverse_transform)
        print("image range:", float(transformed.image.data.min()), float(transformed.image.data.max()))
    print("transform history smoke passed")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate TorchIO transform history and inverse behavior on synthetic tensors.",
    )
    parser.add_argument("--size", type=int, default=8, help="Synthetic cubic image size, default: 8")
    parser.add_argument("--verbose", action="store_true", help="Print applied transform details")
    args = parser.parse_args()
    run(size=args.size, verbose=args.verbose)


if __name__ == "__main__":
    main()
