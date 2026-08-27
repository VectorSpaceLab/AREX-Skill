# API Reference

## Verified MuJoCo calls used here

| API | Purpose | Notes |
| --- | --- | --- |
| `mujoco.MjModel.from_xml_path(path)` | Compile and load a Menagerie XML from disk. | Preferred for direct file-based loading because it preserves relative `include` and `mesh` resolution from the XML location. |
| `mujoco.MjData(model)` | Allocate simulation state for a compiled model. | Required before stepping. |
| `mujoco.mj_step(model, data)` | Advance the simulation by one step. | The smoke test loops until a short time limit is reached. |
| `mujoco.mju_Halton(i, j + 2)` | Produce deterministic control noise. | Matches the repo test pattern exactly, including the dimension offset of `+ 2`. |
| `mujoco.mj_name2id(model, objtype, name)` | Look up a body or actuator by name. | Returns `-1` when the name is missing. Use `mujoco.mjtObj.mjOBJ_BODY` or `mujoco.mjtObj.mjOBJ_ACTUATOR`. |
| `mujoco.mj_id2name(model, objtype, id)` | Enumerate compiled object names. | Useful for `--print-names` style debugging. |
| `data.warning.number` | Read MuJoCo warning counters. | The repo smoke test fails when any warning count is nonzero. |
| `mujoco.mjtWarning(enum_value).name` | Turn warning counters into readable labels. | Use this when reporting warnings to the user. |

## Repo smoke semantics to mirror

The Menagerie test helper does the following:

1. Compile every `scene*.xml`.
2. Construct `mujoco.MjData(model)`.
3. Step until a short time limit is reached.
4. Set each control channel to a deterministic value based on the actuator
   range and a Halton sequence.
5. Fail if any MuJoCo warning counter is nonzero after stepping.

The control update rule is:

```python
for j in range(model.nu):
    ctrlrange = model.actuator_ctrlrange[j]
    if model.actuator_ctrllimited[j]:
        center = 0.5 * (ctrlrange[1] + ctrlrange[0])
        radius = 0.5 * (ctrlrange[1] - ctrlrange[0])
    else:
        center = 0.0
        radius = 1.0
    data.ctrl[j] = center + radius * noise_scale * (2 * mujoco.mju_Halton(i, j + 2) - 1)
```

## Useful model fields

These compiled-model fields are commonly inspected while loading and smoke
checking:

- `model.nbody`
- `model.nq`
- `model.nv`
- `model.nu`
- `model.ngeom`
- `model.nsite`
- `model.actuator_ctrllimited`
- `model.actuator_ctrlrange`

## Optional `robot_descriptions` loader

When the description package is available, you can also load through the dynamic
loader:

```python
from robot_descriptions.loaders.mujoco import load_robot_description
model = load_robot_description("panda_mj_description")
```

The package name is model-specific; if it is not known or not installed, use the
XML path loader instead.
