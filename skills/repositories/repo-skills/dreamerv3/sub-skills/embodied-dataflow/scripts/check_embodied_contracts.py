#!/usr/bin/env python3
"""Safe Embodied Env/Replay/Driver contract checker.

This script is bundled with the DreamerV3 embodied-dataflow skill. It performs
small, deterministic contract smokes and never starts training. Imports of the
DreamerV3/Embodied package are lazy so --help works even before installation is
fixed.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional, Tuple

import numpy as np


REQUIRED_OBS_KEYS = ("reward", "is_first", "is_last", "is_terminal")


@dataclass
class CheckResult:
  name: str
  ok: bool
  details: str


def main(argv: Optional[Iterable[str]] = None) -> int:
  parser = argparse.ArgumentParser(
      description=(
          "Check DreamerV3 Embodied Env, Replay, and Driver dataflow contracts "
          "with tiny safe smokes. No training is started."))
  parser.add_argument(
      "--mode", choices=("env", "replay", "driver"), default=None,
      help="Run one checker mode. Use --all to run every mode.")
  parser.add_argument(
      "--all", action="store_true",
      help="Run env, replay, and driver checks.")
  parser.add_argument(
      "--factory", default=None, metavar="MODULE:CALLABLE",
      help=(
          "Optional zero-argument environment factory for env/driver checks. "
          "When omitted, a tiny built-in dummy-like Embodied env is used."))
  parser.add_argument(
      "--length", type=int, default=4,
      help="Episode/replay sequence length used by the tiny checks (default: 4).")
  parser.add_argument(
      "--steps", type=int, default=12,
      help="Driver steps used in driver mode when episodes are not enough (default: 12).")
  parser.add_argument(
      "--parallel-envs", type=int, default=1,
      help=(
          "Number of env factories for driver mode. The checker keeps Driver "
          "parallel=False for safety; this controls sequential vectorization "
          "only (default: 1)."))
  args = parser.parse_args(argv)

  if args.length < 1:
    parser.error("--length must be >= 1")
  if args.steps < 1:
    parser.error("--steps must be >= 1")
  if args.parallel_envs < 1:
    parser.error("--parallel-envs must be >= 1")
  if not args.all and not args.mode:
    parser.error("choose --mode env|replay|driver or --all")

  modes = ("env", "replay", "driver") if args.all else (args.mode,)

  try:
    embodied, elements = import_embodied()
    factory = load_factory(args.factory) if args.factory else None
    results = []
    for mode in modes:
      if mode == "env":
        results.append(check_env_contract(embodied, elements, factory, args.length))
      elif mode == "replay":
        results.append(check_replay_contract(embodied, args.length))
      elif mode == "driver":
        results.append(check_driver_contract(
            embodied, elements, factory, args.length, args.steps,
            args.parallel_envs))
      else:  # pragma: no cover - argparse prevents this.
        raise AssertionError(mode)
  except Exception as exc:  # Keep command-line failure concise but useful.
    print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 1

  for result in results:
    status = "PASS" if result.ok else "FAIL"
    print(f"{status}: {result.name}: {result.details}")
  return 0 if all(result.ok for result in results) else 1


def import_embodied() -> Tuple[Any, Any]:
  try:
    embodied = importlib.import_module("embodied")
  except Exception as exc:
    raise RuntimeError(
        "Could not import 'embodied'. Install the DreamerV3/dreamer package "
        "before running contract modes. --help does not require it.") from exc
  try:
    elements = importlib.import_module("elements")
  except Exception as exc:
    raise RuntimeError(
        "Could not import 'elements', which provides elements.Space.") from exc
  return embodied, elements


def load_factory(spec: str) -> Callable[[], Any]:
  if ":" not in spec:
    raise ValueError("--factory must have form MODULE:CALLABLE")
  module_name, attr_path = spec.split(":", 1)
  module = importlib.import_module(module_name)
  obj = module
  for part in attr_path.split("."):
    obj = getattr(obj, part)
  if not callable(obj):
    raise TypeError(f"Factory target {spec!r} is not callable")
  return obj


def make_tiny_env_class(embodied: Any, elements: Any):
  class TinyEmbodiedEnv(embodied.Env):

    def __init__(self, length: int = 4):
      self.length = int(length)
      self.count = 0
      self.done = True

    @property
    def obs_space(self) -> Dict[str, Any]:
      return {
          "image": elements.Space(np.uint8, (8, 8, 3)),
          "vector": elements.Space(np.float32, (3,), -10.0, 10.0),
          "count": elements.Space(np.int32, (), 0, self.length + 1),
          "reward": elements.Space(np.float32),
          "is_first": elements.Space(bool),
          "is_last": elements.Space(bool),
          "is_terminal": elements.Space(bool),
          "log/episode_step": elements.Space(np.int32),
      }

    @property
    def act_space(self) -> Dict[str, Any]:
      return {
          "reset": elements.Space(bool),
          "action": elements.Space(np.int32, (), 0, 3),
          "throttle": elements.Space(np.float32, (2,), -1.0, 1.0),
      }

    def step(self, action: Dict[str, Any]) -> Dict[str, Any]:
      if "reset" not in action:
        raise KeyError("reset")
      reset = bool(np.asarray(action["reset"]).item())
      if reset or self.done:
        self.count = 0
        self.done = False
        return self._obs(0.0, is_first=True)
      self.count += 1
      terminal = self.count >= self.length
      self.done = bool(terminal)
      return self._obs(1.0, is_last=self.done, is_terminal=terminal)

    def _obs(
        self, reward: float, is_first: bool = False, is_last: bool = False,
        is_terminal: bool = False) -> Dict[str, Any]:
      return {
          "image": np.zeros((8, 8, 3), np.uint8),
          "vector": np.zeros((3,), np.float32),
          "count": np.asarray(self.count, np.int32),
          "reward": np.asarray(reward, np.float32),
          "is_first": bool(is_first),
          "is_last": bool(is_last),
          "is_terminal": bool(is_terminal),
          "log/episode_step": np.asarray(self.count, np.int32),
      }

    def close(self) -> None:
      pass

  return TinyEmbodiedEnv


def default_factory(embodied: Any, elements: Any, length: int) -> Callable[[], Any]:
  cls = make_tiny_env_class(embodied, elements)
  return lambda: cls(length=length)


def check_env_contract(
    embodied: Any, elements: Any, factory: Optional[Callable[[], Any]],
    length: int) -> CheckResult:
  del embodied
  env_factory = factory or default_factory(sys.modules["embodied"], elements, length)
  env = env_factory()
  try:
    obs_space = require_space_dict(env.obs_space, "obs_space")
    act_space = require_space_dict(env.act_space, "act_space")
    require_keys(obs_space, REQUIRED_OBS_KEYS, "obs_space")
    require_keys(act_space, ("reset",), "act_space")
    overlap = set(obs_space) & set(act_space)
    if overlap:
      raise AssertionError(f"obs_space and act_space overlap: {sorted(overlap)}")

    reset_action = make_action(act_space, reset=True)
    first = env.step(reset_action)
    validate_observation(first, obs_space, expected_first=True)

    normal_action = make_action(act_space, reset=False)
    second = env.step(normal_action)
    validate_observation(second, obs_space, expected_first=False)

    return CheckResult(
        "env", True,
        f"{env.__class__.__name__} exposes {len(obs_space)} obs keys and "
        f"{len(act_space)} act keys including reset")
  finally:
    close_quietly(env)


def check_replay_contract(embodied: Any, length: int) -> CheckResult:
  replay = embodied.Replay(length=length, capacity=max(8, 4 * length), seed=0)
  workers = 2
  raw_steps = length + 2
  for step in range(raw_steps):
    for worker in range(workers):
      replay.add({
          "step": np.asarray(step, np.int32),
          "worker": np.asarray(worker, np.int32),
          "reward": np.asarray(1.0, np.float32),
          "is_first": np.asarray(step == 0, bool),
          "is_last": np.asarray(step == raw_steps - 1, bool),
          "is_terminal": np.asarray(False, bool),
          "log/ignored": np.asarray(123, np.int32),
      }, worker=worker)

  if len(replay) <= 0:
    raise AssertionError("replay did not insert any sampleable items")
  batch = replay.sample(batch=4, mode="train")
  require_keys(batch, ("step", "worker", "stepid"), "sample batch")
  if batch["step"].shape[:2] != (4, length):
    raise AssertionError(
        f"sample step shape {batch['step'].shape} does not start with "
        f"(4, {length})")
  diffs = batch["step"] - batch["step"][:, :1]
  target = np.arange(length, dtype=diffs.dtype)[None, :]
  if not np.all(diffs == target):
    raise AssertionError("sampled steps are not contiguous within rows")
  if not np.all(batch["worker"] == batch["worker"][:, :1]):
    raise AssertionError("sampled rows cross worker streams")
  if "log/ignored" in batch:
    raise AssertionError("replay sample unexpectedly retained log/ key")
  stats = replay.stats()
  return CheckResult(
      "replay", True,
      f"len={len(replay)}, sample shape={batch['step'].shape}, "
      f"stats keys={sorted(stats.keys())}")


def check_driver_contract(
    embodied: Any, elements: Any, factory: Optional[Callable[[], Any]],
    length: int, steps: int, parallel_envs: int) -> CheckResult:
  env_factory = factory or default_factory(embodied, elements, length)

  probe = env_factory()
  try:
    obs_space = require_space_dict(probe.obs_space, "obs_space")
    act_space = require_space_dict(probe.act_space, "act_space")
    require_keys(act_space, ("reset",), "act_space")
    agent = embodied.RandomAgent(obs_space, act_space)
  finally:
    close_quietly(probe)

  driver = embodied.Driver([env_factory for _ in range(parallel_envs)], parallel=False)
  transitions = []
  try:
    driver.reset(agent.init_policy)
    driver.on_step(lambda tran, worker: transitions.append((dict(tran), worker)))
    driver(agent.policy, steps=steps)
  finally:
    close_quietly(driver)

  if len(transitions) < steps:
    raise AssertionError(f"driver produced {len(transitions)} transitions for {steps} steps")
  workers_seen = {worker for _, worker in transitions}
  if workers_seen != set(range(parallel_envs)):
    raise AssertionError(f"workers seen {workers_seen}, expected {set(range(parallel_envs))}")
  first_by_worker = {}
  last_count = 0
  for tran, worker in transitions:
    require_keys(tran, REQUIRED_OBS_KEYS, "driver transition")
    first_by_worker.setdefault(worker, bool(np.asarray(tran["is_first"]).item()))
    last_count += int(bool(np.asarray(tran["is_last"]).item()))
  if not all(first_by_worker.values()):
    raise AssertionError("first transition per worker was not is_first=True")
  return CheckResult(
      "driver", True,
      f"transitions={len(transitions)}, workers={sorted(workers_seen)}, "
      f"episode_endings={last_count}")


def require_space_dict(value: Any, name: str) -> Dict[str, Any]:
  if not isinstance(value, dict):
    raise TypeError(f"{name} must be a dict, got {type(value).__name__}")
  for key, space in value.items():
    if not isinstance(key, str):
      raise TypeError(f"{name} key {key!r} is not a string")
    for attr in ("dtype", "shape"):
      if not hasattr(space, attr):
        raise TypeError(f"{name}[{key!r}] does not look like elements.Space")
  return value


def require_keys(mapping: Dict[str, Any], keys: Iterable[str], name: str) -> None:
  missing = [key for key in keys if key not in mapping]
  if missing:
    raise AssertionError(f"{name} missing required keys: {missing}")


def make_action(act_space: Dict[str, Any], reset: bool) -> Dict[str, Any]:
  action = {}
  for key, space in act_space.items():
    if key == "reset":
      action[key] = np.asarray(reset, dtype=np.dtype(space.dtype))
    elif hasattr(space, "sample"):
      action[key] = space.sample()
    else:
      action[key] = np.zeros(getattr(space, "shape", ()), getattr(space, "dtype", np.float32))
  return action


def validate_observation(
    obs: Dict[str, Any], obs_space: Dict[str, Any], expected_first: bool) -> None:
  if not isinstance(obs, dict):
    raise TypeError(f"step() must return a dict, got {type(obs).__name__}")
  require_keys(obs, REQUIRED_OBS_KEYS, "observation")
  extra = sorted(set(obs) - set(obs_space))
  missing = sorted(set(obs_space) - set(obs))
  if extra:
    raise AssertionError(f"observation has keys not declared in obs_space: {extra}")
  if missing:
    raise AssertionError(f"observation missing declared obs_space keys: {missing}")
  first = bool(np.asarray(obs["is_first"]).item())
  if first != expected_first:
    raise AssertionError(f"is_first={first}, expected {expected_first}")
  for key, value in obs.items():
    space = obs_space[key]
    if not value_in_space(value, space):
      arr = np.asarray(value)
      raise AssertionError(
          f"observation {key!r} not in declared space: dtype={arr.dtype}, "
          f"shape={arr.shape}, space={space}")


def value_in_space(value: Any, space: Any) -> bool:
  try:
    return bool(value in space)
  except Exception:
    arr = np.asarray(value)
    expected_shape = tuple(getattr(space, "shape", ()))
    dtype_ok = np.can_cast(arr.dtype, np.dtype(space.dtype), casting="safe") or arr.dtype == np.dtype(space.dtype)
    return arr.shape == expected_shape and dtype_ok


def close_quietly(obj: Any) -> None:
  close = getattr(obj, "close", None)
  if callable(close):
    try:
      close()
    except Exception:
      pass


if __name__ == "__main__":
  raise SystemExit(main())
