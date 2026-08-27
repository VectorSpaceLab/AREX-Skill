#!/usr/bin/env python3
"""Safe DRL-Pytorch policy-control diagnostics.

This script imports policy-gradient and actor-critic modules from a user-supplied
DRL-Pytorch checkout and performs tiny CPU object checks. It does not train,
create Gymnasium environments, render, write TensorBoard logs, download assets,
or require optional Box2D/MuJoCo dependencies.
"""

from __future__ import annotations

import argparse
import gc
import sys
import traceback
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterable

MODULE_NAMES = ("utils", "PPO", "DDPG", "TD3", "SACD", "SAC")

ALGORITHM_DIRS = {
    "ppo-discrete": "3.1 PPO-Discrete",
    "ppo-continuous": "3.2 PPO-Continuous",
    "ddpg": "4.1 DDPG",
    "td3": "4.2 TD3",
    "sac-discrete": "5.1 SAC-Discrete",
    "sac-continuous": "5.2 SAC-Continuous",
}

ORDER = tuple(ALGORITHM_DIRS)


@contextmanager
def isolated_algorithm_import(algorithm_dir: Path):
    """Import one standalone algorithm directory without leaking short names."""
    if not algorithm_dir.is_dir():
        raise FileNotFoundError(f"missing algorithm directory: {algorithm_dir}")

    old_path = list(sys.path)
    for name in MODULE_NAMES:
        sys.modules.pop(name, None)
    sys.path.insert(0, str(algorithm_dir))
    try:
        yield
    finally:
        sys.path[:] = old_path
        for name in MODULE_NAMES:
            sys.modules.pop(name, None)
        gc.collect()


def _torch_cpu():
    import torch

    return torch.device("cpu")


def smoke_ppo_discrete(repo_root: Path, _args: argparse.Namespace) -> str:
    with isolated_algorithm_import(repo_root / ALGORITHM_DIRS["ppo-discrete"]):
        import numpy as np
        from PPO import PPO_discrete

        agent = PPO_discrete(
            state_dim=4,
            action_dim=2,
            net_width=8,
            dvc=_torch_cpu(),
            lr=1e-4,
            T_horizon=4,
            gamma=0.99,
            lambd=0.95,
            clip_rate=0.2,
            K_epochs=1,
            batch_size=2,
            entropy_coef=0.0,
            entropy_coef_decay=1.0,
            adv_normalization=False,
            l2_reg=0.0,
        )
        action, prob = agent.select_action(np.zeros(4, dtype=np.float32), deterministic=False)
        assert isinstance(action, int) and 0 <= action < 2
        assert prob is not None
        return "PPO_discrete imported; tiny categorical actor sampled an action on CPU"


def smoke_ppo_continuous(repo_root: Path, args: argparse.Namespace) -> str:
    distributions = ("Beta", "GS_ms", "GS_m") if args.ppo_distribution == "all" else (args.ppo_distribution,)
    messages = []
    with isolated_algorithm_import(repo_root / ALGORITHM_DIRS["ppo-continuous"]):
        import numpy as np
        from PPO import PPO_agent
        from utils import Action_adapter

        for distribution in distributions:
            agent = PPO_agent(
                state_dim=3,
                action_dim=2,
                net_width=8,
                dvc=_torch_cpu(),
                Distribution=distribution,
                a_lr=2e-4,
                c_lr=2e-4,
                T_horizon=4,
                gamma=0.99,
                lambd=0.95,
                clip_rate=0.2,
                K_epochs=1,
                a_optim_batch_size=2,
                c_optim_batch_size=2,
                entropy_coef=1e-3,
                entropy_coef_decay=1.0,
                l2_reg=0.0,
            )
            action, logprob = agent.select_action(np.zeros(3, dtype=np.float32), deterministic=False)
            assert action.shape == (2,)
            assert logprob.shape == (2,)
            scaled = Action_adapter(action, 2.0)
            assert scaled.shape == (2,)
            messages.append(distribution)
            del agent
        return "PPO_agent imported; checked distributions " + ", ".join(messages)


def smoke_ddpg(repo_root: Path, _args: argparse.Namespace) -> str:
    with isolated_algorithm_import(repo_root / ALGORITHM_DIRS["ddpg"]):
        import numpy as np
        from DDPG import DDPG_agent

        agent = DDPG_agent(
            state_dim=3,
            action_dim=2,
            net_width=8,
            max_action=2.0,
            dvc=_torch_cpu(),
            a_lr=1e-3,
            c_lr=1e-3,
            gamma=0.99,
            batch_size=1,
            noise=0.1,
        )
        action = agent.select_action(np.zeros(3, dtype=np.float32), deterministic=True)
        assert action.shape == (2,)
        assert float(action.max()) <= 2.0 and float(action.min()) >= -2.0
        return "DDPG_agent imported; deterministic actor produced bounded CPU action"


