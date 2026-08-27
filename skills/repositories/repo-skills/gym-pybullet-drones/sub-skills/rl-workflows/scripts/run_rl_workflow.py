#!/usr/bin/env python3
"""Skill-owned PPO train/play helper for gym-pybullet-drones RL workflows.

The helper intentionally uses only public installed-package imports. It mirrors the
source learn.py/play.py decisions with safer automation defaults: headless smoke
training, explicit model paths, and no accidental full 1e7-step run.
"""
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

RL_ENV_IDS = {
    False: "hover-aviary-v0",
    True: "multihover-aviary-v0",
}
DEFAULT_OBS = "kin"
DEFAULT_ACT = "one_d_rpm"
DEFAULT_NUM_DRONES = 2


@dataclass
class Runtime:
    gym: Any
    np: Any
    PPO: Any
    make_vec_env: Any
    evaluate_policy: Any
    HoverAviary: Any
    MultiHoverAviary: Any
    ObservationType: Any
    ActionType: Any
    Logger: Any
    sync: Any


def _dist_version(dist_name: str) -> str:
    try:
        return version(dist_name)
    except PackageNotFoundError:
        return "not-installed"


def _import_or_collect(import_name: str, failures: list[str]) -> Any | None:
    try:
        return importlib.import_module(import_name)
    except Exception as exc:  # pragma: no cover - diagnostic path
        failures.append(f"{import_name}: {type(exc).__name__}: {exc}")
        return None


def load_runtime() -> Runtime:
    """Import RL dependencies lazily and raise one actionable error if any fail."""
    failures: list[str] = []
    gym = _import_or_collect("gymnasium", failures)
    np = _import_or_collect("numpy", failures)
    _import_or_collect("torch", failures)
    _import_or_collect("stable_baselines3", failures)
    _import_or_collect("gym_pybullet_drones", failures)  # registers env IDs

    if failures:
        details = "\n".join(f"  - {item}" for item in failures)
        raise RuntimeError(
            "Missing or incompatible RL runtime imports. Install gym-pybullet-drones "
            "and its RL dependencies in the active Python environment, then run "
            "`python scripts/run_rl_workflow.py check-imports`.\n"
            f"Import failures:\n{details}"
        )

    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env
    from stable_baselines3.common.evaluation import evaluate_policy
    from gym_pybullet_drones.envs.HoverAviary import HoverAviary
    from gym_pybullet_drones.envs.MultiHoverAviary import MultiHoverAviary
    from gym_pybullet_drones.utils.Logger import Logger
    from gym_pybullet_drones.utils.enums import ActionType, ObservationType
    from gym_pybullet_drones.utils.utils import sync

    return Runtime(
        gym=gym,
        np=np,
        PPO=PPO,
        make_vec_env=make_vec_env,
        evaluate_policy=evaluate_policy,
        HoverAviary=HoverAviary,
        MultiHoverAviary=MultiHoverAviary,
        ObservationType=ObservationType,
        ActionType=ActionType,
        Logger=Logger,
        sync=sync,
    )


def enum_value(enum_cls: Any, value: str, label: str) -> Any:
    try:
        return enum_cls(value)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in enum_cls)
        raise ValueError(f"Unsupported {label} value {value!r}; expected one of: {allowed}") from exc


def env_config(args: argparse.Namespace, rt: Runtime, *, gui: bool, record: bool = False) -> tuple[Any, str, dict[str, Any], Any, Any, int]:
    obs = enum_value(rt.ObservationType, args.obs, "observation")
    act = enum_value(rt.ActionType, args.act, "action")
    if args.multiagent:
        env_cls = rt.MultiHoverAviary
        env_id = RL_ENV_IDS[True]
        num_drones = int(args.num_drones)
        kwargs = {"num_drones": num_drones, "gui": gui, "record": record, "obs": obs, "act": act}
    else:
        env_cls = rt.HoverAviary
        env_id = RL_ENV_IDS[False]
        num_drones = 1
        kwargs = {"gui": gui, "record": record, "obs": obs, "act": act}
    return env_cls, env_id, kwargs, obs, act, num_drones


