---
name: mujoco-menagerie
description: "Use MuJoCo Menagerie robot MJCF assets: choose models, load XML
  scenes, edit variants, and run contributor validation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MuJoCo Menagerie

Use this repo skill when a task involves the Google DeepMind **MuJoCo Menagerie** collection of curated MJCF robot, sensor, hand, gripper, drone, humanoid, quadruped, arm, and mobile-manipulator models.

Menagerie is not a normal Python import package. It is a repository of XML assets, meshes, README metadata, and maintainer scripts used with the `mujoco` Python package, `mujoco.viewer`, optional `robot_descriptions`, and repository validation tools.

## Route by task

- Use [model-catalog](sub-skills/model-catalog/) to choose a model directory, scene XML, variant XML, MJX XML, category, minimum MuJoCo version, or license/metadata entry.
- Use [model-loading](sub-skills/model-loading/) to compile an XML with MuJoCo, open a viewer, load through `robot_descriptions`, short-step a scene, or diagnose mesh/include/runtime warnings.
- Use [model-editing](sub-skills/model-editing/) to plan MJCF changes, attach grippers/hands, compose models with `MjSpec`, compute position-actuator gains, mirror hands, or manage MJX/actuator variants.
- Use [contribution-maintenance](sub-skills/contribution-maintenance/) to format XML, regenerate/check licenses, update the gallery, choose CI-equivalent checks, handle changelog/contributor policy, or prepare a PR.

## Quick prerequisites

For user workflows, install MuJoCo's Python bindings in the active environment:

```bash
python -m pip install "mujoco>=3.2.0"
python - <<'PY'
import mujoco
print(mujoco.__version__)
print(mujoco.MjModel.from_xml_string('<mujoco/>').nbody)
PY
```

For contributor workflows, Menagerie's docs expect `uv` plus the repo's own make targets:

```bash
make install   # one-time pre-commit setup
make check     # lint, format, license, XML checks
make test      # pytest model/structural tests
make all       # check + test
```

When working outside a Menagerie checkout or before running heavier checks, use the bundled environment helper:

```bash
python scripts/check_menagerie_environment.py
python scripts/check_menagerie_environment.py --xml /path/to/unitree_go2/scene.xml --step-seconds 0.02
```

## Operating rules

1. Return repository-relative model paths such as `unitree_go2/scene.xml` or user-supplied absolute XML paths. Do not rely on a hidden checkout path.
2. Keep an XML next to its sibling `assets/` or `meshes/` tree. Menagerie XMLs rely on relative mesh/include resolution from the XML location.
3. Prefer `scene*.xml` for complete simulation scenes and direct `<model>.xml` files for composition or embedding into another scene.
4. Treat `_mjx.xml` and `scene_mjx.xml` as explicit variants. Do not assume every model has an MJX counterpart.
5. Run small compile/smoke checks before expensive gallery rendering or full pytest.
6. For edits, write to explicit output files and validate with `model-loading` before running `contribution-maintenance` checks.

## Shared references

- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is stale for a checkout.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install, XML, asset, viewer, and validation failures.
- `references/repo-routing-metadata.json` contains structured router metadata for a future managed import; this run intentionally does not import the skill.

## Common handoffs

- **Pick and test a model:** `model-catalog` selects XML -> `model-loading` compiles/steps it.
- **Modify a robot model:** `model-editing` plans the XML/MjSpec change -> `model-loading` validates the result -> `contribution-maintenance` formats and selects repo checks.
- **Prepare a contribution:** `contribution-maintenance` creates the check plan -> `model-catalog` verifies new/changed model metadata -> `model-loading` covers selected compile/step checks.
