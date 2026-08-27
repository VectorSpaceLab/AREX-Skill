#!/usr/bin/env python3
"""Safely probe the public skrl Warp imports, versions, CPU device, and config.

This helper intentionally does not create an environment, compile a user model,
run a trainer, allocate CUDA tensors, train, evaluate, or write experiment
outputs. Warp initialization may create its normal kernel cache; that cache is
not a skrl run artifact. This is a package/API probe, not a CUDA or simulator
verification.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import inspect
import json
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe skrl Warp imports and explicit CPU configuration without training or writing files."
    )
    return parser.parse_args()


def main() -> int:
    parse_args()

    try:
        import warp as wp

        wp.init()
        import warp_nn  # noqa: F401

        from skrl import __version__, config
        from skrl.agents.warp.ddpg import DDPG, DDPG_CFG
        from skrl.agents.warp.ppo import PPO, PPO_CFG
        from skrl.agents.warp.sac import SAC, SAC_CFG
        from skrl.envs.wrappers.warp import wrap_env
        from skrl.memories.warp import RandomMemory
        from skrl.models.warp import DeterministicMixin, GaussianMixin, Model
        from skrl.trainers.warp import SequentialTrainer
    except Exception as exc:  # pragma: no cover - exercised by user environments
        print(f"Warp probe failed during import: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        cpu = config.warp.parse_device("cpu")
        config.warp.device = "cpu"
        configured = config.warp.device
        config.warp.key = 0
        signatures = {
            "PPO": str(inspect.signature(PPO)),
            "DDPG": str(inspect.signature(DDPG)),
            "SAC": str(inspect.signature(SAC)),
            "PPO_CFG": str(inspect.signature(PPO_CFG)),
            "DDPG_CFG": str(inspect.signature(DDPG_CFG)),
            "SAC_CFG": str(inspect.signature(SAC_CFG)),
            "Model": str(inspect.signature(Model)),
            "DeterministicMixin": str(inspect.signature(DeterministicMixin)),
            "GaussianMixin": str(inspect.signature(GaussianMixin)),
            "RandomMemory": str(inspect.signature(RandomMemory)),
            "SequentialTrainer": str(inspect.signature(SequentialTrainer)),
            "wrap_env": str(inspect.signature(wrap_env)),
        }
        result = {
            "skrl": __version__,
            "warp_lang": importlib.metadata.version("warp-lang"),
            "warp_nn": importlib.metadata.version("warp-nn"),
            "selected_device": str(cpu),
            "configured_device": str(configured),
            "key_type": type(config.warp.key).__name__,
            "signatures": signatures,
            "cuda_checked": False,
            "training_run": False,
            "persistent_output": False,
        }
    except Exception as exc:  # pragma: no cover - exercised by user environments
        print(f"Warp probe failed during CPU/config check: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if str(cpu) != "cpu" or str(configured) != "cpu":
        print(json.dumps(result, indent=2, sort_keys=True))
        print("CPU probe did not resolve an explicit CPU device", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
