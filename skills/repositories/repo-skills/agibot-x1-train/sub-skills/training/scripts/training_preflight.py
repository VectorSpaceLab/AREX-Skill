#!/usr/bin/env python3
"""Non-launching X1 DH training preflight and CPU shape smoke.

This helper deliberately never constructs an Isaac Gym environment and never
starts humanoid/scripts/train.py.  It reports the required Isaac Gym gate,
prints a bounded command, and (when Torch is available) checks the distilled
ActorCriticDH/RolloutStorage tensor contract on CPU.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import shlex
import sys
import types
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Distilled X1DHStandCfg invariants. Keep this helper usable when Isaac Gym is
# absent: importing humanoid.envs would otherwise construct the full registry
# import chain and fail before static inspection can report the blocker.
ENV = {
    "task": "x1_dh_stand",
    "num_envs": 4096,
    "num_actions": 12,
    "num_single_obs": 47,
    "frame_stack": 66,
    "short_frame_stack": 5,
    "c_frame_stack": 3,
    "single_num_privileged_obs": 73,
    "num_commands": 5,
    "commands_num_commands": 4,
}
PPO = {
    "runner_class_name": "DHOnPolicyRunner",
    "policy_class_name": "ActorCriticDH",
    "algorithm_class_name": "DHPPO",
    "num_steps_per_env": 24,
    "max_iterations": 20000,
    "save_interval": 100,
    "experiment_name": "x1_dh_stand",
}


def derived_config() -> Dict[str, int]:
    return {
        "num_observations": ENV["frame_stack"] * ENV["num_single_obs"],
        "num_short_obs": ENV["short_frame_stack"] * ENV["num_single_obs"],
        "num_privileged_obs": ENV["c_frame_stack"] * ENV["single_num_privileged_obs"],
        "critic_lin_vel_index": (ENV["c_frame_stack"] - 1)
        * ENV["single_num_privileged_obs"]
        + 53,
    }


def invariant_errors() -> list[str]:
    d = derived_config()
    errors = []
    if d["num_observations"] != 3102:
        errors.append("66 * 47 must equal 3102")
    if d["num_short_obs"] != 235:
        errors.append("5 * 47 must equal 235")
    if d["num_privileged_obs"] != 219:
        errors.append("3 * 73 must equal 219")
    if ENV["num_actions"] != 12:
        errors.append("the X1 action width must be 12")
    if ENV["num_commands"] != 5 or ENV["commands_num_commands"] != 4:
        errors.append("observation command width 5 and raw command width 4 are coupled")
    return errors


def find_repo_root() -> Optional[Path]:
    """Find a checkout containing humanoid without printing its private path."""
    candidates = [Path.cwd()]
    here = Path(__file__).resolve()
    candidates.extend(here.parents)
    for candidate in candidates:
        if (candidate / "humanoid" / "algo" / "ppo" / "actor_critic_dh.py").is_file():
            return candidate
    return None


def load_file_class(repo_root: Path, relative: str, name: str) -> Any:
    """Load a torch-only source module without importing Isaac Gym or wandb."""
    path = repo_root / relative
    spec = importlib.util.spec_from_file_location("_x1_training_" + name.lower(), path)
    if spec is None or spec.loader is None:
        raise ImportError("could not create a loader for the training class")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, name)


def check_backend() -> Tuple[bool, str]:
    try:
        importlib.import_module("isaacgym")
    except Exception as exc:  # noqa: BLE001 - report all installation failures
        return False, f"{type(exc).__name__}: {exc}"
    return True, "isaacgym import succeeded; native compatibility still requires an Isaac Gym example and CUDA/PhysX check"


def isolated_config_import() -> Tuple[bool, str]:
    """Import only config classes without executing humanoid.envs.__init__."""
    root = find_repo_root()
    if root is None:
        return False, "repository package not found for isolated config import"

    names = [
        "humanoid",
        "humanoid.envs",
        "humanoid.envs.base",
        "humanoid.envs.x1",
        "humanoid.envs.base.base_config",
        "humanoid.envs.base.legged_robot_config",
        "humanoid.envs.x1.x1_dh_stand_config",
    ]
    saved = {name: sys.modules.get(name) for name in names}
    try:
        package_paths = {
            "humanoid": root / "humanoid",
            "humanoid.envs": root / "humanoid" / "envs",
            "humanoid.envs.base": root / "humanoid" / "envs" / "base",
            "humanoid.envs.x1": root / "humanoid" / "envs" / "x1",
        }
        for name, path in package_paths.items():
            package = types.ModuleType(name)
            package.__path__ = [str(path)]  # type: ignore[attr-defined]
            package.__package__ = name
            sys.modules[name] = package

        files = [
            ("humanoid.envs.base.base_config", root / "humanoid/envs/base/base_config.py"),
            ("humanoid.envs.base.legged_robot_config", root / "humanoid/envs/base/legged_robot_config.py"),
            ("humanoid.envs.x1.x1_dh_stand_config", root / "humanoid/envs/x1/x1_dh_stand_config.py"),
        ]
        module = None
        for name, path in files:
            spec = importlib.util.spec_from_file_location(name, path)
            if spec is None or spec.loader is None:
                raise ImportError(f"could not create a loader for {name}")
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        assert module is not None
        env_cfg = module.X1DHStandCfg()
        train_cfg = module.X1DHStandCfgPPO()
        d = derived_config()
        observed = {
            "num_observations": env_cfg.env.num_observations,
            "num_short_obs": env_cfg.env.short_frame_stack * env_cfg.env.num_single_obs,
            "num_privileged_obs": env_cfg.env.num_privileged_obs,
            "num_actions": env_cfg.env.num_actions,
            "lin_vel_idx": train_cfg.algorithm.lin_vel_idx,
        }
        expected = {
            "num_observations": d["num_observations"],
            "num_short_obs": d["num_short_obs"],
            "num_privileged_obs": d["num_privileged_obs"],
            "num_actions": ENV["num_actions"],
            "lin_vel_idx": d["critic_lin_vel_index"],
        }
        if observed != expected:
            return False, f"isolated config values differed: observed={observed}, expected={expected}"
    except Exception as exc:  # noqa: BLE001 - preserve the actual config failure
        return False, f"isolated config import failed: {type(exc).__name__}: {exc}"
    finally:
        for name in reversed(names):
            old = saved[name]
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old
    return True, "isolated X1DHStandCfg/X1DHStandCfgPPO import and dimensions succeeded"


def check_config_import() -> Tuple[bool, str, bool, str]:
    """Check the CPU config alternative and the separate native backend gate."""
    config_ok, config_detail = isolated_config_import()
    backend_ok, backend_detail = check_backend()
    if not backend_ok:
        backend_detail = "BLOCKED_REQUIRED_BACKEND: Isaac Gym Preview 4 unavailable (" + backend_detail + ")"
    return config_ok, config_detail, backend_ok, backend_detail


def print_report() -> None:
    d = derived_config()
    print("X1 DH static training contract")
    print(f"  task={ENV['task']} actions={ENV['num_actions']} raw_commands={ENV['commands_num_commands']}")
    print(
        "  observations="
        f"{d['num_observations']} (frames={ENV['frame_stack']}, single={ENV['num_single_obs']}); "
        f"short={d['num_short_obs']}; privileged={d['num_privileged_obs']}"
    )
    print(
        "  runner="
        f"{PPO['runner_class_name']} policy={PPO['policy_class_name']} "
        f"algorithm={PPO['algorithm_class_name']} steps/env={PPO['num_steps_per_env']}"
    )
    errors = invariant_errors()
    if errors:
        print("  INVARIANT_FAILURE: " + "; ".join(errors))
    else:
        print("  invariants=OK")


def print_command(args: argparse.Namespace) -> None:
    parts = [
        "python",
        "humanoid/scripts/train.py",
        "--task=x1_dh_stand",
        "--headless",
        f"--num_envs={args.num_envs}",
        f"--max_iterations={args.max_iterations}",
        f"--rl_device={args.rl_device}",
    ]
    if args.run_name:
        parts.append("--run_name=" + args.run_name)
    if args.seed is not None:
        parts.append(f"--seed={args.seed}")
    if args.resume:
        parts.append("--resume")
        if args.load_run is not None:
            parts.append("--load_run=" + args.load_run)
        if args.checkpoint is not None:
            parts.append(f"--checkpoint={args.checkpoint}")
    print("Non-launching bounded command:")
    print(" ".join(shlex.quote(part) for part in parts))
    print("Increase num_envs/max_iterations only after the required backend and a bounded startup are verified.")


def shape_smoke() -> bool:
    """Exercise the real torch-only classes when the checkout is discoverable."""
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        print(f"SHAPE_SMOKE_BLOCKED: PyTorch import failed: {type(exc).__name__}: {exc}")
        return False

    root = find_repo_root()
    if root is None:
        print("SHAPE_SMOKE_BLOCKED: bundled helper could not find the repository package")
        return False
    try:
        ActorCriticDH = load_file_class(root, "humanoid/algo/ppo/actor_critic_dh.py", "ActorCriticDH")
        RolloutStorage = load_file_class(root, "humanoid/algo/ppo/rollout_storage.py", "RolloutStorage")
        policy = ActorCriticDH(
            num_short_obs=235,
            num_proprio_obs=47,
            num_critic_obs=219,
            num_actions=12,
            actor_hidden_dims=[32, 16, 8],
            critic_hidden_dims=[32, 16, 8],
            state_estimator_hidden_dims=[16, 8, 4],
            in_channels=66,
            kernel_size=[6, 4],
            filter_size=[8, 4],
            stride_size=[3, 2],
            lh_output_dim=8,
            init_noise_std=1.0,
        ).to("cpu")
        obs = torch.zeros(2, 3102)
        critic = torch.zeros(2, 219)
        actions = policy.act(obs)
        values = policy.evaluate(critic)
        if tuple(actions.shape) != (2, 12) or tuple(values.shape) != (2, 1):
            raise AssertionError(f"policy shapes were {tuple(actions.shape)} and {tuple(values.shape)}")
        log_prob = policy.get_actions_log_prob(actions)
        if tuple(log_prob.shape) != (2,):
            raise AssertionError(f"log-probability shape was {tuple(log_prob.shape)}")

        storage = RolloutStorage(2, 24, [3102], [219], [12], device="cpu")
        transition = RolloutStorage.Transition()
        transition.observations = obs
        transition.critic_observations = critic
        transition.actions = actions
        transition.rewards = torch.zeros(2)
        transition.dones = torch.zeros(2, dtype=torch.long)
        transition.values = values
        transition.actions_log_prob = log_prob
        transition.action_mean = policy.action_mean
        transition.action_sigma = policy.action_std
        for _ in range(24):
            storage.add_transitions(transition)
        storage.compute_returns(torch.zeros(2, 1), 0.994, 0.9)
        batch = next(storage.mini_batch_generator(4, 1))
        if tuple(storage.observations.shape) != (24, 2, 3102):
            raise AssertionError(f"storage observation shape was {tuple(storage.observations.shape)}")
        if tuple(storage.privileged_observations.shape) != (24, 2, 219):
            raise AssertionError(f"storage critic shape was {tuple(storage.privileged_observations.shape)}")
        if tuple(storage.actions.shape) != (24, 2, 12):
            raise AssertionError(f"storage action shape was {tuple(storage.actions.shape)}")
        if len(batch) != 11:
            raise AssertionError(f"default generator yielded {len(batch)} fields, expected 11")
    except Exception as exc:  # noqa: BLE001 - smoke must preserve the cause
        print(f"SHAPE_SMOKE_FAIL: {type(exc).__name__}: {exc}")
        return False
    print("SHAPE_SMOKE_OK: ActorCriticDH and RolloutStorage CPU tensor contract")
    print("  policy: obs (2,3102) -> actions (2,12), critic (2,219) -> values (2,1)")
    print("  storage: (24,2,3102), (24,2,219), (24,2,12); GAE and one mini-batch consumed")
    return True


def bounded_int(low: int, high: int):
    def parse(value: str) -> int:
        try:
            parsed = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be an integer") from exc
        if not low <= parsed <= high:
            raise argparse.ArgumentTypeError(f"must be between {low} and {high}")
        return parsed

    return parse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Non-launching X1 DH training preflight")
    parser.add_argument("--check-config", action="store_true", help="check Isaac Gym gate and isolated config import")
    parser.add_argument("--shape-smoke", action="store_true", help="run the tiny CPU-only policy/storage shape check")
    parser.add_argument("--print-command", action="store_true", help="print a bounded train.py command; never execute it")
    parser.add_argument("--num-envs", type=bounded_int(1, 4096), default=1, help="bounded value shown in the command (1..4096)")
    parser.add_argument("--max-iterations", type=bounded_int(1, 20000), default=1, help="bounded value shown in the command (1..20000)")
    parser.add_argument("--rl-device", default="cuda:0", help="value shown in the bounded command")
    parser.add_argument("--run-name", default="preflight", help="value shown in the bounded command")
    parser.add_argument("--seed", type=int, default=None, help="optional seed shown in the bounded command")
    parser.add_argument("--resume", action="store_true", help="include resume in the printed command")
    parser.add_argument("--load-run", default=None, help="optional run shown with --resume")
    parser.add_argument("--checkpoint", type=int, default=None, help="optional checkpoint shown with --resume")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if not (args.check_config or args.shape_smoke or args.print_command):
        print_report()
        print("No action requested; use --check-config, --shape-smoke, or --print-command. Training was not launched.")
        return 0

    status = 0
    if args.check_config:
        print_report()
        config_ok, config_detail, backend_ok, backend_detail = check_config_import()
        print("CONFIG_IMPORT_{}: {}".format("OK" if config_ok else "FAIL", config_detail))
        print("BACKEND_CHECK_{}: {}".format("OK" if backend_ok else "BLOCKED", backend_detail))
        if not config_ok:
            status = 1
        elif not backend_ok:
            status = 2
    if args.shape_smoke and not shape_smoke():
        status = 1
    if args.print_command:
        print_report()
        print_command(args)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