def ensure_run_dir(output_folder: str, run_name: str | None = None) -> Path:
    base = Path(output_folder).expanduser().resolve()
    base.mkdir(parents=True, exist_ok=True)
    if run_name:
        run_dir = base / run_name
        if run_dir.exists() and any(run_dir.iterdir()):
            raise FileExistsError(f"Run directory already exists and is not empty: {run_dir}")
    else:
        run_dir = base / f"save-{datetime.now().strftime('%m.%d.%Y_%H.%M.%S')}"
        suffix = 1
        while run_dir.exists():
            run_dir = base / f"save-{datetime.now().strftime('%m.%d.%Y_%H.%M.%S')}-{suffix}"
            suffix += 1
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def check_imports(_args: argparse.Namespace, *, emit: bool = True) -> dict[str, Any]:
    rt = load_runtime()
    specs: dict[str, str] = {}
    for env_id in (RL_ENV_IDS[False], RL_ENV_IDS[True]):
        specs[env_id] = str(rt.gym.spec(env_id).entry_point)
    payload = {
        "ok": True,
        "versions": {
            "gym-pybullet-drones": _dist_version("gym-pybullet-drones"),
            "gymnasium": _dist_version("gymnasium"),
            "stable-baselines3": _dist_version("stable-baselines3"),
            "torch": _dist_version("torch"),
        },
        "registered_envs": specs,
    }
    if emit:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def train_policy(args: argparse.Namespace, *, emit: bool = True) -> dict[str, Any]:
    rt = load_runtime()
    env_cls, env_id, kwargs, obs, act, num_drones = env_config(args, rt, gui=False, record=False)
    run_dir = ensure_run_dir(args.output_folder, args.run_name)

    n_envs = max(1, int(args.n_envs))
    n_steps = max(2, int(args.n_steps))
    batch_size = max(2, min(int(args.batch_size), n_steps * n_envs))
    requested_timesteps = max(1, int(args.timesteps))
    effective_timesteps = max(requested_timesteps, n_steps * n_envs)

    train_env = None
    eval_env = None
    summary: dict[str, Any] = {
        "command": "train",
        "env_id": env_id,
        "multiagent": bool(args.multiagent),
        "num_drones": num_drones,
        "obs": obs.value,
        "act": act.value,
        "run_dir": str(run_dir),
        "requested_timesteps": requested_timesteps,
        "effective_timesteps": effective_timesteps,
        "n_envs": n_envs,
        "n_steps": n_steps,
        "batch_size": batch_size,
        "n_epochs": int(args.n_epochs),
        "seed": int(args.seed),
    }

    try:
        train_env = rt.make_vec_env(env_cls, env_kwargs=kwargs, n_envs=n_envs, seed=int(args.seed))
        eval_env = env_cls(**kwargs)
        print(f"[INFO] Training {env_id} with PPO for {effective_timesteps} timesteps")
        print("[INFO] Action space:", train_env.action_space)
        print("[INFO] Observation space:", train_env.observation_space)

        model = rt.PPO(
            "MlpPolicy",
            train_env,
            verbose=int(args.verbose),
            seed=int(args.seed),
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=max(1, int(args.n_epochs)),
        )
        model.learn(total_timesteps=effective_timesteps, log_interval=100)

        final_model = run_dir / "final_model.zip"
        best_model = run_dir / "best_model.zip"
        model.save(str(final_model))
        shutil.copy2(final_model, best_model)
        summary["final_model_path"] = str(final_model)
        summary["best_model_path"] = str(best_model)

        if int(args.eval_episodes) > 0:
            try:
                mean_reward, std_reward = rt.evaluate_policy(
                    model,
                    eval_env,
                    n_eval_episodes=int(args.eval_episodes),
                    deterministic=True,
                )
                summary["eval_mean_reward"] = float(mean_reward)
                summary["eval_std_reward"] = float(std_reward)
                summary["eval_episodes"] = int(args.eval_episodes)
            except Exception as exc:  # Keep save/load artifact even if tiny eval fails.
                summary["evaluation_error"] = f"{type(exc).__name__}: {exc}"

        summary_path = run_dir / "rl_workflow_summary.json"
        summary["summary_path"] = str(summary_path)
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    finally:
        if train_env is not None:
            train_env.close()
        if eval_env is not None:
            eval_env.close()

    if emit:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def _done_flag(value: Any, np: Any) -> bool:
    arr = np.asarray(value)
    return bool(arr.any())


