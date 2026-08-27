#!/usr/bin/env python3
"""Check common Albumentations pipeline-composition contracts on tiny fixtures."""

from __future__ import annotations

import argparse
import random
import sys
from typing import Callable, Any

A: Any = None
np: Any = None


def _load_runtime() -> None:
    global A, np
    if A is not None and np is not None:
        return
    try:
        import albumentations as albumentations_module
        import numpy as numpy_module
    except Exception as exc:  # pragma: no cover - meant for user environments
        raise SystemExit(f"Could not import runtime dependencies: {exc}") from exc
    A = albumentations_module
    np = numpy_module


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _tiny_fixtures() -> tuple[Any, Any, Any]:
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    image[:, :4, 0] = 255
    mask = np.zeros((8, 8), dtype=np.uint8)
    mask[:, :4] = 1
    depth = np.arange(64, dtype=np.uint8).reshape(8, 8)
    return image, mask, depth


def check_strict_and_shapes() -> None:
    image, mask, _ = _tiny_fixtures()
    pipeline = A.Compose([A.NoOp()], strict=True)
    pipeline(image=image, mask=mask)

    try:
        pipeline(image=image, unknown=image)
    except ValueError as exc:
        _assert("not in available keys" in str(exc), "strict mode raised an unexpected message")
    else:
        raise AssertionError("strict=True accepted an unknown key")

    bad_mask = np.zeros((7, 8), dtype=np.uint8)
    try:
        pipeline(image=image, mask=bad_mask)
    except ValueError as exc:
        _assert("Height and Width" in str(exc), "shape check raised an unexpected message")
    else:
        raise AssertionError("is_check_shapes=True accepted mismatched image/mask shapes")


def check_additional_targets_and_mask_interpolation() -> None:
    image, mask, depth = _tiny_fixtures()
    pipeline = A.Compose(
        [A.Resize(4, 4, p=1), A.HorizontalFlip(p=1)],
        additional_targets={"depth": "mask"},
        strict=True,
        mask_interpolation=0,
        seed=137,
    )
    result = pipeline(image=image, mask=mask, depth=depth)
    _assert(result["image"].shape[:2] == (4, 4), "image was not resized")
    _assert(result["mask"].shape == (4, 4), "mask was not resized")
    _assert(result["depth"].shape == (4, 4), "additional depth target was not resized")
    _assert(result["depth"].dtype == depth.dtype, "depth dtype changed unexpectedly")

    for transform in pipeline.transforms:
        if hasattr(transform, "mask_interpolation"):
            _assert(transform.mask_interpolation == 0, "top-level mask_interpolation was not propagated")


def check_operator_and_tracking_contracts() -> None:
    image, mask, _ = _tiny_fixtures()
    base = A.Compose(
        [A.HorizontalFlip(p=1)],
        additional_targets={"mask2": "mask"},
        strict=True,
        is_check_shapes=False,
        seed=137,
        save_applied_params=True,
    )
    edited = base + A.Blur(blur_limit=3, p=1)
    _assert(edited is not base, "operator edit mutated the original instance")
    _assert(len(base.transforms) == 1 and len(edited.transforms) == 2, "operator edit produced wrong transform count")
    _assert(edited.additional_targets == {"mask2": "mask"}, "additional_targets were not preserved")
    _assert(edited.strict is True, "strict flag was not preserved")
    _assert(edited.is_check_shapes is False, "is_check_shapes flag was not preserved")

    result = edited(image=image, mask=mask, mask2=mask.copy())
    _assert("applied_transforms" in result, "save_applied_params did not add applied_transforms")
    applied_names = [name for name, _params in result["applied_transforms"]]
    _assert("HorizontalFlip" in applied_names and "Blur" in applied_names, "expected transforms were not tracked")

    removed = edited - A.HorizontalFlip
    _assert(len(removed.transforms) == 1, "subtraction did not remove one transform")
    _assert(type(removed.transforms[0]) is A.Blur, "subtraction removed the wrong transform")

    try:
        edited + A.Sequential([A.NoOp()])
    except TypeError as exc:
        _assert("BasicTransform" in str(exc), "invalid operator operand raised an unexpected message")
    else:
        raise AssertionError("operator accepted a nested compose operand")


def check_seed_contract() -> None:
    image, _, _ = _tiny_fixtures()
    make_pipeline: Callable[[], object] = lambda: A.Compose(
        [A.HorizontalFlip(p=0.5), A.RandomBrightnessContrast(p=0.5)],
        seed=137,
    )

    first = make_pipeline()
    second = make_pipeline()
    np.random.seed(1)
    random.seed(1)
    out1 = first(image=image.copy())["image"]
    np.random.seed(999)
    random.seed(999)
    out2 = second(image=image.copy())["image"]
    np.testing.assert_array_equal(out1, out2, "same Compose seed did not produce matching first results")

    first.set_random_seed(137)
    repeated = first(image=image.copy())["image"]
    np.testing.assert_array_equal(out1, repeated, "set_random_seed did not reset the sequence")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run tiny Albumentations composition contract checks.",
    )
    parser.add_argument(
        "--case",
        choices=["all", "strict", "targets", "operators", "seed"],
        default="all",
        help="Subset of checks to run; defaults to all.",
    )
    args = parser.parse_args()
    _load_runtime()

    checks: dict[str, Callable[[], None]] = {
        "strict": check_strict_and_shapes,
        "targets": check_additional_targets_and_mask_interpolation,
        "operators": check_operator_and_tracking_contracts,
        "seed": check_seed_contract,
    }
    selected = checks if args.case == "all" else {args.case: checks[args.case]}

    for name, check in selected.items():
        check()
        print(f"ok: {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
