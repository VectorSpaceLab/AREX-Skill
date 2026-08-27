#!/usr/bin/env python3
"""Estimate training-loop scale for compact optimizer/meta/RL examples.

Stdlib-only: this helper imports no torch, keras, gym, or repository modules and
never runs a native paper implementation.
"""
from __future__ import annotations

import argparse
import json
import math
from typing import Any, Dict, Iterable, Optional


def _int(text: str) -> int:
    try:
        value = int(text.replace("_", ""))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected integer, got {text!r}") from exc
    if value < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return value


def _pos_int(text: str) -> int:
    value = _int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return value


def _float(text: str) -> float:
    try:
        value = float(text.replace("_", ""))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected number, got {text!r}") from exc
    if value < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return value


def _fmt(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value)):,}"
    return f"{value:,.2f}"


def _duration(seconds: Optional[float]) -> Optional[str]:
    if seconds is None:
        return None
    days, rem = divmod(float(seconds), 86_400)
    hours, rem = divmod(rem, 3_600)
    minutes, sec = divmod(rem, 60)
    pieces = []
    if int(days):
        pieces.append(f"{int(days)}d")
    if int(hours) or pieces:
        pieces.append(f"{int(hours)}h")
    if int(minutes) or pieces:
        pieces.append(f"{int(minutes)}m")
    pieces.append(f"{sec:.1f}s")
    return " ".join(pieces)


def _markers(total: float, interval: int, limit: int) -> list[int]:
    if not interval or total <= 0:
        return []
    count = int(total // interval)
    return [interval * i for i in range(1, min(count, limit) + 1)]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Estimate loop size, update counts, and time markers without running ML code.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  DQN: estimate_training_steps.py --nb-epochs 30000000 --warmup-steps 80000 "
            "--train-frequency 4 --eval-interval 50000 --target-update-interval 10000\n"
            "  PPO: estimate_training_steps.py --nb-epochs 40000 --actors 8 --rollout-length 128 "
            "--ppo-update-epochs 3 --batch-size 256\n"
            "  MNIST: estimate_training_steps.py --nb-epochs 150 --steps-per-epoch 938 --eval-interval 1"
        ),
    )
    p.add_argument("--nb-epochs", type=_int, default=0, help="outer-loop epochs, iterations, or env steps")
    p.add_argument("--steps-per-epoch", type=_float, default=1.0, help="work units per epoch when no rollout length is used")
    p.add_argument("--episodes", type=_int, default=0, help="episode count for episode-driven estimates")
    p.add_argument("--steps-per-episode", type=_float, default=0.0, help="average steps per episode")
    p.add_argument("--actors", type=_pos_int, default=1, help="parallel actors/environments for rollout loops")
    p.add_argument("--rollout-length", type=_int, default=0, help="steps per actor per outer iteration, e.g. PPO T")
    p.add_argument("--batch-size", type=_pos_int, default=0, help="minibatch size for rollout update estimates")
    p.add_argument("--ppo-update-epochs", type=_int, default=0, help="optimization passes over each rollout buffer")
    p.add_argument("--warmup-steps", type=_int, default=0, help="steps before training updates begin")
    p.add_argument("--train-frequency", type=_pos_int, default=0, help="one train event every N steps after warmup")
    p.add_argument("--updates-per-event", type=_float, default=1.0, help="updates per train-frequency event")
    p.add_argument("--eval-interval", type=_pos_int, default=0, help="evaluation/plot interval in primary steps")
    p.add_argument("--target-update-interval", type=_pos_int, default=0, help="target/checkpoint interval in primary steps")
    p.add_argument("--time-per-step-ms", type=_float, default=0.0, help="optional time per primary step in milliseconds")
    p.add_argument("--time-per-episode-sec", type=_float, default=0.0, help="optional time per episode in seconds")
    p.add_argument("--marker-limit", type=_pos_int, default=12, help="number of marker values to preview")
    p.add_argument("--json", action="store_true", help="emit JSON instead of text")
    return p


