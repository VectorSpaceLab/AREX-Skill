#!/usr/bin/env python3
"""Run a bounded, non-training Rex-Gym environment smoke test.

The default is PyBullet DIRECT/headless mode. This script imports a task,
constructs it with packaged terrain/URDF arguments, resets, performs a bounded
number of zero-action steps, reports legacy Gym values, and closes the env.
It never trains, downloads, or invokes the PPO/TensorFlow CLI.
"""
from __future__ import print_function

import argparse
import contextlib
import ctypes
import io
import json
import os
import sys
import tempfile
import traceback


TASKS = {
    "poses": ("rex_gym.envs.gym.poses_env", "RexPosesEnv", "ik"),
    "gallop": ("rex_gym.envs.gym.gallop_env", "RexReactiveEnv", "ik"),
    "walk": ("rex_gym.envs.gym.walk_env", "RexWalkEnv", "ik"),
    "turn": ("rex_gym.envs.gym.turn_env", "RexTurnEnv", "ol"),
    "standup": ("rex_gym.envs.gym.standup_env", "RexStandupEnv", "ol"),
}
SIGNALS = ("ik", "ol")
TERRAIN_TYPES = {
    "plane": "plane",
    "random": "random",
    "hills": "csv",
    "mounts": "png",
    "maze": "png",
}
MARKS = ("base", "arm")
MAX_STEPS = 100


def bounded_steps(value):
    """Argparse validator: prevent an accidental long-running smoke."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("steps must be an integer")
    if number < 0 or number > MAX_STEPS:
        raise argparse.ArgumentTypeError(
            "steps must be between 0 and {}".format(MAX_STEPS))
    return number


def finite_float(value):
    """Argparse validator for finite task targets."""
    try:
        number = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("target-position must be a number")
    if number != number or number in (float("inf"), float("-inf")):
        raise argparse.ArgumentTypeError("target-position must be finite")
    return number


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=sorted(TASKS), default="walk",
                        help="task environment (default: walk)")
    parser.add_argument("--signal", choices=SIGNALS, default=None,
                        help="ik or ol; task default when omitted")
    parser.add_argument("--terrain", choices=sorted(TERRAIN_TYPES),
                        default="plane", help="terrain id (default: plane)")
    parser.add_argument("--mark", choices=MARKS, default="base",
                        help="robot mark/URDF (default: base)")
    parser.add_argument("--target-position", type=finite_float, default=None,
                        help="optional x target for walk or gallop")
    parser.add_argument("--direction", choices=("forward", "backward", "random"),
                        default="forward",
                        help="walk direction; default: forward")
    parser.add_argument("--steps", type=bounded_steps, default=1,
                        help="number of zero-action steps, 0-{} (default: 1)"
                             .format(MAX_STEPS))
    parser.add_argument("--render", action="store_true",
                        help="explicitly request PyBullet GUI; default is DIRECT")
    return parser.parse_args(argv)


def shape_of(value):
    """Return a JSON-friendly shape for arrays and legacy Python sequences."""
    if value is None:
        return None
    shape = getattr(value, "shape", None)
    if shape is not None:
        return list(shape)
    try:
        return [len(value)]
    except (TypeError, AttributeError):
        return []


def jsonable(value):
    """Convert small NumPy/scalar values without requiring NumPy at import."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    shape = getattr(value, "shape", None)
    if shape is not None:
        return {"shape": list(shape), "dtype": str(getattr(value, "dtype", "unknown"))}
    item = getattr(value, "item", None)
    if item is not None:
        try:
            return item()
        except Exception:
            pass
    return str(value)


def error_result(args, stage, exc):
    missing = isinstance(exc, ImportError) or exc.__class__.__name__ == "ModuleNotFoundError"
    result = {
        "ok": False,
        "stage": stage,
        "task": args.task,
        "signal": args.signal or TASKS[args.task][2],
        "terrain": args.terrain,
        "mark": args.mark,
        "error_type": exc.__class__.__name__,
        "error": str(exc),
    }
    if missing:
        result["hint"] = (
            "Install rex_gym and its legacy environment dependencies in the "
            "same interpreter; environment smoke needs Gym, NumPy, and PyBullet. "
            "TensorFlow is only needed for PPO train/policy commands.")
    elif stage == "construct/reset":
        result["hint"] = (
            "Retry headless with --terrain plane and the explicit packaged "
            "terrain id; inspect terrain-and-assets.md for data/URDF issues.")
    elif stage == "step":
        result["hint"] = (
            "Check the task/signal action shape and legacy four-return Gym API; "
            "the gallop Box bounds are reversed in this old package.")
    result["traceback"] = traceback.format_exc(limit=3).splitlines()
    return result


