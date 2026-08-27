#!/usr/bin/env python3
"""Run a tiny Newton solver smoke with selectable public solver classes."""

from __future__ import annotations

import argparse

SOLVER_EXTRAS = {
    "xpbd": "base Newton package",
    "semi-implicit": "base Newton package",
    "featherstone": "base Newton package",
    "mujoco": "newton[sim] (mujoco and mujoco-warp)",
}


def _make_solver(newton, model, name: str):
    if name == "xpbd":
        return newton.solvers.SolverXPBD(model, iterations=4)
    if name == "semi-implicit":
        return newton.solvers.SolverSemiImplicit(model)
    if name == "featherstone":
        return newton.solvers.SolverFeatherstone(model)
    if name == "mujoco":
        return newton.solvers.SolverMuJoCo(model)
    raise ValueError(f"unknown solver {name!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Step a minimal scene with one Newton solver.")
    parser.add_argument("--solver", choices=sorted(SOLVER_EXTRAS), default="xpbd")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--use-collision-pipeline", action="store_true", help="Pass Newton contacts to the solver. MuJoCo defaults to native contacts unless this is set.")
    args = parser.parse_args()

    try:
        import warp as wp
        import newton
    except ModuleNotFoundError as exc:
        print(f"ERROR: missing required package {exc.name!r}. Install Newton and warp-lang first.")
        return 2

    try:
        wp.init()
        wp.set_device(args.device)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: device {args.device!r} is not usable: {type(exc).__name__}: {exc}")
        return 3

    newton.use_coord_layout_targets = True
    builder = newton.ModelBuilder()
    body = builder.add_body(xform=wp.transform((0.0, 0.0, 0.75), wp.quat_identity()), mass=1.0)
    builder.add_shape_sphere(body, radius=0.25)
    builder.add_ground_plane()
    model = builder.finalize(device=args.device)
    state0 = model.state()
    state1 = model.state()
    control = model.control()
    newton.eval_fk(model, model.joint_q, model.joint_qd, state0)

    try:
        solver = _make_solver(newton, model, args.solver)
    except ModuleNotFoundError as exc:
        print(f"ERROR: solver {args.solver!r} needs optional dependency {exc.name!r}.")
        print(f"Install/verify: {SOLVER_EXTRAS[args.solver]}")
        return 4
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: could not construct solver {args.solver!r}: {type(exc).__name__}: {exc}")
        print(f"Expected dependency variant: {SOLVER_EXTRAS[args.solver]}")
        return 5

    pipeline = newton.CollisionPipeline(model)
    contacts = pipeline.contacts()
    dt = 1.0 / 60.0
    for _ in range(args.steps):
        state0.clear_forces()
        step_contacts = None
        if args.use_collision_pipeline or args.solver != "mujoco":
            pipeline.collide(state0, contacts)
            step_contacts = contacts
        solver.step(state0, state1, control, step_contacts, dt)
        state0, state1 = state1, state0

    print(f"solver={args.solver}")
    print(f"device={args.device}")
    print(f"body_q_shape={state0.body_q.numpy().shape}")
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
