# Troubleshooting

## Missing mesh or include file

**Symptom**: MuJoCo fails to compile with an error about a missing `mesh`,
`include`, or another referenced file.

**Likely cause**: The XML was moved without its sibling files. Menagerie XMLs
usually rely on relative paths such as `include file="..."` and
`meshdir="assets"`.

**Fix**:

- Restore the original directory layout so the XML sits next to its asset tree.
- Make sure the `assets/` directory is still present beside the XML.
- If you copied only the XML, copy the full model directory instead.
- Re-run the compile-only smoke first so you get the first unresolved path in the
  error message.

## Scene XML versus bare model XML confusion

**Symptom**: The model loads, but the expected world objects or frame names are
missing.

**Likely cause**: You loaded a bare model XML when you wanted the full scene, or
vice versa.

**Fix**:

- Use the scene XML when you need the floor, lighting, and any extra world
  bodies.
- Use the bare model XML when you want the robot/device only.
- If a specialized variant exists, load that exact XML rather than assuming the
  scene and model files are interchangeable.

## Body or actuator not found

**Symptom**: The smoke script reports that an expected body or actuator is
missing.

**Likely cause**: The wrong XML variant was loaded, or the expected name is not
part of that model.

**Fix**:

- Run the smoke script with `--print-names`.
- Use `mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)` or the actuator
  equivalent to check the compiled model directly.
- Reconfirm the XML path before changing the model.

## Warnings after stepping

**Symptom**: The short simulation runs, but `data.warning.number` contains one or
more nonzero counters.

**Likely cause**: The model, controls, or initial state are not stable for the
chosen runtime.

**Fix**:

- Re-run with `--skip-step` to separate compile-time failures from runtime
  warnings.
- Lower the noise scale if you are probing a fragile model.
- Inspect the printed `mjtWarning` names and treat them as runtime bugs unless
  you explicitly allowed warnings while debugging.

## Viewer does not open

**Symptom**: `python -m mujoco.viewer --mjcf ...` fails or opens no window.

**Likely cause**: The host does not have a usable GUI or OpenGL context.

**Fix**:

- Use the smoke helper first to verify compile/step behavior without a viewer.
- Switch to a desktop session or a backend that your host supports.
- Do not assume the viewer can run inside a headless container.

## `robot_descriptions` import or load failure

**Symptom**: Importing the description package or calling the loader raises an
error.

**Likely cause**: The package is not installed, or the package name/variant is
not the one published for that model.

**Fix**:

- Fall back to the direct XML path loader.
- Use the exact package name published for the model.
- If a variant is not available, load the default model first.

## When to route elsewhere

- If you need to decide *which* XML to load, route to the catalog sub-skill.
- If you need to change the XML or compose models, route to the editing
  sub-skill.
- If you need repo-wide check orchestration, route to the maintainer sub-skill.
