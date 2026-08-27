---
name: pypose
description: "Use PyPose for differentiable robotics with PyTorch: Lie-group
  geometry, state estimation and control modules, dense or sparse nonlinear
  optimization, projection/spline utilities, and trajectory evaluation; route
  each task to the matching workflow and backend contract."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PyPose

PyPose is a PyTorch-based library for differentiable robotics, Lie groups, and
physics-based optimization. Use this skill when a task mentions PyPose,
`pypose`, LieTensor, SO3/SE3, pose graphs, bundle adjustment, filters, MPC,
IMU preintegration, ICP/PnP, splines, reprojection, APE/RPE, or second-order
optimization.

## Start here

1. Install the public package and a compatible PyTorch 2.x build:
   `python -m pip install pypose` (or install the repository package with its
   `requirements/runtime.txt` when working from a source checkout).
2. Check the package before writing a larger experiment:
   `python scripts/check_pypose_env.py`.
3. Decide the representation, module, objective, and device first. Keep all
   related tensors on one device and in a compatible floating dtype.
4. Read exactly one focused sub-skill below, then its nearest API/workflow
   references and troubleshooting guide. Use bundled smoke scripts for a small
   deterministic check before a dataset-scale run.

```python
import torch
import pypose as pp

xi = pp.se3([0.1, -0.2, 0.05, 0.02, 0.03, -0.01])
pose = xi.Exp()
points = torch.randn(8, 3)
transformed = pose.Act(points)
assert transformed.shape == points.shape
```

## Route by task

- **`lie-tensor`** — SO3/SE3/Sim3/RxSO3 groups and algebras; typed
  construction, `Exp`/`Log`, composition, inverse, point action, conversions,
  batching, gradients, and manifold parameters. Read
  [sub-skills/lie-tensor/SKILL.md](sub-skills/lie-tensor/SKILL.md).
- **`robotics-modules`** — dynamics and systems, EKF/UKF/PF, LQR/MPC,
  IMUPreintegrator, EPnP, ICP, and GeodesicLoss. Read
  [sub-skills/robotics-modules/SKILL.md](sub-skills/robotics-modules/SKILL.md).
- **`optimization`** — residual modules, GN/LM, solvers, damping strategies,
  robust kernels/correctors, schedulers, Jacobians, and BAE/CUDA sparse LM.
  Read [sub-skills/optimization/SKILL.md](sub-skills/optimization/SKILL.md).
- **`geometry-evaluation`** — camera projection and reprojection, point-set
  utilities, splines, downsampling, trajectory association and APE/RPE.
  Read
  [sub-skills/geometry-evaluation/SKILL.md](sub-skills/geometry-evaluation/SKILL.md).

If a request crosses routes, normalize the data and transform conventions in
`lie-tensor` first, then use the owning workflow: for example,
SE(3)-parameter LM belongs to `optimization`, while an EKF over SE(3) states
belongs to `robotics-modules`.

## Device and optional backend policy

The base package requires PyTorch 2.x and runs on CPU or a compatible PyTorch
accelerator. CUDA may accelerate ordinary operations, but do not call a CPU
smoke proof of CUDA support. The sparse Jacobian/sparse LM route is different:
it requires CUDA and the optional `bae` backend, with the verified compatible
release `bae==0.2.1`; it has no CPU substitute. Read
[optimization/references/sparse-optimization.md](sub-skills/optimization/references/sparse-optimization.md)
before selecting `sjac`, `psjac`, `PCG`, or `sparse=True`.

Use the root diagnostic for an import/version/device report. Use
[sub-skills/optimization/scripts/sparse_lm_smoke.py](sub-skills/optimization/scripts/sparse_lm_smoke.py)
with `--check-only` when sparse readiness is a hard requirement. If CUDA or
BAE is absent, narrow the task to dense optimization or record the sparse
capability as unverified; do not silently switch to CPU and claim equivalent
coverage.

## Shared references and maintenance

- Read [references/troubleshooting.md](references/troubleshooting.md) for
  package import, PyTorch compatibility, device, optional dependency, and
  general shape failures.
- Read [references/repo-provenance.md](references/repo-provenance.md) before
  deciding whether this skill matches a repository revision; refresh it when
  the package version, public entry points, or evidence baseline changes.
- `references/repo-routing-metadata.json` contains structured placement data
  for the managed repo-skill router; it is metadata, not a second usage guide.

The runtime files are self-contained. Original examples, tests, notebooks,
data downloads, and plotting programs informed the references but are not
runtime dependencies. Prefer the bundled helpers and small in-memory fixtures
for verification. Do not copy private environment paths, activation commands,
or checkout-specific imports into a Researcher task.
