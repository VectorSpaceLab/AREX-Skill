#!/usr/bin/env python3
"""Compile a MJCF XML or robot_descriptions model and smoke-step it safely.

The helper is intentionally generic:
- it works from any current working directory,
- it resolves a user-provided XML path to an absolute path before loading,
- it can optionally load through robot_descriptions,
- it can short-step with deterministic Halton control noise, and
- it can assert expected bodies, actuators, and model counts.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import mujoco


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compile a Menagerie-style MJCF XML or robot_descriptions model, "
            "optionally short-step it with deterministic safe controls, and "
            "assert expected names/counts."
        )
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--xml",
        type=str,
        help="Path to an MJCF XML file to compile.",
    )
    source.add_argument(
        "--robot-description",
        type=str,
        help="robot_descriptions package name to load.",
    )
    parser.add_argument(
        "--variant",
        type=str,
        default=None,
        help="Optional robot_descriptions variant name.",
    )
    parser.add_argument(
        "--max-sim-time",
        "--step-time",
        dest="max_sim_time",
        type=float,
        default=0.1,
        help=(
            "Upper bound on simulated time for the smoke step. Set to 0 to "
            "compile only."
        ),
    )
    parser.add_argument(
        "--noise-scale",
        type=float,
        default=1.0,
        help="Scale factor for deterministic control noise.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=100000,
        help="Safety cap on the number of mj_step calls.",
    )
    parser.add_argument(
        "--skip-step",
        action="store_true",
        help="Compile only; do not advance the simulation.",
    )
    parser.add_argument(
        "--allow-warnings",
        action="store_true",
        help="Do not fail the smoke test if MuJoCo warnings are recorded.",
    )
    parser.add_argument(
        "--expect-body",
        action="append",
        default=[],
        metavar="NAME",
        help="Body name that must exist in the compiled model.",
    )
    parser.add_argument(
        "--expect-actuator",
        action="append",
        default=[],
        metavar="NAME",
        help="Actuator name that must exist in the compiled model.",
    )
    parser.add_argument(
        "--expect-nbody",
        type=int,
        default=None,
        help="Expected body count.",
    )
    parser.add_argument(
        "--expect-nq",
        type=int,
        default=None,
        help="Expected qpos size.",
    )
    parser.add_argument(
        "--expect-nv",
        type=int,
        default=None,
        help="Expected qvel size.",
    )
    parser.add_argument(
        "--expect-nu",
        type=int,
        default=None,
        help="Expected actuator count.",
    )
    parser.add_argument(
        "--expect-ngeom",
        type=int,
        default=None,
        help="Expected geom count.",
    )
    parser.add_argument(
        "--expect-nsite",
        type=int,
        default=None,
        help="Expected site count.",
    )
    parser.add_argument(
        "--print-names",
        action="store_true",
        help="Print compiled body and actuator names after loading.",
    )
    return parser.parse_args()


def _load_model(args: argparse.Namespace) -> tuple[mujoco.MjModel, str]:
    if args.xml is not None:
        xml_path = Path(args.xml).expanduser().resolve()
        if not xml_path.is_file():
            raise FileNotFoundError(f"XML path does not exist: {xml_path}")
        return mujoco.MjModel.from_xml_path(str(xml_path)), f"xml:{xml_path}"

    try:
        from robot_descriptions.loaders.mujoco import load_robot_description
    except ImportError as exc:  # pragma: no cover - depends on optional package.
        raise RuntimeError(
            "robot_descriptions is not installed; use --xml instead or install "
            "the optional package."
        ) from exc

    kwargs = {}
    if args.variant is not None:
        kwargs["variant"] = args.variant

    try:
        model = load_robot_description(args.robot_description, **kwargs)
    except Exception as exc:  # pragma: no cover - loader/package specific.
        raise RuntimeError(
            f"Failed to load robot description {args.robot_description!r}: {exc}"
        ) from exc
    return model, f"robot_description:{args.robot_description}"


def _object_count(model: mujoco.MjModel, obj_type: mujoco.mjtObj) -> int:
    if obj_type == mujoco.mjtObj.mjOBJ_BODY:
        return model.nbody
    if obj_type == mujoco.mjtObj.mjOBJ_ACTUATOR:
        return model.nu
    raise ValueError(f"Unsupported object type: {obj_type}")


def _enumerate_names(
    model: mujoco.MjModel, obj_type: mujoco.mjtObj
) -> list[str]:
    names: list[str] = []
    for index in range(_object_count(model, obj_type)):
        name = mujoco.mj_id2name(model, obj_type, index)
        if name:
            names.append(name)
    return names


def _check_expected_names(
    model: mujoco.MjModel,
    obj_type: mujoco.mjtObj,
    expected_names: list[str],
    label: str,
) -> None:
    missing = [
        name for name in expected_names if mujoco.mj_name2id(model, obj_type, name) < 0
    ]
    if not missing:
        return

    available = _enumerate_names(model, obj_type)
    sample = ", ".join(available[:30]) if available else "<none>"
    raise RuntimeError(
        f"Missing {label}(s): {', '.join(missing)}. "
        f"Available {label}s: {sample}"
    )


def _check_expected_count(actual: int, expected: int | None, label: str) -> None:
    if expected is None:
        return
    if actual != expected:
        raise RuntimeError(f"Expected {label}={expected}, got {actual}")


def _apply_safe_controls(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    step_index: int,
    noise_scale: float,
) -> None:
    if model.nu == 0:
        return
    for j in range(model.nu):
        ctrlrange = model.actuator_ctrlrange[j]
        if model.actuator_ctrllimited[j]:
            center = 0.5 * (ctrlrange[1] + ctrlrange[0])
            radius = 0.5 * (ctrlrange[1] - ctrlrange[0])
        else:
            center = 0.0
            radius = 1.0
        data.ctrl[j] = center + radius * noise_scale * (
            2 * mujoco.mju_Halton(step_index, j + 2) - 1
        )


def _warning_summary(data: mujoco.MjData) -> list[tuple[str, int]]:
    summary: list[tuple[str, int]] = []
    for enum_value, count in enumerate(data.warning.number):
        count_int = int(count)
        if count_int:
            summary.append((mujoco.mjtWarning(enum_value).name, count_int))
    return summary


def main() -> int:
    args = parse_args()

    if args.max_sim_time < 0:
        raise SystemExit("--max-sim-time must be non-negative")
    if args.noise_scale < 0:
        raise SystemExit("--noise-scale must be non-negative")
    if args.max_steps <= 0:
        raise SystemExit("--max-steps must be positive")

    model, source = _load_model(args)
    print(f"Loaded {source}")
    print(
        "Model summary: "
        f"nbody={model.nbody}, nq={model.nq}, nv={model.nv}, "
        f"nu={model.nu}, ngeom={model.ngeom}, nsite={model.nsite}"
    )

    _check_expected_count(model.nbody, args.expect_nbody, "nbody")
    _check_expected_count(model.nq, args.expect_nq, "nq")
    _check_expected_count(model.nv, args.expect_nv, "nv")
    _check_expected_count(model.nu, args.expect_nu, "nu")
    _check_expected_count(model.ngeom, args.expect_ngeom, "ngeom")
    _check_expected_count(model.nsite, args.expect_nsite, "nsite")
    _check_expected_names(model, mujoco.mjtObj.mjOBJ_BODY, args.expect_body, "body")
    _check_expected_names(
        model,
        mujoco.mjtObj.mjOBJ_ACTUATOR,
        args.expect_actuator,
        "actuator",
    )

    if args.print_names:
        body_names = _enumerate_names(model, mujoco.mjtObj.mjOBJ_BODY)
        actuator_names = _enumerate_names(model, mujoco.mjtObj.mjOBJ_ACTUATOR)
        print("Bodies:", ", ".join(body_names) if body_names else "<none>")
        print(
            "Actuators:",
            ", ".join(actuator_names) if actuator_names else "<none>",
        )

    if args.skip_step or args.max_sim_time == 0:
        print("Compile-only smoke passed.")
        return 0

    data = mujoco.MjData(model)
    step_index = 0
    while data.time < args.max_sim_time:
        _apply_safe_controls(model, data, step_index, args.noise_scale)
        mujoco.mj_step(model, data)
        step_index += 1
        if step_index > args.max_steps:
            raise RuntimeError(
                f"Exceeded --max-steps={args.max_steps} before reaching "
                f"--max-sim-time={args.max_sim_time}."
            )

    warnings = _warning_summary(data)
    if warnings:
        warning_text = "\n".join(f"  {name}: count={count}" for name, count in warnings)
        message = (
            f"MuJoCo warning(s) encountered after stepping to t={data.time:.6f}:\n"
            f"{warning_text}"
        )
        if args.allow_warnings:
            print(message)
        else:
            raise RuntimeError(message)

    print(f"Smoke step passed: t={data.time:.6f}, steps={step_index}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
