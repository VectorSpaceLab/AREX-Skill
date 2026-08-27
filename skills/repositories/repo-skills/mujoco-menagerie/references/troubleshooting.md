# Cross-Cutting Troubleshooting

## Purpose

Use this reference for failures that can appear across catalog, loading, editing, and contribution workflows. For route-specific failures, also read the nearest sub-skill troubleshooting file.

## `ModuleNotFoundError: mujoco` or incompatible MuJoCo version

Symptoms:
- `import mujoco` fails.
- `mujoco.MjModel.from_xml_path(...)` fails on XML that should be valid.
- A model README requires a newer MuJoCo release than the installed version.

Recovery:
1. Install or upgrade the bindings: `python -m pip install "mujoco>=3.2.0"`.
2. Re-run `python scripts/check_menagerie_environment.py`.
3. For per-model minimum versions, use `model-catalog` to check the bundled index or the model README metadata.
4. If a task specifically requires MJX/JAX execution, treat that as an additional environment requirement beyond this skill's default CPU MuJoCo coverage.

## XML moved without assets or includes

Symptoms:
- Compile errors mention a missing mesh, texture, include, STL, OBJ, or relative path.
- A copied `scene.xml` fails even though it worked in the original model directory.

Recovery:
1. Keep the XML in the same relative layout as its `assets/` or `meshes/` directory.
2. Prefer copying the entire model directory when sharing a Menagerie asset.
3. Use `model-catalog` to identify whether the chosen XML is a scene, direct model XML, variant, or sensor-only asset.
4. Use `sub-skills/model-loading/scripts/smoke_load_model.py` with the actual XML path to reproduce the compile error with a clear message.

## Viewer/OpenGL/headless failures

Symptoms:
- `python -m mujoco.viewer --mjcf ...` fails on a server or CI runner.
- OpenGL/GLFW/display errors appear before the XML itself is tested.

Recovery:
1. Separate viewer availability from XML validity: run a compile-only smoke first.
2. Use `model-loading` for script-based validation on headless machines.
3. Only launch the interactive viewer in a GUI-capable session.
4. For gallery rendering, use `contribution-maintenance` and expect heavier rendering dependencies.

## MuJoCo warnings after stepping

Symptoms:
- A short simulation compiles but reports `mjtWarning` counts.
- The repo-style compile/step test fails after applying controls.

Recovery:
1. Re-run with a smaller step duration to localize whether the warning appears immediately.
2. Check actuator ranges, joint limits, keyframes, contacts, and inertial properties.
3. If the XML was edited, use `model-editing` to review keyframe lengths and actuator references.
4. If validating a contribution, route the final check plan through `contribution-maintenance`.

## Stale skill or stale catalog snapshot

Symptoms:
- A current checkout has model directories or XML files not listed in `model-index.json`.
- The current commit differs from `references/repo-provenance.md`.

Recovery:
1. Use `sub-skills/model-catalog/scripts/inspect_model_catalog.py --repo-root <checkout> --markdown` to inspect the current checkout.
2. If the difference is material, refresh the repo skill before relying on the bundled catalog snapshot.
3. Do not silently combine old catalog metadata with new XML behavior.

## Contribution checks take too long

Symptoms:
- Full `make test` or gallery rendering exceeds the available time.
- The task only changed one XML or one license file.

Recovery:
1. Use `sub-skills/contribution-maintenance/scripts/menagerie_checklist.py` on changed paths to select targeted checks.
2. For XML-only edits, run formatting plus selected loading smoke before full tests.
3. Reserve `make gallery` for gallery-facing changes and `make all` for PR readiness or broader changes.
