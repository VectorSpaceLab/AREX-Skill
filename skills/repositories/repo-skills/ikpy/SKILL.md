---
name: ikpy
description: "Use IKPy for Python robot kinematics: construct or import chains,
  compute forward/inverse kinematics, handle URDF/MJCF/DH models, validate
  transforms, use the optional JAX backend, and create headless diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# IKPy

IKPy is a pure-Python inverse-kinematics library for serial robot chains. Use
this skill when a task mentions IKPy, `Chain`, `URDFLink`, `DHLink`, URDF/MJCF
robot descriptions, homogeneous transforms, position/orientation IK, or the
optional JAX backend.

## Start safely

- Install the base package with `python -m pip install ikpy` for NumPy/SciPy/
  SymPy kinematics.
- Add plotting with `python -m pip install 'ikpy[plot]'` and JAX with
  `python -m pip install 'ikpy[jax]'`. These extras are optional; no robot
  hardware or accelerator is required for the core library.
- Verify the active interpreter with `python -c "import ikpy; print(ikpy.__version__)"`.
  The bundled [`scripts/check_env.py`](scripts/check_env.py) reports core and
  optional dependency availability without reading a model or writing files.
- Work with a complete joint vector: one value per chain link, including the
  origin and terminal fixed links. Set fixed/terminal entries inactive in the
  `active_links_mask`.

## Route the task

- **Build or solve a chain in memory:** read
  [chain-kinematics](sub-skills/chain-kinematics/SKILL.md) for `Chain`, FK/IK,
  orientation modes, bounds, active masks, DH/custom links, and numerical checks.
- **Load or inspect robot descriptions:** read
  [robot-model-import](sub-skills/robot-model-import/SKILL.md) for URDF, MJCF,
  IKPy JSON metadata, path selection, prismatic joints, and parser diagnostics.
- **Use `backend="jax"`:** read
  [jax-backend](sub-skills/jax-backend/SKILL.md) for optional CPU JAX, cache
  compilation, autodiff Jacobians, solver options, and NumPy parity. Do not
  infer CUDA support from a visible GPU.
- **Inspect transforms or render diagnostics:** read
  [visualization-geometry](sub-skills/visualization-geometry/SKILL.md) for
  4x4 matrix conventions, headless Matplotlib plots, target overlays, and
  Graphviz URDF trees.

For exact public signatures, cross-cutting install notes, and package version
facts, read [the API overview](references/api-overview.md) and
[troubleshooting](references/troubleshooting.md). Read
[repo-provenance.md](references/repo-provenance.md) before deciding whether
this skill matches a changed checkout; refresh it when the recorded commit or
public API baseline differs.

## Operational boundaries

IKPy computes kinematic transforms and numerical solutions; it does not by
itself command motors, simulate a robot, validate collision safety, or prove a
solution is physically reachable. Confirm units, frames, joint limits, target
reachability, and downstream controller safety separately. Keep hardware,
third-party simulators, credentials, and indefinite control loops outside this
runtime skill.
