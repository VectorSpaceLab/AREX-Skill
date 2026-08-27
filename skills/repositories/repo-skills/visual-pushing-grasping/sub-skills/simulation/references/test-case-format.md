# Preset test-case format

A preset is a plain-text file consumed by `robot.py` when both
`--is_testing` and `--test_preset_cases` are set. The historical loader reads
exactly `--num_obj` lines and splits each line on whitespace. Each object line
has **ten fields**:

```text
mesh_name red green blue pos_x pos_y pos_z orientation_x orientation_y orientation_z
```

For example, a source-compatible line is:

```text
0.obj 0.3058823529411765 0.4745098039215686 0.6549019607843137 -0.50 0.02 0.026 -1.5708 -0.41 -0.001
```

## Field contract

| Fields | Meaning | Static validation |
|---|---|---|
| 1 | Mesh name/path token, normally `0.obj`-style basename | Non-empty, `.obj` suffix, not absolute, no `..`; if `--mesh-dir` is supplied, resolves to an existing regular file below that directory |
| 2–4 | RGB color used for the imported shape | Three finite real numbers in the inclusive `[0, 1]` range; the source presets use normalized Tableau-like values |
| 5–7 | Object position `(x, y, z)` in simulator/robot coordinates | Three finite real numbers; no `NaN` or infinity |
| 8–10 | Object Euler orientation `(x, y, z)` in radians | Three finite real numbers; no `NaN` or infinity; no artificial angle wrapping is imposed |

The static validator intentionally does not assert that positions are inside
the source workspace, that meshes are watertight, that objects do not overlap,
or that a pose is dynamically stable. Those require the external simulator.
The source workspace defaults are `x=[-0.724,-0.276]`, `y=[-0.224,0.224]`, and
`z=[-0.0001,0.4]`; historical presets include extreme fallen-object `z` values,
so a finite-value gate must not silently rewrite or reject them as if it were a
physics checker.

## Count and ordering

The expected count is the number of nonempty object lines and must equal
`--num_obj` at runtime. The bundled source presets are named `test-10-obj-00.txt`
through `test-10-obj-10.txt` and each contains ten object lines. The adapter
uses the line index as the object index, chooses the corresponding color, and
creates a shape name `shape_00`, `shape_01`, and so on. Preserve ordering when
the intended object identity matters.

The validator rejects an empty line rather than silently dropping it because
the historical loader indexes raw `readlines()` entries. It also rejects extra
lines when an expected count is supplied. A file with fewer lines would cause
the loader to index past the available content; do not rely on a runtime error
to discover this mismatch.

## Mesh directory and path safety

Use approved external mesh names such as `0.obj` with
`--obj_mesh_dir <MESH_DIR>`. Do not put an absolute path in a preset. Let
`<skill-root>` mean the directory containing the root `SKILL.md`; `<CASE>`,
`<COUNT>`, and `<MESH_DIR>` are operator-supplied:

```shell
python <skill-root>/sub-skills/simulation/scripts/validate_test_case.py \
  <CASE> --expected-object-count <COUNT> --mesh-dir <MESH_DIR>
```

`--mesh-dir` is optional. Without it, the validator still checks the token
shape and numeric fields but cannot prove that a mesh exists. The external
simulator may assemble a path from the approved mesh directory and the preset
name; keep that directory trusted and read-only during testing. Never use a
preset as an opportunity to load arbitrary files. The runtime graph does not
contain source `objects/blocks` or source preset files.

## Colors, poses, and orientations

Colors are data sent to the scene's `importShape` callback, not CSS names or
0–255 integers. Convert 8-bit colors to normalized floats before authoring.
Positions are meters in the scene's robot frame. Orientations are the three
Euler values passed by the historical adapter; they are not quaternions and
need not be in `[-pi, pi]` for the static gate. A valid finite pose can still
put an object under the table, outside the camera, or in collision. Validate
those conditions in the scene with a manual, bounded trial.

## Authoring checklist

1. Choose `--num_obj` and the same number of object lines.
2. Use only approved `.obj` names from the mesh directory.
3. Write normalized RGB values and finite position/orientation values.
4. Validate with `--expected-object-count` and `--mesh-dir`.
5. Start the external scene manually, then run a short controlled test.
6. If objects import but the robot or camera is unstable, stop and diagnose the
   scene/API contract rather than editing numeric values blindly.

The validator is safe to run in CI or without V-REP/CoppeliaSim. It never
imports `robot.py`, `simulation.vrep`, `remoteApi.so`, or any simulator client.
