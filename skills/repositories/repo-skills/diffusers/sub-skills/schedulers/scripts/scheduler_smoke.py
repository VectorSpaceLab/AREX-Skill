#!/usr/bin/env python3
"""Smoke-check Diffusers scheduler imports, signatures, timesteps, and tiny CPU steps."""

import argparse
import inspect
import sys
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import common Diffusers schedulers and run tiny deterministic scheduler checks.",
    )
    parser.add_argument(
        "--schedulers",
        nargs="+",
        default=["DDIMScheduler", "DDPMScheduler", "EulerDiscreteScheduler", "DPMSolverMultistepScheduler"],
        help="Scheduler class names to inspect and smoke-check.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=4,
        help="Number of inference timesteps for generated schedules.",
    )
    parser.add_argument(
        "--train-timesteps",
        type=int,
        default=20,
        help="Small num_train_timesteps value for synthetic scheduler construction.",
    )
    parser.add_argument(
        "--skip-step",
        action="store_true",
        help="Only inspect imports/signatures and set_timesteps; do not call scheduler.step.",
    )
    return parser.parse_args()


def import_scheduler(name: str):
    import diffusers

    try:
        return getattr(diffusers, name)
    except AttributeError as error:
        raise SystemExit(f"Scheduler {name!r} is not available from diffusers: {error}") from error


def summarize_values(values: Iterable, limit: int = 5) -> str:
    as_list = list(values)
    shown = as_list[:limit]
    suffix = "" if len(as_list) <= limit else f" ... ({len(as_list)} total)"
    return f"{shown}{suffix}"


def supports_kwarg(callable_obj, name: str) -> bool:
    return name in inspect.signature(callable_obj).parameters


def build_scheduler(cls, train_timesteps: int):
    kwargs = {}
    init_signature = inspect.signature(cls)
    if "num_train_timesteps" in init_signature.parameters:
        kwargs["num_train_timesteps"] = train_timesteps
    if "prediction_type" in init_signature.parameters:
        kwargs["prediction_type"] = "epsilon"
    return cls(**kwargs)


def set_short_timesteps(scheduler, steps: int):
    set_timesteps = getattr(scheduler, "set_timesteps", None)
    if set_timesteps is None:
        print("  set_timesteps: not available")
        return False

    if supports_kwarg(set_timesteps, "num_inference_steps"):
        scheduler.set_timesteps(num_inference_steps=steps)
    else:
        scheduler.set_timesteps(steps)

    timesteps = getattr(scheduler, "timesteps", None)
    if timesteps is not None:
        print(f"  timesteps: {summarize_values(timesteps.tolist() if hasattr(timesteps, 'tolist') else timesteps)}")
    sigmas = getattr(scheduler, "sigmas", None)
    if sigmas is not None:
        print(f"  sigmas: {summarize_values(sigmas.tolist() if hasattr(sigmas, 'tolist') else sigmas)}")
    return True


def tiny_step_check(scheduler) -> None:
    import torch

    if not hasattr(scheduler, "step") or not hasattr(scheduler, "timesteps"):
        print("  step: skipped; scheduler lacks step or timesteps")
        return
    if len(scheduler.timesteps) == 0:
        print("  step: skipped; no timesteps")
        return

    sample = torch.linspace(-1, 1, 16, dtype=torch.float32).reshape(1, 1, 4, 4)
    model_output = torch.zeros_like(sample)
    timestep = scheduler.timesteps[0]
    if hasattr(scheduler, "scale_model_input"):
        scaled = scheduler.scale_model_input(sample, timestep)
        assert scaled.shape == sample.shape, "scale_model_input changed sample shape"

    output = scheduler.step(model_output, timestep, sample)
    prev_sample = output.prev_sample if hasattr(output, "prev_sample") else output[0]
    assert prev_sample.shape == sample.shape, "prev_sample shape mismatch"
    assert torch.isfinite(prev_sample).all(), "prev_sample contains NaN or Inf"
    print(f"  step: ok prev_sample_mean={prev_sample.mean().item():.6f}")


def misuse_check(cls, train_timesteps: int) -> None:
    import torch

    scheduler = build_scheduler(cls, train_timesteps)
    if not hasattr(scheduler, "step"):
        return
    try:
        sample = torch.zeros(1, 1, 4, 4)
        model_output = torch.zeros_like(sample)
        timestep = getattr(scheduler, "timesteps", [0])[0]
        scheduler.step(model_output, timestep, sample)
    except Exception as error:
        print(f"  misuse step-before-set_timesteps: expected error: {type(error).__name__}: {str(error).splitlines()[0]}")
    else:
        print("  misuse step-before-set_timesteps: no error for this scheduler")


def main() -> int:
    args = parse_args()
    if args.steps < 1:
        raise SystemExit("--steps must be >= 1")
    if args.train_timesteps < args.steps:
        raise SystemExit("--train-timesteps must be >= --steps")

    try:
        import diffusers
        import torch
    except Exception as error:
        raise SystemExit(f"Failed to import required packages: {type(error).__name__}: {error}") from error

    print(f"diffusers={getattr(diffusers, '__version__', 'unknown')}")
    print(f"torch={getattr(torch, '__version__', 'unknown')} cuda_available={torch.cuda.is_available()}")

    for name in args.schedulers:
        cls = import_scheduler(name)
        print(f"\n{name}")
        print(f"  init: {inspect.signature(cls)}")
        if hasattr(cls, "step"):
            print(f"  step: {inspect.signature(cls.step)}")

        scheduler = build_scheduler(cls, args.train_timesteps)
        if set_short_timesteps(scheduler, args.steps) and not args.skip_step:
            tiny_step_check(scheduler)
        misuse_check(cls, args.train_timesteps)

    print("\nscheduler smoke checks completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
