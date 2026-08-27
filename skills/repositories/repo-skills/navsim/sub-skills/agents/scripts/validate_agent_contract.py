#!/usr/bin/env python3
"""Run dataset-free checks for the NAVSIM agent interface.

The default checks exercise trajectory rank/count invariants and sensor-history
selection with synthetic values.  ``--module`` may point at a Python file or an
importable module; its agent classes are inspected but not instantiated and no
agent inference, checkpoint loading, dataset access, download, or benchmark is
performed.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import inspect
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, List, Optional, Sequence, Tuple


def _expected_poses(time_horizon: float, interval_length: float) -> int:
    """Return the nearest integral sample count for a synthetic fallback."""
    if time_horizon <= 0 or interval_length <= 0:
        raise ValueError("time-horizon and interval-length must be positive")
    quotient = time_horizon / interval_length
    rounded = int(round(quotient))
    if abs(quotient - rounded) > 1e-6:
        raise ValueError("time-horizon must be an integral number of intervals")
    return rounded


def _shape(value: Any) -> Tuple[int, ...]:
    """Get a small shape tuple without depending on NumPy."""
    if hasattr(value, "shape"):
        return tuple(int(item) for item in value.shape)
    if not isinstance(value, (list, tuple)):
        return ()
    if not value:
        return (0,)
    return (len(value),) + _shape(value[0])


def _synthetic_shape_checks(expected: int) -> List[str]:
    """Check the shape and sampling cases without importing NAVSIM."""
    valid = [[0.0, 0.0, 0.0] for _ in range(expected)]
    wrong_rank = [0.0, 0.0, 0.0]
    wrong_columns = [[0.0, 0.0] for _ in range(expected)]
    wrong_count = [[0.0, 0.0, 0.0] for _ in range(expected - 1)]

    assert _shape(valid) == (expected, 3), "synthetic valid trajectory has the wrong shape"
    assert _shape(wrong_rank) != (expected, 3), "wrong-rank case was not detected"
    assert _shape(wrong_columns) != (expected, 3), "wrong-column case was not detected"
    assert _shape(wrong_count) != (expected, 3), "sampling-mismatch case was not detected"
    return [
        f"valid synthetic poses: ({expected}, 3)",
        "rejected synthetic wrong-rank, wrong-column, and sampling-mismatch shapes",
    ]


def _navsim_checks(
    time_horizon: float, interval_length: float, strict: bool
) -> Tuple[List[str], List[str], int]:
    """Run package-backed checks when the optional runtime is available."""
    passed: List[str] = []
    skipped: List[str] = []
    try:
        import numpy as np
        from nuplan.planning.simulation.trajectory.trajectory_sampling import TrajectorySampling
        from navsim.common.dataclasses import SensorConfig, Trajectory
    except Exception as exc:  # pragma: no cover - depends on caller environment
        message = f"NAVSIM/nuPlan checks skipped ({type(exc).__name__}: {exc})"
        if strict:
            raise RuntimeError(message) from exc
        skipped.append(message)
        return passed, skipped, _expected_poses(time_horizon, interval_length)

    sampling = TrajectorySampling(time_horizon=time_horizon, interval_length=interval_length)
    expected = int(sampling.num_poses)
    poses = np.zeros((expected, 3), dtype=np.float32)
    Trajectory(poses, sampling)
    passed.append(f"Trajectory accepts ({expected}, 3) for the declared sampling")

    invalid_cases: Sequence[Tuple[str, Any]] = (
        ("wrong rank", np.zeros((expected, 3, 1), dtype=np.float32)),
        ("wrong final dimension", np.zeros((expected, 2), dtype=np.float32)),
        ("sampling mismatch", np.zeros((max(0, expected - 1), 3), dtype=np.float32)),
    )
    for label, invalid_poses in invalid_cases:
        try:
            Trajectory(invalid_poses, sampling)
        except (AssertionError, ValueError, TypeError):
            passed.append(f"Trajectory rejects synthetic {label} case")
        else:
            raise AssertionError(f"Trajectory accepted synthetic {label} case")

    no_sensors = SensorConfig.build_no_sensors()
    all_sensors = SensorConfig.build_all_sensors()
    assert no_sensors.get_sensors_at_iteration(3) == [], "no-sensor config selected a modality"
    assert len(all_sensors.get_sensors_at_iteration(3)) == 9, "all-sensor config did not select nine modalities"
    current = SensorConfig.build_all_sensors(include=[3])
    assert len(current.get_sensors_at_iteration(3)) == 9
    assert current.get_sensors_at_iteration(0) == []
    passed.append("SensorConfig no/all/current-history selections are consistent")

    # This is the contract-level latent check; constructing a TransFuser model
    # would initialize optional vision backends and may fetch weights.
    latent_sensor_names = set(
        SensorConfig(
            cam_f0=[3],
            cam_l0=[3],
            cam_l1=False,
            cam_l2=False,
            cam_r0=[3],
            cam_r1=False,
            cam_r2=False,
            cam_b0=False,
            lidar_pc=False,
        ).get_sensors_at_iteration(3)
    )
    assert "lidar_pc" not in latent_sensor_names
    assert {"cam_f0", "cam_l0", "cam_r0"}.issubset(latent_sensor_names)
    passed.append("latent sensor contract excludes LiDAR while retaining front cameras")
    return passed, skipped, expected


def _load_module(module_ref: str) -> ModuleType:
    """Load a user module from a file or importable dotted name."""
    path = Path(module_ref)
    if path.suffix == ".py" or path.exists():
        if not path.is_file():
            raise FileNotFoundError(f"module file does not exist: {path}")
        spec = importlib.util.spec_from_file_location("navsim_user_agent", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"could not create an import spec for {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(module_ref)


def _inspect_module(module_ref: str, object_name: Optional[str]) -> List[str]:
    """Inspect agent-shaped classes without constructing or running them."""
    module = _load_module(module_ref)
    if object_name:
        candidate = getattr(module, object_name)
        candidates: Iterable[Any] = (candidate,)
    else:
        candidates = vars(module).values()

    try:
        from navsim.agents.abstract_agent import AbstractAgent
    except Exception:
        AbstractAgent = None  # type: ignore[assignment]

    classes: List[type] = []
    for candidate in candidates:
        if not inspect.isclass(candidate):
            continue
        if AbstractAgent is not None:
            try:
                if issubclass(candidate, AbstractAgent) and candidate is not AbstractAgent:
                    classes.append(candidate)
            except TypeError:
                continue
        elif all(callable(getattr(candidate, name, None)) for name in ("name", "initialize", "get_sensor_config")):
            classes.append(candidate)

    if not classes:
        raise ValueError("no AbstractAgent subclass (or agent-shaped class) found")

    messages: List[str] = []
    required = ("name", "initialize", "get_sensor_config")
    for cls in classes:
        missing = [name for name in required if not callable(getattr(cls, name, None))]
        if missing:
            raise AssertionError(f"{cls.__name__} is missing required methods: {', '.join(missing)}")
        requires_scene = bool(getattr(cls, "requires_scene", False))
        mode = "privileged/scene-dependent" if requires_scene else "AgentInput-only"
        messages.append(f"inspected {cls.__module__}.{cls.__name__} ({mode}); not instantiated")
    return messages


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse arguments, run safe checks, and return a shell status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", help="optional .py file or dotted module to inspect")
    parser.add_argument("--object", help="specific class/object name within --module")
    parser.add_argument("--time-horizon", type=float, default=4.0)
    parser.add_argument("--interval-length", type=float, default=0.5)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail instead of skipping checks when NAVSIM/nuPlan cannot be imported",
    )
    args = parser.parse_args(argv)

    try:
        fallback_expected = _expected_poses(args.time_horizon, args.interval_length)
        messages = _synthetic_shape_checks(fallback_expected)
        passed, skipped, expected = _navsim_checks(args.time_horizon, args.interval_length, args.strict)
        print("PASS: " + "; ".join(messages + passed))
        for message in skipped:
            print("SKIP: " + message)
        if expected != fallback_expected:
            print(f"INFO: runtime sampling reports {expected} poses (fallback was {fallback_expected})")
        if args.module:
            for message in _inspect_module(args.module, args.object):
                print("PASS: " + message)
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
