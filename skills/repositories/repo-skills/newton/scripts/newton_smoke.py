#!/usr/bin/env python3
"""Run a tiny Newton simulation smoke test with public APIs.

The smoke is safe by default: it creates one rigid sphere above a ground plane,
steps SolverXPBD for a few iterations, and prints counts and final state shape.
It does not use repo-local files, viewers, downloads, or optional importer assets.
"""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny public Newton simulation smoke test.")
    parser.add_argument("--device", default="cpu", help="Warp device string, e.g. cpu or cuda:0.")
    parser.add_argument("--steps", type=int, default=4, help="Number of frame steps to run.")
    parser.add_argument("--substeps", type=int, default=2, help="Solver substeps per frame.")
    parser.add_argument("--dt", type=float, default=1.0 / 60.0, help="Frame time step in seconds.")
    args = parser.parse_args()

    if args.steps < 0 or args.substeps <= 0 or args.dt <= 0:
        print("ERROR: --steps must be >= 0, --substeps > 0, and --dt > 0.")
        return 2

    try:
        import warp as wp
        import newton
    except ModuleNotFoundError as exc:
        print(f"ERROR: missing required package {exc.name!r}. Install Newton and Warp first.")
        return 3

    try:
        wp.init()
        wp.set_device(args.device)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Warp device {args.device!r} is not usable: {type(exc).__name__}: {exc}")
        return 4

    newton.use_coord_layout_targets = True
    builder = newton.ModelBuilder(gravity=(0.0, 0.0, -9.81))
    body = builder.add_body(xform=wp.transform((0.0, 0.0, 0.75), wp.quat_identity()), mass=1.0, label="smoke_sphere")
    builder.add_shape_sphere(body, radius=0.25, label="smoke_sphere_shape")
    builder.add_ground_plane(label="ground")
    model = builder.finalize(device=args.device)

    state_in = model.state()
    state_out = model.state()
    control = model.control()
    pipeline = newton.CollisionPipeline(model)
    contacts = pipeline.contacts()
    solver = newton.solvers.SolverXPBD(model, iterations=4)
    newton.eval_fk(model, model.joint_q, model.joint_qd, state_in)

    sub_dt = args.dt / args.substeps
    for _ in range(args.steps):
        for _ in range(args.substeps):
            state_in.clear_forces()
            pipeline.collide(state_in, contacts)
            solver.step(state_in, state_out, control, contacts, sub_dt)
            state_in, state_out = state_out, state_in

    body_q = state_in.body_q.numpy()
    print(f"newton={newton.__version__}")
    print(f"device={args.device}")
    print(f"model.body_count={model.body_count}")
    print(f"model.shape_count={model.shape_count}")
    print(f"contacts.rigid_contact_max={contacts.rigid_contact_max}")
    print(f"final.body_q.shape={body_q.shape}")
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
