---
name: visual-pushing-grasping
description: "Route Visual Pushing and Grasping workflows for RGB-D robotic
  manipulation, including VPG model training/testing, heightmap geometry,
  CoppeliaSim simulation, session evaluation, and guarded UR5/RealSense
  operation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Visual Pushing and Grasping

Use this operating skill when a task involves the historical
`andyzeng/visual-pushing-grasping` implementation: complementary pushing and
grasping from RGB-D observations, pixel-wise affordance/Q maps, V-REP or
CoppeliaSim scenes, VPG transition logs, or a UR5 plus RealSense camera.

## Route the request

- **Train, resume, or test a reactive/reinforcement VPG policy:** read
  [`training`](sub-skills/training/SKILL.md). It owns CLI flags, model behavior,
  snapshots, logging, exploration, replay, and CPU/CUDA decisions.
- **Project RGB-D data into robot-frame heightmaps or validate calibration:**
  read [`perception-geometry`](sub-skills/perception-geometry/SKILL.md). It owns
  array shapes, units, workspace bounds, depth scale, and rigid transforms.
- **Run or author a simulated manipulation scenario:** read
  [`simulation`](sub-skills/simulation/SKILL.md). It owns CoppeliaSim/V-REP
  startup, remote API prerequisites, object meshes, preset files, and safe
  preflight validation.
- **Summarize a completed session or plot training curves:** read
  [`evaluation`](sub-skills/evaluation/SKILL.md). It owns transition-log
  schemas, reactive/reinforcement metric thresholds, and headless plots.
- **Connect a RealSense stream, calibrate, or operate an UR5:** read
  [`real-robot`](sub-skills/real-robot/SKILL.md). It is safety-first and never
  starts physical motion implicitly.

For requests spanning routes, begin here, then load only the owning sub-skills:
`perception-geometry` supplies camera/heightmap contracts to `training` and
`real-robot`; `simulation` or `real-robot` supplies observations/actions to
`training`; `evaluation` consumes the logs produced by `training`.

## Runtime boundary

This is a historical research implementation, not a packaged distribution.
The source artifact has no `pyproject.toml`, `setup.py`, or console entry point.
Use an isolated environment with the public numerical requirements (NumPy,
SciPy, OpenCV-Python, Matplotlib, PyTorch, and TorchVision) before any
operator-supplied application run. Current-Python checks are bounded
compatibility diagnostics only; the full loop may require an older compatible
Torch/Python combination, especially for the historical pretrained snapshot.

Let `<skill-root>` mean the directory containing this root `SKILL.md`. The
self-contained environment check is the only root runtime prerequisite probe:

```console
python <skill-root>/scripts/check_environment.py
```

The historical source-module import check was construction evidence only; it
is not a runtime instruction and must not be used after this graph is deployed.
Use `--cpu` for a deliberate CPU run. CUDA is optional for correctness but
practically useful for training; verify it with the bundled helper rather than
assuming a visible device is usable. Read
[`troubleshooting.md`](references/troubleshooting.md) before changing Torch,
NumPy, snapshot, or simulator versions.

## Safety and verification gates

Do not start the main loop merely to inspect the CLI: construction opens a
camera/robot adapter and can connect to external services. First run parser
help, validate paths and preset schemas with the bundled helpers, and confirm
that the requested external service or hardware is present. Never run
calibration, touch/debug, grasp, push, or restart procedures without a human
approved workspace and an explicit stop plan.

The generated graph deliberately does not bundle a V-REP/CoppeliaSim main
loop, scene, native remote-API binary, RealSense SDK libraries, UR5 services,
model weights, or large presentation assets. Those are operator-supplied
external prerequisites and are described with their failure signals in the
focused routes. The root helper is linked here:
[`check_environment.py`](scripts/check_environment.py). Read
[`repo-provenance.md`](references/repo-provenance.md) before deciding whether
this graph is stale for another checkout.

## Shared source facts

- Observations are RGB-D images reprojected into a top-down heightmap; the
  default heightmap resolution is 0.002 metres per pixel.
- The model evaluates 16 rotations and separate push/grasp branches. Reactive
  mode emits class-like affordances; reinforcement mode emits Q values.
- `0` is the push action and `1` is the grasp action in transition logs.
- Session evaluation interprets reactive grasp success as reward `0`, and
  reinforcement grasp success as reward at least `0.5`; pushes never count as
  successful grasps.
- Simulation uses the implemented V-REP remote API endpoint on port `19997`.
  The physical camera streamer defaults to TCP port `50000`; UR5 command and
  real-time channels default to `30002` and `30003`.

All detailed commands, data contracts, and recovery steps live in the linked
sub-skills and references rather than in this router.
