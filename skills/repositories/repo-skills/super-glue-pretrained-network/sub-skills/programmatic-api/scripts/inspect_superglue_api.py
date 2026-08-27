#!/usr/bin/env python3
"""Inspect the SuperGlue programmatic API from an explicit repo root."""

from __future__ import annotations

import argparse
import importlib
import inspect
import sys
from pathlib import Path
from pprint import pformat

REQUIRED_WEIGHTS = [
    Path("models/weights/superpoint_v1.pth"),
    Path("models/weights/superglue_indoor.pth"),
    Path("models/weights/superglue_outdoor.pth"),
]

MODULE_NAMES = [
    "models.matching",
    "models.superpoint",
    "models.superglue",
    "models.utils",
]

UTILITY_CALLABLES = {
    "models.superpoint": [
        "simple_nms",
        "remove_borders",
        "top_k_keypoints",
        "sample_descriptors",
    ],
    "models.superglue": [
        "normalize_keypoints",
        "log_sinkhorn_iterations",
        "log_optimal_transport",
        "arange_like",
    ],
    "models.utils": [
        "process_resize",
        "frame2tensor",
        "read_image",
        "estimate_pose",
        "rotate_intrinsics",
        "rotate_pose_inplane",
        "scale_intrinsics",
        "to_homogeneous",
        "compute_epipolar_error",
        "compute_pose_error",
        "pose_auc",
        "plot_image_pair",
        "plot_keypoints",
        "plot_matches",
        "make_matching_plot",
        "make_matching_plot_fast",
        "error_colormap",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print the SuperGlue programmatic API signatures, defaults, imports, "
            "and local weight status."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        type=Path,
        help="Path to the repository root that contains the models/ package.",
    )
    return parser.parse_args()


def ensure_repo_root(repo_root: Path) -> Path:
    repo_root = repo_root.expanduser().resolve()
    if not repo_root.exists():
        raise SystemExit(f"repo root does not exist: {repo_root}")
    if not (repo_root / "models").is_dir():
        raise SystemExit(f"repo root does not contain models/: {repo_root}")
    return repo_root


def add_to_path(repo_root: Path) -> None:
    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)


def sig(obj) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "<signature unavailable>"


def section(title: str) -> None:
    print(f"\n== {title} ==")


def main() -> int:
    args = parse_args()
    repo_root = ensure_repo_root(args.repo_root)
    add_to_path(repo_root)

    modules = {module_name: importlib.import_module(module_name) for module_name in MODULE_NAMES}

    from models.matching import Matching
    from models.superpoint import SuperPoint
    from models.superglue import SuperGlue
    import torch

    section("Imports")
    for module_name, module in modules.items():
        print(f"{module_name} -> {Path(module.__file__).resolve()}")
    print(
        "torch -> "
        f"{torch.__version__} | cuda_available={torch.cuda.is_available()} | "
        f"device_count={torch.cuda.device_count() if torch.cuda.is_available() else 0}"
    )

    section("Class signatures")
    print(f"Matching.__init__{sig(Matching.__init__)}")
    print(f"Matching.forward{sig(Matching.forward)}")
    print(f"SuperPoint.__init__{sig(SuperPoint.__init__)}")
    print(f"SuperPoint.forward{sig(SuperPoint.forward)}")
    print(f"SuperGlue.__init__{sig(SuperGlue.__init__)}")
    print(f"SuperGlue.forward{sig(SuperGlue.forward)}")

    section("Default configs")
    print(f"SuperPoint.default_config = {pformat(SuperPoint.default_config, sort_dicts=False)}")
    print(f"SuperGlue.default_config = {pformat(SuperGlue.default_config, sort_dicts=False)}")

    section("Utility signatures")
    for module_name, names in UTILITY_CALLABLES.items():
        module = modules[module_name]
        for name in names:
            obj = getattr(module, name)
            print(f"{module_name}.{name}{sig(obj)}")

    section("Weights")
    missing = []
    for rel in REQUIRED_WEIGHTS:
        path = repo_root / rel
        status = "present" if path.is_file() else "missing"
        print(f"{rel.as_posix()} -> {status}")
        if status == "missing":
            missing.append(rel.as_posix())

    if missing:
        print("\nMissing required checkpoint files:")
        for item in missing:
            print(f"- {item}")
        return 2

    section("Quick pointers")
    print("- Matching is easiest to use one pair at a time.")
    print("- Keep images grayscale, float, and shaped 1x1xHxW.")
    print("- Use eval() and torch.no_grad() for inference.")
    print("- Use the bundled smoke helper to confirm a forward pass.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
