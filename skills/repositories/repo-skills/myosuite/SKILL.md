---
name: "myosuite"
description: "Use MyoSuite's MuJoCo musculoskeletal environments, task registry,
  model and kinematics tools, reference-motion utilities, optional MJX
  acceleration, rendering, and bounded reinforcement-learning integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MyoSuite operating guide

MyoSuite is a Python package of musculoskeletal MuJoCo environments exposed
through Gymnasium-compatible APIs. Use this skill for task selection, short
control rollouts, observation/reward inspection, simulation and rendering,
model edits/IK, reference trajectories, optional JAX/MJX acceleration, or RL
integration planning. This is a self-contained operating graph: use its bundled
references and scripts, not the source checkout's tests, tutorials, or
launchers.

## Route first

- **Environment/task creation, reset/step, seeds, spaces, task IDs, or safe
  headless rollouts:** read [environments](sub-skills/environments/SKILL.md).
- **MuJoCo model state, XML loading, cameras, offscreen/onscreen rendering, or
  viewer failures:** read [simulation-rendering](sub-skills/simulation-rendering/SKILL.md).
- **XML/model transformations, robot edits, site-pose IK, or quaternion/vector
  utilities:** read [model-editing-kinematics](sub-skills/model-editing-kinematics/SKILL.md).
- **Fixed/random/tracked trajectories, interpolation, playback, or reference
  logs:** read [reference-motion](sub-skills/reference-motion/SKILL.md).
- **JAX/MJX/MJWarp, device probes, CUDA, or NumPy/JAX parity:** read
  [mjx-acceleration](sub-skills/mjx-acceleration/SKILL.md).
- **Saved-policy evaluation, SB3/MJRL/DEP-RL/TorchRL boundaries, or training
  handoff/config validation:** read [training-integration](sub-skills/training-integration/SKILL.md).

For package-wide setup failures, read [installation and assets](references/installation-and-assets.md)
and [troubleshooting](references/troubleshooting.md). Read
[repository provenance](references/repo-provenance.md) before treating this
graph as current for a changed checkout.

## Install and smoke check

Use an isolated Python 3.10–3.13 environment and install the released package
or an editable source distribution with its documented MuJoCo model assets.
The core route needs Gymnasium below 1.3, MuJoCo 3.6.x, NumPy, Click, and the
other base dependencies declared by the package. Do not install MJX/CUDA or RL
extras unless the requested route needs them.

```bash
python -m pip install -U myosuite
python -c "import myosuite, mujoco; print(myosuite.__version__, mujoco.__version__)"
python sub-skills/environments/scripts/environment_smoke.py \
  --env-id myoElbowPose1D6MRandom-v0 --steps 3 --seed 123 --render none
```

For a source checkout, missing MuJoCo include files usually mean the repository's
asset submodules/package data are unavailable; see the asset guidance rather
than changing task IDs. The verified package snapshot imported MyoSuite 2.12.2,
MuJoCo 3.6.0, and Gymnasium 1.2.3, registered 398 environments, and completed
a seeded pose reset/step smoke after model assets were available.

## Operating rules

1. Import `myosuite` before querying the Gymnasium registry; registration is an
   import side effect. Prefer `gym.spec(task_id)` and an exact task ID from the
   linked task catalog before `gym.make(task_id)`.
2. Use `reset(seed=...)`, seed the action space for deterministic sampled
   controls, honor the five-value Gymnasium `step` result, and close every
   environment in a `finally` block.
3. Keep CPU/base behavior separate from optional display and MJX/CUDA claims.
   A successful MuJoCo CPU step does not prove JAX, CUDA, or a windowing stack.
4. Bound episodes, frames, output files, and training plans. Do not fetch model
   assets, open viewers, deserialize untrusted policies, or launch long
   experiments without explicit user intent.
5. Preserve task-specific observation/action shapes and reference joint order;
   do not copy a control vector or reference file between tasks without checking
   its declared spaces and dimensions.

## Verification boundary

The base package, registry, seeded environment lifecycle, model-editor tests,
CLI help, and safe bundled scripts are CPU-verifiable. MJX/JAX/CUDA, onscreen
viewer behavior, networked asset setup, and long RL training are optional or
environment-dependent; route them to the relevant sub-skill and keep any
unverified backend visible. The generated skill is intentionally **not imported**
into the managed DisCo repo-skill collection for this run.
