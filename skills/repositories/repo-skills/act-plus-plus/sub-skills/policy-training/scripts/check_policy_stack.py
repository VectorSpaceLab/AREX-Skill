#!/usr/bin/env python3
"""Smoke-check the ACT++ policy-training stack.

This helper imports the repository's training/evaluation modules from an
explicit checkout, checks the CUDA backend, and verifies the policy wrapper
surface without launching a training loop.

Example:
    python scripts/check_policy_stack.py --repo-root /path/to/act-plus-plus
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def add_repo_root(repo_root: str) -> None:
    root = Path(repo_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"repo root does not exist: {root}")
    sys.path.insert(0, str(root))


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check ACT++ policy-training imports.")
    parser.add_argument("--repo-root", required=True, help="Path to an ACT++ checkout.")
    args = parser.parse_args()

    add_repo_root(args.repo_root)

    try:
        import torch
        import policy
        import imitate_episodes
        import train_latent_model
        import detr.main
        import detr.models.latent_model
        import robomimic.algo.diffusion_policy as robodiff
    except Exception as exc:
        print(f"IMPORT FAIL: {type(exc).__name__}: {exc}")
        print("Missing optional dependency or incompatible package surface likely caused the failure.")
        return 1

    print(f"MUJOCO_GL={os.environ.get('MUJOCO_GL', '<unset>')}")
    print(f"CUDA available={torch.cuda.is_available()}")
    print(f"CUDA device count={torch.cuda.device_count()}")
    print(f"policy module={policy.__file__}")
    print(f"imitate_episodes module={imitate_episodes.__file__}")
    print(f"train_latent_model module={train_latent_model.__file__}")
    print(f"detr.main module={detr.main.__file__}")
    print(f"latent model module={detr.models.latent_model.__file__}")
    print(f"robomimic diffusion policy exports ConditionalUnet1D={hasattr(robodiff, 'ConditionalUnet1D')}")
    print(f"robomimic diffusion policy exports replace_bn_with_gn={hasattr(robodiff, 'replace_bn_with_gn')}")
    print(f"policy classes={[name for name in ['ACTPolicy', 'CNNMLPPolicy', 'DiffusionPolicy'] if hasattr(policy, name)]}")

    if not torch.cuda.is_available():
        print("ERROR: CUDA is required for the unmodified ACT++, Diffusion, and VINN training/eval paths.")
        return 2

    print("policy stack smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