def _log_source_like_kinematics(
    rt: Runtime,
    logger: Any,
    *,
    multiagent: bool,
    num_drones: int,
    obs: Any,
    action: Any,
    step_idx: int,
    ctrl_freq: float,
    obs_type: Any,
    act_type: Any,
) -> int:
    """Log the source play.py kinematic layout when it fits Logger.log."""
    if obs_type != rt.ObservationType.KIN or act_type != rt.ActionType.ONE_D_RPM:
        return 0

    np = rt.np
    logged = 0
    if not multiagent:
        obs_vec = np.asarray(obs).squeeze().reshape(-1)
        act_vec = np.asarray(action).squeeze().reshape(-1)
        if obs_vec.size >= 15 and act_vec.size >= 1:
            state = np.hstack([obs_vec[0:3], np.zeros(4), obs_vec[3:15], act_vec[0:1]])
            if state.size == 20:
                logger.log(
                    drone=0,
                    timestamp=step_idx / ctrl_freq,
                    state=state,
                    control=np.zeros(12),
                )
                logged += 1
        return logged

    obs_arr = np.asarray(obs)
    act_arr = np.asarray(action)
    if obs_arr.shape[0] < num_drones or act_arr.shape[0] < num_drones:
        return 0
    for drone_id in range(num_drones):
        obs_vec = np.asarray(obs_arr[drone_id]).reshape(-1)
        act_vec = np.asarray(act_arr[drone_id]).reshape(-1)
        if obs_vec.size >= 15 and act_vec.size >= 1:
            state = np.hstack([obs_vec[0:3], np.zeros(4), obs_vec[3:15], act_vec[0:1]])
            if state.size == 20:
                logger.log(
                    drone=drone_id,
                    timestamp=step_idx / ctrl_freq,
                    state=state,
                    control=np.zeros(12),
                )
                logged += 1
    return logged


def play_policy(args: argparse.Namespace, *, emit: bool = True) -> dict[str, Any]:
    model_path = Path(args.model_path).expanduser().resolve()
    if not model_path.is_file():
        raise FileNotFoundError(
            f"Model path does not exist: {model_path}. Train first and pass the exact "
            "best_model.zip or final_model.zip path printed in rl_workflow_summary.json."
        )

    rt = load_runtime()
    env_cls, env_id, kwargs, obs_type, act_type, num_drones = env_config(
        args,
        rt,
        gui=bool(args.gui),
        record=bool(args.record_video),
    )
    output_folder = Path(args.output_folder).expanduser().resolve()
    output_folder.mkdir(parents=True, exist_ok=True)

    env = None
    logger = None
    rewards: list[float] = []
    logged_entries = 0
    terminated = False
    truncated = False

    try:
        model = rt.PPO.load(str(model_path))
        env = env_cls(**kwargs)
        logger = rt.Logger(
            logging_freq_hz=int(env.CTRL_FREQ),
            num_drones=num_drones,
            output_folder=str(output_folder),
            colab=False,
        )
        steps = int(args.steps) if int(args.steps) > 0 else int((env.EPISODE_LEN_SEC + 2) * env.CTRL_FREQ)
        print(f"[INFO] Loaded model from {model_path}")
        print(f"[INFO] Playing {env_id} for up to {steps} steps (gui={bool(args.gui)})")

        obs, _info = env.reset(seed=int(args.seed), options={})
        start = time.time()
        for i in range(steps):
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, _info = env.step(action)
            rewards.append(float(rt.np.asarray(reward).mean()))
            logged_entries += _log_source_like_kinematics(
                rt,
                logger,
                multiagent=bool(args.multiagent),
                num_drones=num_drones,
                obs=obs,
                action=action,
                step_idx=i,
                ctrl_freq=float(env.CTRL_FREQ),
                obs_type=obs_type,
                act_type=act_type,
            )
            if bool(args.render):
                env.render()
            if bool(args.realtime):
                rt.sync(i, start, env.CTRL_TIMESTEP)
            if bool(args.stop_on_done) and (_done_flag(terminated, rt.np) or _done_flag(truncated, rt.np)):
                break

        if bool(args.save_log) and logger is not None:
            logger.save()
        if bool(args.plot) and logger is not None:
            logger.plot()
    finally:
        if env is not None:
            env.close()

    summary = {
        "command": "play",
        "env_id": env_id,
        "multiagent": bool(args.multiagent),
        "num_drones": num_drones,
        "obs": obs_type.value,
        "act": act_type.value,
        "model_path": str(model_path),
        "output_folder": str(output_folder),
        "steps_run": len(rewards),
        "last_reward": rewards[-1] if rewards else None,
        "mean_step_reward": sum(rewards) / len(rewards) if rewards else None,
        "terminated": _done_flag(terminated, rt.np),
        "truncated": _done_flag(truncated, rt.np),
        "logged_entries": logged_entries,
        "logger_note": "source-like Logger.log entries are emitted for kin + one_d_rpm only",
    }
    if emit:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def train_then_play(args: argparse.Namespace, *, emit: bool = True) -> dict[str, Any]:
    train_summary = train_policy(args, emit=False)
    play_args = argparse.Namespace(**vars(args))
    play_args.model_path = train_summary["best_model_path"]
    play_args.steps = int(args.play_steps)
    play_args.output_folder = str(Path(train_summary["run_dir"]) / "playback_logs")
    play_args.record_video = False
    play_args.render = False
    play_args.stop_on_done = True
    play_summary = play_policy(play_args, emit=False)
    payload = {"command": "train-play", "train": train_summary, "play": play_summary}
    if emit:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def add_env_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--multiagent", action="store_true", help="Use MultiHoverAviary/multihover-aviary-v0 instead of HoverAviary")
    parser.add_argument("--num-drones", type=int, default=DEFAULT_NUM_DRONES, help="Number of drones for multi-agent hover")
    parser.add_argument("--obs", default=DEFAULT_OBS, choices=["kin", "rgb", "dep", "all"], help="ObservationType value")
    parser.add_argument("--act", default=DEFAULT_ACT, choices=["rpm", "pid", "vel", "one_d_rpm", "one_d_pid"], help="ActionType value")
    parser.add_argument("--seed", type=int, default=0, help="Reset/training seed")


