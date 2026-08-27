#!/usr/bin/env python3
"""Safe Tianshou import/API smoke check.

This script performs imports and lightweight object/API checks only. It does not
train, render, download datasets, launch subprocess workers, or read an original
source checkout.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import inspect
import json
from typing import Any


def _signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "<signature unavailable>"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe Tianshou import/API smoke check.")
    parser.add_argument(
        "--include-evaluation",
        action="store_true",
        help="Also import evaluation launcher/rliable modules. This requires optional evaluation deps.",
    )
    args = parser.parse_args()

    import tianshou
    from tianshou.algorithm.modelfree.dqn import DQN, DiscreteQLearningPolicy
    from tianshou.algorithm.modelfree.ppo import PPO
    from tianshou.algorithm.modelfree.sac import SAC
    from tianshou.data import Batch, Collector, ReplayBuffer
    from tianshou.env import DummyVectorEnv, SubprocVectorEnv
    from tianshou.highlevel.config import OffPolicyTrainingConfig, OnPolicyTrainingConfig
    from tianshou.highlevel.experiment import DQNExperimentBuilder, Experiment, ExperimentConfig
    from tianshou.highlevel.params.algorithm_params import DQNParams, PPOParams, SACParams
    from tianshou.trainer import OfflineTrainerParams, OffPolicyTrainerParams, OnPolicyTrainerParams

    modules = [
        "tianshou",
        "tianshou.data",
        "tianshou.env",
        "tianshou.highlevel.experiment",
        "tianshou.algorithm.modelfree.dqn",
        "tianshou.algorithm.modelfree.ppo",
        "tianshou.algorithm.modelfree.sac",
        "tianshou.trainer",
    ]
    if args.include_evaluation:
        modules.extend(["tianshou.evaluation.launcher", "tianshou.evaluation.rliable_evaluation"])

    imports = {}
    for module_name in modules:
        module = importlib.import_module(module_name)
        imports[module_name] = bool(module)

    batch = Batch(obs=[1, 2], act=[0, 1])
    facts = {
        "ok": True,
        "tianshou_version": getattr(tianshou, "__version__", None),
        "distribution_version": metadata.version("tianshou"),
        "imports": imports,
        "batch_length": len(batch),
        "signatures": {
            "ReplayBuffer": _signature(ReplayBuffer),
            "Collector": _signature(Collector),
            "DummyVectorEnv": _signature(DummyVectorEnv),
            "SubprocVectorEnv": _signature(SubprocVectorEnv),
            "ExperimentConfig": _signature(ExperimentConfig),
            "Experiment.run": _signature(Experiment.run),
            "DQNExperimentBuilder": DQNExperimentBuilder.__name__,
            "OffPolicyTrainingConfig": _signature(OffPolicyTrainingConfig),
            "OnPolicyTrainingConfig": _signature(OnPolicyTrainingConfig),
            "DQNParams": _signature(DQNParams),
            "PPOParams": _signature(PPOParams),
            "SACParams": _signature(SACParams),
            "DiscreteQLearningPolicy": _signature(DiscreteQLearningPolicy),
            "DQN": _signature(DQN),
            "PPO": _signature(PPO),
            "SAC": _signature(SAC),
            "OffPolicyTrainerParams": _signature(OffPolicyTrainerParams),
            "OnPolicyTrainerParams": _signature(OnPolicyTrainerParams),
            "OfflineTrainerParams": _signature(OfflineTrainerParams),
        },
    }
    print(json.dumps(facts, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