@contextlib.contextmanager
def redirect_native_output():
    """Capture C-level Bullet startup chatter as well as Python output."""
    sys.stdout.flush()
    sys.stderr.flush()
    stdout_fd = os.dup(1)
    stderr_fd = os.dup(2)
    try:
        with tempfile.TemporaryFile(mode="w+b") as sink:
            os.dup2(sink.fileno(), 1)
            os.dup2(sink.fileno(), 2)
            try:
                yield
            finally:
                sys.stdout.flush()
                sys.stderr.flush()
                try:
                    ctypes.CDLL(None).fflush(None)
                except Exception:
                    pass
                os.dup2(stdout_fd, 1)
                os.dup2(stderr_fd, 2)
    finally:
        os.close(stdout_fd)
        os.close(stderr_fd)


def run(args):
    module_name, class_name, default_signal = TASKS[args.task]
    signal = args.signal or default_signal
    env = None
    try:
        if args.direction != "forward" and args.task != "walk":
            return error_result(
                args, "arguments",
                ValueError("--direction is only supported for the walk task"))
        if args.target_position is not None and args.task not in ("walk", "gallop"):
            return error_result(
                args, "arguments",
                ValueError("--target-position is only supported for walk or gallop"))
        try:
            module = __import__(module_name, fromlist=[class_name])
            env_class = getattr(module, class_name)
            import numpy as np
        except Exception as exc:
            return error_result(args, "import", exc)

        kwargs = {
            "render": bool(args.render),
            "terrain_type": TERRAIN_TYPES[args.terrain],
            # Direct construction needs this even for the ordinary plane.
            "terrain_id": args.terrain,
            "signal_type": signal,
            "mark": args.mark,
        }
        if args.target_position is not None:
            kwargs["target_position"] = args.target_position
        if args.task == "walk":
            kwargs["backwards"] = {
                "forward": False,
                "backward": True,
                "random": None,
            }[args.direction]
        try:
            env = env_class(**kwargs)
            observation = env.reset()
        except Exception as exc:
            return error_result(args, "construct/reset", exc)

        action_shape = tuple(getattr(env.action_space, "shape", ()))
        action = np.zeros(action_shape, dtype=np.float32)
        steps = []
        try:
            for index in range(args.steps):
                observation, reward, done, info = env.step(action)
                steps.append({
                    "index": index + 1,
                    "observation_shape": shape_of(observation),
                    "reward": jsonable(reward),
                    "done": bool(done),
                    "info_keys": sorted(str(key) for key in info.keys()),
                    "info_action_shape": shape_of(info.get("action"))
                    if isinstance(info, dict) and info.get("action") is not None else None,
                })
                if done:
                    break
        except Exception as exc:
            return error_result(args, "step", exc)

        return {
            "ok": True,
            "task": args.task,
            "class": class_name,
            "signal": signal,
            "terrain": args.terrain,
            "terrain_type": TERRAIN_TYPES[args.terrain],
            "terrain_id": args.terrain,
            "mark": args.mark,
            "target_position": args.target_position,
            "direction": args.direction if args.task == "walk" else "forward",
            "constructor_kwargs": kwargs,
            "render": bool(args.render),
            "observation_shape": shape_of(observation),
            "action_shape": list(action_shape),
            "action_dtype": str(action.dtype),
            "action_is_zero": True,
            "requested_steps": args.steps,
            "executed_steps": len(steps),
            "steps": steps,
            "legacy_api": "(observation, reward, done, info)",
        }
    except Exception as exc:
        return error_result(args, "unexpected", exc)
    finally:
        if env is not None:
            try:
                env.close()
            except Exception as close_exc:
                # Keep cleanup failures visible without replacing the useful
                # construction/step result. The legacy close hook is minimal.
                pass


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    runtime_log = io.StringIO()
    # Rex.Reset() prints a legacy status line. Capture package chatter so the
    # contract remains one machine-readable JSON object on stdout.
    with redirect_native_output():
        with contextlib.redirect_stdout(runtime_log), contextlib.redirect_stderr(runtime_log):
            result = run(args)
    captured = runtime_log.getvalue().strip().splitlines()
    if captured:
        result["runtime_log"] = captured[-20:]
    print(json.dumps(result, sort_keys=True, default=jsonable))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