def smoke_td3(repo_root: Path, _args: argparse.Namespace) -> str:
    with isolated_algorithm_import(repo_root / ALGORITHM_DIRS["td3"]):
        import numpy as np
        from TD3 import TD3_agent

        agent = TD3_agent(
            state_dim=3,
            action_dim=2,
            net_width=8,
            max_action=2.0,
            dvc=_torch_cpu(),
            a_lr=1e-4,
            c_lr=1e-4,
            gamma=0.99,
            batch_size=1,
            delay_freq=1,
            explore_noise=0.15,
        )
        action = agent.select_action(np.zeros(3, dtype=np.float32), deterministic=True)
        assert action.shape == (2,)
        assert float(action.max()) <= 2.0 and float(action.min()) >= -2.0
        return "TD3_agent imported; twin-critic actor stack produced bounded CPU action"


def smoke_sac_discrete(repo_root: Path, _args: argparse.Namespace) -> str:
    with isolated_algorithm_import(repo_root / ALGORITHM_DIRS["sac-discrete"]):
        import numpy as np
        from SACD import SACD_agent

        agent = SACD_agent(
            state_dim=4,
            action_dim=3,
            hid_shape=[8, 8],
            dvc=_torch_cpu(),
            lr=3e-4,
            gamma=0.99,
            batch_size=1,
            alpha=0.2,
            adaptive_alpha=True,
        )
        action = agent.select_action(np.zeros(4, dtype=np.float32), deterministic=False)
        assert isinstance(action, int) and 0 <= action < 3
        assert hasattr(agent, "H_mean") and hasattr(agent, "alpha")
        return "SACD_agent imported; categorical policy sampled an action on CPU"


def smoke_sac_continuous(repo_root: Path, _args: argparse.Namespace) -> str:
    with isolated_algorithm_import(repo_root / ALGORITHM_DIRS["sac-continuous"]):
        import numpy as np
        from SAC import SAC_countinuous
        from utils import Action_adapter, Action_adapter_reverse

        agent = SAC_countinuous(
            state_dim=3,
            action_dim=2,
            net_width=8,
            dvc=_torch_cpu(),
            a_lr=3e-4,
            c_lr=3e-4,
            gamma=0.99,
            batch_size=1,
            alpha=0.12,
            adaptive_alpha=True,
        )
        action = agent.select_action(np.zeros(3, dtype=np.float32), deterministic=False)
        assert action.shape == (2,)
        assert float(action.max()) <= 1.0 and float(action.min()) >= -1.0
        scaled = Action_adapter(action, 2.0)
        restored = Action_adapter_reverse(scaled, 2.0)
        assert restored.shape == (2,)
        return "SAC_countinuous imported; tanh-squashed actor and action adapters checked on CPU"


CHECKS: dict[str, Callable[[Path, argparse.Namespace], str]] = {
    "ppo-discrete": smoke_ppo_discrete,
    "ppo-continuous": smoke_ppo_continuous,
    "ddpg": smoke_ddpg,
    "td3": smoke_td3,
    "sac-discrete": smoke_sac_discrete,
    "sac-continuous": smoke_sac_continuous,
}


def expand_algorithms(selected: Iterable[str]) -> list[str]:
    requested = list(selected)
    if "all" in requested:
        return list(ORDER)
    seen: set[str] = set()
    expanded: list[str] = []
    for name in requested:
        if name not in seen:
            expanded.append(name)
            seen.add(name)
    return expanded


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import DRL-Pytorch policy/actor-critic modules from a checkout and "
            "run tiny CPU object checks without training, downloads, rendering, or optional env creation."
        )
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Path to a DRL-Pytorch checkout containing the policy-control algorithm directories.",
    )
    parser.add_argument(
        "--algorithm",
        nargs="+",
        choices=("all",) + ORDER,
        default=["all"],
        help="Algorithm(s) to check. Default: all.",
    )
    parser.add_argument(
        "--ppo-distribution",
        choices=("Beta", "GS_ms", "GS_m", "all"),
        default="Beta",
        help="PPO-Continuous actor distribution(s) to instantiate. Default: Beta.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first failed algorithm check.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print traceback details for failed checks.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.is_dir():
        print(f"FAIL repo-root: not a directory: {repo_root}", file=sys.stderr)
        return 2

    algorithms = expand_algorithms(args.algorithm)
    failures = 0
    for algorithm in algorithms:
        try:
            message = CHECKS[algorithm](repo_root, args)
            print(f"OK {algorithm}: {message}")
        except Exception as exc:  # pragma: no cover - diagnostic path
            failures += 1
            print(f"FAIL {algorithm}: {exc}", file=sys.stderr)
            if args.verbose:
                traceback.print_exc()
            if args.fail_fast:
                break
    if failures:
        print(f"completed with {failures} failure(s)", file=sys.stderr)
        return 1
    print("all selected policy-control checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
