#!/usr/bin/env python3
"""Print representative policy and backbone signatures.

This script is intentionally read-only: it imports representative classes when
possible, prints constructor and method signatures, and exits without downloads,
training, or checkpoint mutation.
"""

from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path
from typing import Sequence

CASES = [
    (
        "BaseLowdimPolicy",
        "diffusion_policy.policy.base_lowdim_policy",
        "BaseLowdimPolicy",
        ["predict_action", "set_normalizer", "reset"],
    ),
    (
        "BaseImagePolicy",
        "diffusion_policy.policy.base_image_policy",
        "BaseImagePolicy",
        ["predict_action", "set_normalizer", "reset"],
    ),
    (
        "ConditionalUnet1D",
        "diffusion_policy.model.diffusion.conditional_unet1d",
        "ConditionalUnet1D",
        ["forward"],
    ),
    (
        "TransformerForDiffusion",
        "diffusion_policy.model.diffusion.transformer_for_diffusion",
        "TransformerForDiffusion",
        ["forward", "get_optim_groups", "configure_optimizers"],
    ),
    (
        "DiffusionUnetLowdimPolicy",
        "diffusion_policy.policy.diffusion_unet_lowdim_policy",
        "DiffusionUnetLowdimPolicy",
        ["predict_action", "set_normalizer", "compute_loss", "conditional_sample"],
    ),
]


def add_repo_root_to_path() -> None:
    """Add the repository root to sys.path when running from the skill tree."""

    this_file = Path(__file__).resolve()
    for parent in this_file.parents:
        if (parent / "diffusion_policy").is_dir():
            parent_str = str(parent)
            if parent_str not in sys.path:
                sys.path.insert(0, parent_str)
            return


def import_class(module_name: str, class_name: str):
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def format_signature(obj) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "<signature unavailable>"


def describe_case(label: str, module_name: str, class_name: str, methods: Sequence[str]) -> bool:
    try:
        cls = import_class(module_name, class_name)
    except Exception as exc:  # pragma: no cover - graceful fallback path
        print(f"[missing] {label}")
        print(f"  module: {module_name}")
        print(f"  error: {exc.__class__.__name__}: {exc}")
        return False

    print(f"[ok] {label}")
    print(f"  module: {module_name}")
    print(f"  class signature: {format_signature(cls)}")
    for method_name in methods:
        method = getattr(cls, method_name, None)
        if method is None:
            print(f"  {method_name}: <missing>")
            continue
        print(f"  {method_name}{format_signature(method)}")
    print()
    return True


def main() -> int:
    add_repo_root_to_path()

    print("Policy interface inspection")
    print("===========================")
    print()

    ok = 0
    for case in CASES:
        if describe_case(*case):
            ok += 1

    print(f"Summary: {ok}/{len(CASES)} representative classes imported successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