def estimate(args: argparse.Namespace) -> Dict[str, Any]:
    epoch_steps = args.nb_epochs * args.steps_per_epoch
    rollout_steps = args.nb_epochs * args.actors * args.rollout_length if args.rollout_length else 0
    episode_steps = args.episodes * args.steps_per_episode if args.episodes and args.steps_per_episode else 0
    if args.rollout_length:
        primary_steps = rollout_steps
        basis = "nb_epochs * actors * rollout_length"
    elif epoch_steps:
        primary_steps = epoch_steps
        basis = "nb_epochs * steps_per_epoch"
    else:
        primary_steps = episode_steps
        basis = "episodes * steps_per_episode"
    trainable = max(0.0, primary_steps - args.warmup_steps)
    train_events = math.floor(trainable / args.train_frequency) if args.train_frequency else 0
    freq_updates = train_events * args.updates_per_event
    rollout_minibatch_updates = 0
    if args.rollout_length and args.batch_size and args.ppo_update_epochs:
        rollout_items = args.actors * args.rollout_length
        rollout_minibatch_updates = args.nb_epochs * args.ppo_update_epochs * math.ceil(rollout_items / args.batch_size)
    seconds = None
    if args.time_per_step_ms:
        seconds = primary_steps * args.time_per_step_ms / 1000.0
    if args.time_per_episode_sec and args.episodes:
        seconds = (seconds or 0.0) + args.episodes * args.time_per_episode_sec
    risk = "small"
    if primary_steps >= 10_000_000 or (seconds is not None and seconds >= 6 * 3600):
        risk = "very-long"
    elif primary_steps >= 1_000_000 or (seconds is not None and seconds >= 1800):
        risk = "long"
    elif primary_steps >= 100_000:
        risk = "moderate"
    return {
        "basis": basis,
        "epoch_steps": epoch_steps,
        "rollout_steps": rollout_steps,
        "episode_steps": episode_steps,
        "primary_steps": primary_steps,
        "trainable_steps_after_warmup": trainable,
        "train_update_events": train_events,
        "estimated_updates_from_frequency": freq_updates,
        "estimated_rollout_minibatch_updates": rollout_minibatch_updates,
        "eval_marker_count": math.floor(primary_steps / args.eval_interval) if args.eval_interval else 0,
        "eval_marker_preview": _markers(primary_steps, args.eval_interval, args.marker_limit),
        "target_update_count": math.floor(primary_steps / args.target_update_interval) if args.target_update_interval else 0,
        "target_update_preview": _markers(primary_steps, args.target_update_interval, args.marker_limit),
        "estimated_seconds": seconds,
        "estimated_duration": _duration(seconds),
        "risk": risk,
    }


def print_text(report: Dict[str, Any]) -> None:
    print("Training loop estimate")
    print("======================")
    print(f"Primary basis: {report['basis']}")
    print(f"Primary steps: {_fmt(report['primary_steps'])}")
    print(f"Epoch-derived steps: {_fmt(report['epoch_steps'])}")
    if report["rollout_steps"]:
        print(f"Rollout-derived environment steps: {_fmt(report['rollout_steps'])}")
    if report["episode_steps"]:
        print(f"Episode-derived steps: {_fmt(report['episode_steps'])}")
    if report["train_update_events"] or report["trainable_steps_after_warmup"]:
        print(f"Trainable steps after warmup: {_fmt(report['trainable_steps_after_warmup'])}")
        print(f"Train update events: {_fmt(report['train_update_events'])}")
        print(f"Estimated updates from frequency: {_fmt(report['estimated_updates_from_frequency'])}")
    if report["estimated_rollout_minibatch_updates"]:
        print(f"Estimated rollout minibatch updates: {_fmt(report['estimated_rollout_minibatch_updates'])}")
    if report["eval_marker_count"]:
        print(f"Eval/plot markers: {_fmt(report['eval_marker_count'])}")
        print("  first markers: " + ", ".join(f"{m:,}" for m in report["eval_marker_preview"]))
    if report["target_update_count"]:
        print(f"Target/checkpoint update markers: {_fmt(report['target_update_count'])}")
        print("  first markers: " + ", ".join(f"{m:,}" for m in report["target_update_preview"]))
    if report["estimated_duration"]:
        print(f"Estimated wall time: {report['estimated_duration']}")
    print(f"Risk label: {report['risk']}")
    if report["risk"] in {"long", "very-long"}:
        print("Recommendation: reduce to a synthetic smoke test unless full data/hardware/time is approved.")


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parser().parse_args(argv)
    report = estimate(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
