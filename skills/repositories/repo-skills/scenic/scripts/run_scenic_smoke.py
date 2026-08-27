#!/usr/bin/env python3
"""Run self-contained Scenic smoke checks against an installed package.

This helper does not run original repository tests, download data, or launch
training. It checks the small API surfaces that the generated skill references.

Examples:
  python run_scenic_smoke.py
  python run_scenic_smoke.py --check-trainers
"""
from __future__ import annotations

import argparse
import importlib
import sys
from typing import Callable


def check_imports() -> None:
    modules = [
        "scenic",
        "scenic.app",
        "scenic.dataset_lib.datasets",
        "scenic.model_lib.models",
        "scenic.model_lib.base_models.base_model",
        "scenic.train_lib.lr_schedules",
        "scenic.train_lib.optimizers",
        "scenic.train_lib.train_utils",
    ]
    for module in modules:
        importlib.import_module(module)
        print(f"import ok: {module}")


def check_jax() -> None:
    import jax  # type: ignore
    import jax.numpy as jnp  # type: ignore
    value = float(jnp.sum(jnp.asarray([1.0, 2.0])))
    if value != 3.0:
        raise AssertionError(f"unexpected JAX tiny sum: {value}")
    print("jax ok:", getattr(jax, "__version__", "unknown"), [str(d) for d in jax.devices()])


def check_lr_schedule() -> None:
    import ml_collections  # type: ignore
    from scenic.train_lib import lr_schedules  # type: ignore
    config = ml_collections.ConfigDict({
        "lr_configs": {
            "learning_rate_schedule": "compound",
            "factors": "constant*linear_warmup",
            "base_learning_rate": 1.0,
            "warmup_steps": 10,
            "warmup_alpha": 0.1,
        }
    })
    lr_fn = lr_schedules.get_learning_rate_fn(config)
    first = float(lr_fn(0))
    last = float(lr_fn(10))
    if abs(first - 0.1) > 1e-6 or abs(last - 1.0) > 1e-6:
        raise AssertionError(f"unexpected LR schedule values: first={first}, warm={last}")
    print("lr schedule ok")


def check_registries() -> None:
    from scenic.dataset_lib import datasets  # type: ignore
    from scenic.model_lib import models  # type: ignore
    lazy = sorted(getattr(datasets, "_IMPORT_TABLE", {}).keys())
    model_names = sorted(models.ALL_MODELS.keys())
    for required in ["mnist", "imagenet", "cifar10"]:
        if required not in lazy:
            raise AssertionError(f"missing expected lazy dataset name: {required}")
    for required in ["fully_connected_classification", "resnet_classification", "simple_cnn_segmentation"]:
        if required not in model_names:
            raise AssertionError(f"missing expected registered model: {required}")
    print("dataset registry names ok:", ", ".join(lazy))
    print("model registry names ok:", ", ".join(model_names))


def check_trainers_optional() -> None:
    try:
        from scenic.train_lib import trainers  # type: ignore
    except Exception as exc:  # noqa: BLE001
        print("optional trainer registry import failed:", type(exc).__name__, exc)
        print("This is a known optional dependency surface in some Scenic environments; see running-and-training troubleshooting.")
        return
    print("trainer registry ok:", ", ".join(sorted(trainers.ALL_TRAINERS.keys())))


def run_checks(check_trainers: bool) -> int:
    checks: list[tuple[str, Callable[[], None]]] = [
        ("imports", check_imports),
        ("jax", check_jax),
        ("lr_schedule", check_lr_schedule),
        ("registries", check_registries),
    ]
    failures: list[str] = []
    for name, fn in checks:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{name}: {type(exc).__name__}: {exc}")
            print(f"FAIL {name}: {type(exc).__name__}: {exc}", file=sys.stderr)
    if check_trainers:
        check_trainers_optional()
    if failures:
        print("Scenic smoke failed:", file=sys.stderr)
        for failure in failures:
            print(" -", failure, file=sys.stderr)
        return 1
    print("Scenic smoke checks passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run self-contained Scenic package smoke checks without launching training or loading data.")
    parser.add_argument("--check-trainers", action="store_true", help="Also try the optional trainer registry import and report dependency failures without failing the smoke.")
    args = parser.parse_args()
    return run_checks(args.check_trainers)


if __name__ == "__main__":
    raise SystemExit(main())
