# Loading Workflows

## Prerequisites

- Python with a working `mujoco` import and native XML compile support.
- The repo smoke-test environment also uses `absl-py` and `pytest-xdist`; the
  bundled smoke helper itself only needs `mujoco` and, optionally,
  `robot_descriptions`.
- Optional `robot_descriptions` if you want to load a model through a published
  description package instead of a file path.
- A local display/OpenGL context if you plan to use the viewer command.
  Compile-and-step smoke checks can run headless.

## 1) Load a Menagerie XML directly

Use the exact XML path you were given. An absolute path is safest when you are
running from an arbitrary working directory.

```python
import mujoco

model = mujoco.MjModel.from_xml_path("/abs/path/to/model/scene.xml")
data = mujoco.MjData(model)
```

Tips:

- Use a `scene*.xml` file when you want the full environment with floor,
  lighting, and any included scene objects.
- Use the bare model XML when you only want the robot or device itself.
- Use an `_mjx.xml` or `scene_mjx.xml` file only when the task explicitly wants
  the MJX-compatible variant.

### Quick smoke command

```bash
python skills/disco/mujoco-menagerie/sub-skills/model-loading/scripts/smoke_load_model.py \
  --xml /abs/path/to/model/scene.xml \
  --skip-step
```

## 2) Load through `robot_descriptions` when available

The Menagerie README demonstrates the published description-package pattern for
Panda. The package name may vary by model, so use the package that is actually
published for the model you want.

```python
import mujoco
from robot_descriptions import panda_mj_description

model = mujoco.MjModel.from_xml_path(panda_mj_description.MJCF_PATH)
```

The dynamic loader is convenient when you know the package name:

```python
from robot_descriptions.loaders.mujoco import load_robot_description

model = load_robot_description("panda_mj_description")
model = load_robot_description("panda_mj_description", variant="panda_nohand")
```

If the package is not installed or the package name is unknown, use the direct
XML path workflow instead.

## 3) Open the model in the viewer

The standard viewer command is:

```bash
python -m mujoco.viewer --mjcf /abs/path/to/model/scene.xml
```

Use it only when a GUI/OpenGL-capable session is available. If the host is
headless, prefer `scripts/smoke_load_model.py` first and only enable a viewer
once a display backend is known to work.

## 4) Run a short deterministic smoke step

The repo test pattern is:

- compile each `scene*.xml`
- create `mujoco.MjData(model)`
- step until a short time limit is reached
- populate controls with deterministic Halton noise
- fail if any MuJoCo warning counter is nonzero

The bundled helper follows that pattern and adds optional body/actuator checks.

```bash
python skills/disco/mujoco-menagerie/sub-skills/model-loading/scripts/smoke_load_model.py \
  --xml /abs/path/to/model/scene.xml \
  --max-sim-time 0.02 \
  --expect-body base \
  --expect-actuator FL_hip \
  --expect-nu 12
```

Use `--max-sim-time 0.02` for a fast headless CI smoke and increase toward the repo test's `0.1` seconds when you want stricter coverage. Do **not** pass `--allow-warnings` when the requirement is "no MuJoCo warnings"; by default the helper fails on any nonzero warning counter.

If you want a compile-only pass, set `--max-sim-time 0` or `--skip-step`.

### Control noise rule

The safe-control pattern matches the repo smoke test:

```python
if model.actuator_ctrllimited[j]:
    center = 0.5 * (ctrlrange[1] + ctrlrange[0])
    radius = 0.5 * (ctrlrange[1] - ctrlrange[0])
else:
    center = 0.0
    radius = 1.0

value = center + radius * noise_scale * (2 * mujoco.mju_Halton(i, j + 2) - 1)
```

This keeps controls bounded by the actuator range when one exists, while still
being deterministic across runs.

## 5) Interpret warnings

After stepping, the helper checks `data.warning.number`. Any nonzero entry is a
load/runtime problem unless you explicitly allow warnings while debugging.

Use the warning names from `mujoco.mjtWarning(enum_value).name` to decide whether
it is a bad control, invalid state, contact issue, or another runtime problem.

## 6) Asset-path resolution rules

- `include file="..."` and `mesh file="..."` are resolved from the XML's own
directory.
- Model XMLs in Menagerie typically point at a sibling `assets/` directory.
- If you copied only the XML and not its sibling files, missing-mesh failures are
  expected.
- If the XML was moved, restore the full model directory layout before retrying
  the load.

When the path layout is unclear, run the helper in compile-only mode first so the
error message shows the first unresolved include or mesh file.
