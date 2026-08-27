#!/usr/bin/env python3
"""Safe random rollout smoke test for dm_control suite environments.

Examples:
  python scripts/suite_random_rollout.py
  python scripts/suite_random_rollout.py --domain cartpole --task swingup --steps 3 --seed 1
  python scripts/suite_random_rollout.py --domain cartpole --task balance --flat-observation \
      --visualize-reward --render-frame

Expected output starts with lines like:
  domain=cartpole task=balance seed=0 steps=5
  action_spec: BoundedArray(...)
  observation_spec: {position: Array(...), velocity: Array(...)}
  step_spec: <not implemented>
  reset: step_type=FIRST reward=None discount=None observation=...
  step 1: step_type=MID reward=... discount=...
  render_frame: shape=(240, 320, 3) dtype=uint8
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping

import numpy as np
from dm_control import suite
from dm_env import specs

_RENDER_HEIGHT = 240
_RENDER_WIDTH = 320


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter,
                    argparse.RawDescriptionHelpFormatter):
  pass


def format_array(array, precision=3, threshold=8):
  return np.array2string(
      np.asarray(array), precision=precision, separator=", ", threshold=threshold)


def describe_spec(spec):
  if isinstance(spec, specs.BoundedArray):
    return (
        f"BoundedArray(shape={spec.shape}, dtype={spec.dtype}, "
        f"minimum={format_array(spec.minimum)}, maximum={format_array(spec.maximum)})")
  if isinstance(spec, specs.Array):
    return f"Array(shape={spec.shape}, dtype={spec.dtype})"
  if isinstance(spec, Mapping):
    inner = ", ".join(f"{key}: {describe_spec(value)}" for key, value in spec.items())
    return "{" + inner + "}"
  return repr(spec)


def describe_value(value):
  if isinstance(value, Mapping):
    inner = ", ".join(f"{key}: {describe_value(item)}" for key, item in value.items())
    return "{" + inner + "}"
  array = np.asarray(value)
  return f"shape={array.shape}, dtype={array.dtype}"


def validate_domain_task(domain_name, task_name):
  valid_tasks = suite.TASKS_BY_DOMAIN.get(domain_name)
  if valid_tasks is None:
    raise SystemExit(
        f"Unknown domain {domain_name!r}. Valid domains: "
        f"{', '.join(sorted(suite.TASKS_BY_DOMAIN))}")
  if task_name not in valid_tasks:
    raise SystemExit(
        f"Unknown task {task_name!r} for domain {domain_name!r}. "
        f"Valid tasks: {', '.join(valid_tasks)}")


def make_action_sampler(action_spec, seed):
  if not isinstance(action_spec, specs.BoundedArray):
    raise SystemExit(
        f"Expected env.action_spec() to return a BoundedArray, got {type(action_spec).__name__}: {action_spec!r}")

  lower = np.asarray(action_spec.minimum, dtype=np.float64)
  upper = np.asarray(action_spec.maximum, dtype=np.float64)
  if np.any(np.isfinite(lower) & np.isfinite(upper) & (upper < lower)):
    raise SystemExit(
        "action_spec has lower bounds greater than upper bounds; "
        "refuse to sample from an invalid range.")

  invalid_bounds = ~np.isfinite(lower) | ~np.isfinite(upper)
  sample_lower = np.where(invalid_bounds, -1.0, lower)
  sample_upper = np.where(invalid_bounds, 1.0, upper)
  if np.any(invalid_bounds):
    print(
        f"warning: action_spec has {int(invalid_bounds.sum())} non-finite bound(s); "
        "sampling those dimensions from [-1, 1].",
        file=sys.stderr)

  rng = np.random.default_rng(seed)

  def sample():
    action = rng.uniform(sample_lower, sample_upper, size=action_spec.shape)
    return np.asarray(action, dtype=action_spec.dtype)

  return sample


def render_frame(env):
  try:
    frame = env.physics.render(height=_RENDER_HEIGHT, width=_RENDER_WIDTH)
  except Exception as exc:  # pragma: no cover - backend dependent
    print(f"render_frame: skipped ({exc.__class__.__name__}: {exc})", file=sys.stderr)
    return
  print(f"render_frame: shape={frame.shape} dtype={frame.dtype}")


def build_parser():
  parser = argparse.ArgumentParser(
      description="Run a deterministic random rollout against a built-in dm_control suite task.",
      formatter_class=HelpFormatter,
      epilog=(
          "Examples:\n"
          "  python scripts/suite_random_rollout.py\n"
          "  python scripts/suite_random_rollout.py --domain cartpole --task swingup --steps 3 --seed 1\n"
          "  python scripts/suite_random_rollout.py --domain cartpole --task balance --flat-observation --visualize-reward --render-frame\n\n"
          "Expected output begins with:\n"
          "  domain=cartpole task=balance seed=0 steps=5\n"
          "  action_spec: BoundedArray(...)\n"
          "  observation_spec: {position: Array(...), velocity: Array(...)}\n"
          "  step_spec: <not implemented>\n"
          "  reset: step_type=FIRST reward=None discount=None observation=...\n"
          "  step 1: step_type=MID reward=... discount=...\n"
          "  render_frame: shape=(240, 320, 3) dtype=uint8"))
  parser.add_argument("--domain", default="cartpole",
                      help="Control Suite domain name to load.")
  parser.add_argument("--task", default="balance",
                      help="Control Suite task name to load.")
  parser.add_argument("--steps", type=int, default=5,
                      help="Maximum number of rollout steps to take after reset.")
  parser.add_argument("--seed", type=int, default=0,
                      help="Seed for both the task random state and the rollout sampler.")
  parser.add_argument("--flat-observation", action="store_true",
                      help="Request flat observations via environment_kwargs.")
  parser.add_argument("--visualize-reward", action="store_true",
                      help="Enable reward-colored geoms in rendered frames.")
  parser.add_argument("--render-frame", action="store_true",
                      help="Render one frame after reset and print its shape/dtype.")
  return parser


def main(argv=None):
  parser = build_parser()
  args = parser.parse_args(argv)

  if args.steps < 0:
    parser.error("--steps must be non-negative")

  validate_domain_task(args.domain, args.task)

  environment_kwargs = {}
  if args.flat_observation:
    environment_kwargs["flat_observation"] = True

  env = suite.load(
      args.domain,
      args.task,
      task_kwargs={"random": args.seed},
      environment_kwargs=environment_kwargs or None,
      visualize_reward=args.visualize_reward,
  )

  action_spec = env.action_spec()
  action_sampler = make_action_sampler(action_spec, args.seed)

  print(
      f"domain={args.domain} task={args.task} seed={args.seed} steps={args.steps} "
      f"flat_observation={args.flat_observation} visualize_reward={args.visualize_reward}")
  print(f"control_timestep: {env.control_timestep():.6f}s")
  print(f"action_spec: {describe_spec(action_spec)}")
  print(f"observation_spec: {describe_spec(env.observation_spec())}")
  try:
    step_spec = env.step_spec()
  except NotImplementedError:
    step_spec = None
  if step_spec is None:
    print("step_spec: <not implemented>")
  else:
    print(f"step_spec: {describe_spec(step_spec)}")

  time_step = env.reset()
  print(
      f"reset: step_type={time_step.step_type.name} reward={time_step.reward} "
      f"discount={time_step.discount} observation={describe_value(time_step.observation)}")

  if args.render_frame:
    render_frame(env)

  for step_index in range(1, args.steps + 1):
    action = action_sampler()
    action_spec.validate(action)
    time_step = env.step(action)
    print(
        f"step {step_index}: action={format_array(action)} -> "
        f"step_type={time_step.step_type.name} reward={time_step.reward} "
        f"discount={time_step.discount} observation={describe_value(time_step.observation)}")
    if time_step.last():
      break

  return 0


if __name__ == "__main__":
  raise SystemExit(main())
