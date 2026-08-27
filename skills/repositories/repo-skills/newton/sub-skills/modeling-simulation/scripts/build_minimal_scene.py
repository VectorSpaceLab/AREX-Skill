#!/usr/bin/env python3
"""Build and step a minimal Newton scene using only public APIs."""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a minimal Newton sphere scene and step SolverXPBD.")
    parser.add_argument("--device", default="cpu", help="Warp device string such as cpu or cuda:0.")
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--dt", type=float, default=1.0 / 60.0)
    parser.add_argument("--world-count", type=int, default=1, help="Replicate the tiny scene into N worlds.")
    args = parser.parse_args()
    if args.steps < 0 or args.dt <= 0 or args.world_count <= 0:
        print("ERROR: --steps must be >=0, --dt >0, --world-count >0")
        return 2

    try:
        import warp as wp
        import newton
    except ModuleNotFoundError as exc:
        print(f"ERROR: missing {exc.name!r}. Install Newton with its required warp-lang dependency.")
        return 3

    try:
        wp.init()
        wp.set_device(args.device)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: device {args.device!r} is not usable: {type(exc).__name__}: {exc}")
        return 4

    newton.use_coord_layout_targets = True
    template = newton.ModelBuilder()
    body = template.add_body(xform=wp.transform((0.0, 0.0, 0.8), wp.quat_identity()), mass=1.0, label="body")
    template.add_shape_sphere(body, radius=0.25, label="sphere")
    template.add_ground_plane(label="ground")

    if args.world_count == 1:
        builder = template
    else:
        builder = newton.ModelBuilder()
        builder.replicate(template, args.world_count, spacing=(1.0, 0.0, 0.0))

    model = builder.finalize(device=args.device)
    state0 = model.state()
    state1 = model.state()
    control = model.control()
    pipeline = newton.CollisionPipeline(model)
    contacts = pipeline.contacts()
    solver = newton.solvers.SolverXPBD(model, iterations=4)
    newton.eval_fk(model, model.joint_q, model.joint_qd, state0)

    for _ in range(args.steps):
        state0.clear_forces()
        pipeline.collide(state0, contacts)
        solver.step(state0, state1, control, contacts, args.dt)
        state0, state1 = state1, state0

    print(f"body_count={model.body_count}")
    print(f"shape_count={model.shape_count}")
    print(f"joint_coord_count={model.joint_coord_count}")
    print(f"joint_dof_count={model.joint_dof_count}")
    print(f"body_q_shape={state0.body_q.numpy().shape}")
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