def add_train_args(parser: argparse.ArgumentParser) -> None:
    add_env_args(parser)
    parser.add_argument("--output-folder", default="results", help="Folder where timestamped training output is written")
    parser.add_argument("--run-name", default=None, help="Optional exact run directory name under --output-folder")
    parser.add_argument("--timesteps", type=int, default=256, help="Requested PPO timesteps; short by default for smoke tests")
    parser.add_argument("--n-envs", type=int, default=1, help="Vectorized env count")
    parser.add_argument("--n-steps", type=int, default=64, help="PPO rollout steps per env; kept small for smoke tests")
    parser.add_argument("--batch-size", type=int, default=64, help="PPO minibatch size, clipped to n_steps*n_envs")
    parser.add_argument("--n-epochs", type=int, default=1, help="PPO optimization epochs per rollout")
    parser.add_argument("--eval-episodes", type=int, default=1, help="Small post-train evaluation episode count; set 0 to skip")
    parser.add_argument("--verbose", type=int, default=1, help="SB3 PPO verbosity")


def add_play_args(parser: argparse.ArgumentParser) -> None:
    add_env_args(parser)
    parser.add_argument("--model-path", required=True, help="Existing best_model.zip or final_model.zip path")
    parser.add_argument("--output-folder", default="logs_playback", help="Folder for playback logger output")
    parser.add_argument("--steps", type=int, default=0, help="Playback steps; 0 means env episode length plus two seconds")
    parser.add_argument("--gui", action="store_true", help="Enable PyBullet GUI; keep off for headless automation")
    parser.add_argument("--record-video", action="store_true", help="Ask the env to record video frames")
    parser.add_argument("--render", action="store_true", help="Call env.render() each step")
    parser.add_argument("--realtime", action="store_true", help="Use gym_pybullet_drones.utils.sync for wall-clock pacing")
    parser.add_argument("--plot", action="store_true", help="Call Logger.plot() after playback; avoid in headless CI")
    parser.add_argument("--save-log", action="store_true", help="Call Logger.save() after playback")
    parser.add_argument("--no-stop-on-done", dest="stop_on_done", action="store_false", help="Continue until --steps even after terminated/truncated")
    parser.set_defaults(stop_on_done=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run gym-pybullet-drones PPO smoke training and playback workflows.")
    parser.add_argument("--debug", action="store_true", help="Print tracebacks for unexpected errors")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check-imports", help="Verify RL imports and Gymnasium env registration")
    check.set_defaults(func=check_imports)

    train = sub.add_parser("train", help="Run a short headless PPO training smoke and save model artifacts")
    add_train_args(train)
    train.set_defaults(func=train_policy)

    play = sub.add_parser("play", help="Load and play an existing PPO model")
    add_play_args(play)
    play.set_defaults(func=play_policy)

    train_play = sub.add_parser("train-play", help="Train a short smoke model and immediately play it headless")
    add_train_args(train_play)
    train_play.add_argument("--play-steps", type=int, default=60, help="Playback steps after training")
    train_play.add_argument("--gui", action="store_true", help="Enable GUI for the playback half")
    train_play.add_argument("--realtime", action="store_true", help="Use sync during the playback half")
    train_play.add_argument("--plot", action="store_true", help="Plot playback logger output")
    train_play.add_argument("--save-log", action="store_true", help="Save playback logger output")
    train_play.set_defaults(func=train_then_play)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args, emit=True)
        return 0
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    except (RuntimeError, ValueError, FileExistsError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 3
    except Exception as exc:  # pragma: no cover - final CLI guard
        print(f"[ERROR] Unexpected failure: {type(exc).__name__}: {exc}", file=sys.stderr)
        if getattr(args, "debug", False):
            raise
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
