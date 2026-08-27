# Troubleshooting guide

This page focuses on the failures that matter for RoboTwin simulator-core work:
imports, scene bootstrap, render checks, planner setup, and camera capture.

## 1) Import-time failures

### `ModuleNotFoundError: sapien` or a render backend error

The simulator core depends on a SAPIEN-capable Python environment. If `sapien`
cannot be imported or the renderer cannot be created, the environment is not
ready for simulation work yet.

RoboTwin itself is not packaged as an installable Python project here, so do
not expect a plain `pip install` of the repo to expose its modules.

Use the bundled render smoke first:

```bash
python scripts/check_render_smoke.py
```

If that fails before the scene is created, treat it as an environment/backend
issue rather than a task bug.

### `envs` import fails before any task runs

Some RoboTwin imports touch asset metadata during module import. A common
failure mode is missing object metadata for the cluttered-object loader.
In particular, the import path can fail until the asset bundle has populated
`assets/objects/objaverse/list.json`.

Fix the assets first, then retry the task import.

### `XPolicyLab` is missing

If a future workflow touches policy evaluation, the embedded submodule must be
initialized before those tools can run. The simulator-core skill does not own
that setup, but it should recognize the failure and route the user to the
policy-eval skill.

## 2) Render smoke failures

### Renderer creation fails

If `SapienRenderer()` or `scene.update_render()` fails, check:

- whether the Python environment has the required SAPIEN build,
- whether the machine has a render-capable backend,
- whether the session is headless and requires a supported offscreen setup.

The smoke script is intentionally small: it should fail fast and localize the
problem to import, renderer creation, scene creation, or camera capture.

### Camera capture fails

If `camera.take_picture()` or `camera.get_picture("Color")` fails, inspect the
scene bootstrap path instead of the task logic.
Common causes are missing renderer initialization, invalid camera pose, or an
unsupported graphics backend.

## 3) Task bootstrap failures

### `UnStableError` during task initialization

The task bootstrap checks whether the initial scene has stabilized. If this
fails, revisit:

- object pose sampling,
- table height and table-height bias,
- object mass or collision parameters,
- randomization settings that place objects too close together.

### Planning failure or `plan_success = False`

A failed path plan should be treated as a real task failure until the target or
constraint is corrected. Debug in this order:

1. verify the actor contact or functional point used to build the target pose,
2. relax or adjust `pre_dis`, `dis`, or `constraint_pose`,
3. try a different contact point or a different arm,
4. inspect the planner inputs from `left_plan_path` / `right_plan_path`.

### Alternating-arm collision issues

When tasks alternate between arms, keep one arm retracted while the other moves.
Useful tools:

- `move_by_displacement(..., move_axis="arm")`
- `add_prohibit_area(...)`
- a short retract step before switching arms

## 4) Camera and point-cloud issues

### RGB/depth appears empty or stale

Check that:

- the relevant camera is enabled in the task config,
- `collect_head_camera` / `collect_wrist_camera` match the task expectation,
- `_update_render()` or `scene.update_render()` is called before capture.

### Point-cloud capture fails

Point-cloud helpers depend on the CUDA path and `pytorch3d`-backed sampling.
If a point-cloud helper exits early, treat it as a missing dependency rather
than a task bug. Render smoke does not prove the point-cloud path is ready.

## 5) What to do next

- If the problem is assets, fix the assets and retry the task import.
- If the problem is rendering, use the bundled smoke script to localize the
  backend issue.
- If the problem is action layout or evaluation wiring, route to the sibling
  `policy-eval` skill.
- If the problem is dataset layout or collected outputs, route to the sibling
  `data-pipeline` skill.
