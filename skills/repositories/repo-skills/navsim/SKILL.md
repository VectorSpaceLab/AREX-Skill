---
name: navsim
description: "Use NAVSIM v2 for autonomous-driving agent development, OpenScene
  data setup, learned-agent training, EPDMS evaluation, traffic-policy
  experiments, visualization, and leaderboard submission preparation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# NAVSIM v2 operating guide

Use this skill when a task names NAVSIM, OpenScene, EPDMS/PDM score, pseudo
closed-loop driving evaluation, TransFuser/LTF, `Trajectory`, `SensorConfig`,
NAVSIM split names, or the NAVSIM submission pickle. This is a self-contained
operating graph: use its bundled references and safe helpers rather than
reopening a NAVSIM checkout.

## Route by task

- **Install, workspace, maps, logs, sensors, split choice, or loader/data
  layout:** read [setup-and-data](sub-skills/setup-and-data/SKILL.md).
- **Create/debug a planner agent, sensor history, trajectory, checkpoint, or
  TransFuser/LTF configuration:** read [agents](sub-skills/agents/SKILL.md).
- **Train a learned agent, build/reuse feature caches, or diagnose Lightning and
  Hydra training configuration:** read [training](sub-skills/training/SKILL.md).
- **Build metric caches, run one-/two-stage EPDMS, select traffic policies, or
  diagnose score CSVs:** read [evaluation](sub-skills/evaluation/SKILL.md).
- **Plot camera/BEV/LiDAR data or prepare/validate a warmup/challenge pickle:**
  read [visualization-and-submission](sub-skills/visualization-and-submission/SKILL.md).

For a request that spans routes, start with `setup-and-data`, then follow the
links from `agents` into `training` or `evaluation`; use
`visualization-and-submission` only for plotting and submission artifacts.

## Installation baseline

NAVSIM v2.0.0 documents Python 3.9+, a nuPlan devkit dependency, PyTorch 2.0.1,
Hydra, PyTorch Lightning, NumPy, OpenCV, geospatial libraries, and optional
visualization/Jupyter packages. Use a fresh environment and the package's
versioned requirements rather than mutating an unrelated environment. For a
public source installation, use a compatible Python 3.9+ environment and pin
this source revision:

```bash
python -m pip install "navsim @ git+https://github.com/autonomousvision/navsim.git@0a380a9063d7162ec93d0f51e9990ebac585f720"
python -m pip check
```

If a user already has a source checkout, editable installation is equivalent:
`python -m pip install -e .` from that checkout. A minimal public import check
is:

```bash
python -c "import navsim; from navsim.common.dataclasses import SensorConfig, Trajectory; print('NAVSIM import OK')"
```

GPU is not required for metadata/API inspection, but learned TransFuser
training and realistic sensor/evaluation workloads should use a compatible
CUDA Torch installation. Never call a CPU import proof of GPU capability.

## Workspace contract

Before any data-backed command, define these public variables and validate the
selected roots with the bundled [workspace validator](sub-skills/setup-and-data/scripts/validate_workspace.py)
from the `setup-and-data` route:

- `NUPLAN_MAP_VERSION=nuplan-maps-v1.0`
- `NUPLAN_MAPS_ROOT`: readable nuPlan map database
- `NAVSIM_EXP_ROOT`: experiment outputs and metric cache
- `NAVSIM_DEVKIT_ROOT`: the NAVSIM installation/project root used by the user's
  command context
- `OPENSCENE_DATA_ROOT`: OpenScene logs, sensor blobs, and two-stage bundles

Do not create empty directories to satisfy the checker. Logs, sensor paths,
map data, synthetic scenes, and metric caches are separate resources.

## Cross-cutting guardrails

- Keep agent trajectories in local rear-axle BEV `(x, y, heading)` form with a
  matching `TrajectorySampling`; the default model output is 4 seconds at
  0.5-second intervals, while proposal evaluation commonly samples 4 seconds
  at 0.1 seconds.
- Keep the metric-cache split, scene-filter split, synthetic roots, proposal
  sampling, and traffic policy aligned. Treat missing/unused token warnings or
  invalid pseudo-closed-loop aggregation as failed evaluation evidence.
- Do not train challenge/test splits. `navtrain`/`trainval`/`mini` are training
  candidates; `test`, `navtest`, `navhard_two_stage`, `warmup_two_stage`, and
  private challenge splits are evaluation/submission surfaces.
- Submission agents receive `AgentInput`, not an annotated `Scene`; a
  `requires_scene=True` privileged agent cannot generate a valid server pickle.
- Dataset downloads, large cache creation, training, benchmark scoring,
  private-data access, uploads, and notebook rendering are explicit operations,
  not default smoke checks.

For a package/API/backend smoke, run the shared [runtime inspector](scripts/inspect_navsim_runtime.py)
with `--help`, `--json`, or the explicitly requested `--cuda` probe. Read
[troubleshooting.md](references/troubleshooting.md) for cross-cutting
install/import, environment-variable, split/cache, backend, Hydra, and output
failures. Read [repo-provenance.md](references/repo-provenance.md) before
refreshing this graph against a newer NAVSIM source version.
