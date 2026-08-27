---
name: chain-kinematics
description: "Use for direct IKPy Chain and Link construction, NumPy forward or
  inverse kinematics, masks, bounds, orientations, DH/URDFLink modeling,
  serialization, concatenation, and numerical validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Chain kinematics

Use this route when a user needs to build or manipulate an IKPy `Chain`, compute
forward kinematics, solve a position/orientation inverse-kinematics target, or
validate a result numerically.

## Route by task

- **Novice:** read [workflows.md](references/workflows.md) first for the tiny
  `OriginLink` + `URDFLink` fixture, full joint-vector convention, FK/IK
  recipes, and a validation loop.
- **Expert:** read [api-reference.md](references/api-reference.md) for exact
  v4.0.0 signatures, shapes, DH/URDF conventions, optimizer arguments, masks,
  and serialization constraints. Use [troubleshooting.md](references/troubleshooting.md)
  when a solver, bound, orientation, or input-shape check fails.
- Run the safe deterministic helper
  [`scripts/smoke_chain.py`](scripts/smoke_chain.py) after installation; it
  exercises construction, FK, masks, IK, bounds, orientation, DH, prismatic
  links, and geometry shapes without loading a robot file.

## Scope and handoffs

This route owns direct `Chain`, `Link`, `OriginLink`, `URDFLink`, and `DHLink`
construction; NumPy FK/IK; full versus active joint vectors; bounds and
orientation targets; chain conversion/concatenation; JSON serialization
contracts; and residual-based numerical checks.

- Keep every joint value, including inactive links and the terminal link, in a
  full vector. The terminal link should be fixed and inactive; verify the mask
  explicitly because this release's constructor check is implementation-
  brittle.
- Route URDF/MJCF file parsing, model-tree discovery, and parser-specific
  selection to [robot-model-import](../robot-model-import/SKILL.md).
- Route `backend="jax"` and JAX-specific optimizer behavior to
  [jax-backend](../jax-backend/SKILL.md).
- Route plotting and geometry visualization implementation to
  [visualization-geometry](../visualization-geometry/SKILL.md).
