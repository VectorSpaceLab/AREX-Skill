#!/usr/bin/env python3
"""Headless-first runner for gym-pybullet-drones control examples.

This bundled script mirrors the package's PID, velocity, downwash, and MRAC
example workflows using public package APIs. It intentionally defaults to short,
headless, no-plot smoke runs so future agents can validate control simulations
without relying on the original repository checkout or a GUI display.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

DRONE_CHOICES = ("cf2x", "cf2p", "racer")
PHYSICS_CHOICES = ("pyb", "dyn", "pyb_gnd", "pyb_drag", "pyb_dw", "pyb_gnd_drag_dw")
EXAMPLE_CHOICES = ("pid", "pid_velocity", "velocity", "downwash", "mrac", "all")


def _load_runtime() -> SimpleNamespace:
    """Import runtime dependencies with a useful failure message."""
    try:
        import numpy as np
        from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
        from gym_pybullet_drones.control.MRACControl import MRACControl
        from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
        from gym_pybullet_drones.envs.VelocityAviary import VelocityAviary
        from gym_pybullet_drones.utils.Logger import Logger
        from gym_pybullet_drones.utils.enums import DroneModel, Physics
        from gym_pybullet_drones.utils.utils import sync
    except Exception as exc:  # noqa: BLE001 - this is a CLI boundary.
        raise SystemExit(
            "Failed to import gym-pybullet-drones control runtime dependencies. "
            "Install the package and dependencies (notably pybullet, numpy, scipy, "
            "matplotlib, and python-control) in the active environment. "
            f"Original error: {type(exc).__name__}: {exc}"
        ) from exc

    return SimpleNamespace(
        np=np,
        DSLPIDControl=DSLPIDControl,
        MRACControl=MRACControl,
        CtrlAviary=CtrlAviary,
        VelocityAviary=VelocityAviary,
        Logger=Logger,
        DroneModel=DroneModel,
        Physics=Physics,
        sync=sync,
    )


def _enum(enum_cls, value: str, label: str):
    try:
        return enum_cls(value)
    except ValueError as exc:
        choices = ", ".join(item.value for item in enum_cls)
        raise SystemExit(f"Invalid {label} {value!r}; choose one of: {choices}") from exc


def _workflow_name(name: str) -> str:
    return "pid_velocity" if name == "velocity" else name


def _default_control_freq(workflow: str) -> int:
    return 120 if workflow == "mrac" else 48


def _default_physics(workflow: str) -> str:
    return "pyb_dw" if workflow == "downwash" else "pyb"


def _default_obstacles(workflow: str) -> bool:
    return workflow in {"pid", "downwash"}


def _freqs(args: argparse.Namespace, workflow: str) -> tuple[int, int]:
    sim_freq = int(args.simulation_freq_hz)
    ctrl_freq = int(args.control_freq_hz or _default_control_freq(workflow))
    if sim_freq <= 0 or ctrl_freq <= 0:
        raise SystemExit("--simulation-freq-hz and --control-freq-hz must be positive integers")
    if sim_freq % ctrl_freq != 0:
        raise SystemExit(
            "Invalid timing: --simulation-freq-hz must be divisible by "
            "--control-freq-hz because BaseAviary requires pyb_freq % ctrl_freq == 0 "
            f"(got {sim_freq} % {ctrl_freq} = {sim_freq % ctrl_freq})."
        )
    return sim_freq, ctrl_freq


def _steps(duration_sec: float, ctrl_freq: int) -> int:
    if duration_sec <= 0:
        raise SystemExit("--duration-sec must be positive")
    return max(1, int(math.ceil(duration_sec * ctrl_freq)))


def _ensure_output_folder(path: str | os.PathLike[str]) -> Path:
    output = Path(path).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    return output


def _new_logger(rt: SimpleNamespace, output: Path, ctrl_freq: int, num_drones: int, colab: bool):
    # duration_sec=0 lets Logger grow arrays dynamically and avoids extra zero
    # columns when the smoke duration is fractional.
    return rt.Logger(
        logging_freq_hz=ctrl_freq,
        num_drones=num_drones,
        duration_sec=0,
        output_folder=str(output),
        colab=colab,
    )


def _files_under(path: Path) -> set[Path]:
    if not path.exists():
        return set()
    return {item.resolve() for item in path.rglob("*") if item.is_file()}


def _finish_logger(logger, tag: str, args: argparse.Namespace, output: Path, before: set[Path]) -> list[str]:
    logger.save()
    if args.csv:
        logger.save_as_csv(tag)
    # Plot only after logs are saved so display/backend failures do not drop data.
    if args.plot:
        logger.plot()
    after = _files_under(output)
    created = []
    for file_path in sorted(after - before):
        try:
            created.append(str(file_path.relative_to(output)))
        except ValueError:
            created.append(str(file_path))
    return created


def _maybe_render(env, i: int, render_every: int) -> None:
    if render_every > 0 and i % render_every == 0:
        env.render()


def _maybe_sync(rt: SimpleNamespace, args: argparse.Namespace, i: int, start: float, timestep: float) -> None:
    if args.gui and args.sync_gui:
        rt.sync(i, start, timestep)


def _validate_pid_like_drone(workflow: str, drone_value: str) -> None:
    if drone_value == "racer":
        raise SystemExit(
            f"{workflow} uses DSLPIDControl/VelocityAviary and requires --drone cf2x or cf2p; "
            "use mrac for the racer model in this bundled runner."
        )


def run_pid(rt: SimpleNamespace, args: argparse.Namespace) -> dict:
    workflow = "pid"
    _validate_pid_like_drone(workflow, args.drone)
    sim_freq, ctrl_freq = _freqs(args, workflow)
    num_drones = int(args.num_drones or 3)
    if num_drones <= 0:
        raise SystemExit("pid requires --num-drones >= 1")
    steps = _steps(args.duration_sec, ctrl_freq)
    output = _ensure_output_folder(args.output_folder)
    before = _files_under(output)

    np = rt.np
    drone = _enum(rt.DroneModel, args.drone, "drone")
    physics = _enum(rt.Physics, args.physics or _default_physics(workflow), "physics")
    obstacles = _default_obstacles(workflow) if args.obstacles is None else args.obstacles

    h0 = 0.1
    h_step = 0.05
    radius = 0.3
    init_xyzs = np.array([
        [
            radius * np.cos((i / 6) * 2 * np.pi + np.pi / 2),
            radius * np.sin((i / 6) * 2 * np.pi + np.pi / 2) - radius,
            h0 + i * h_step,
        ]
        for i in range(num_drones)
    ])
    init_rpys = np.array([[0.0, 0.0, i * (np.pi / 2) / num_drones] for i in range(num_drones)])

    period = 10
    num_wp = max(1, ctrl_freq * period)
    target_pos = np.zeros((num_wp, 3))
    for i in range(num_wp):
        target_pos[i, :] = [
            radius * np.cos((i / num_wp) * 2 * np.pi + np.pi / 2) + init_xyzs[0, 0],
            radius * np.sin((i / num_wp) * 2 * np.pi + np.pi / 2) - radius + init_xyzs[0, 1],
            0.0,
        ]
    wp_counters = np.array([int((i * num_wp / 6) % num_wp) for i in range(num_drones)])

    env = None
    logger = None
    try:
        env = rt.CtrlAviary(
            drone_model=drone,
            num_drones=num_drones,
            initial_xyzs=init_xyzs,
            initial_rpys=init_rpys,
            physics=physics,
            neighbourhood_radius=10,
            pyb_freq=sim_freq,
            ctrl_freq=ctrl_freq,
            gui=args.gui,
            record=args.record_video,
            obstacles=obstacles,
            user_debug_gui=args.user_debug_gui,
            output_folder=str(output),
        )
        logger = _new_logger(rt, output, ctrl_freq, num_drones, args.colab)
        controllers = [rt.DSLPIDControl(drone_model=drone) for _ in range(num_drones)]
        action = np.zeros((num_drones, 4))
        start = time.time()

        for i in range(steps):
            obs, reward, terminated, truncated, info = env.step(action)
            for j in range(num_drones):
                action[j, :], _, _ = controllers[j].computeControlFromState(
                    control_timestep=env.CTRL_TIMESTEP,
                    state=obs[j],
                    target_pos=np.hstack([target_pos[wp_counters[j], 0:2], init_xyzs[j, 2]]),
                    target_rpy=init_rpys[j, :],
                )
            for j in range(num_drones):
                wp_counters[j] = wp_counters[j] + 1 if wp_counters[j] < (num_wp - 1) else 0
                logger.log(
                    drone=j,
                    timestamp=i / env.CTRL_FREQ,
                    state=obs[j],
                    control=np.hstack([target_pos[wp_counters[j], 0:2], init_xyzs[j, 2], init_rpys[j, :], np.zeros(6)]),
                )
            _maybe_render(env, i, args.render_every)
            _maybe_sync(rt, args, i, start, env.CTRL_TIMESTEP)
    finally:
        if env is not None:
            env.close()

    created = _finish_logger(logger, workflow, args, output, before) if logger is not None else []
    return {"example": workflow, "steps": steps, "num_drones": num_drones, "output_folder": str(output), "created_files": created}


def run_velocity(rt: SimpleNamespace, args: argparse.Namespace) -> dict:
    workflow = "pid_velocity"
    _validate_pid_like_drone(workflow, args.drone)
    if args.num_drones not in (None, 4):
        raise SystemExit("pid_velocity mirrors the package workflow with exactly 4 drones; omit --num-drones or pass 4")
    sim_freq, ctrl_freq = _freqs(args, workflow)
    num_drones = 4
    steps = _steps(args.duration_sec, ctrl_freq)
    output = _ensure_output_folder(args.output_folder)
    before = _files_under(output)

    np = rt.np
    drone = _enum(rt.DroneModel, args.drone, "drone")
    physics = _enum(rt.Physics, args.physics or _default_physics(workflow), "physics")
    obstacles = _default_obstacles(workflow) if args.obstacles is None else args.obstacles

    init_xyzs = np.array([[0, 0, 0.1], [0.3, 0, 0.1], [0.6, 0, 0.1], [0.9, 0, 0.1]])
    init_rpys = np.array([[0, 0, 0], [0, 0, np.pi / 3], [0, 0, np.pi / 4], [0, 0, np.pi / 2]])
    num_wp = max(1, steps)
    wp_counters = np.zeros(num_drones, dtype=int)
    target_vel = np.zeros((num_drones, num_wp, 4))
    for i in range(num_wp):
        target_vel[0, i, :] = [-0.5, 1, 0, 0.99] if i < (num_wp / 8) else [0.5, -1, 0, 0.99]
        target_vel[1, i, :] = [0, 1, 0, 0.99] if i < (num_wp / 8 + num_wp / 6) else [0, -1, 0, 0.99]
        target_vel[2, i, :] = [0.2, 1, 0.2, 0.99] if i < (num_wp / 8 + 2 * num_wp / 6) else [-0.2, -1, -0.2, 0.99]
        target_vel[3, i, :] = [0, 1, 0.5, 0.99] if i < (num_wp / 8 + 3 * num_wp / 6) else [0, -1, -0.5, 0.99]

    env = None
    logger = None
    try:
        env = rt.VelocityAviary(
            drone_model=drone,
            num_drones=num_drones,
            initial_xyzs=init_xyzs,
            initial_rpys=init_rpys,
            physics=physics,
            neighbourhood_radius=10,
            pyb_freq=sim_freq,
            ctrl_freq=ctrl_freq,
            gui=args.gui,
            record=args.record_video,
            obstacles=obstacles,
            user_debug_gui=args.user_debug_gui,
            output_folder=str(output),
        )
        logger = _new_logger(rt, output, ctrl_freq, num_drones, args.colab)
        action = np.zeros((num_drones, 4))
        start = time.time()

        for i in range(steps):
            obs, reward, terminated, truncated, info = env.step(action)
            for j in range(num_drones):
                action[j, :] = target_vel[j, wp_counters[j], :]
            for j in range(num_drones):
                wp_counters[j] = wp_counters[j] + 1 if wp_counters[j] < (num_wp - 1) else 0
                logger.log(
                    drone=j,
                    timestamp=i / env.CTRL_FREQ,
                    state=obs[j],
                    control=np.hstack([target_vel[j, wp_counters[j], 0:3], np.zeros(9)]),
                )
            _maybe_render(env, i, args.render_every)
            _maybe_sync(rt, args, i, start, env.CTRL_TIMESTEP)
    finally:
        if env is not None:
            env.close()

    created = _finish_logger(logger, workflow, args, output, before) if logger is not None else []
    return {"example": workflow, "steps": steps, "num_drones": num_drones, "output_folder": str(output), "created_files": created}


def run_downwash(rt: SimpleNamespace, args: argparse.Namespace) -> dict:
    workflow = "downwash"
    _validate_pid_like_drone(workflow, args.drone)
    if args.num_drones not in (None, 2):
        raise SystemExit("downwash mirrors the package workflow with exactly 2 drones; omit --num-drones or pass 2")
    sim_freq, ctrl_freq = _freqs(args, workflow)
    num_drones = 2
    steps = _steps(args.duration_sec, ctrl_freq)
    output = _ensure_output_folder(args.output_folder)
    before = _files_under(output)

    np = rt.np
    drone = _enum(rt.DroneModel, args.drone, "drone")
    physics = _enum(rt.Physics, args.physics or _default_physics(workflow), "physics")
    obstacles = _default_obstacles(workflow) if args.obstacles is None else args.obstacles

    init_xyzs = np.array([[0.5, 0, 1.0], [-0.5, 0, 0.5]])
    period = 5
    num_wp = max(1, ctrl_freq * period)
    target_pos = np.zeros((num_wp, 2))
    for i in range(num_wp):
        target_pos[i, :] = [0.5 * np.cos(2 * np.pi * (i / num_wp)), 0.0]
    wp_counters = np.array([0, int(num_wp / 2)])

    env = None
    logger = None
    try:
        env = rt.CtrlAviary(
            drone_model=drone,
            num_drones=num_drones,
            initial_xyzs=init_xyzs,
            physics=physics,
            neighbourhood_radius=10,
            pyb_freq=sim_freq,
            ctrl_freq=ctrl_freq,
            gui=args.gui,
            record=args.record_video,
            obstacles=obstacles,
            user_debug_gui=args.user_debug_gui,
            output_folder=str(output),
        )
        logger = _new_logger(rt, output, ctrl_freq, num_drones, args.colab)
        controllers = [rt.DSLPIDControl(drone_model=drone) for _ in range(num_drones)]
        action = np.zeros((num_drones, 4))
        start = time.time()

        for i in range(steps):
            obs, reward, terminated, truncated, info = env.step(action)
            for j in range(num_drones):
                action[j, :], _, _ = controllers[j].computeControlFromState(
                    control_timestep=env.CTRL_TIMESTEP,
                    state=obs[j],
                    target_pos=np.hstack([target_pos[wp_counters[j], :], init_xyzs[j, 2]]),
                )
            for j in range(num_drones):
                wp_counters[j] = wp_counters[j] + 1 if wp_counters[j] < (num_wp - 1) else 0
                logger.log(
                    drone=j,
                    timestamp=i / env.CTRL_FREQ,
                    state=obs[j],
                    control=np.hstack([target_pos[wp_counters[j], :], init_xyzs[j, 2], np.zeros(9)]),
                )
            _maybe_render(env, i, args.render_every)
            _maybe_sync(rt, args, i, start, env.CTRL_TIMESTEP)
    finally:
        if env is not None:
            env.close()

    created = _finish_logger(logger, workflow, args, output, before) if logger is not None else []
    return {"example": workflow, "steps": steps, "num_drones": num_drones, "output_folder": str(output), "created_files": created}


def run_mrac(rt: SimpleNamespace, args: argparse.Namespace) -> dict:
    workflow = "mrac"
    sim_freq, ctrl_freq = _freqs(args, workflow)
    num_drones = int(args.num_drones or 1)
    if num_drones <= 0:
        raise SystemExit("mrac requires --num-drones >= 1")
    steps = _steps(args.duration_sec, ctrl_freq)
    output = _ensure_output_folder(args.output_folder)
    before = _files_under(output)

    np = rt.np
    drone = _enum(rt.DroneModel, args.drone, "drone")
    physics = _enum(rt.Physics, args.physics or _default_physics(workflow), "physics")
    obstacles = _default_obstacles(workflow) if args.obstacles is None else args.obstacles

    init_xyzs = np.zeros((num_drones, 3))
    init_xyzs[:, 0] = 0.3 * np.arange(num_drones)
    init_rpys = np.zeros((num_drones, 3))
    target_pos = init_xyzs.copy()
    target_pos[:, 2] = 1.0
    target_rpy = np.zeros((num_drones, 3))

    env = None
    logger = None
    try:
        env = rt.CtrlAviary(
            drone_model=drone,
            num_drones=num_drones,
            initial_xyzs=init_xyzs,
            initial_rpys=init_rpys,
            physics=physics,
            neighbourhood_radius=10,
            pyb_freq=sim_freq,
            ctrl_freq=ctrl_freq,
            gui=args.gui,
            record=args.record_video,
            obstacles=obstacles,
            user_debug_gui=args.user_debug_gui,
            output_folder=str(output),
        )
        logger = _new_logger(rt, output, ctrl_freq, num_drones, args.colab)
        controllers = [rt.MRACControl(drone_model=drone) for _ in range(num_drones)]
        action = np.zeros((num_drones, 4))
        start = time.time()

        for i in range(steps):
            obs, reward, terminated, truncated, info = env.step(action)
            for j in range(num_drones):
                action[j, :], _, _ = controllers[j].computeControlFromState(
                    control_timestep=env.CTRL_TIMESTEP,
                    state=obs[j],
                    target_pos=target_pos[j, :],
                    target_rpy=target_rpy[j, :],
                )
            for j in range(num_drones):
                logger.log(
                    drone=j,
                    timestamp=i / env.CTRL_FREQ,
                    state=obs[j],
                    control=np.hstack([target_pos[j, :], target_rpy[j, :], np.zeros(6)]),
                )
            _maybe_render(env, i, args.render_every)
            _maybe_sync(rt, args, i, start, env.CTRL_TIMESTEP)
    finally:
        if env is not None:
            env.close()

    created = _finish_logger(logger, workflow, args, output, before) if logger is not None else []
    return {"example": workflow, "steps": steps, "num_drones": num_drones, "output_folder": str(output), "created_files": created}


RUNNERS = {
    "pid": run_pid,
    "pid_velocity": run_velocity,
    "downwash": run_downwash,
    "mrac": run_mrac,
}


def _prevalidate_static(workflow: str, args: argparse.Namespace) -> None:
    """Validate CLI mistakes that do not require importing the package."""
    _freqs(args, workflow)
    _steps(args.duration_sec, int(args.control_freq_hz or _default_control_freq(workflow)))
    if workflow in {"pid", "pid_velocity", "downwash"}:
        _validate_pid_like_drone(workflow, args.drone)
    if workflow == "pid_velocity" and args.num_drones not in (None, 4):
        raise SystemExit("pid_velocity mirrors the package workflow with exactly 4 drones; omit --num-drones or pass 4")
    if workflow == "downwash" and args.num_drones not in (None, 2):
        raise SystemExit("downwash mirrors the package workflow with exactly 2 drones; omit --num-drones or pass 2")
    if workflow in {"pid", "mrac"} and args.num_drones is not None and args.num_drones <= 0:
        raise SystemExit(f"{workflow} requires --num-drones >= 1")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run bundled gym-pybullet-drones control workflow smoke examples.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("example", nargs="?", choices=EXAMPLE_CHOICES, help="Control workflow to run; 'velocity' aliases 'pid_velocity'.")
    parser.add_argument("--list", action="store_true", help="List wrapped workflows and exit.")
    parser.add_argument("--output-folder", default="control-results", help="Folder for Logger outputs. Created if needed.")
    parser.add_argument("--duration-sec", type=float, default=1.0, help="Short smoke duration in seconds.")
    parser.add_argument("--simulation-freq-hz", type=int, default=240, help="PyBullet stepping frequency.")
    parser.add_argument("--control-freq-hz", type=int, default=None, help="Control frequency; defaults to 48 Hz, except MRAC uses 120 Hz.")
    parser.add_argument("--drone", choices=DRONE_CHOICES, default="cf2x", help="Drone model value.")
    parser.add_argument("--physics", choices=PHYSICS_CHOICES, default=None, help="Physics value; downwash defaults to pyb_dw, others to pyb.")
    parser.add_argument("--num-drones", type=int, default=None, help="Workflow-specific drone count override where supported.")

    gui_group = parser.add_mutually_exclusive_group()
    gui_group.add_argument("--gui", dest="gui", action="store_true", help="Use PyBullet GUI; requires display/OpenGL.")
    gui_group.add_argument("--no-gui", dest="gui", action="store_false", help="Run headless with PyBullet DIRECT.")
    parser.set_defaults(gui=False)

    plot_group = parser.add_mutually_exclusive_group()
    plot_group.add_argument("--plot", dest="plot", action="store_true", help="Call Logger.plot() after saving logs.")
    plot_group.add_argument("--no-plot", dest="plot", action="store_false", help="Do not plot logs.")
    parser.set_defaults(plot=False)

    record_group = parser.add_mutually_exclusive_group()
    record_group.add_argument("--record-video", dest="record_video", action="store_true", help="Enable BaseAviary recording.")
    record_group.add_argument("--no-record-video", dest="record_video", action="store_false", help="Disable recording.")
    parser.set_defaults(record_video=False)

    debug_group = parser.add_mutually_exclusive_group()
    debug_group.add_argument("--user-debug-gui", dest="user_debug_gui", action="store_true", help="Enable PyBullet GUI sliders/axes when GUI is used.")
    debug_group.add_argument("--no-user-debug-gui", dest="user_debug_gui", action="store_false", help="Disable PyBullet user debug GUI helpers.")
    parser.set_defaults(user_debug_gui=False)

    obstacle_group = parser.add_mutually_exclusive_group()
    obstacle_group.add_argument("--obstacles", dest="obstacles", action="store_true", help="Force obstacles on.")
    obstacle_group.add_argument("--no-obstacles", dest="obstacles", action="store_false", help="Force obstacles off.")
    parser.set_defaults(obstacles=None)

    parser.add_argument("--csv", action="store_true", help="Also write source-like per-signal CSV outputs.")
    parser.add_argument("--render-every", type=int, default=0, help="Call env.render() every N control steps; 0 disables text render.")
    parser.add_argument("--no-sync", dest="sync_gui", action="store_false", default=True, help="Do not wall-clock sync even when GUI is enabled.")
    parser.add_argument("--colab", action="store_true", help="Pass colab=True to Logger.")
    parser.add_argument("--summary-json", default=None, help="Optional path for a JSON summary of runs and created files.")
    return parser


def _print_list() -> None:
    print("Wrapped control workflows:")
    print("  pid          CtrlAviary + DSLPIDControl trajectory tracking; default 3 drones")
    print("  pid_velocity VelocityAviary velocity-command workflow; fixed 4 drones")
    print("  downwash     CtrlAviary + DSLPIDControl with Physics.PYB_DW; fixed 2 drones")
    print("  mrac         CtrlAviary + MRACControl hover workflow; default 1 drone")
    print("  all          Runs pid, pid_velocity, downwash, and mrac into subfolders")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.render_every < 0:
        parser.error("--render-every must be >= 0")

    if args.list:
        _print_list()
        return 0

    if args.example is None:
        parser.error("example is required unless --list is used")

    workflow = _workflow_name(args.example)
    if workflow == "all":
        workflows = ["pid", "pid_velocity", "downwash", "mrac"]
    else:
        workflows = [workflow]

    summaries = []
    base_output = Path(args.output_folder).expanduser()

    prepared_args = []
    for item in workflows:
        item_args = argparse.Namespace(**vars(args))
        if len(workflows) > 1:
            item_args.output_folder = str(base_output / item)
            # Let each workflow use its own control-frequency default when --control-freq-hz is omitted.
            item_args.control_freq_hz = args.control_freq_hz
        _prevalidate_static(item, item_args)
        prepared_args.append((item, item_args))

    rt = _load_runtime()

    for item, item_args in prepared_args:
        summary = RUNNERS[item](rt, item_args)
        summaries.append(summary)

    result = {"runs": summaries}
    print(json.dumps(result, indent=2))

    if args.summary_json:
        summary_path = Path(args.summary_json).expanduser().resolve()
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(result, indent=2) + "\n")
        print(f"Wrote summary JSON to {summary_path}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit("Interrupted by user")
